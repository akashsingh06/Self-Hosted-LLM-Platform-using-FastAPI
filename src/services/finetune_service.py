import os
import json
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import asyncio
from concurrent.futures import ProcessPoolExecutor
import subprocess
import tempfile

import pandas as pd
from loguru import logger
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.models.schemas import FinetuneJob, FinetuneMethod
from src.database.models import FinetuneJob as FinetuneJobModel
from src.database.crud import update_finetune_job


class FinetuneService:
    """Service for fine-tuning LLM models"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.executor = ProcessPoolExecutor(max_workers=2)
        self.finetune_path = Path(settings.FINETUNE_STORAGE_PATH)
        self.finetune_path.mkdir(parents=True, exist_ok=True)
        
        # Training templates
        self.templates = {
            "lora": self._create_lora_config,
            "p_tuning": self._create_p_tuning_config,
            "prefix_tuning": self._create_prefix_tuning_config,
            "full": self._create_full_finetune_config,
        }
    
    async def create_finetune_job(
        self,
        user_id: int,
        base_model: str,
        dataset_path: str,
        method: FinetuneMethod = FinetuneMethod.LORA,
        epochs: int = 5,
        batch_size: int = 4,
        learning_rate: float = 2e-5,
        lora_rank: int = 16,
        target_modules: Optional[List[str]] = None,
        new_model_name: Optional[str] = None
    ) -> FinetuneJob:
        """Create a new fine-tuning job"""
        from src.database.crud import create_finetune_job as create_job
        
        # Generate model name if not provided
        if not new_model_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_model_name = f"{base_model.replace(':', '_')}_finetuned_{timestamp}"
        
        # Create job record
        job_data = {
            "user_id": user_id,
            "base_model": base_model,
            "new_model_name": new_model_name,
            "dataset_path": dataset_path,
            "method": method.value,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "lora_rank": lora_rank,
            "target_modules": target_modules or ["q_proj", "v_proj"],
            "status": "pending",
        }
        
        job = create_job(self.db, job_data)
        
        # Start training asynchronously
        asyncio.create_task(self._run_finetune_job(job.id))
        
        return FinetuneJob.from_orm(job)
    
    async def _run_finetune_job(self, job_id: int):
        """Run fine-tuning job in background"""
        from src.database.crud import get_finetune_job
        
        job = get_finetune_job(self.db, job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        try:
            # Update status to running
            update_finetune_job(
                self.db,
                job_id,
                {"status": "running", "started_at": datetime.now()}
            )
            
            # Prepare dataset
            dataset = await self._prepare_dataset(job.dataset_path, job.base_model)
            
            # Create training configuration
            config = self.templates[job.method](
                base_model=job.base_model,
                dataset=dataset,
                epochs=job.epochs,
                batch_size=job.batch_size,
                learning_rate=job.learning_rate,
                lora_rank=job.lora_rank,
                target_modules=job.target_modules,
                output_dir=str(self.finetune_path / job.new_model_name)
            )
            
            # Save config
            config_path = self.finetune_path / f"{job.new_model_name}_config.json"
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            
            # Run training (in separate process)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._train_model,
                config_path,
                job.id
            )
            
            # Update job status
            if result["success"]:
                update_finetune_job(
                    self.db,
                    job_id,
                    {
                        "status": "completed",
                        "completed_at": datetime.now(),
                        "epochs_completed": job.epochs,
                        "loss_history": result.get("loss_history", []),
                        "metrics": result.get("metrics", {}),
                    }
                )
                
                # Push model to Ollama
                await self._push_to_ollama(job.new_model_name, result["model_path"])
                
                logger.info(f"Finetune job {job_id} completed successfully")
            else:
                update_finetune_job(
                    self.db,
                    job_id,
                    {
                        "status": "failed",
                        "completed_at": datetime.now(),
                        "error_message": result.get("error", "Unknown error"),
                    }
                )
                logger.error(f"Finetune job {job_id} failed: {result.get('error')}")
                
        except Exception as e:
            logger.exception(f"Error in finetune job {job_id}: {e}")
            update_finetune_job(
                self.db,
                job_id,
                {
                    "status": "failed",
                    "completed_at": datetime.now(),
                    "error_message": str(e),
                }
            )
    
    async def _prepare_dataset(self, dataset_path: str, base_model: str) -> Dict[str, Any]:
        """Prepare dataset for fine-tuning"""
        path = Path(dataset_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
        
        # Support multiple formats
        if path.suffix == ".jsonl":
            with open(path, "r") as f:
                lines = [json.loads(line) for line in f]
            
            # Convert to conversation format
            conversations = []
            for item in lines:
                if "conversations" in item:
                    conversations.append(item["conversations"])
                elif "messages" in item:
                    conversations.append(item["messages"])
                else:
                    # Assume it's already in the right format
                    conversations.append(item)
            
            return {
                "format": "conversation",
                "data": conversations,
                "size": len(conversations),
            }
        
        elif path.suffix == ".csv":
            df = pd.read_csv(path)
            # Assume columns: prompt, completion
            conversations = []
            for _, row in df.iterrows():
                conversations.append([
                    {"role": "user", "content": row["prompt"]},
                    {"role": "assistant", "content": row["completion"]}
                ])
            
            return {
                "format": "conversation",
                "data": conversations,
                "size": len(conversations),
            }
        
        else:
            raise ValueError(f"Unsupported dataset format: {path.suffix}")
    
    def _create_lora_config(
        self,
        base_model: str,
        dataset: Dict[str, Any],
        epochs: int,
        batch_size: int,
        learning_rate: float,
        lora_rank: int,
        target_modules: List[str],
        output_dir: str
    ) -> Dict[str, Any]:
        """Create LoRA configuration"""
        return {
            "model_type": "lora",
            "base_model": base_model,
            "dataset": dataset,
            "training_args": {
                "num_train_epochs": epochs,
                "per_device_train_batch_size": batch_size,
                "learning_rate": learning_rate,
                "warmup_steps": 100,
                "logging_steps": 10,
                "save_steps": 100,
                "eval_steps": 100,
                "output_dir": output_dir,
                "overwrite_output_dir": True,
                "save_total_limit": 2,
                "load_best_model_at_end": True,
                "metric_for_best_model": "loss",
                "greater_is_better": False,
            },
            "lora_config": {
                "r": lora_rank,
                "lora_alpha": 32,
                "target_modules": target_modules,
                "lora_dropout": 0.1,
                "bias": "none",
                "task_type": "CAUSAL_LM",
            },
            "data_collator": {
                "type": "default",
                "padding": True,
                "max_length": 2048,
            }
        }
    
    def _create_p_tuning_config(self, **kwargs) -> Dict[str, Any]:
        """Create P-Tuning configuration"""
        config = self._create_lora_config(**kwargs)
        config["model_type"] = "p_tuning"
        config["p_tuning_config"] = {
            "encoder_hidden_size": 128,
            "num_virtual_tokens": 20,
            "num_transformer_submodules": 1,
        }
        return config
    
    def _create_prefix_tuning_config(self, **kwargs) -> Dict[str, Any]:
        """Create Prefix Tuning configuration"""
        config = self._create_lora_config(**kwargs)
        config["model_type"] = "prefix_tuning"
        config["prefix_tuning_config"] = {
            "num_virtual_tokens": 20,
            "encoder_hidden_size": 128,
        }
        return config
    
    def _create_full_finetune_config(self, **kwargs) -> Dict[str, Any]:
        """Create full fine-tuning configuration"""
        config = self._create_lora_config(**kwargs)
        config["model_type"] = "full"
        del config["lora_config"]
        config["training_args"]["learning_rate"] = kwargs["learning_rate"] * 0.1  # Lower LR for full finetune
        return config
    
    def _train_model(self, config_path: str, job_id: int) -> Dict[str, Any]:
        """Train model using transformers/peft"""
        try:
            import torch
            from transformers import (
                AutoModelForCausalLM,
                AutoTokenizer,
                TrainingArguments,
                Trainer,
                DataCollatorForLanguageModeling,
            )
            from peft import LoraConfig, get_peft_model, TaskType
            from datasets import Dataset
            
            # Load config
            with open(config_path, "r") as f:
                config = json.load(f)
            
            # Load model and tokenizer
            model_name = config["base_model"].replace("ollama/", "")
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
            )
            
            # Add padding token if not present
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Prepare dataset
            def tokenize_function(examples):
                texts = []
                for conv in examples["conversations"]:
                    text = ""
                    for msg in conv:
                        text += f"{msg['role']}: {msg['content']}\n"
                    texts.append(text)
                
                return tokenizer(
                    texts,
                    truncation=True,
                    padding="max_length",
                    max_length=512,
                )
            
            dataset_dict = {
                "conversations": config["dataset"]["data"]
            }
            dataset = Dataset.from_dict(dataset_dict)
            tokenized_dataset = dataset.map(tokenize_function, batched=True)
            
            # Apply PEFT if needed
            if config["model_type"] in ["lora", "p_tuning", "prefix_tuning"]:
                if config["model_type"] == "lora":
                    peft_config = LoraConfig(
                        task_type=TaskType.CAUSAL_LM,
                        **config["lora_config"]
                    )
                elif config["model_type"] == "p_tuning":
                    from peft import PromptEncoderConfig
                    peft_config = PromptEncoderConfig(
                        task_type=TaskType.CAUSAL_LM,
                        **config.get("p_tuning_config", {})
                    )
                elif config["model_type"] == "prefix_tuning":
                    from peft import PrefixTuningConfig
                    peft_config = PrefixTuningConfig(
                        task_type=TaskType.CAUSAL_LM,
                        **config.get("prefix_tuning_config", {})
                    )
                
                model = get_peft_model(model, peft_config)
                model.print_trainable_parameters()
            
            # Training arguments
            training_args = TrainingArguments(**config["training_args"])
            
            # Data collator
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer,
                mlm=False,
            )
            
            # Trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset,
                data_collator=data_collator,
            )
            
            # Train
            train_result = trainer.train()
            
            # Save model
            output_dir = Path(config["training_args"]["output_dir"])
            trainer.save_model(str(output_dir))
            tokenizer.save_pretrained(str(output_dir))
            
            # Save training metrics
            metrics = train_result.metrics
            metrics["train_samples"] = len(tokenized_dataset)
            
            # Create Modelfile for Ollama
            self._create_modelfile(output_dir, config["base_model"])
            
            return {
                "success": True,
                "model_path": str(output_dir),
                "loss_history": trainer.state.log_history,
                "metrics": metrics,
            }
            
        except Exception as e:
            logger.exception(f"Training error: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def _create_modelfile(self, model_dir: Path, base_model: str):
        """Create Modelfile for Ollama"""
        modelfile_content = f"""FROM {base_model}

