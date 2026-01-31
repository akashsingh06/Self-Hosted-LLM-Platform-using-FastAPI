from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_current_user
from src.models.schemas import ModelInfo, User
from src.services.llm_service import LLMService

router = APIRouter()


@router.get("/", response_model=List[ModelInfo])
async def list_models(
    current_user: User = Depends(get_current_user),
    llm_service: LLMService = Depends(lambda: router.llm_service),
):
    """List available models"""
    try:
        models = await llm_service.get_available_models()
        return [
            ModelInfo(
                name=model["name"],
                model_type="code" if "coder" in model["name"].lower() else "chat",
                parameters=model.get("size", 0),
                context_size=model.get("context", 2048),
                description=model.get("description", ""),
                tags=model.get("tags", []),
                is_local=True,
                is_available=True,
            )
            for model in models
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pull/{model_name}")
async def pull_model(
    model_name: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    llm_service: LLMService = Depends(lambda: router.llm_service),
):
    """Pull a model to Ollama"""
    try:
        # Start pull in background
        background_tasks.add_task(llm_service.pull_model, model_name)
        
        return {
            "message": f"Started pulling model {model_name}",
            "model_name": model_name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{model_name}")
async def delete_model(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a model from Ollama"""
    # TODO: Implement model deletion
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/instances")
async def list_instances(
    current_user: User = Depends(get_current_user),
    llm_service: LLMService = Depends(lambda: router.llm_service),
):
    """List Ollama instances"""
    try:
        return llm_service.load_balancer.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))