#!/usr/bin/env python3
"""
Complete Dialect System Testing and Deployment Guide
Run this script to test your dialect endpoints locally before deployment
"""
import sys
import os
import time
import requests
import subprocess
import json
from pathlib import Path

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_core_dialect_service():
    """Test the core dialect translation service directly"""
    print("=" * 60)
    print("🧪 TESTING CORE DIALECT SERVICE")
    print("=" * 60)
    
    try:
        from services.dialect_translator import ArabicDialectTranslator
        
        dialect_json_path = 'app/data/arabic_dialect_dictionary_enriched (1).json'
        main_db_path = 'app/arabic_dict.db'
        
        translator = ArabicDialectTranslator(dialect_json_path, main_db_path)
        print(f"✅ Translator initialized with {len(translator.supported_dialects)} dialects")
        
        # Test key functionality
        test_cases = [
            ('ابغى', 'Gulf dialect word'),
            ('عايز', 'Egyptian dialect word'), 
            ('بدي', 'Levantine dialect word'),
            ('شنو', 'Sudanese dialect word')
        ]
        
        success_count = 0
        for word, description in test_cases:
            try:
                result = translator.translate_dialect_to_fusha(word)
                if result['found']:
                    trans = result['translations'][0]
                    print(f"✅ {word} -> {trans['fusha']} ({trans['english']}) [{trans['dialect']}]")
                    success_count += 1
                else:
                    print(f"❌ {word} -> Not found")
            except Exception as e:
                print(f"❌ {word} -> Error: {e}")
        
        print(f"\n📊 Core Service: {success_count}/{len(test_cases)} tests passed")
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"❌ Core service initialization failed: {e}")
        return False

