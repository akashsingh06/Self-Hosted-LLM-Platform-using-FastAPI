import os
from typing import List, Optional
import json

class Settings:
    """Simple settings class without Pydantic validation issues"""
    
    # Application
    APP_NAME: str = "Local LLM Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-in-production-make-it-long-and-secure"
    API_KEY: str = "default-api-key"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    LOG_LEVEL: str = "info"
    
    # Database
    DATABASE_URL: str = "sqlite:///./llm_platform.db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 5
    CACHE_TTL: int = 3600
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_INSTANCES: str = "http://localhost:11434"  # Simple string
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
    FINETUNE_DEVICE: str = "cpu"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Monitoring
    METRICS_ENABLED: bool = True
    
    # Storage
    UPLOAD_PATH: str = "./data/uploads"
    EXPORT_PATH: str = "./data/exports"
    LOG_PATH: str = "./data/logs"
    
    # Security
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    BCRYPT_ROUNDS: int = 12
    
    def __init__(self):
        """Load from environment variables"""
        self._load_from_env()
    
    def _load_from_env(self):
        """Load settings from environment variables"""
        for key in dir(self):
            if not key.startswith('_') and key.isupper():
                env_value = os.getenv(key)
                if env_value is not None:
                    # Handle special cases
                    if key in ['DEBUG', 'METRICS_ENABLED']:
                        setattr(self, key, env_value.lower() in ['true', '1', 'yes'])
                    elif key in ['PORT', 'MAX_TOKENS', 'RATE_LIMIT_PER_MINUTE', 
                                'RATE_LIMIT_PER_HOUR', 'DATABASE_POOL_SIZE', 
                                'DATABASE_MAX_OVERFLOW', 'REDIS_POOL_SIZE',
                                'CACHE_TTL', 'FINETUNE_MAX_EPOCHS', 'FINETUNE_BATCH_SIZE',
                                'WORKERS', 'JWT_EXPIRE_MINUTES', 'BCRYPT_ROUNDS']:
                        try:
                            setattr(self, key, int(env_value))
                        except:
                            pass
                    elif key in ['TEMPERATURE', 'FINETUNE_LEARNING_RATE']:
                        try:
                            setattr(self, key, float(env_value))
                        except:
                            pass
                    else:
                        setattr(self, key, env_value)
    
    def get_ollama_instances(self) -> List[str]:
        """Get OLLAMA_INSTANCES as list"""
        if not self.OLLAMA_INSTANCES:
            return [self.OLLAMA_BASE_URL]
        return [x.strip() for x in self.OLLAMA_INSTANCES.split(',') if x.strip()]
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS_ORIGINS as list"""
        if not self.CORS_ORIGINS:
            return ["http://localhost:3000"]
        return [x.strip() for x in self.CORS_ORIGINS.split(',') if x.strip()]

# Create global settings instance
settings = Settings()