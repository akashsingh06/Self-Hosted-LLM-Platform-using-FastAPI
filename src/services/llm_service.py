import asyncio
import json
import hashlib
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import settings
from src.services.cache_service import CacheService
from src.services.load_balancer import LoadBalancer
from src.utils.code_extractor import CodeExtractor


class LLMService:
    """Robust LLM service with load balancing and caching"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.load_balancer = LoadBalancer()
        self.code_extractor = CodeExtractor()
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "errors": 0,
            "total_tokens": 0,
        }
    
    async def initialize(self):
        """Initialize service"""
        await self.load_balancer.initialize()
        logger.info(f"LLM Service initialized with {len(self.load_balancer.instances)} instances")
    
    async def close(self):
        """Cleanup resources"""
        await self.http_client.aclose()
        await self.load_balancer.close()
    
    def _generate_cache_key(self, prompt: str, model: str, **kwargs) -> str:
        """Generate cache key for prompt"""
        key_data = f"{model}:{prompt}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        cache: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Generate text with load balancing and caching
        """
        self.stats["total_requests"] += 1
        model = model or settings.DEFAULT_MODEL
        temperature = temperature or settings.TEMPERATURE
        max_tokens = max_tokens or settings.MAX_TOKENS
        
        # Check cache
        if cache and not stream:
            cache_key = self._generate_cache_key(
                prompt, model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            cached = await self.cache_service.get(cache_key)
            if cached:
                self.stats["cache_hits"] += 1
                logger.debug(f"Cache hit for key: {cache_key[:16]}")
                yield cached
                return
        
        # Get instance from load balancer
        instance = await self.load_balancer.get_instance()
        
        # Prepare request
        url = f"{instance.url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        try:
            start_time = datetime.now()
            
            if stream:
                async with self.http_client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    full_response = ""
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    chunk = data["response"]
                                    full_response += chunk
                                    yield chunk
                                if data.get("done", False):
                                    # Update instance metrics
                                    await self.load_balancer.update_metrics(
                                        instance.id,
                                        success=True,
                                        response_time=(datetime.now() - start_time).total_seconds(),
                                        tokens_used=data.get("total_tokens", 0)
                                    )
                                    self.stats["total_tokens"] += data.get("total_tokens", 0)
                                    break
                            except json.JSONDecodeError:
                                continue
            else:
                response = await self.http_client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                full_response = data.get("response", "")
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Update instance metrics
                await self.load_balancer.update_metrics(
                    instance.id,
                    success=True,
                    response_time=processing_time,
                    tokens_used=data.get("total_tokens", 0)
                )
                
                self.stats["total_tokens"] += data.get("total_tokens", 0)
                
                # Cache the response
                if cache:
                    cache_key = self._generate_cache_key(
                        prompt, model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    await self.cache_service.set(cache_key, full_response, ttl=settings.CACHE_TTL)
                
                yield full_response
                
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error generating with instance {instance.id}: {e}")
            
            # Mark instance as unhealthy
            await self.load_balancer.mark_unhealthy(instance.id)
            
            # Retry with another instance
            if not stream:
                raise
            else:
                yield f"Error: Failed to generate response. {str(e)}"
    
    async def get_available_models(self, instance_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available models from Ollama instances"""
        models = []
        
        if instance_id:
            instances = [await self.load_balancer.get_instance_by_id(instance_id)]
        else:
            instances = self.load_balancer.get_all_instances()
        
        for instance in instances:
            try:
                response = await self.http_client.get(f"{instance.url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    for model_info in data.get("models", []):
                        model_info["instance_id"] = instance.id
                        model_info["instance_url"] = instance.url
                        models.append(model_info)
            except Exception as e:
                logger.warning(f"Failed to get models from {instance.id}: {e}")
        
        return models
    
    async def pull_model(self, model_name: str, instance_id: Optional[str] = None):
        """Pull a model to Ollama instances"""
        if instance_id:
            instances = [await self.load_balancer.get_instance_by_id(instance_id)]
        else:
            instances = self.load_balancer.get_all_instances()
        
        tasks = []
        for instance in instances:
            task = self._pull_model_to_instance(instance, model_name)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def _pull_model_to_instance(self, instance, model_name: str):
        """Pull model to specific instance"""
        try:
            url = f"{instance.url}/api/pull"
            payload = {"name": model_name}
            
            async with self.http_client.stream("POST", url, json=payload) as response:
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if data.get("status") == "success":
                                logger.info(f"Model {model_name} pulled to {instance.id}")
                                return {"instance": instance.id, "status": "success"}
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Failed to pull model to {instance.id}: {e}")
            return {"instance": instance.id, "status": "error", "error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        cache_stats = self.cache_service.get_stats()
        load_balancer_stats = self.load_balancer.get_stats()
        
        return {
            **self.stats,
            "cache_stats": cache_stats,
            "load_balancer_stats": load_balancer_stats,
            "cache_hit_rate": (
                self.stats["cache_hits"] / self.stats["total_requests"]
                if self.stats["total_requests"] > 0 else 0
            )
        }
