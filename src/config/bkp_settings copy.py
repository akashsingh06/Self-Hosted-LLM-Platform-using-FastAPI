from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import secrets


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Local LLM Platform"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(32)
    API_KEY: str = "default-api-key"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    LOG_LEVEL: str = "info"
    
    # Database
    DATABASE_URL: str = "postgresql://llm_user:llm_password@localhost:5432/llm_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 10
    CACHE_TTL: int = 3600
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_INSTANCES: List[str] = []  # Changed to empty list default
    DEFAULT_MODEL: str = "deepseek-coder:6.7b"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7
    
    # Load Balancing
    LOAD_BALANCER_STRATEGY: str = "round_robin"  # round_robin, least_connections, random
    
    # Fine-tuning
    FINETUNE_STORAGE_PATH: str = "./data/finetune"
    FINETUNE_MAX_EPOCHS: int = 10
    FINETUNE_BATCH_SIZE: int = 4
    FINETUNE_LEARNING_RATE: float = 2e-5
    FINETUNE_DEVICE: str = "cuda"  # or "cpu"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Monitoring
    METRICS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    
    # Storage
    UPLOAD_PATH: str = "./data/uploads"
    EXPORT_PATH: str = "./data/exports"
    LOG_PATH: str = "./data/logs"
    
    # Security
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    BCRYPT_ROUNDS: int = 12
    
    @validator("OLLAMA_INSTANCES", pre=True)
    def parse_ollama_instances(cls, v):
        """Parse OLLAMA_INSTANCES from comma-separated string or list"""
        if isinstance(v, str):
            if not v.strip():  # If empty string
                return []
            # Split by comma and strip whitespace
            return [instance.strip() for instance in v.split(",") if instance.strip()]
        elif isinstance(v, list):
            return v
        else:
            return []
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            if not v.strip():  # If empty string
                return []
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        else:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()