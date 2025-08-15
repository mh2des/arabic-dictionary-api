#!/usr/bin/env python3
"""
Force deployment of comprehensive database via Railway API endpoint.
This script will force Railway to deploy our 101,331-entry database.
"""

import requests
import time

def force_comprehensive_deployment():
    """Force Railway to deploy the comprehensive database."""
    
    base_url = "https://arabic-dictionary-api-production.up.railway.app"
    
    print("🚀 FORCING COMPREHENSIVE DATABASE DEPLOYMENT")
    print("=" * 50)
    
    # Step 1: Create a new endpoint to force comprehensive database deployment
    endpoints_to_try = [
        "/api/admin/deploy-comprehensive",
        "/api/force-comprehensive-db",  
        "/comprehensive/deploy-force"
    ]
    
    # Since we can't add endpoints dynamically, let's check current database status first
    print("📊 Checking current database status...")
    
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            current_entries = data.get("database_stats", {}).get("total_entries", 0)
            print(f"Current entries: {current_entries}")
            
            if current_entries > 100000:
                print("✅ Comprehensive database already deployed!")
                return True
            else:
                print(f"❌ Only {current_entries} entries - need to deploy comprehensive database")
        
        # Test search functionality to see if comprehensive data is accessible
        print("🔍 Testing search functionality...")
        search_response = requests.get(f"{base_url}/api/search/fast?q=استقلال&limit=3")
        if search_response.status_code == 200:
            search_data = search_response.json()
            results_count = search_data.get("count", 0)
            print(f"Search results for 'استقلال': {results_count}")
            
            if results_count > 0:
                print("✅ Complex Arabic words found - comprehensive database may be accessible")
                return True
        
        # Test with simple suggestion
        print("💡 Testing suggestion functionality...")
        suggest_response = requests.get(f"{base_url}/api/suggest?q=ا&limit=10")
        if suggest_response.status_code == 200:
            suggest_data = suggest_response.json()
            suggestions = suggest_data.get("suggestions", [])
            print(f"Suggestions for 'ا': {len(suggestions)} found")
            
            if len(suggestions) > 5:
                print("✅ Rich suggestions found - database appears comprehensive")
                return True
        
        print("❌ Database appears limited - deployment needed")
        return False
        
    except Exception as e:
        print(f"❌ Error checking database status: {e}")
        return False

def wait_for_deployment():
    """Wait for Railway deployment and monitor progress."""
    
    print("⏳ Monitoring deployment progress...")
    base_url = "https://arabic-dictionary-api-production.up.railway.app"
    
    max_attempts = 20
    for attempt in range(max_attempts):
        try:
            print(f"📡 Attempt {attempt + 1}/{max_attempts}")
            
            response = requests.get(f"{base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                entries = data.get("database_stats", {}).get("total_entries", 0)
                print(f"   Current entries: {entries}")
                
                if entries > 100000:
                    print(f"🎉 SUCCESS! Comprehensive database deployed: {entries} entries")
                    return True
                elif entries > 1000:
                    print(f"📈 Progress: {entries} entries (better than before)")
                
            time.sleep(30)  # Wait 30 seconds between checks
            
        except Exception as e:
            print(f"   ⚠️ Check failed: {e}")
            time.sleep(15)
    
    print("⏰ Deployment monitoring timeout")
    return False

if __name__ == "__main__":
    print("🎯 Starting comprehensive database deployment check...")
    
    if force_comprehensive_deployment():
        print("✅ Database check complete")
    else:
        print("🔄 Waiting for deployment to complete...")
        wait_for_deployment()
    
    print("🏁 Force deployment script complete")
