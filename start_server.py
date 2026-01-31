#!/usr/bin/env python3
import os
import sys
import uvicorn
from pathlib import Path

print("🚀 Starting LLM Platform Server...")

# 1. Set up environment
os.environ["DATABASE_URL"] = "sqlite:///./llm_platform.db"
os.environ["OLLAMA_INSTANCES"] = "http://localhost:11434"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"
os.environ["API_KEY"] = "default-api-key"
os.environ["SECRET_KEY"] = "test-secret-key-for-development-only"
os.environ["DEBUG"] = "true"

# 2. Create a simple working settings module
settings_content = '''
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
'''

# Write the simple settings file
settings_path = Path("src/config") / "settings_simple.py"
settings_path.parent.mkdir(exist_ok=True)
settings_path.write_text(settings_content)
print(f"✅ Created simple settings at {settings_path}")

# 3. Create a simple main.py that works
main_content = '''
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
'''

main_path = Path("src") / "main_simple.py"
main_path.write_text(main_content)
print(f"✅ Created simple main.py at {main_path}")

# 4. Start the server
print("\n" + "="*50)
print("🚀 STARTING SERVER...")
print("="*50)
print("\n📊 Access URLs:")
print("  • API: http://localhost:8000")
print("  • Docs: http://localhost:8000/docs")
print("  • Health: http://localhost:8000/health")
print("\n🛑 Press Ctrl+C to stop the server")
print("="*50 + "\n")

# Start uvicorn
uvicorn.run(
    "src.main_simple:app",
    host="0.0.0.0",
    port=8000,
    reload=True,
    log_level="info"
)