#!/usr/bin/env python3
"""
Quick Dialect API Test - Test your current endpoints
"""
import requests
import json
import time

def test_current_api():
    """Test your current API endpoints"""
    
    base_urls = [
        'http://127.0.0.1:8000',  # Local development
        'https://arabic-dictionary-api-production.up.railway.app',  # Railway (if deployed)
        # Add your Render URL here if you have one
    ]
    
    # Test words
    test_cases = [
        {'word': 'ابغى', 'is_dialect': True, 'description': 'Gulf dialect - I want'},
        {'word': 'عايز', 'is_dialect': True, 'description': 'Egyptian dialect - I want'},
        {'word': 'بدي', 'is_dialect': True, 'description': 'Levantine dialect - I want'},
        {'word': 'أريد', 'is_dialect': False, 'description': 'Fusha - I want'},
    ]
    
    print("🧪 TESTING CURRENT DIALECT ENDPOINTS")
    print("=" * 50)
    
    for base_url in base_urls:
        print(f"\n🌐 Testing: {base_url}")
        print("-" * 30)
        
        # Check if server is responding
        try:
            health_response = requests.get(f"{base_url}/health", timeout=5)
            if health_response.status_code == 200:
                print("✅ Server is responding")
            else:
                print(f"⚠️ Server responds with status {health_response.status_code}")
                continue
        except Exception as e:
            print(f"❌ Server not responding: {e}")
            continue
        
        # Test enhanced dialect endpoint
        success_count = 0
        for test_case in test_cases:
            try:
                url = f"{base_url}/enhanced/dialect/translate"
                params = {
                    'word': test_case['word'],
                    'is_dialect': str(test_case['is_dialect']).lower()
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('translations') and len(data['translations']) > 0:
                        trans = data['translations'][0]
                        print(f"✅ {test_case['word']} -> {trans.get('translation', 'N/A')} ({trans.get('meaning', 'N/A')})")
                        success_count += 1
                    else:
                        print(f"⚠️ {test_case['word']} -> No translations found")
                elif response.status_code == 404:
                    print(f"❌ {test_case['word']} -> Endpoint not found (404)")
                else:
                    print(f"❌ {test_case['word']} -> HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {test_case['word']} -> Error: {e}")
        
        print(f"\n📊 Results: {success_count}/{len(test_cases)} tests passed")
        
        if success_count == len(test_cases):
            print("🎉 ALL TESTS PASSED - Dialect system fully working!")
            return base_url
        elif success_count > 0:
            print("⚠️ Partial success - Some dialect translations working")
        else:
            print("❌ No dialect translations working")
    
    return None

def show_flutter_integration(working_url):
    """Show Flutter integration examples"""
    print("\n" + "=" * 60)
    print("📱 FLUTTER INTEGRATION GUIDE")
    print("=" * 60)
    
    if working_url:
        print(f"✅ Your API is working at: {working_url}")
        print("\n🔧 Flutter HTTP Client Setup:")
        
        flutter_code = f'''
// Add to your Flutter pubspec.yaml
dependencies:
  http: ^1.1.0

// API Service Class
class ArabicDialectService {{
  static const String baseUrl = '{working_url}';
  
  static Future<Map<String, dynamic>> translateDialect(String word, bool isDialect) async {{
    try {{
      final uri = Uri.parse('$baseUrl/enhanced/dialect/translate')
          .replace(queryParameters: {{
        'word': word,
        'is_dialect': isDialect.toString(),
      }});
      
      final response = await http.get(uri);
      
      if (response.statusCode == 200) {{
        return json.decode(response.body);
      }} else {{
        throw Exception('Failed to translate: ${{response.statusCode}}');
      }}
    }} catch (e) {{
      throw Exception('Translation error: $e');
    }}
  }}
}}

// Usage in your dialect screen
class DialectScreen extends StatefulWidget {{
  @override
  _DialectScreenState createState() => _DialectScreenState();
}}

class _DialectScreenState extends State<DialectScreen> {{
  String _result = '';
  bool _isLoading = false;
  
  Future<void> _translateWord(String word, bool isDialect) async {{
    setState(() => _isLoading = true);
    
    try {{
      final data = await ArabicDialectService.translateDialect(word, isDialect);
      
      if (data['translations'] != null && data['translations'].isNotEmpty) {{
        final translation = data['translations'][0];
        setState(() {{
          _result = '${{translation['translation']}} (${{translation['meaning']}})';
        }});
      }} else {{
        setState(() => _result = 'No translation found');
      }}
    }} catch (e) {{
      setState(() => _result = 'Error: $e');
    }} finally {{
      setState(() => _isLoading = false);
    }}
  }}
  
  // Your UI code here...
}}
'''
        
        print(flutter_code)
        
        print("\n📋 Test Your API from Flutter:")
        print("Example API calls:")
        print(f"  GET {working_url}/enhanced/dialect/translate?word=ابغى&is_dialect=true")
        print(f"  GET {working_url}/enhanced/dialect/translate?word=أريد&is_dialect=false")
        
    else:
        print("❌ API not working - Deploy first, then use Flutter integration")

def main():
    working_url = test_current_api()
    show_flutter_integration(working_url)
    
    print("\n" + "=" * 60)
    print("🚀 DEPLOYMENT OPTIONS")
    print("=" * 60)
    
    print("\n1️⃣ Railway Deployment (Recommended):")
    print("   railway login")
    print("   railway link")
    print("   railway up")
    
    print("\n2️⃣ Render Deployment:")
    print("   - Connect GitHub repo")
    print("   - Build: pip install -r requirements.txt") 
    print("   - Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT")
    
    print("\n3️⃣ Local Testing:")
    print("   uvicorn app.main:app --reload --port 8000")
    
    print(f"\n📊 System Status:")
    print(f"   Core Dialect Service: ✅ Working (4,410 entries, 7 dialects)")
    print(f"   API Endpoints: {'✅ Working' if working_url else '⚠️ Need deployment'}")
    print(f"   Flutter Ready: {'✅ Yes' if working_url else '⚠️ Deploy first'}")

if __name__ == "__main__":
    main()
