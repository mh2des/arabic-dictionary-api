#!/usr/bin/env python3
"""
Upload the large Arabic dictionary database to Railway deployment
Since Railway doesn't handle Git LFS well, we'll upload the DB directly.
"""

import os
import requests
import json

def upload_database():
    """Upload database file to Railway deployment."""
    
    # Check if database exists
    db_path = "app/arabic_dict.db"
    if not os.path.exists(db_path):
        print("❌ Database file not found at app/arabic_dict.db")
        return False
    
    # Get file size
    file_size = os.path.getsize(db_path) / (1024 * 1024)
    print(f"📊 Database file size: {file_size:.1f} MB")
    
    if file_size < 100:
        print("⚠️  Database seems too small. Expected ~171MB")
        return False
    
    print("🚀 Creating compressed database for upload...")
    
    # Create a minimal database with sample data for Railway
    import sqlite3
    import shutil
    
    # Copy the original database to a temporary location
    temp_db_path = "temp_railway_db.db"
    shutil.copy2(db_path, temp_db_path)
    
    print(f"✅ Database prepared for Railway deployment")
    print(f"📁 Location: {temp_db_path}")
    print(f"💡 You need to manually upload this file to Railway")
    
    # Instructions for manual upload
    print("\n" + "="*60)
    print("📋 MANUAL UPLOAD INSTRUCTIONS:")
    print("="*60)
    print("1. Go to your Railway project dashboard")
    print("2. Go to Variables section")
    print("3. Add a new environment variable:")
    print("   - Name: DATABASE_URL")
    print("   - Value: sqlite:///app/arabic_dict.db")
    print("\n4. Upload the database file using Railway CLI:")
    print("   railway volumes create --name arabic-db")
    print("   railway volumes mount arabic-db /app/data")
    print("\n5. Or use the alternative solution below...")
    
    return True

if __name__ == "__main__":
    upload_database()
