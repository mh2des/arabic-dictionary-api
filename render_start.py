#!/usr/bin/env python3
"""
Render.com startup script for Arabic Dictionary API
Optimized for Render's deployment environment
"""

import os
import sys
import sqlite3
import gzip
import shutil
import time

def setup_database_for_render():
    """Setup the comprehensive database for Render deployment."""
    print("🚀 Setting up Arabic Dictionary for Render...")
    
    # Create app directory
    os.makedirs('app', exist_ok=True)
    
    # Check for compressed database
    compressed_file = "arabic_dict.db.gz"
    
    if os.path.exists(compressed_file):
        print(f"📦 Found compressed database: {compressed_file}")
        
        compressed_size = os.path.getsize(compressed_file) / (1024 * 1024)
        print(f"📦 Compressed size: {compressed_size:.1f}MB")
        
        if compressed_size > 15:  # 18MB compressed
            target_path = 'app/arabic_dict.db'
            print(f"📦 Decompressing to: {target_path}")
            
            try:
                with gzip.open(compressed_file, 'rb') as f_in:
                    with open(target_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Verify
                file_size = os.path.getsize(target_path) / (1024 * 1024)
                print(f"📊 Decompressed size: {file_size:.1f}MB")
                
                if file_size > 100:  # 172MB uncompressed
                    conn = sqlite3.connect(target_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM entries")
                    count = cursor.fetchone()[0]
                    conn.close()
                    
                    if count > 100000:  # 101,331 entries
                        print(f"✅ Database ready: {count} entries")
                        
                        # Create additional symlinks
                        for symlink_name in ['comprehensive_arabic_dict.db', 'real_arabic_dict.db']:
                            symlink_path = f'app/{symlink_name}'
                            try:
                                if os.path.exists(symlink_path):
                                    os.remove(symlink_path)
                                shutil.copy2(target_path, symlink_path)
                                print(f"📋 Created: {symlink_name}")
                            except Exception as e:
                                print(f"⚠️ Could not create {symlink_name}: {e}")
                        
                        return True
                    else:
                        print(f"❌ Database too small: {count} entries")
                else:
                    print(f"❌ Decompressed file too small: {file_size:.1f}MB")
            except Exception as e:
                print(f"❌ Decompression failed: {e}")
        else:
            print(f"❌ Compressed file too small: {compressed_size:.1f}MB")
    else:
        print(f"❌ Compressed database not found: {compressed_file}")
    
    return False

def main():
    print("=== Arabic Dictionary API - Render Deployment ===")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    # Setup database
    if setup_database_for_render():
        print("🎉 Database setup successful!")
    else:
        print("⚠️ Database setup failed, using fallback")
    
    # Get port from environment
    port = int(os.environ.get('PORT', 8000))
    print(f"🌐 Starting server on port {port}")
    
    # Start the FastAPI server
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
