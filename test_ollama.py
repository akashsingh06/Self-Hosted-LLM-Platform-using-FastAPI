#!/usr/bin/env python3
import requests
import json
import time
import subprocess
import sys
import os

def print_colored(text, color="white"):
    """Print colored text in terminal"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def test_ollama_api():
    """Test if Ollama API is responding"""
    print_colored("1. Testing Ollama API...", "yellow")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            print_colored(f"   ✅ Ollama API is responding", "green")
            print_colored(f"   📦 Models available ({len(models)}):", "white")
            for model in models:
                size_gb = model.get("size", 0) / (1024**3)  # Convert to GB
                print_colored(f"     • {model['name']} ({size_gb:.1f} GB)", "gray")
            return True, models
        else:
            print_colored(f"   ❌ Ollama API returned status: {response.status_code}", "red")
            return False, []
    except requests.ConnectionError:
        print_colored("   ❌ Ollama API not responding - Ollama is not running", "red")
        return False, []
    except Exception as e:
        print_colored(f"   ❌ Error: {e}", "red")
        return False, []

def check_deepseek_model(models):
    """Check if deepseek-coder is available"""
    print_colored("2. Checking for deepseek-coder model...", "yellow")
    for model in models:
        if model["name"] == "deepseek-coder:6.7b":
            print_colored("   ✅ deepseek-coder:6.7b is available", "green")
            return True
    
    print_colored("   ❌ deepseek-coder:6.7b is NOT available", "red")
    return False

def pull_deepseek_model():
    """Pull the deepseek-coder model"""
    print_colored("3. Pulling deepseek-coder:6.7b...", "yellow")
    print_colored("   ⏳ This may take 5-10 minutes...", "cyan")
    
    try:
        # Start the pull process
        process = subprocess.Popen(
            ["ollama", "pull", "deepseek-coder:6.7b"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Show progress
        for line in process.stdout:
            if "pulling" in line.lower() or "downloading" in line.lower():
                print_colored(f"   📥 {line.strip()}", "gray")
            elif "success" in line.lower():
                print_colored(f"   ✅ {line.strip()}", "green")
        
        process.wait()
        
        if process.returncode == 0:
            print_colored("   ✅ Model pulled successfully!", "green")
            return True
        else:
            print_colored("   ❌ Failed to pull model", "red")
            return False
            
    except FileNotFoundError:
        print_colored("   ❌ Ollama command not found. Make sure Ollama is installed.", "red")
        return False
    except Exception as e:
        print_colored(f"   ❌ Error: {e}", "red")
        return False

def start_ollama():
    """Start Ollama service"""
    print_colored("4. Starting Ollama service...", "yellow")
    
    # Check if already running
    if test_ollama_api()[0]:
        print_colored("   ✅ Ollama is already running", "green")
        return True
    
    print_colored("   🚀 Starting Ollama...", "cyan")
    
    try:
        # Try to start Ollama
        process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print_colored("   ⏳ Waiting for Ollama to start...", "cyan")
        
        # Wait and check
        for i in range(30):  # 30 seconds max
            time.sleep(1)
            if test_ollama_api()[0]:
                print_colored(f"   ✅ Ollama started successfully! (took {i+1}s)", "green")
                return True
            if i % 5 == 0:
                print_colored(f"   ⏳ Still waiting... ({i+1}s)", "gray")
        
        print_colored("   ❌ Ollama failed to start after 30 seconds", "red")
        return False
        
    except FileNotFoundError:
        print_colored("   ❌ Ollama not found. Is it installed?", "red")
        print_colored("   💡 Download from: https://ollama.com", "yellow")
        return False
    except Exception as e:
        print_colored(f"   ❌ Error starting Ollama: {e}", "red")
        return False

def test_ollama_generate():
    """Test Ollama generate endpoint"""
    print_colored("5. Testing Ollama generate endpoint...", "yellow")
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "deepseek-coder:6.7b",
                "prompt": "Write hello world in Python",
                "stream": False
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print_colored("   ✅ Ollama generate is working!", "green")
            print_colored(f"   📝 Response: {data.get('response', '')[:100]}...", "gray")
            return True
        else:
            print_colored(f"   ❌ Ollama generate failed: {response.status_code}", "red")
            print_colored(f"   Error: {response.text[:200]}", "red")
            return False
            
    except requests.ConnectionError:
        print_colored("   ❌ Cannot connect to Ollama", "red")
        return False
    except Exception as e:
        print_colored(f"   ❌ Error: {e}", "red")
        return False

def test_llm_platform():
    """Test LLM Platform API"""
    print_colored("6. Testing LLM Platform API...", "yellow")
    
    try:
        # Test health
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print_colored("   ✅ LLM Platform API is running", "green")
            
            # Test models endpoint
            headers = {"Authorization": "Bearer default-api-key"}
            response = requests.get("http://localhost:8000/api/models", headers=headers, timeout=5)
            
            if response.status_code == 200:
                models = response.json()
                print_colored(f"   ✅ Models endpoint working ({len(models)} models)", "green")
                
                # Test chat
                chat_data = {
                    "message": "Write Python hello world",
                    "model_name": "deepseek-coder:6.7b"
                }
                
                response = requests.post(
                    "http://localhost:8000/api/chat",
                    headers=headers,
                    json=chat_data,
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print_colored("   ✅ Chat endpoint working!", "green")
                    
                    if "fallback" in result.get("message", "").lower():
                        print_colored("   ⚠ Using fallback mode (Ollama not connected)", "yellow")
                        return False, "fallback"
                    else:
                        print_colored("   ✅ Real Ollama response!", "green")
                        return True, "real"
                else:
                    print_colored(f"   ❌ Chat failed: {response.status_code}", "red")
                    return False, "chat_failed"
            else:
                print_colored(f"   ❌ Models endpoint failed: {response.status_code}", "red")
                return False, "models_failed"
        else:
            print_colored(f"   ❌ Health check failed: {response.status_code}", "red")
            return False, "health_failed"
            
    except requests.ConnectionError:
        print_colored("   ❌ LLM Platform API not running", "red")
        print_colored("   💡 Start it with: python run.py", "yellow")
        return False, "not_running"
    except Exception as e:
        print_colored(f"   ❌ Error: {e}", "red")
        return False, "error"

def main():
    """Main function"""
    print_colored("🔍 Testing LLM Platform Setup", "cyan")
    print_colored("=" * 60, "cyan")
    print()
    
    # Test Ollama
    ollama_working, models = test_ollama_api()
    
    # If Ollama not working, try to start it
    if not ollama_working:
        print()
        start_ollama()
        # Test again
        ollama_working, models = test_ollama_api()
    
    # Check for deepseek model
    deepseek_available = False
    if ollama_working:
        deepseek_available = check_deepseek_model(models)
        
        # If not available, pull it
        if not deepseek_available:
            print()
            pull_deepseek_model()
            # Check again
            ollama_working, models = test_ollama_api()
            if ollama_working:
                deepseek_available = check_deepseek_model(models)
    
    # Test Ollama generate
    generate_working = False
    if ollama_working and deepseek_available:
        print()
        generate_working = test_ollama_generate()
    
    # Test LLM Platform
    print()
    platform_working, platform_status = test_llm_platform()
    
    # Summary
    print()
    print_colored("📊 TEST SUMMARY", "cyan")
    print_colored("=" * 60, "cyan")
    
    print_colored(f"• Ollama API: {'✅ Working' if ollama_working else '❌ Not working'}", 
                 "green" if ollama_working else "red")
    
    print_colored(f"• Deepseek Model: {'✅ Available' if deepseek_available else '❌ Not available'}", 
                 "green" if deepseek_available else "red")
    
    print_colored(f"• Ollama Generate: {'✅ Working' if generate_working else '❌ Not working'}", 
                 "green" if generate_working else "red")
    
    print_colored(f"• LLM Platform: {'✅ Working' if platform_working else '❌ Not working'}", 
                 "green" if platform_working else "red")
    
    if platform_status == "fallback":
        print_colored("  ⚠ Platform is using fallback mode (not connected to Ollama)", "yellow")
    elif platform_status == "not_running":
        print_colored("  ⚠ Platform API is not running", "yellow")
    
    print()
    print_colored("🚀 QUICK FIXES", "cyan")
    print_colored("=" * 60, "cyan")
    
    if not ollama_working:
        print_colored("1. Start Ollama manually:", "yellow")
        print_colored("   Open a NEW terminal and run:", "white")
        print_colored("   ollama serve", "gray")
        print()
    
    if not deepseek_available:
        print_colored("2. Pull the model:", "yellow")
        print_colored("   In a NEW terminal, run:", "white")
        print_colored("   ollama pull deepseek-coder:6.7b", "gray")
        print()
    
    if platform_status == "not_running":
        print_colored("3. Start the LLM Platform:", "yellow")
        print_colored("   In this terminal, run:", "white")
        print_colored("   python run.py", "gray")
        print()
    
    print_colored("💡 QUICK TEST COMMANDS:", "cyan")
    print_colored("=" * 60, "cyan")
    print_colored("# Test Ollama:", "white")
    print_colored('curl http://localhost:11434/api/tags', "gray")
    print()
    print_colored("# Test LLM Platform:", "white")
    print_colored('curl http://localhost:8000/health', "gray")
    print_colored('curl -H "Authorization: Bearer default-api-key" http://localhost:8000/api/models', "gray")
    print()
    print_colored("# Test Chat:", "white")
    print_colored('curl -X POST http://localhost:8000/api/chat \\', "gray")
    print_colored('  -H "Authorization: Bearer default-api-key" \\', "gray")
    print_colored('  -H "Content-Type: application/json" \\', "gray")
    print_colored('  -d "{\\"message\\": \\"Hello\\"}"', "gray")
    
    print()
    print_colored("=" * 60, "cyan")
    
    if ollama_working and platform_working and platform_status == "real":
        print_colored("🎉 SUCCESS! Everything is working perfectly!", "green")
    elif platform_working:
        print_colored("⚠ PARTIAL SUCCESS - Platform works but may not use Ollama", "yellow")
    else:
        print_colored("❌ Some components need attention", "red")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_colored("🛑 Tests interrupted by user", "yellow")
    except Exception as e:
        print_colored(f"❌ Unexpected error: {e}", "red")