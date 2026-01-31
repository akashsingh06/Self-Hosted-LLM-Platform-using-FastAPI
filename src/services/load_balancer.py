from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import random
import statistics
from enum import Enum
from loguru import logger


class LoadBalancerStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    WEIGHTED = "weighted"


@dataclass
class InstanceMetrics:
    instance_id: str
    url: str
    active_connections: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0
    average_response_time: float = 0
    total_tokens: int = 0
    last_request_time: Optional[datetime] = None
    last_error_time: Optional[datetime] = None
    error_count: int = 0
    is_healthy: bool = True
    health_check_failures: int = 0
    weight: float = 1.0


class LoadBalancer:
    """Load balancer for multiple Ollama instances"""
    
    def __init__(self, strategy: LoadBalancerStrategy = LoadBalancerStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.instances: Dict[str, InstanceMetrics] = {}
        self.instance_list: List[str] = []
        self.current_index = 0
        self.lock = asyncio.Lock()
        self.health_check_interval = 30  # seconds
        
        # Statistics
        self.total_requests = 0
        self.request_distribution: Dict[str, int] = {}
    
    async def initialize(self):
        """Initialize load balancer with instances from settings"""
        from src.config.settings import settings
        
        # Parse Ollama instances
        if settings.OLLAMA_INSTANCES:
            instances = settings.OLLAMA_INSTANCES
        else:
            instances = [settings.OLLAMA_BASE_URL]
        
        # Add instances
        for i, url in enumerate(instances):
            instance_id = f"ollama-{i+1}"
            await self.add_instance(instance_id, url)
        
        # Start health checks
        asyncio.create_task(self._health_check_task())
        logger.info(f"Load balancer initialized with {len(self.instances)} instances")
    
    async def add_instance(self, instance_id: str, url: str, weight: float = 1.0):
        """Add an instance to load balancer"""
        async with self.lock:
            if instance_id in self.instances:
                return
            
            self.instances[instance_id] = InstanceMetrics(
                instance_id=instance_id,
                url=url.rstrip("/"),
                weight=weight
            )
            self.instance_list.append(instance_id)
            self.request_distribution[instance_id] = 0
            logger.info(f"Added instance {instance_id} ({url}) to load balancer")
    
    async def remove_instance(self, instance_id: str):
        """Remove an instance from load balancer"""
        async with self.lock:
            if instance_id in self.instances:
                del self.instances[instance_id]
                self.instance_list.remove(instance_id)
                del self.request_distribution[instance_id]
                logger.info(f"Removed instance {instance_id} from load balancer")
    
    async def get_instance(self) -> InstanceMetrics:
        """Get an instance based on load balancing strategy"""
        async with self.lock:
            self.total_requests += 1
            
            if not self.instances:
                raise RuntimeError("No instances available")
            
            # Filter healthy instances
            healthy_instances = [
                inst for inst in self.instances.values()
                if inst.is_healthy
            ]
            
            if not healthy_instances:
                # Fallback to any instance
                healthy_instances = list(self.instances.values())
            
            # Select instance based on strategy
            if self.strategy == LoadBalancerStrategy.ROUND_ROBIN:
                instance = await self._round_robin_select(healthy_instances)
            elif self.strategy == LoadBalancerStrategy.LEAST_CONNECTIONS:
                instance = await self._least_connections_select(healthy_instances)
            elif self.strategy == LoadBalancerStrategy.RANDOM:
                instance = await self._random_select(healthy_instances)
            elif self.strategy == LoadBalancerStrategy.WEIGHTED:
                instance = await self._weighted_select(healthy_instances)
            else:
                instance = await self._round_robin_select(healthy_instances)
            
            # Update metrics
            instance.active_connections += 1
            instance.total_requests += 1
            instance.last_request_time = datetime.now()
            self.request_distribution[instance.instance_id] += 1
            
            return instance
    
    async def _round_robin_select(self, instances: List[InstanceMetrics]) -> InstanceMetrics:
        """Round robin selection"""
        if self.current_index >= len(instances):
            self.current_index = 0
        
        instance = instances[self.current_index]
        self.current_index += 1
        return instance
    
    async def _least_connections_select(self, instances: List[InstanceMetrics]) -> InstanceMetrics:
        """Select instance with least active connections"""
        return min(instances, key=lambda x: x.active_connections)
    
    async def _random_select(self, instances: List[InstanceMetrics]) -> InstanceMetrics:
        """Random selection"""
        return random.choice(instances)
    
    async def _weighted_select(self, instances: List[InstanceMetrics]) -> InstanceMetrics:
        """Weighted random selection"""
        weights = [inst.weight for inst in instances]
        return random.choices(instances, weights=weights, k=1)[0]
    
    async def release_instance(self, instance_id: str):
        """Release an instance (decrement active connections)"""
        async with self.lock:
            if instance_id in self.instances:
                self.instances[instance_id].active_connections = max(
                    0, self.instances[instance_id].active_connections - 1
                )
    
    async def update_metrics(
        self,
        instance_id: str,
        success: bool,
        response_time: float,
        tokens_used: int = 0
    ):
        """Update instance metrics after request"""
        async with self.lock:
            if instance_id in self.instances:
                instance = self.instances[instance_id]
                instance.active_connections = max(0, instance.active_connections - 1)
                
                if success:
                    instance.successful_requests += 1
                    instance.total_response_time += response_time
                    instance.total_tokens += tokens_used
                    
                    # Update average response time
                    if instance.successful_requests > 0:
                        instance.average_response_time = (
                            instance.total_response_time / instance.successful_requests
                        )
                    
                    # Reset error count on success
                    instance.error_count = 0
                else:
                    instance.failed_requests += 1
                    instance.error_count += 1
                    instance.last_error_time = datetime.now()
                    
                    # Mark as unhealthy if too many errors
                    if instance.error_count >= 5:
                        instance.is_healthy = False
                        logger.warning(f"Instance {instance_id} marked as unhealthy")
    
    async def mark_unhealthy(self, instance_id: str):
        """Mark instance as unhealthy"""
        async with self.lock:
            if instance_id in self.instances:
                self.instances[instance_id].is_healthy = False
                self.instances[instance_id].health_check_failures += 1
    
    async def mark_healthy(self, instance_id: str):
        """Mark instance as healthy"""
        async with self.lock:
            if instance_id in self.instances:
                self.instances[instance_id].is_healthy = True
                self.instances[instance_id].health_check_failures = 0
    
    async def get_instance_by_id(self, instance_id: str) -> Optional[InstanceMetrics]:
        """Get instance by ID"""
        return self.instances.get(instance_id)
    
    def get_all_instances(self) -> List[InstanceMetrics]:
        """Get all instances"""
        return list(self.instances.values())
    
    async def _health_check_task(self):
        """Background task for health checking"""
        import httpx
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            while True:
                try:
                    await self._perform_health_checks(client)
                except Exception as e:
                    logger.error(f"Health check error: {e}")
                
                await asyncio.sleep(self.health_check_interval)
    
    async def _perform_health_checks(self, client: httpx.AsyncClient):
        """Perform health checks on all instances"""
        tasks = []
        for instance in self.instances.values():
            task = self._check_instance_health(client, instance)
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_instance_health(self, client: httpx.AsyncClient, instance: InstanceMetrics):
        """Check health of a single instance"""
        try:
            response = await client.get(f"{instance.url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                if not instance.is_healthy:
                    await self.mark_healthy(instance.instance_id)
                    logger.info(f"Instance {instance.instance_id} is now healthy")
            else:
                await self.mark_unhealthy(instance.instance_id)
                logger.warning(f"Instance {instance.instance_id} health check failed: {response.status_code}")
        except Exception as e:
            await self.mark_unhealthy(instance.instance_id)
            logger.warning(f"Instance {instance.instance_id} health check error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        total_instances = len(self.instances)
        healthy_instances = sum(1 for inst in self.instances.values() if inst.is_healthy)
        
        # Calculate distribution percentages
        distribution = {}
        if self.total_requests > 0:
            for instance_id, count in self.request_distribution.items():
                distribution[instance_id] = (count / self.total_requests) * 100
        
        # Calculate average metrics
        response_times = [
            inst.average_response_time for inst in self.instances.values()
            if inst.average_response_time > 0
        ]
        
        return {
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "unhealthy_instances": total_instances - healthy_instances,
            "total_requests": self.total_requests,
            "request_distribution": distribution,
            "average_response_time": statistics.mean(response_times) if response_times else 0,
            "total_tokens_served": sum(inst.total_tokens for inst in self.instances.values()),
            "instances": [
                {
                    "id": inst.instance_id,
                    "url": inst.url,
                    "is_healthy": inst.is_healthy,
                    "active_connections": inst.active_connections,
                    "total_requests": inst.total_requests,
                    "success_rate": (
                        inst.successful_requests / inst.total_requests * 100
                        if inst.total_requests > 0 else 0
                    ),
                    "average_response_time": inst.average_response_time,
                    "error_count": inst.error_count,
                    "weight": inst.weight,
                }
                for inst in self.instances.values()
            ]
        }
    
    async def close(self):
        """Cleanup resources"""
        # Nothing to cleanup for now
        pass
