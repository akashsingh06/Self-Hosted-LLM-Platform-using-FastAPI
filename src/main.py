from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import logging
from datetime import datetime

# Import our simple settings
from src.config.settings import settings

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

async def verify_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key"""
    if credentials.credentials != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"user_id": 1, "username": "api_user"}

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=" * 60)
    logger.info(f"🚀 Starting {settings.APP_NAME}")
    logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🌐 Host: {settings.HOST}:{settings.PORT}")
    logger.info(f"🔧 Debug: {settings.DEBUG}")
    logger.info(f"🗄️  Database: {settings.DATABASE_URL}")
    logger.info("=" * 60)
    
    # Startup complete
    logger.info("✅ Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("🛑 Application shutdown")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Local LLM Platform for chatting and fine-tuning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "/health": "Health check",
            "/docs": "API documentation",
            "/api/models": "List available models",
            "/api/chat": "Chat with LLM"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "llm-platform",
        "version": "1.0.0"
    }

@app.get("/api/models")
async def get_models(current_user: dict = Depends(verify_auth)):
    """Get available models"""
    try:
        import httpx
        
        # Try to get models from Ollama
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return [
                    {
                        "name": model["name"],
                        "size": model.get("size", 0),
                        "modified": model.get("modified_at", ""),
                        "available": True
                    }
                    for model in models
                ]
    except Exception as e:
        logger.warning(f"Could not fetch models from Ollama: {e}")
    
    # Fallback to default models
    return [
        {"name": "deepseek-coder:6.7b", "type": "code", "available": True},
        {"name": "llama2:7b", "type": "chat", "available": True},
        {"name": "mistral:7b", "type": "chat", "available": True},
    ]

@app.post("/api/chat")
async def chat(request: Request, current_user: dict = Depends(verify_auth)):
    """Chat with LLM"""
    try:
        data = await request.json()
        message = data.get("message", "")
        model_name = data.get("model_name", settings.DEFAULT_MODEL)
        stream = data.get("stream", False)
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        logger.info(f"Chat request - User: {current_user['username']}, Model: {model_name}")
        
        # Try to get response from Ollama
        try:
            import httpx
            import json
            
            ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
            payload = {
                "model": model_name,
                "prompt": message,
                "stream": stream,
                "options": {
                    "temperature": settings.TEMPERATURE,
                    "num_predict": settings.MAX_TOKENS,
                }
            }
            
            if stream:
                # Handle streaming response
                async def generate():
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        async with client.stream("POST", ollama_url, json=payload) as response:
                            async for line in response.aiter_lines():
                                if line.strip():
                                    try:
                                        data = json.loads(line)
                                        if "response" in data:
                                            yield f"data: {json.dumps({'chunk': data['response']})}\n\n"
                                        if data.get("done", False):
                                            yield f"data: {json.dumps({'done': True})}\n\n"
                                            break
                                    except:
                                        continue
                
                from fastapi.responses import StreamingResponse
                return StreamingResponse(
                    generate(),
                    media_type="text/event-stream",
                    headers={
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                    }
                )
            else:
                # Handle non-streaming response
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(ollama_url, json=payload)
                    response.raise_for_status()
                    result = response.json()
                    
                    full_response = result.get("response", "")
                    
                    # Extract code blocks
                    code_blocks = []
                    lines = full_response.split('\n')
                    in_code_block = False
                    current_code = []
                    current_language = ""
                    
                    for line in lines:
                        if line.strip().startswith('```'):
                            if in_code_block:
                                # End of code block
                                in_code_block = False
                                if current_code:
                                    code_blocks.append({
                                        "language": current_language,
                                        "code": '\n'.join(current_code)
                                    })
                                current_code = []
                                current_language = ""
                            else:
                                # Start of code block
                                in_code_block = True
                                current_language = line.strip().replace('```', '').strip()
                        elif in_code_block:
                            current_code.append(line)
                    
                    return {
                        "message": full_response,
                        "conversation_id": 1,
                        "code_blocks": code_blocks,
                        "tokens_used": result.get("total_duration", 0),
                        "model": model_name
                    }
                    
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            # Fallback response
            return {
                "message": f"Test response (Ollama not available): You asked: '{message}'. Model: {model_name}. This is a fallback response since Ollama connection failed: {str(e)}",
                "conversation_id": 1,
                "code_blocks": [
                    {
                        "language": "python",
                        "code": f'print("Fallback response for: {message}")'
                    }
                ],
                "tokens_used": 0,
                "model": model_name
            }
            
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Run server
if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL,
    )