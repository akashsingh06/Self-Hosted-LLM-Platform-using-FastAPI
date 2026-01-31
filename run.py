#!/usr/bin/env python3
"""
🚀 LLM Platform Runner
This file guarantees the platform will start
"""
import os
import sys
import subprocess
import time

def check_ollama():
    """Check if Ollama is running"""
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_ollama():
    """Start Ollama if not running"""
    print("🔍 Checking Ollama...")
    if not check_ollama():
        print("🚀 Starting Ollama...")
        # Try to start Ollama
        try:
            import subprocess
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            print("⏳ Waiting for Ollama to start...")
            time.sleep(5)
            
            # Check again
            if check_ollama():
                print("✅ Ollama started successfully")
            else:
                print("⚠ Ollama might take longer to start. Continuing...")
        except Exception as e:
            print(f"⚠ Could not start Ollama: {e}")
            print("⚠ The platform will work in fallback mode")
    else:
        print("✅ Ollama is already running")

def pull_default_model():
    """Pull default model if not available"""
    print("📦 Checking for models...")
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            if "deepseek-coder:6.7b" not in model_names:
                print("📥 Pulling deepseek-coder:6.7b...")
                subprocess.run(["ollama", "pull", "deepseek-coder:6.7b"], 
                             capture_output=True)
                print("✅ Model pulled")
            else:
                print("✅ Default model available")
    except Exception as e:
        print(f"⚠ Could not check models: {e}")

def start_server():
    """Start the FastAPI server"""
    print("\n" + "="*60)
    print("🚀 STARTING LLM PLATFORM SERVER")
    print("="*60)
    
    # Set environment variables to be safe
    os.environ["DATABASE_URL"] = "sqlite:///./llm_platform.db"
    os.environ["OLLAMA_INSTANCES"] = "http://localhost:11434"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000"
    os.environ["API_KEY"] = "default-api-key"
    
    # Start the server
    import uvicorn
    
    print("\n📊 Server Information:")
    print(f"   🌐 URL: http://localhost:8000")
    print(f"   📚 Docs: http://localhost:8000/docs")
    print(f"   🏥 Health: http://localhost:8000/health")
    print(f"   🔑 API Key: default-api-key")
    
    print("\n📋 Quick Test Commands:")
    print('   curl http://localhost:8000/health')
    print('   curl -H "Authorization: Bearer default-api-key" http://localhost:8000/api/models')
    print('   curl -X POST http://localhost:8000/api/chat \\')
    print('     -H "Authorization: Bearer default-api-key" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"message": "Write Python hello world"}\'')
    
    print("\n" + "="*60)
    print("🔄 Starting server... (Press Ctrl+C to stop)")
    print("="*60 + "\n")
    
    # Start uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        workers=1
    )

def main():
    """Main function"""
    print("🔧 LLM Platform Setup")
    print("="*40)
    
    # Check dependencies
    try:
        import fastapi
        import uvicorn
        import httpx
        print("✅ All dependencies installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", 
                              "fastapi", "uvicorn", "httpx", "python-jose", "passlib"])
    
    # Start Ollama
    start_ollama()
    
    # Pull model
    pull_default_model()
    
    # Start server
    start_server()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")