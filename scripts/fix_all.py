#!/usr/bin/env python3
import os
import sys

def fix_env_file():
    """Create a clean .env file"""
    env_content = """# Application
APP_NAME=Local-LLM-Platform
APP_ENV=development
DEBUG=true
SECRET_KEY=change-this-in-production-make-it-long-and-secure
API_KEY=default-api-key

# Database
DATABASE_URL=sqlite:///./llm_platform.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_INSTANCES=http://localhost:11434
DEFAULT_MODEL=deepseek-coder:6.7b
MAX_TOKENS=4096
TEMPERATURE=0.7

# Load Balancing
LOAD_BALANCER_STRATEGY=round_robin

# Caching
CACHE_ENABLED=true
CACHE_TTL=3600

# Fine-tuning
FINETUNE_STORAGE_PATH=./data/finetune
FINETUNE_MAX_EPOCHS=10
FINETUNE_BATCH_SIZE=4
FINETUNE_LEARNING_RATE=0.00002

# Monitoring
METRICS_ENABLED=true

# Storage
UPLOAD_PATH=./data/uploads
EXPORT_PATH=./data/exports
LOG_PATH=./data/logs

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# CORS
CORS_ORIGINS=http://localhost:3000
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Created clean .env file")

def test_settings():
    """Test if settings load correctly"""
    print("\n🧪 Testing settings...")
    try:
        # Temporarily add src to path
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        # Import settings
        from src.config.settings import settings
        
        print(f"✅ Settings loaded successfully!")
        print(f"   OLLAMA_INSTANCES: {settings.OLLAMA_INSTANCES}")
        print(f"   Type: {type(settings.OLLAMA_INSTANCES)}")
        print(f"   As list: {settings.get_ollama_instances_list()}")
        
        return True
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False

def start_server():
    """Start the server"""
    print("\n🚀 Starting server...")
    import subprocess
    
    try:
        # Start uvicorn
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for server to start
        import time
        time.sleep(5)
        
        # Test if server is responding
        import requests
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            print(f"✅ Server is running! Health: {response.status_code}")
            print(f"\n📊 Access URLs:")
            print(f"   • API: http://localhost:8000")
            print(f"   • Docs: http://localhost:8000/docs")
            print(f"   • Health: http://localhost:8000/health")
            
            # Keep server running
            print(f"\n🔄 Server is running. Press Ctrl+C to stop.")
            process.wait()
            
        except requests.ConnectionError:
            print("❌ Server started but not responding")
            process.terminate()
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")

def main():
    """Main function"""
    print("🔧 Fixing LLM Platform Configuration")
    print("="*50)
    
    # Fix .env file
    fix_env_file()
    
    # Test settings
    if test_settings():
        # Ask if user wants to start server
        response = input("\n🚀 Start the server now? (y/n): ")
        if response.lower() in ['y', 'yes']:
            start_server()
        else:
            print("\n✅ Configuration fixed!")
            print("\n📝 Next steps:")
            print("   1. Start Ollama: ollama serve")
            print("   2. Start server: uvicorn src.main:app --reload --host 0.0.0.0 --port 8000")
            print("   3. Test: curl http://localhost:8000/health")
    else:
        print("\n❌ Failed to fix configuration. Please check manually.")

if __name__ == "__main__":
    main()