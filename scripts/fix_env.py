#!/usr/bin/env python3
import os
import sys

def fix_env_file():
    """Fix the .env file to prevent JSON parsing errors"""
    
    env_file = ".env"
    
    if not os.path.exists(env_file):
        print("❌ .env file not found!")
        return False
    
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    for line in lines:
        # Fix OLLAMA_INSTANCES line
        if line.startswith("OLLAMA_INSTANCES="):
            value = line.split("=", 1)[1].strip()
            # If it looks like JSON, replace with simple string
            if value.startswith("[") or value.startswith("{"):
                fixed_lines.append("OLLAMA_INSTANCES=http://localhost:11434\n")
            elif not value or value == '""' or value == "''":
                fixed_lines.append("OLLAMA_INSTANCES=http://localhost:11434\n")
            else:
                fixed_lines.append(line)
        # Fix CORS_ORIGINS line
        elif line.startswith("CORS_ORIGINS="):
            value = line.split("=", 1)[1].strip()
            if value.startswith("[") or value.startswith("{"):
                fixed_lines.append('CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000\n')
            elif not value or value == '""' or value == "''":
                fixed_lines.append('CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000\n')
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Write fixed file
    with open(env_file, 'w') as f:
        f.writelines(fixed_lines)
    
    print("✅ Fixed .env file")
    print("\nUpdated .env contents:")
    print("=" * 40)
    with open(env_file, 'r') as f:
        print(f.read())
    print("=" * 40)
    
    return True

def create_default_env():
    """Create a default .env file if it doesn't exist"""
    
    default_env = """# Application
APP_NAME=Local-LLM-Platform
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-change-this-in-production
API_KEY=your-api-key-here

# Database
DATABASE_URL=postgresql://llm_user:llm_password@localhost:5432/llm_db
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
CACHE_MAX_SIZE=10000

# Fine-tuning
FINETUNE_STORAGE_PATH=./data/finetune
FINETUNE_MAX_EPOCHS=10
FINETUNE_BATCH_SIZE=4
FINETUNE_LEARNING_RATE=2e-5

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
METRICS_ENABLED=true

# Storage
UPLOAD_PATH=./data/uploads
EXPORT_PATH=./data/exports
LOG_PATH=./data/logs

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
"""
    
    with open(".env", "w") as f:
        f.write(default_env)
    
    print("✅ Created default .env file")
    return True

def main():
    """Main function"""
    print("🔧 Fixing environment configuration...")
    
    if not os.path.exists(".env"):
        print("📝 Creating new .env file...")
        create_default_env()
    else:
        print("🔄 Fixing existing .env file...")
        fix_env_file()
    
    print("\n✅ Environment configuration fixed!")
    print("\n📝 Next steps:")
    print("1. Edit the .env file with your actual database credentials")
    print("2. Run: python scripts/setup_database.py")
    print("3. Or run: alembic upgrade head")

if __name__ == "__main__":
    main()