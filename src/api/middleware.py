from typing import Dict, Tuple
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import time

from src.config.settings import settings

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limits: Dict[str, Tuple[int, float]] = {}
        
    async def dispatch(self, request: Request, call_next):
        # Check rate limit
        client_ip = get_remote_address(request)
        current_time = time.time()
        
        # Get rate limit for endpoint
        endpoint_limit = self._get_endpoint_limit(request.url.path)
        if endpoint_limit:
            requests, window_start = self.rate_limits.get(client_ip, (0, current_time))
            
            # Reset if window has passed
            if current_time - window_start > 60:  # 1 minute window
                requests = 0
                window_start = current_time
            
            # Check if limit exceeded
            if requests >= endpoint_limit:
                return JSONResponse(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"}
                )
            
            # Update counter
            self.rate_limits[client_ip] = (requests + 1, window_start)
        
        # Add rate limit headers
        response = await call_next(request)
        if endpoint_limit:
            response.headers["X-RateLimit-Limit"] = str(endpoint_limit)
            response.headers["X-RateLimit-Remaining"] = str(endpoint_limit - requests - 1)
            response.headers["X-RateLimit-Reset"] = str(int(window_start + 60))
        
        return response
    
    def _get_endpoint_limit(self, path: str) -> int:
        """Get rate limit for specific endpoint"""
        if "/api/chat" in path:
            return settings.RATE_LIMIT_PER_MINUTE
        elif "/api/finetune" in path:
            return 10  # Lower limit for fine-tuning
        elif "/api/models" in path and "pull" in path:
            return 5  # Very low for model pulling
        return 0  # No limit for other endpoints


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log request
        from loguru import logger
        logger.info(
            f"{request.method} {request.url.path} "
            f"{response.status_code} {process_time:.3f}s"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
