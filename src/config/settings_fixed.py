from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import secrets
import json


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
    DATABASE_URL: str = "sqlite:///./llm_platform.db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 10
    CACHE_TTL: int = 3600
    
    # Ollama - FIXED: Remove JSON parsing
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_INSTANCES: str = "http://localhost:11434"  # Changed to string
    DEFAULT_MODEL: str = "deepseek-coder:6.7b"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7
    
    # Load Balancing
    LOAD_BALANCER_STRATEGY: str = "round_robin"
    
    # Fine-tuning
    FINETUNE_STORAGE_PATH: str = "./data/finetune"
    FINETUNE_MAX_EPOCHS: int = 10
    FINETUNE_BATCH_SIZE: int = 4
    FINETUNE_LEARNING_RATE: float = 2e-5
    FINETUNE_DEVICE: str = "cuda"
    
    # CORS - FIXED: Simple string
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
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
    
    # Helper methods to get lists when needed
    def get_ollama_instances(self) -> List[str]:
        """Get OLLAMA_INSTANCES as list"""
        if not self.OLLAMA_INSTANCES or self.OLLAMA_INSTANCES.strip() == "":
            return [self.OLLAMA_BASE_URL]
        return [instance.strip() for instance in self.OLLAMA_INSTANCES.split(",") if instance.strip()]
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS_ORIGINS as list"""
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "":
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()