import asyncio
import json
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import aioredis
from loguru import logger

from src.config.settings import settings


class CacheService:
    """Redis-based caching service"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.prefix = "llm:cache:"
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.errors = 0
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.REDIS_POOL_SIZE,
            )
            await self.redis.ping()
            logger.info("Cache service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize cache service: {e}")
            self.redis = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis:
            return None
        
        try:
            full_key = f"{self.prefix}{key}"
            value = await self.redis.get(full_key)
            
            if value:
                self.hits += 1
                return json.loads(value)
            else:
                self.misses += 1
                return None
                
        except Exception as e:
            self.errors += 1
            logger.warning(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        if not self.redis:
            return False
        
        try:
            full_key = f"{self.prefix}{key}"
            ttl = ttl or settings.CACHE_TTL
            
            serialized = json.dumps(value)
            await self.redis.setex(full_key, ttl, serialized)
            return True
            
        except Exception as e:
            self.errors += 1
            logger.warning(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.redis:
            return False
        
        try:
            full_key = f"{self.prefix}{key}"
            await self.redis.delete(full_key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False
    
    async def clear_prefix(self, prefix: str) -> int:
        """Clear all keys with prefix"""
        if not self.redis:
            return 0
        
        try:
            pattern = f"{self.prefix}{prefix}*"
            keys = await self.redis.keys(pattern)
            
            if keys:
                await self.redis.delete(*keys)
            
            return len(keys)
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis:
            return {"status": "disconnected"}
        
        try:
            # Get Redis info
            info = await self.redis.info()
            
            # Count keys with our prefix
            pattern = f"{self.prefix}*"
            keys = await self.redis.keys(pattern)
            
            return {
                "status": "connected",
                "hits": self.hits,
                "misses": self.misses,
                "errors": self.errors,
                "hit_rate": (
                    self.hits / (self.hits + self.misses) * 100
                    if (self.hits + self.misses) > 0 else 0
                ),
                "key_count": len(keys),
                "memory_used": info.get("used_memory_human", "N/A"),
                "connections": info.get("connected_clients", 0),
                "uptime": info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Cache service closed")
