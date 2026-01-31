
class Settings:
    DATABASE_URL = "sqlite:///./llm_platform.db"
    OLLAMA_INSTANCES = "http://localhost:11434"
    CORS_ORIGINS = "http://localhost:3000"
    API_KEY = "default-api-key"
    SECRET_KEY = "test-secret-key-for-development-only"
    DEBUG = True
    
    def get_ollama_instances_list(self):
        return [self.OLLAMA_INSTANCES]
    
    def get_cors_origins_list(self):
        return [self.CORS_ORIGINS]

settings = Settings()
