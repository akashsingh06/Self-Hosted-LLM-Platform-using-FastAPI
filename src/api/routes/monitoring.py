from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_current_admin_user
from src.models.schemas import SystemStatus, User
from src.services.llm_service import LLMService
from src.services.cache_service import CacheService

router = APIRouter()


@router.get("/stats", response_model=SystemStatus)
async def get_system_stats(
    current_user: User = Depends(get_current_admin_user),
    llm_service: LLMService = Depends(lambda: router.llm_service),
    cache_service: CacheService = Depends(lambda: router.cache_service),
):
    """Get system statistics"""
    try:
        import psutil
        from datetime import datetime
        
        # Get service stats
        llm_stats = llm_service.get_stats()
        cache_stats = await cache_service.get_stats()
        
        # System metrics
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        
        return SystemStatus(
            api_healthy=True,
            database_healthy=True,
            redis_healthy=cache_stats.get("status") == "connected",
            ollama_healthy=llm_stats.get("healthy_instances", 0) > 0,
            ollama_instances=llm_stats.get("instances", []),
            active_users=0,  # TODO: Track active users
            active_conversations=0,  # TODO: Track active conversations
            total_requests_today=llm_stats.get("total_requests", 0),
            average_response_time=llm_stats.get("average_response_time", 0),
            cache_hit_rate=llm_stats.get("cache_hit_rate", 0),
            memory_usage=memory.percent,
            cpu_usage=cpu,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_prometheus_metrics():
    """Get Prometheus metrics"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@router.get("/logs")
async def get_logs(
    lines: int = 100,
    current_user: User = Depends(get_current_admin_user),
):
    """Get application logs"""
    try:
        from pathlib import Path
        
        log_file = Path("logs/app.log")
        if not log_file.exists():
            return {"logs": []}
        
        with open(log_file, "r") as f:
            log_lines = f.readlines()[-lines:]
        
        return {"logs": log_lines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
