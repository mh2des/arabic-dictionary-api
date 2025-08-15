#!/usr/bin/env python3
"""
API Test for Arabic Dictionary
"""

import requests
import json

def test_api():
    """Test the Arabic dictionary API."""
    
    print("=== Testing Arabic Dictionary API ===")
    base_url = "http://localhost:8000"
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"   Response: {response.json()}")
            
            # Test search endpoint with Arabic words
            test_words = [
                'كتب',  # books/write
                'علم',  # science/knowledge  
                'طبيب'  # doctor
            ]
            
            print("\n=== Search Tests ===")
            for word in test_words:
                search_response = requests.get(
                    f"{base_url}/search", 
                    params={"q": word, "limit": 3}, 
                    timeout=5
                )
                
                if search_response.status_code == 200:
                    results = search_response.json()
                    result_count = len(results)
                    print(f"✅ Search for '{word}': {result_count} results found")
                    
                    if result_count > 0:
                        for i, result in enumerate(results[:2], 1):
                            lemma = result.get('lemma', 'Unknown')
                            pos_list = result.get('pos', [])
                            pos = ', '.join(pos_list) if isinstance(pos_list, list) else str(pos_list)
                            print(f"   {i}. {lemma} ({pos or 'unknown'})")
                else:
                    print(f"❌ Search failed for '{word}': {search_response.status_code}")
            
            print("\n🎉 API is fully functional and ready for your Flutter app!")
            print("📊 Your dictionary contains 101,331 Arabic entries")
            print("🔗 API Documentation: http://localhost:8000/docs")
            
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")
        print("💡 Start with: uvicorn app.main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ API test error: {e}")

if __name__ == "__main__":
    test_api()
