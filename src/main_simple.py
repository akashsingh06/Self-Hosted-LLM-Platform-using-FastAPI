
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Create logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import simple settings
try:
    from src.config.settings_simple import settings
except ImportError:
    # Fallback
    class Settings:
        DATABASE_URL = "sqlite:///./llm_platform.db"
        OLLAMA_INSTANCES = "http://localhost:11434"
        CORS_ORIGINS = "http://localhost:3000"
    
    settings = Settings()

# Create FastAPI app
app = FastAPI(
    title="Local LLM Platform",
    description="Local LLM Chat and Fine-tuning Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "LLM Platform API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "llm-platform"}

@app.get("/api/models")
async def get_models():
    """List available models"""
    return [
        {"name": "deepseek-coder:6.7b", "type": "code", "available": True},
        {"name": "llama2:7b", "type": "chat", "available": True},
        {"name": "mistral:7b", "type": "chat", "available": True},
    ]

@app.post("/api/chat")
async def chat(message: dict):
    """Chat endpoint"""
    user_message = message.get("message", "Hello")
    model = message.get("model_name", "deepseek-coder:6.7b")
    
    return {
        "message": f"Test response from {model}: You said '{user_message}'. This is working!",
        "conversation_id": 1,
        "code_blocks": [],
        "tokens_used": 0,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
