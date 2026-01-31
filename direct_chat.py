#!/usr/bin/env python3
"""
DIRECT CHAT with Ollama - Bypasses the LLM Platform if it's having issues
"""
import requests
import json
import sys
import time

def chat_with_ollama_direct(message, model="deepseek-coder:6.7b", stream=False):
    """Chat directly with Ollama, bypassing the LLM Platform"""
    
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": message,
        "stream": stream,
        "options": {
            "temperature": 0.7,
            "num_predict": 1000
        }
    }
    
    print(f"\n🤖 Chatting with {model}...")
    print(f"📝 You: {message}")
    print("-" * 50)
    
    try:
        if stream:
            print("🔄 Streaming response:")
            print()
            response = requests.post(url, json=payload, stream=True, timeout=120)
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            chunk = data["response"]
                            print(chunk, end="", flush=True)
                            full_response += chunk
                        if data.get("done", False):
                            print("\n")
                            break
                    except:
                        continue
            
            return full_response
            
        else:
            print("⏳ Generating response (may take 30-60 seconds on first load)...")
            response = requests.post(url, json=payload, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                
                print("\n" + "=" * 50)
                print("🤖 Assistant:")
                print("=" * 50)
                print(response_text)
                print("=" * 50)
                
                # Extract code blocks
                code_blocks = []
                lines = response_text.split('\n')
                in_code = False
                current_code = []
                current_lang = ""
                
                for line in lines:
                    if line.strip().startswith('```'):
                        if in_code:
                            # End of code block
                            in_code = False
                            if current_code:
                                code_blocks.append({
                                    "language": current_lang,
                                    "code": "\n".join(current_code)
                                })
                            current_code = []
                        else:
                            # Start of code block
                            in_code = True
                            current_lang = line.strip().replace('```', '').strip()
                    elif in_code:
                        current_code.append(line)
                
                if code_blocks:
                    print(f"\n📦 Extracted {len(code_blocks)} code block(s):")
                    for i, block in enumerate(code_blocks, 1):
                        print(f"\n[{i}] {block['language']}:")
                        print("-" * 40)
                        print(block['code'])
                
                return response_text
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
                return None
                
    except requests.exceptions.Timeout:
        print("❌ Timeout! The model is taking too long to respond.")
        print("💡 First load can take 3-5 minutes. Try:")
        print("   1. Wait 2 minutes and try again")
        print("   2. Use a smaller model: llama2:7b")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_ollama_connection():
    """Test if Ollama is ready"""
    print("🔍 Testing Ollama connection...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            print(f"✅ Ollama is running ({len(models)} models)")
            
            if models:
                print("📦 Available models:")
                for model in models:
                    print(f"   • {model['name']}")
            
            # Test if model is loaded
            print("\n🧪 Testing model responsiveness...")
            test_response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "deepseek-coder:6.7b",
                    "prompt": "Say 'ready'",
                    "stream": False,
                    "options": {"num_predict": 5}
                },
                timeout=30
            )
            
            if test_response.status_code == 200:
                print("✅ Model is loaded and ready!")
                return True
            else:
                print("⚠ Model might need time to load")
                return False
                
        else:
            print(f"❌ Ollama error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama. Make sure it's running:")
        print("   In a PowerShell window, run: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def interactive_chat():
    """Interactive chat interface"""
    print("=" * 60)
    print("💬 DIRECT OLLAMA CHAT INTERFACE")
    print("=" * 60)
    print()
    
    # Test connection
    if not test_ollama_connection():
        print("\n❌ Cannot connect to Ollama")
        return
    
    print("\n🎯 Ready to chat! Commands:")
    print("  • Type 'quit' or 'exit' to end")
    print("  • Type 'model <name>' to switch models")
    print("  • Type 'stream on/off' to toggle streaming")
    print("  • Type 'test' for a quick test")
    print("=" * 60)
    
    current_model = "deepseek-coder:6.7b"
    stream_mode = False
    
    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            elif user_input.lower() == 'test':
                print("🧪 Running test...")
                chat_with_ollama_direct("Say 'Hello, I am working'", current_model, False)
                continue
            
            elif user_input.lower().startswith('model '):
                new_model = user_input[6:].strip()
                current_model = new_model
                print(f"✅ Switched to model: {current_model}")
                continue
            
            elif user_input.lower() == 'stream on':
                stream_mode = True
                print("✅ Streaming enabled")
                continue
            
            elif user_input.lower() == 'stream off':
                stream_mode = False
                print("✅ Streaming disabled")
                continue
            
            # Send message
            start_time = time.time()
            chat_with_ollama_direct(user_input, current_model, stream_mode)
            elapsed = time.time() - start_time
            print(f"⏱️  Response time: {elapsed:.1f} seconds")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "test":
            test_ollama_connection()
        else:
            message = " ".join(sys.argv[1:])
            chat_with_ollama_direct(message)
    else:
        # Interactive mode
        interactive_chat()

if __name__ == "__main__":
    main()