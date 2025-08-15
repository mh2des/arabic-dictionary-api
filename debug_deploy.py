#!/usr/bin/env python3
"""
Debug script to see what's happening with database deployment on Railway.
"""

import os
import sqlite3
import subprocess

def debug_railway_deployment():
    print("🔍 Railway Deployment Debug")
    print("=" * 50)
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python executable: {subprocess.check_output(['which', 'python3']).decode().strip()}")
    print(f"Environment variables:")
    for key, value in os.environ.items():
        if 'RAILWAY' in key or 'PORT' in key:
            print(f"  {key}: {value}")
    
    print("\n📁 File System Analysis:")
    
    # Check root directory
    if os.path.exists('/app'):
        print(f"Files in /app: {os.listdir('/app')}")
        
        # Check for our deployment script
        deploy_script = '/app/deploy_real_database.py'
        if os.path.exists(deploy_script):
            print(f"✅ Deploy script found: {deploy_script}")
        else:
            print(f"❌ Deploy script missing: {deploy_script}")
        
        # Check for compressed database
        compressed_db = '/app/arabic_dict.db.gz'
        if os.path.exists(compressed_db):
            size = os.path.getsize(compressed_db) / (1024 * 1024)
            print(f"✅ Compressed database found: {compressed_db} ({size:.1f} MB)")
        else:
            print(f"❌ Compressed database missing: {compressed_db}")
    
    # Check app directory
    if os.path.exists('/app/app'):
        files = os.listdir('/app/app')
        print(f"Files in /app/app: {files}")
        
        # Check for any databases
        for file in files:
            if file.endswith('.db'):
                path = os.path.join('/app/app', file)
                size = os.path.getsize(path) / (1024 * 1024)
                print(f"📊 Database found: {file} ({size:.1f} MB)")
                
                # Check entries count
                try:
                    conn = sqlite3.connect(path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM entries")
                    count = cursor.fetchone()[0]
                    print(f"   Entries: {count}")
                    
                    # Test for complex Arabic words
                    cursor.execute("SELECT lemma FROM entries WHERE lemma LIKE '%استقلال%' OR lemma LIKE '%محاضرة%' LIMIT 5")
                    complex_words = cursor.fetchall()
                    if complex_words:
                        print(f"   ✅ Contains complex Arabic words: {[w[0] for w in complex_words]}")
                    else:
                        print(f"   ❌ No complex Arabic words found")
                    
                    conn.close()
                except Exception as e:
                    print(f"   Error checking database: {e}")
    
    print("\n🚀 Testing Deployment System:")
    try:
        from deploy_real_database import download_real_database
        result = download_real_database()
        if result:
            print(f"✅ Deployment system succeeded: {result}")
        else:
            print(f"❌ Deployment system failed")
    except Exception as e:
        print(f"❌ Deployment system error: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    debug_railway_deployment()
