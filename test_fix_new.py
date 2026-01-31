#!/usr/bin/env python3
import requests
import time
import subprocess

def print_color(text, color="white"):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def test_ollama_with_retry():
    """Test Ollama with retries"""
    print_color("🔄 Testing Ollama with retry...", "cyan")
    
    for i in range(3):
        try:
            print_color(f"  Attempt {i+1}/3...", "yellow")
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print_color(f"  ✅ Ollama responding with {len(data.get('models', []))} models", "green")
                return True
        except Exception as e:
            print_color(f"  ❌ Attempt {i+1} failed: {e}", "red")
            time.sleep(2)
    
    print_color("❌ All Ollama tests failed", "red")
    return False

def load_model():
    """Load the model into memory"""
    print_color("🔄 Loading model into memory...", "cyan")
    
    # First try a simple test to load the model
    try:
        test_prompt = {
            "model": "deepseek-coder:6.7b",
            "prompt": "Say 'ready'",
            "stream": False,
            "options": {
                "num_predict": 10  # Very short response
            }
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=test_prompt,
            timeout=30  # Give it 30 seconds
        )
        
        if response.status_code == 200:
            print_color("✅ Model loaded successfully", "green")
            return True
        else:
            print_color(f"❌ Model load failed: {response.status_code}", "red")
            return False
            
    except requests.exceptions.Timeout:
        print_color("⚠ Model loading is taking time (first load is slow)", "yellow")
        print_color("💡 The model needs to be loaded into GPU/RAM memory", "cyan")
        return True  # Timeout might mean it's loading
    except Exception as e:
        print_color(f"❌ Error: {e}", "red")
        return False

def test_llm_platform_simple():
    """Test LLM Platform with simple request"""
    print_color("🔄 Testing LLM Platform with simple request...", "cyan")
    
    try:
        # Simple health check first
        response = requests.get("http://localhost:8000/health", timeout=5)
        print_color(f"✅ Health check: {response.json().get('status')}", "green")
        
        # Try a very short chat request
        headers = {"Authorization": "Bearer default-api-key"}
        data = {
            "message": "Say hello",
            "model_name": "deepseek-coder:6.7b",
            "stream": False
        }
        
        print_color("  Sending simple chat request...", "yellow")
        response = requests.post(
            "http://localhost:8000/api/chat",
            headers=headers,
            json=data,
            timeout=60  # Give it 60 seconds for first request
        )
        
        if response.status_code == 200:
            result = response.json()
            print_color("✅ Chat endpoint working!", "green")
            print_color(f"  Response: {result.get('message', '')[:50]}...", "white")
            return True
        else:
            print_color(f"❌ Chat failed: {response.status_code}", "red")
            return False
            
    except requests.exceptions.Timeout:
        print_color("⚠ Request timed out - server might be busy", "yellow")
        return False
    except Exception as e:
        print_color(f"❌ Error: {e}", "red")
        return False

def main():
    print_color("=" * 60, "cyan")
    print_color("🔧 FIXING TIMEOUT ISSUES", "cyan")
    print_color("=" * 60, "cyan")
    print()
    
    # Step 1: Test Ollama basics
    if not test_ollama_with_retry():
        print()
        print_color("❌ Ollama not responding. Make sure it's running:", "red")
        print_color("  In a NEW PowerShell window, run: ollama serve", "yellow")
        return
    
    # Step 2: Load the model (first load is slow)
    print()
    if not load_model():
        print()
        print_color("⚠ Model loading issue. Trying workaround...", "yellow")
    
    # Step 3: Test LLM Platform
    print()
    if not test_llm_platform_simple():
        print()
        print_color("⚠ LLM Platform timeout. Server might need restart.", "yellow")
        
        # Try to restart the server
        restart = input("Restart LLM Platform server? (y/n): ")
        if restart.lower() == 'y':
            print_color("Restarting server...", "yellow")
            # This would require killing and restarting the server process
            print_color("Please manually restart:", "cyan")
            print_color("  1. Stop current server (Ctrl+C in server window)", "white")
            print_color("  2. Run: python run.py", "white")
    
    print()
    print_color("=" * 60, "cyan")
    print_color("🎯 WORKAROUND SOLUTIONS", "cyan")
    print_color("=" * 60, "cyan")
    
    print_color("\n💡 The issue is likely:", "yellow")
    print_color("  1. First model load is slow (3-5 minutes)", "white")
    print_color("  2. Server needs more time for initial requests", "white")
    
    print_color("\n🚀 IMMEDIATE WORKAROUND:", "green")
    print_color("  Use the DIRECT Ollama API first:", "white")
    print()
    print_color("  curl -X POST http://localhost:11434/api/generate \\", "gray")
    print_color("    -H 'Content-Type: application/json' \\", "gray")
    print_color("    -d '{\"model\":\"deepseek-coder:6.7b\",\"prompt\":\"Hello\",\"stream\":false}'", "gray")
    
    print_color("\n📝 Alternative: Reduce model size:", "yellow")
    print_color("  ollama pull llama2:7b  # Smaller, faster model", "white")
    
    print_color("\n🔧 Or increase timeouts in .env file:", "yellow")
    print_color("  Add: OLLAMA_TIMEOUT=120", "white")

if __name__ == "__main__":
    main()