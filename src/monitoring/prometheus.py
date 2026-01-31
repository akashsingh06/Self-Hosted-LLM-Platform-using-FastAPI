from prometheus_client import Counter, Histogram, Gauge, Summary
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_fastapi_instrumentator.metrics import Info


# Custom metrics
llm_requests_total = Counter(
    "llm_requests_total",
    "Total number of LLM requests",
    ["model", "endpoint", "status"]
)

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total tokens processed",
    ["model", "endpoint"]
)

llm_response_time = Histogram(
    "llm_response_time_seconds",
    "LLM response time in seconds",
    ["model", "endpoint"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)

cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"]
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"]
)

finetune_jobs_total = Counter(
    "finetune_jobs_total",
    "Total fine-tuning jobs",
    ["status", "model"]
)

finetune_job_duration = Histogram(
    "finetune_job_duration_seconds",
    "Fine-tuning job duration in seconds",
    ["model", "method"],
    buckets=(60.0, 300.0, 600.0, 1800.0, 3600.0, 7200.0, 18000.0)
)

active_conversations = Gauge(
    "active_conversations_total",
    "Number of active conversations"
)

active_users = Gauge(
    "active_users_total",
    "Number of active users"
)

system_memory_usage = Gauge(
    "system_memory_usage_percent",
    "System memory usage percentage"
)

system_cpu_usage = Gauge(
    "system_cpu_usage_percent",
    "System CPU usage percentage"
)

database_connections = Gauge(
    "database_connections_total",
    "Number of database connections"
)

redis_memory_usage = Gauge(
    "redis_memory_usage_bytes",
    "Redis memory usage in bytes"
)


def add_custom_metrics():
    """Add custom metrics to instrumentator"""
    
    def latency_metric(info: Info) -> None:
        """Custom latency metric"""
        if info.modified_handler == "/api/chat":
            model = info.request.query_params.get("model", "default")
            llm_response_time.labels(
                model=model,
                endpoint=info.modified_handler
            ).observe(info.modified_duration)
    
    def requests_metric(info: Info) -> None:
        """Custom requests metric"""
        if info.modified_handler == "/api/chat":
            model = info.request.query_params.get("model", "default")
            status = "success" if info.modified_status < 400 else "error"
            llm_requests_total.labels(
                model=model,
                endpoint=info.modified_handler,
                status=status
            ).inc()
    
    def tokens_metric(info: Info) -> None:
        """Custom tokens metric"""
        # This would be updated from the LLM service
        pass
    
    return [latency_metric, requests_metric, tokens_metric]


def setup_monitoring(app):
    """Setup Prometheus monitoring"""
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="inprogress",
        inprogress_labels=True,
    )
    
    # Add default metrics
    instrumentator.add(
        metrics.request_size(
            should_include_handler=True,
            should_include_method=True,
            should_include_status=True,
            metric_namespace="llm",
            metric_subsystem="http",
        )
    )
    
    instrumentator.add(
        metrics.response_size(
            should_include_handler=True,
            should_include_method=True,
            should_include_status=True,
            metric_namespace="llm",
            metric_subsystem="http",
        )
    )
    
    instrumentator.add(
        metrics.latency(
            should_include_handler=True,
            should_include_method=True,
            should_include_status=True,
            metric_namespace="llm",
            metric_subsystem="http",
        )
    )
    
    # Add custom metrics
    for metric in add_custom_metrics():
        instrumentator.add(metric)
    
    # Instrument the app
    instrumentator.instrument(app).expose(app, include_in_schema=False)
    
    return instrumentator


class MetricsCollector:
    """Collect system and application metrics"""
    
    @staticmethod
    async def collect_system_metrics():
        """Collect system metrics"""
        import psutil
        
        # Memory usage
        memory = psutil.virtual_memory()
        system_memory_usage.set(memory.percent)
        
        # CPU usage
        cpu = psutil.cpu_percent(interval=1)
        system_cpu_usage.set(cpu)
        
        # Disk usage
        disk = psutil.disk_usage("/")
        Gauge(
            "system_disk_usage_percent",
            "System disk usage percentage"
        ).set(disk.percent)
        
        # Network I/O
        net_io = psutil.net_io_counters()
        Gauge(
            "network_bytes_sent_total",
            "Total bytes sent"
        ).set(net_io.bytes_sent)
        
        Gauge(
            "network_bytes_recv_total",
            "Total bytes received"
        ).set(net_io.bytes_recv)
    
    @staticmethod
    def update_conversation_metrics(count: int):
        """Update conversation metrics"""
        active_conversations.set(count)
    
    @staticmethod
    def update_user_metrics(count: int):
        """Update user metrics"""
        active_users.set(count)
    
    @staticmethod
    def update_cache_metrics(hits: int, misses: int):
        """Update cache metrics"""
        cache_hits_total.labels(cache_type="response").inc(hits)
        cache_misses_total.labels(cache_type="response").inc(misses)
    
    @staticmethod
    def update_llm_metrics(model: str, tokens: int, response_time: float):
        """Update LLM metrics"""
        llm_tokens_total.labels(
            model=model,
            endpoint="chat"
        ).inc(tokens)
        
        llm_response_time.labels(
            model=model,
            endpoint="chat"
        ).observe(response_time)
    
    @staticmethod
    def update_finetune_metrics(job_id: int, model: str, method: str, duration: float):
        """Update fine-tuning metrics"""
        finetune_jobs_total.labels(
            status="completed",
            model=model
        ).inc()
        
        finetune_job_duration.labels(
            model=model,
            method=method
        ).observe(duration)
