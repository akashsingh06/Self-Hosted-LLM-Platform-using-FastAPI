#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import requests

def run_command(cmd, description=""):
    """Run a command and show output"""
    if description:
        print(f"🔧 {description}...")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"✅ Success")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()[:100]}...")
            return True
        else:
            print(f"❌ Failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_ollama_running():
    """Check if Ollama is running"""
    print("🔍 Checking if Ollama is running...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            return True
        else:
            print(f"❌ Ollama returned status: {response.status_code}")
            return False
    except:
        print("❌ Ollama is not running")
        return False

def start_ollama():
    """Start Ollama service"""
    print("🚀 Starting Ollama...")
    
    # Check if already running
    if check_ollama_running():
        return True
    
    # Try to start Ollama
    print("   Opening Ollama in new window...")
    
    # For Windows
    if sys.platform == "win32":
        try:
            # Try to start Ollama in background
            subprocess.Popen(
                ["start", "cmd", "/k", "ollama", "serve"],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except:
            print("   Please manually open a new Command Prompt and run: ollama serve")
            print("   Then press Enter here to continue...")
            input()
    
    # For Mac/Linux
    else:
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except:
            print("   Please manually open a new terminal and run: ollama serve")
            print("   Then press Enter here to continue...")
            input()
    
    # Wait and check
    print("⏳ Waiting for Ollama to start...")
    for i in range(30):
        time.sleep(1)
        if check_ollama_running():
            print(f"✅ Ollama started successfully (took {i+1} seconds)")
            return True
        if i % 5 == 0:
            print(f"   Still waiting... ({i+1}s)")
    
    print("❌ Ollama failed to start after 30 seconds")
    return False

def pull_deepseek_model():
    """Pull the deepseek-coder model"""
    print("📥 Pulling deepseek-coder:6.7b model...")
    print("⚠ This may take 5-10 minutes depending on your internet speed")
    
    success = run_command("ollama pull deepseek-coder:6.7b", "Downloading model")
    
    if success:
        print("✅ Model downloaded successfully!")
        return True
    else:
        print("❌ Failed to download model")
        return False

def check_deepseek_model():
    """Check if deepseek-coder is available"""
    print("🔍 Checking for deepseek-coder model...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            for model in models:
                if model["name"] == "deepseek-coder:6.7b":
                    print("✅ deepseek-coder:6.7b is available")
                    return True
        
        print("❌ deepseek-coder:6.7b is not available")
        return False
    except:
        print("❌ Could not check models")
        return False

def test_ollama_generate():
    """Test if Ollama can generate responses"""
    print("🧪 Testing Ollama generate...")
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
            print("✅ Ollama generate is working!")
            return True
        else:
            print(f"❌ Ollama generate failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing Ollama: {e}")
        return False

def start_llm_platform():
    """Start the LLM Platform"""
    print("🌐 Starting LLM Platform...")
    
    # Check if already running
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ LLM Platform is already running")
            return True
    except:
        pass
    
    print("   Starting server...")
    
    # For Windows
    if sys.platform == "win32":
        print("   Please manually start the LLM Platform:")
        print("   In a NEW Command Prompt, run:")
        print("   cd D:\\ollama\\local-llm-platform")
        print("   python run.py")
        print()
        print("   Then press Enter here to continue...")
        input()
        return True
    else:
        # For Mac/Linux, start in background
        try:
            subprocess.Popen(
                ["python", "run.py"],
                cwd=os.getcwd(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(5)
            
            # Check if started
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    print("✅ LLM Platform started")
                    return True
            except:
                print("❌ LLM Platform failed to start")
                return False
        except:
            print("❌ Could not start LLM Platform")
            return False

def main():
    """Main fix function"""
    print("=" * 60)
    print("🔧 FIXING OLLAMA CONNECTION")
    print("=" * 60)
    print()
    
    # Step 1: Start Ollama
    print("STEP 1: Start Ollama")
    print("-" * 40)
    ollama_started = start_ollama()
    
    if not ollama_started:
        print("\n❌ Cannot continue without Ollama")
        print("Please make sure Ollama is installed and running")
        return
    
    # Step 2: Check/Pull model
    print("\nSTEP 2: Check for deepseek-coder model")
    print("-" * 40)
    model_available = check_deepseek_model()
    
    if not model_available:
        pull = input("\nDo you want to pull the deepseek-coder:6.7b model? (y/n): ")
        if pull.lower() == 'y':
            pull_deepseek_model()
            model_available = check_deepseek_model()
    
    if not model_available:
        print("\n⚠ Warning: No deepseek-coder model available")
        print("The platform will use fallback responses")
    
    # Step 3: Test Ollama
    print("\nSTEP 3: Test Ollama")
    print("-" * 40)
    if model_available:
        test_ollama_generate()
    else:
        print("⚠ Skipping Ollama test (no model)")
    
    # Step 4: Start LLM Platform
    print("\nSTEP 4: Start LLM Platform")
    print("-" * 40)
    platform_started = start_llm_platform()
    
    # Final test
    print("\n" + "=" * 60)
    print("🎯 FINAL TEST")
    print("=" * 60)
    
    if platform_started:
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            print(f"✅ LLM Platform Health: {response.json().get('status')}")
            
            # Test chat
            headers = {"Authorization": "Bearer default-api-key"}
            chat_response = requests.post(
                "http://localhost:8000/api/chat",
                headers=headers,
                json={"message": "Hello"},
                timeout=10
            )
            
            if chat_response.status_code == 200:
                result = chat_response.json()
                print("✅ Chat endpoint working!")
                
                if "fallback" in result.get("message", "").lower():
                    print("⚠ Using fallback mode (Ollama not properly connected)")
                else:
                    print("✅ Real Ollama responses working!")
            else:
                print(f"❌ Chat failed: {chat_response.status_code}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 60)
    print("📋 SETUP COMPLETE")
    print("=" * 60)
    
    print("\n🎯 NEXT STEPS:")
    print("1. Keep the Ollama window open (running 'ollama serve')")
    print("2. Keep the LLM Platform window open (running 'python run.py')")
    print("3. Test with: python test_ollama.py")
    print("\n🔗 Access URLs:")
    print("   • LLM Platform: http://localhost:8000")
    print("   • API Docs: http://localhost:8000/docs")
    print("   • Ollama API: http://localhost:11434/api/tags")
    
    print("\n💡 Quick test command:")
    print('   curl -X POST http://localhost:8000/api/chat \\')
    print('     -H "Authorization: Bearer default-api-key" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d "{\\"message\\": \\"Hello\\"}"')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Fix interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")