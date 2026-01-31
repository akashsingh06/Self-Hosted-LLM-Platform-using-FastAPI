from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import json

# === SIMPLE MODELS ===
class ChatRequest(BaseModel):
    message: str
    model_name: Optional[str] = "deepseek-coder:6.7b"
    stream: Optional[bool] = False

# === CREATE APP ===
app = FastAPI(
    title="LLM Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ROUTES ===
@app.get("/")
def root():
    return {
        "service": "LLM Platform",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/api/models": "List models",
            "/api/chat": "Chat endpoint"
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": "now"}

@app.get("/api/models")
def get_models():
    return [
        {"name": "deepseek-coder:6.7b", "type": "code", "size": "6.7B"},
        {"name": "llama2:7b", "type": "chat", "size": "7B"},
        {"name": "mistral:7b", "type": "chat", "size": "7.3B"},
        {"name": "codellama:7b", "type": "code", "size": "7B"}
    ]

@app.post("/api/chat")
def chat(request: ChatRequest):
    """Simple chat that always works"""
    response_text = f"""I received your message: "{request.message}"

You requested model: {request.model_name}

Here's a Python hello world program:

```python
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()