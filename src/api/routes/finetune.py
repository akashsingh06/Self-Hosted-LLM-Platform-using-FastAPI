from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from loguru import logger

from src.api.deps import get_db, get_current_user
from src.models.schemas import (
    FinetuneJob,
    FinetuneJobCreate,
    FinetuneDataset,
    User,
)
from src.services.finetune_service import FinetuneService
from src.utils.file_utils import save_upload_file

router = APIRouter()


@router.post("/datasets", response_model=FinetuneDataset)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a dataset for fine-tuning"""
    try:
        # Validate file type
        allowed_extensions = {".jsonl", ".csv", ".txt", ".parquet"}
        file_ext = file.filename.split(".")[-1].lower()
        if f".{file_ext}" not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {allowed_extensions}"
            )
        
        # Save file
        file_path = await save_upload_file(
            file,
            prefix=f"datasets/{current_user.id}",
            allowed_extensions=allowed_extensions
        )
        
        # Create dataset record
        dataset = FinetuneDataset(
            name=name,
            description=description,
            format=file_ext,
            file_path=str(file_path),
            size=file.size,
        )
        
        # TODO: Store in database
        
        return dataset
        
    except Exception as e:
        logger.error(f"Dataset upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs", response_model=FinetuneJob)
async def create_finetune_job(
    job: FinetuneJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new fine-tuning job"""
    try:
        finetune_service = FinetuneService(db)
        
        # Verify dataset exists
        # TODO: Check dataset in database
        
        # Create job
        finetune_job = await finetune_service.create_finetune_job(
            user_id=current_user.id,
            base_model=job.base_model,
            dataset_path=job.dataset_id,  # TODO: Get actual path from dataset_id
            method=job.method,
            epochs=job.epochs,
            batch_size=job.batch_size,
            learning_rate=job.learning_rate,
            lora_rank=job.lora_rank,
            target_modules=job.target_modules,
        )
        
        return finetune_job
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Finetune job creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[FinetuneJob])
async def list_finetune_jobs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List fine-tuning jobs"""
    try:
        finetune_service = FinetuneService(db)
        jobs = await finetune_service.list_jobs(
            user_id=current_user.id,
            limit=limit,
            offset=skip
        )
        return jobs
    except Exception as e:
        logger.error(f"List jobs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=FinetuneJob)
async def get_finetune_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get fine-tuning job details"""
    try:
        finetune_service = FinetuneService(db)
        job = await finetune_service.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check permission
        if job.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def cancel_finetune_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a fine-tuning job"""
    try:
        finetune_service = FinetuneService(db)
        success = await finetune_service.cancel_job(job_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or permission denied")
        
        return {"message": "Job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel job error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/logs")
async def get_finetune_job_logs(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream fine-tuning job logs"""
    # TODO: Implement log streaming
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/models/templates")
async def get_finetune_templates():
    """Get fine-tuning templates"""
    return {
        "lora": {
            "description": "Low-Rank Adaptation - Efficient fine-tuning",
            "parameters": {
                "lora_rank": {"type": "int", "default": 16, "min": 4, "max": 128},
                "lora_alpha": {"type": "int", "default": 32},
                "target_modules": {"type": "list", "default": ["q_proj", "v_proj"]},
            }
        },
        "p_tuning": {
            "description": "P-Tuning - Continuous prompt optimization",
            "parameters": {
                "num_virtual_tokens": {"type": "int", "default": 20, "min": 1, "max": 100},
            }
        },
        "prefix_tuning": {
            "description": "Prefix Tuning - Optimize prefix tokens",
            "parameters": {
                "num_virtual_tokens": {"type": "int", "default": 20, "min": 1, "max": 100},
            }
        },
        "full": {
            "description": "Full fine-tuning - Train all parameters",
            "parameters": {}
        }
    }