# System prompt
SYSTEM You are a fine-tuned version of {base_model}

# Copy fine-tuned weights
COPY ./pytorch_model.bin /pytorch_model.bin
COPY ./adapter_config.json /adapter_config.json
COPY ./adapter_model.bin /adapter_model.bin

# Parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
"""
        
        with open(model_dir / "Modelfile", "w") as f:
            f.write(modelfile_content)
    
    async def _push_to_ollama(self, model_name: str, model_path: str):
        """Push fine-tuned model to Ollama"""
        try:
            import httpx
            
            # Create a temporary tar file
            import tarfile
            temp_dir = Path(tempfile.mkdtemp())
            tar_path = temp_dir / f"{model_name}.tar"
            
            with tarfile.open(tar_path, "w") as tar:
                tar.add(model_path, arcname=os.path.basename(model_path))
            
            # Push to Ollama
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(tar_path, "rb") as f:
                    files = {"file": (f"{model_name}.tar", f, "application/x-tar")}
                    response = await client.post(
                        f"{settings.OLLAMA_BASE_URL}/api/create",
                        files=files,
                        data={"name": model_name}
                    )
                
                if response.status_code == 200:
                    logger.info(f"Model {model_name} pushed to Ollama successfully")
                else:
                    logger.error(f"Failed to push model to Ollama: {response.text}")
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
        except Exception as e:
            logger.error(f"Error pushing model to Ollama: {e}")
    
    async def get_job_status(self, job_id: int) -> Optional[FinetuneJob]:
        """Get fine-tuning job status"""
        from src.database.crud import get_finetune_job
        
        job = get_finetune_job(self.db, job_id)
        if job:
            return FinetuneJob.from_orm(job)
        return None
    
    async def list_jobs(
        self,
        user_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[FinetuneJob]:
        """List fine-tuning jobs"""
        from src.database.crud import list_finetune_jobs
        
        jobs = list_finetune_jobs(self.db, user_id, limit, offset)
        return [FinetuneJob.from_orm(job) for job in jobs]
    
    async def cancel_job(self, job_id: int, user_id: Optional[int] = None) -> bool:
        """Cancel a fine-tuning job"""
        from src.database.crud import update_finetune_job, get_finetune_job
        
        job = get_finetune_job(self.db, job_id)
        if not job:
            return False
        
        if user_id and job.user_id != user_id:
            return False
        
        update_finetune_job(
            self.db,
            job_id,
            {"status": "cancelled", "completed_at": datetime.now()}
        )
        
        # TODO: Actually stop the training process
        
        return True
