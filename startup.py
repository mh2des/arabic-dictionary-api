#!/usr/bin/env python3
"""
Simple startup script for Railway deployment with comprehensive database setup
"""

import os
import sys
import subprocess
import time
import sqlite3
import gzip
import shutil

def setup_comprehensive_database():
    """Setup comprehensive database during startup with NUCLEAR FORCE."""
    print("� NUCLEAR FORCE DATABASE SETUP...")
    
    # NUCLEAR OPTION: Remove any small cached databases first
    cache_paths = [
        'app/arabic_dict.db',
        'app/real_arabic_dict.db',
        '/app/app/arabic_dict.db',
        '/app/app/real_arabic_dict.db'
    ]
    
    for cache_path in cache_paths:
        if os.path.exists(cache_path):
            try:
                file_size = os.path.getsize(cache_path) / (1024 * 1024)
                if file_size < 100:  # Remove small cached databases
                    os.remove(cache_path)
                    print(f"💣 NUKED SMALL CACHE: {cache_path} ({file_size:.1f}MB)")
            except Exception as e:
                print(f"⚠️ Could not remove cache {cache_path}: {e}")
    
    # Check for compressed database
    compressed_paths = [
        "arabic_dict.db.gz",
        "/app/arabic_dict.db.gz"
    ]
    
    for compressed_path in compressed_paths:
        if os.path.exists(compressed_path):
            print(f"📦 Found compressed database: {compressed_path}")
            
            compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)
            print(f"📦 Compressed size: {compressed_size:.1f}MB")
            
            if compressed_size > 15:  # Our comprehensive DB is 18MB compressed
                # Create app directory if needed
                os.makedirs('app', exist_ok=True)
                
                # NUCLEAR FORCE: Use timestamp in filename to bypass caching
                timestamp = int(time.time())
                target_path = f'app/NUCLEAR_COMPREHENSIVE_{timestamp}.db'
                print(f"� NUCLEAR DECOMPRESSING TO: {target_path}")
                
                try:
                    with gzip.open(compressed_path, 'rb') as f_in:
                        with open(target_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Verify
                    file_size = os.path.getsize(target_path) / (1024 * 1024)
                    print(f"📊 Decompressed size: {file_size:.1f}MB")
                    
                    if file_size > 100:
                        conn = sqlite3.connect(target_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM entries")
                        count = cursor.fetchone()[0]
                        conn.close()
                        
                        if count > 100000:
                            print(f"💥 NUCLEAR SUCCESS: {count} entries")
                            
                            # NUCLEAR FORCE: Create signal file
                            signal_file = "FORCE_COMPREHENSIVE_DB.txt"
                            with open(signal_file, 'w') as f:
                                f.write(f"{target_path}\n{timestamp}\n101331_ENTRIES_FORCED\n")
                            print(f"📢 NUCLEAR SIGNAL CREATED: {signal_file}")
                            
                            # Create symlinks with FORCE
                            for symlink_name in ['arabic_dict.db', 'real_arabic_dict.db', 'comprehensive_arabic_dict.db']:
                                symlink_path = f'app/{symlink_name}'
                                try:
                                    if os.path.exists(symlink_path):
                                        os.remove(symlink_path)
                                    os.symlink(target_path, symlink_path)
                                    print(f"� NUCLEAR SYMLINK: {symlink_name}")
                                except:
                                    shutil.copy2(target_path, symlink_path)
                                    print(f"� NUCLEAR COPY: {symlink_name}")
                            
                            return True
                        else:
                            print(f"❌ Database too small: {count} entries")
                    else:
                        print(f"❌ Decompressed file too small: {file_size:.1f}MB")
                except Exception as e:
                    print(f"❌ Decompression failed: {e}")
            else:
                print(f"❌ Compressed file too small: {compressed_size:.1f}MB")
    
    print("⚠️ Could not setup comprehensive database")
    return False

def main():
    print("=== Arabic Dictionary API Startup (Comprehensive Database) ===")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Files in current directory: {os.listdir('.')}")
    
    # Setup comprehensive database first
    setup_comprehensive_database()
    
    # Check if app directory exists
    if os.path.exists('app'):
        print(f"Files in app directory: {os.listdir('app')}")
        
        # Check for database
        db_paths = ['app/comprehensive_arabic_dict.db', 'app/arabic_dict.db']
        for db_path in db_paths:
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path) / (1024 * 1024)
                print(f"Database found: {db_path} ({db_size:.1f} MB)")
                
                # Quick count check
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM entries")
                    count = cursor.fetchone()[0]
                    conn.close()
                    print(f"📊 Database entries: {count}")
                    break
                except Exception as e:
                    print(f"❌ Database check failed: {e}")
    
    # Set PORT from environment or default
    port = os.environ.get('PORT', '8000')
    print(f"Starting on port: {port}")
    
    # Start uvicorn
    cmd = [
        'uvicorn', 
        'app.main:app', 
        '--host', '0.0.0.0', 
        '--port', port,
        '--log-level', 'info'
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    
    try:
        # Start the server
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