def test_api_server():
    """Test the FastAPI server and endpoints"""
    print("\n" + "=" * 60)
    print("🌐 TESTING API SERVER")
    print("=" * 60)
    
    # Start server
    print("Starting FastAPI server...")
    server_process = None
    
    try:
        # Start server in background
        server_process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 'app.main:app', '--port', '8080'
        ], cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(5)
        
        base_url = 'http://127.0.0.1:8080'
        
        # Test 1: Check if server is running
        try:
            response = requests.get(f'{base_url}/health', timeout=5)
            if response.status_code == 200:
                print("✅ Server is running")
            else:
                print(f"⚠️ Server responds with status {response.status_code}")
        except Exception as e:
            print(f"❌ Server not responding: {e}")
            return False
        
        # Test 2: Check available routes
        try:
            response = requests.get(f'{base_url}/openapi.json', timeout=5)
            if response.status_code == 200:
                openapi = response.json()
                paths = list(openapi.get('paths', {}).keys())
                
                # Look for dialect routes
                dialect_routes = [p for p in paths if 'dialect' in p.lower()]
                
                print(f"📋 Total API routes: {len(paths)}")
                if dialect_routes:
                    print("✅ Dialect routes found:")
                    for route in sorted(dialect_routes):
                        print(f"   {route}")
                else:
                    print("⚠️ No dialect routes found in OpenAPI spec")
                    print("Available routes:")
                    for route in sorted(paths)[:10]:
                        print(f"   {route}")
                
        except Exception as e:
            print(f"❌ Could not get OpenAPI spec: {e}")
        
        # Test 3: Try direct API calls if enhanced endpoint exists
        enhanced_endpoint_works = False
        try:
            test_word = 'ابغى'
            response = requests.get(f'{base_url}/enhanced/dialect/translate', 
                                 params={'word': test_word, 'is_dialect': 'true'}, 
                                 timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('translations'):
                    print("✅ Enhanced dialect endpoint working")
                    enhanced_endpoint_works = True
                else:
                    print("⚠️ Enhanced dialect endpoint returns empty results")
            else:
                print(f"❌ Enhanced dialect endpoint failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Enhanced dialect endpoint error: {e}")
        
        return enhanced_endpoint_works
        
    except Exception as e:
        print(f"❌ Server testing failed: {e}")
        return False
        
    finally:
        # Clean up server process
        if server_process:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("🛑 Server stopped")

def check_deployment_readiness():
    """Check if the system is ready for deployment"""
    print("\n" + "=" * 60)
    print("🚀 DEPLOYMENT READINESS CHECK")
    print("=" * 60)
    
    checks = []
    
    # Check 1: Required files exist
    required_files = [
        'app/main.py',
        'app/services/dialect_translator.py',
        'app/data/arabic_dialect_dictionary_enriched (1).json',
        'app/arabic_dict.db',
        'requirements.txt'
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    checks.append(len(missing_files) == 0)
    
    # Check 2: JSON data size
    json_path = 'app/data/arabic_dialect_dictionary_enriched (1).json'
    if os.path.exists(json_path):
        size_mb = os.path.getsize(json_path) / (1024 * 1024)
        print(f"✅ Dialect JSON size: {size_mb:.1f} MB")
        checks.append(size_mb > 1.0)  # Should be > 1MB
    else:
        checks.append(False)
    
    # Check 3: Database exists and has data
    if os.path.exists('app/arabic_dict.db'):
        size_mb = os.path.getsize('app/arabic_dict.db') / (1024 * 1024)
        print(f"✅ Main database size: {size_mb:.1f} MB")
        checks.append(size_mb > 10.0)  # Should be > 10MB
    else:
        checks.append(False)
    
    return all(checks)

def generate_deployment_commands():
    """Generate deployment commands for different platforms"""
    print("\n" + "=" * 60)
    print("📋 DEPLOYMENT COMMANDS")
    print("=" * 60)
    
    print("\n🔹 Local Development:")
    print("   uvicorn app.main:app --reload --port 8000")
    
    print("\n🔹 Production (Local):")
    print("   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4")
    
    print("\n🔹 Railway Deployment:")
    print("   1. Ensure railway.json or Procfile exists")
    print("   2. Run: railway login")
    print("   3. Run: railway link [your-project]")
    print("   4. Run: railway up")
    
    print("\n🔹 Render Deployment:")
    print("   1. Connect your GitHub repo to Render")
    print("   2. Set build command: pip install -r requirements.txt")
    print("   3. Set start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT")
    
    print("\n🔹 Docker Deployment:")
    print("   docker build -t arabic-dict-api .")
    print("   docker run -p 8000:8000 arabic-dict-api")

def main():
    """Main testing function"""
    print("🎯 ARABIC DIALECT SYSTEM - TESTING & DEPLOYMENT")
    print("=" * 60)
    
    # Test 1: Core Service
    core_works = test_core_dialect_service()
    
    # Test 2: API Server
    api_works = test_api_server()
    
    # Test 3: Deployment Readiness
    deploy_ready = check_deployment_readiness()
    
    # Generate deployment commands
    generate_deployment_commands()
    
    # Final Report
    print("\n" + "=" * 60)
    print("📊 FINAL REPORT")
    print("=" * 60)
    
    print(f"🧪 Core Dialect Service: {'✅ WORKING' if core_works else '❌ ISSUES'}")
    print(f"🌐 API Server: {'✅ WORKING' if api_works else '❌ ISSUES'}")
    print(f"🚀 Deployment Ready: {'✅ YES' if deploy_ready else '❌ NO'}")
    
    if core_works and deploy_ready:
        print("\n🎉 SYSTEM STATUS: READY FOR DEPLOYMENT!")
        print("\n📌 Next Steps:")
        print("   1. Choose your deployment platform (Railway, Render, etc.)")
        print("   2. Update environment variables if needed")
        print("   3. Deploy using the commands shown above")
        print("   4. Test your deployed endpoints")
        
        print("\n📱 Flutter Integration:")
        print("   Base URL: https://your-deployed-app.com")
        print("   Dialect Endpoint: /enhanced/dialect/translate")
        print("   Example: GET /enhanced/dialect/translate?word=ابغى&is_dialect=true")
        
    else:
        print("\n⚠️ ISSUES DETECTED - Fix before deployment:")
        if not core_works:
            print("   - Core dialect service has issues")
        if not api_works:
            print("   - API server endpoints not working")
        if not deploy_ready:
            print("   - Missing required files or dependencies")

if __name__ == "__main__":
    main()
