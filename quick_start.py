#!/usr/bin/env python3
"""
🚀 Quick Start Script for LLM Platform
Run this to start everything automatically
"""
import subprocess
import time
import sys
import os

def start_ollama_in_background():
    """Start Ollama in background"""
    print("🚀 Starting Ollama...")
    
    # Check if Ollama is already running
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("✅ Ollama is already running")
            return True
    except:
        pass
    
    # Start Ollama based on OS
    if sys.platform == "win32":
        # Windows
        try:
            # Try to start Ollama minimized
            subprocess.Popen(
                ["ollama", "serve"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("✅ Ollama started in background")
            time.sleep(5)
            return True
        except:
            print("❌ Could not start Ollama automatically")
            print("💡 Please manually open a new Command Prompt and run: ollama serve")
            return False
    else:
        # Mac/Linux
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("✅ Ollama started in background")
            time.sleep(5)
            return True
        except:
            print("❌ Could not start Ollama")
            return False

def check_and_pull_model():
    """Check and pull model if needed"""
    print("\n🔍 Checking for deepseek-coder model...")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            for model in models:
                if model["name"] == "deepseek-coder:6.7b":
                    print("✅ deepseek-coder:6.7b is available")
                    return True
            
            print("📥 Model not found, pulling deepseek-coder:6.7b...")
            print("⚠ This may take 5-10 minutes...")
            
            process = subprocess.Popen(
                ["ollama", "pull", "deepseek-coder:6.7b"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Show progress
            for line in process.stdout:
                if "pulling" in line.lower():
                    print(f"   {line.strip()}")
                elif "success" in line.lower():
                    print(f"   ✅ {line.strip()}")
            
            process.wait()
            print("✅ Model pulled successfully!")
            return True
    except:
        print("❌ Could not check/pull model (Ollama might not be ready)")
        return False

def start_llm_platform():
    """Start LLM Platform"""
    print("\n🌐 Starting LLM Platform...")
    
    # Check if already running
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ LLM Platform is already running")
            return True
    except:
        pass
    
    print("🚀 Starting server...")
    
    # Start the server
    try:
        process = subprocess.Popen(
            [sys.executable, "run.py"],
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        for i in range(30):
            time.sleep(1)
            try:
                import requests
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    print(f"✅ LLM Platform started successfully! (took {i+1}s)")
                    return True, process
            except:
                if i % 5 == 0:
                    print(f"   Still waiting... ({i+1}s)")
        
        print("❌ Server failed to start after 30 seconds")
        return False, process
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False, None

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 LLM PLATFORM QUICK START")
    print("=" * 60)
    
    # Step 1: Start Ollama
    ollama_started = start_ollama_in_background()
    
    if ollama_started:
        # Step 2: Check/Pull model
        time.sleep(3)  # Give Ollama time to start
        model_ready = check_and_pull_model()
    else:
        model_ready = False
    
    # Step 3: Start LLM Platform
    platform_started, server_process = start_llm_platform()
    
    print("\n" + "=" * 60)
    print("📊 STARTUP SUMMARY")
    print("=" * 60)
    
    print(f"• Ollama: {'✅ Running' if ollama_started else '❌ Not running'}")
    print(f"• Model: {'✅ Available' if model_ready else '❌ Not available'}")
    print(f"• LLM Platform: {'✅ Running' if platform_started else '❌ Not running'}")
    
    print("\n🔗 ACCESS URLs:")
    print("   • LLM Platform: http://localhost:8000")
    print("   • API Documentation: http://localhost:8000/docs")
    print("   • Health Check: http://localhost:8000/health")
    print("   • Ollama API: http://localhost:11434/api/tags")
    
    print("\n🔑 AUTHENTICATION:")
    print("   • API Key: default-api-key")
    
    print("\n🧪 QUICK TEST:")
    print("   Run: python -c \"import requests; ")
    print("   r = requests.get('http://localhost:8000/health'); ")
    print("   print(r.json())\"")
    
    print("\n💡 INTERACTIVE CHAT:")
    print("   Run: python chat_interface.py")
    
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    
    print("\n🛑 To stop everything:")
    print("   1. Press Ctrl+C in this window")
    print("   2. Close any Ollama windows")
    
    # Keep running
    try:
        if server_process:
            # Print server output
            print("\n📝 Server logs:")
            print("-" * 40)
            for line in server_process.stdout:
                print(line, end='')
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        if server_process:
            server_process.terminate()
        print("✅ All services stopped")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Startup interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")