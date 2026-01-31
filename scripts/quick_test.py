#!/usr/bin/env python3
import requests
import json
import time

def test_server():
    """Test if server is working"""
    print("🧪 Testing LLM Platform...")
    print("="*50)
    
    base_url = "http://localhost:8000"
    headers = {"Authorization": "Bearer default-api-key"}
    
    tests = [
        ("Health Check", "GET", "/health", None),
        ("List Models", "GET", "/api/models", None),
        ("Chat", "POST", "/api/chat", {"message": "Write Python hello world"})
    ]
    
    for test_name, method, endpoint, data in tests:
        print(f"\n🔍 {test_name}...")
        try:
            url = f"{base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            else:  # POST
                response = requests.post(
                    url, 
                    headers={**headers, "Content-Type": "application/json"},
                    json=data,
                    timeout=30
                )
            
            if response.status_code == 200:
                print(f"   ✅ Success: {response.status_code}")
                if endpoint == "/api/chat":
                    result = response.json()
                    print(f"   📝 Response: {result.get('message', '')[:100]}...")
                    if result.get('code_blocks'):
                        print(f"   📦 Code blocks: {len(result['code_blocks'])}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                
        except requests.ConnectionError:
            print(f"   ❌ Connection refused - Is server running?")
            return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "="*50)
    print("✅ All tests completed!")
    print("\n📊 Server is working correctly!")
    print("\n🎉 Access URLs:")
    print("   • API: http://localhost:8000")
    print("   • Docs: http://localhost:8000/docs")
    print("   • Health: http://localhost:8000/health")
    
    return True

if __name__ == "__main__":
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    for i in range(30):
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✅ Server is responding!")
                break
        except:
            print(".", end="", flush=True)
            time.sleep(1)
    else:
        print("\n❌ Server not responding after 30 seconds")
        print("   Please start the server first:")
        print("   python run.py")
        exit(1)
    
    # Run tests
    test_server()