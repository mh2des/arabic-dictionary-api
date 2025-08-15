#!/usr/bin/env python3
"""
🚀 RAILWAY DEPLOYMENT SCRIPT
============================

This script helps you deploy your Arabic Dictionary API to Railway.
Run this script to get step-by-step deployment instructions.
"""

import os
import subprocess
import json

def check_deployment_readiness():
    """Check if the project is ready for deployment."""
    print("🔍 CHECKING DEPLOYMENT READINESS...")
    print("=" * 40)
    
    # Check required files
    required_files = [
        'railway.json',
        'requirements.txt', 
        'Procfile',
        'runtime.txt',
        'app/main.py',
        'app/arabic_dict.db'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        return False
    
    # Check database
    try:
        import sqlite3
        conn = sqlite3.connect('app/arabic_dict.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM entries")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"✅ Database: {count:,} entries")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Test API
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get('/')
        if response.status_code == 200:
            print("✅ API test: PASSED")
        else:
            print(f"❌ API test: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False
    
    print("\n🎉 PROJECT IS READY FOR DEPLOYMENT!")
    return True

def show_railway_instructions():
    """Show Railway deployment instructions."""
    print("\n🚀 RAILWAY DEPLOYMENT INSTRUCTIONS")
    print("=" * 40)
    
    print("""
STEP 1: CREATE GITHUB REPOSITORY
1. Create a new repository on GitHub
2. Push your project to GitHub:
   
   git init
   git add .
   git commit -m "Initial commit: Arabic Dictionary API"
   git branch -M main
   git remote add origin <your-repo-url>
   git push -u origin main

STEP 2: DEPLOY TO RAILWAY
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway will automatically:
   - Detect FastAPI
   - Install dependencies
   - Start the application

STEP 3: CONFIGURE (OPTIONAL)
1. Set custom domain (if needed)
2. Configure environment variables (none needed for basic setup)
3. Monitor deployment logs

STEP 4: TEST DEPLOYMENT
1. Wait for deployment to complete (2-3 minutes)
2. Visit your Railway URL
3. Test endpoints:
   - https://your-app.railway.app/
   - https://your-app.railway.app/docs
   - https://your-app.railway.app/api/suggest?q=كت

STEP 5: FLUTTER INTEGRATION
Use your Railway URL as the base URL in your Flutter app:

```dart
class ArabicDictionaryAPI {
  static const String baseUrl = 'https://your-app.railway.app';
  
  static Future<List<String>> getSuggestions(String query) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/suggest?q=$query&limit=10')
    );
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return List<String>.from(data['suggestions']);
    }
    return [];
  }
}
```

🎯 EXPECTED PERFORMANCE:
- Deployment time: 2-3 minutes
- Cold start: < 2 seconds
- API response: < 100ms
- Cost: FREE (500 hours/month)

🎉 CONGRATULATIONS!
Your Arabic Dictionary API will be live and ready for Flutter integration!
""")

def main():
    """Main deployment script."""
    print("🚀 ARABIC DICTIONARY - RAILWAY DEPLOYMENT")
    print("=" * 50)
    
    if check_deployment_readiness():
        show_railway_instructions()
        
        print("\n🤖 NEXT STEPS:")
        print("1. Create GitHub repository")
        print("2. Push code to GitHub") 
        print("3. Deploy to Railway")
        print("4. Test your live API")
        print("5. Integrate with Flutter app")
        
        print("\n💡 NEED HELP?")
        print("- Railway docs: https://docs.railway.app")
        print("- FastAPI docs: https://fastapi.tiangolo.com")
        print("- Your API docs: https://your-app.railway.app/docs")
        
    else:
        print("\n❌ DEPLOYMENT NOT READY")
        print("Please fix the issues above before deploying.")

if __name__ == "__main__":
    main()
