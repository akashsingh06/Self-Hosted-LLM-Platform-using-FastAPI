#!/usr/bin/env python3
import requests
import json
import sys

class LLMChat:
    def __init__(self, base_url="http://localhost:8000", api_key="default-api-key"):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def test_connection(self):
        """Test if API is reachable"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API is reachable")
                return True
            else:
                print(f"❌ API returned status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            print(f"   Make sure server is running: python run.py")
            return False
    
    def get_models(self):
        """Get available models"""
        try:
            response = requests.get(
                f"{self.base_url}/api/models",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                models = response.json()
                print(f"📦 Available models ({len(models)}):")
                for model in models:
                    print(f"   • {model.get('name')} ({model.get('type', 'unknown')})")
                return models
            else:
                print(f"❌ Failed to get models: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error getting models: {e}")
            return []
    
    def chat(self, message, model="deepseek-coder:6.7b", stream=False):
        """Send chat message"""
        try:
            payload = {
                "message": message,
                "model_name": model,
                "stream": stream
            }
            
            if stream:
                # Streaming response
                print("🔄 Streaming response... (Press Ctrl+C to stop)")
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    headers=self.headers,
                    json=payload,
                    stream=True,
                    timeout=30
                )
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]  # Remove 'data: ' prefix
                            try:
                                chunk_data = json.loads(data)
                                if 'chunk' in chunk_data:
                                    print(chunk_data['chunk'], end='', flush=True)
                                if chunk_data.get('done'):
                                    print()
                                    break
                            except:
                                pass
            else:
                # Non-streaming response
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("\n" + "="*60)
                    print("🤖 ASSISTANT RESPONSE:")
                    print("="*60)
                    print(result.get("message", ""))
                    
                    # Show code blocks
                    code_blocks = result.get("code_blocks", [])
                    if code_blocks:
                        print("\n" + "="*60)
                        print(f"📦 EXTRACTED CODE BLOCKS ({len(code_blocks)}):")
                        print("="*60)
                        for i, block in enumerate(code_blocks, 1):
                            print(f"\n[{i}] Language: {block.get('language', 'unknown')}")
                            print("-"*40)
                            print(block.get('code', ''))
                    
                    print("\n" + "="*60)
                    return result
                else:
                    print(f"❌ Chat failed: {response.status_code}")
                    print(f"   Error: {response.text[:200]}")
                    return None
                    
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return None
    
    def interactive_chat(self):
        """Start interactive chat session"""
        print("💬 LLM CHAT INTERFACE")
        print("="*60)
        
        if not self.test_connection():
            return
        
        models = self.get_models()
        if not models:
            print("⚠ No models found, using default")
            model = "deepseek-coder:6.7b"
        else:
            model = models[0].get('name')
        
        print(f"\n📝 Using model: {model}")
        print("💡 Type 'quit' or 'exit' to end the chat")
        print("💡 Type 'model <name>' to switch models")
        print("💡 Type 'stream on/off' to toggle streaming")
        print("="*60)
        
        stream_mode = False
        
        while True:
            try:
                # Get user input
                user_input = input("\n👤 YOU: ").strip()
                
                if not user_input:
                    continue
                
                # Check for commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                elif user_input.lower().startswith('model '):
                    new_model = user_input[6:].strip()
                    if any(m.get('name') == new_model for m in models):
                        model = new_model
                        print(f"✅ Switched to model: {model}")
                    else:
                        print(f"❌ Model '{new_model}' not found")
                    continue
                
                elif user_input.lower() == 'stream on':
                    stream_mode = True
                    print("✅ Streaming enabled")
                    continue
                
                elif user_input.lower() == 'stream off':
                    stream_mode = False
                    print("✅ Streaming disabled")
                    continue
                
                # Send chat message
                print("\n⏳ Thinking...")
                self.chat(user_input, model, stream_mode)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main function"""
    chat = LLMChat()
    
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "test":
            chat.test_connection()
            chat.get_models()
        elif sys.argv[1] == "chat" and len(sys.argv) > 2:
            message = " ".join(sys.argv[2:])
            chat.chat(message)
        else:
            print("Usage:")
            print("  python chat_interface.py                 # Interactive mode")
            print("  python chat_interface.py test            # Test connection")
            print("  python chat_interface.py chat <message>  # Send single message")
    else:
        # Interactive mode
        chat.interactive_chat()

if __name__ == "__main__":
    main()