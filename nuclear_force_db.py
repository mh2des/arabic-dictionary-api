#!/usr/bin/env python3
"""
NUCLEAR OPTION: Force Railway to completely refresh and use the comprehensive database.
This script will aggressively force the deployment of our 101,331-entry database.
"""

import os
import sys
import sqlite3
import gzip
import shutil
import time
from pathlib import Path

def nuclear_force_comprehensive_db():
    """Nuclear option to force comprehensive database deployment."""
    
    print("💥 NUCLEAR FORCE DEPLOYMENT - COMPREHENSIVE DATABASE")
    print("=" * 60)
    print("🎯 Target: FORCE Railway to use 101,331 entries")
    print("=" * 60)
    
    # Step 1: Remove ALL cached databases
    cache_locations = [
        "/app/app/arabic_dict.db",
        "/app/app/real_arabic_dict.db", 
        "/app/app/comprehensive_arabic_dict.db",
        "/app/arabic_dict.db",
        "/app/real_arabic_dict.db",
        "app/arabic_dict.db",
        "app/real_arabic_dict.db",
        "app/comprehensive_arabic_dict.db"
    ]
    
    print("🗑️  NUKING ALL CACHED DATABASES...")
    for cache_path in cache_locations:
        if os.path.exists(cache_path):
            try:
                file_size = os.path.getsize(cache_path) / (1024 * 1024)
                os.remove(cache_path)
                print(f"💣 NUKED: {cache_path} ({file_size:.1f}MB)")
            except Exception as e:
                print(f"⚠️  Could not nuke {cache_path}: {e}")
    
    # Step 2: Force create comprehensive database with timestamp
    timestamp = int(time.time())
    force_db_name = f"FORCE_COMPREHENSIVE_{timestamp}.db"
    
    print(f"🚀 FORCE CREATING: {force_db_name}")
    
    # Find our compressed database
    compressed_paths = [
        "/app/arabic_dict.db.gz",
        os.path.join(os.path.dirname(__file__), "arabic_dict.db.gz"),
        "arabic_dict.db.gz"
    ]
    
    deployed_path = None
    
    for compressed_path in compressed_paths:
        if os.path.exists(compressed_path):
            print(f"📦 FOUND COMPRESSED DB: {compressed_path}")
            
            compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)
            print(f"📦 Size: {compressed_size:.1f}MB")
            
            if compressed_size > 15:  # Our 18MB compressed DB
                # Create target directory
                target_dir = "/app/app"
                os.makedirs(target_dir, exist_ok=True)
                
                # Force decompress with timestamp name
                force_path = os.path.join(target_dir, force_db_name)
                
                print(f"💥 FORCE DECOMPRESSING TO: {force_path}")
                
                try:
                    with gzip.open(compressed_path, 'rb') as f_in:
                        with open(force_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Verify the forced database
                    file_size = os.path.getsize(force_path) / (1024 * 1024)
                    print(f"💪 FORCED DB SIZE: {file_size:.1f}MB")
                    
                    if file_size > 100:  # Should be ~172MB
                        conn = sqlite3.connect(force_path)
                        cursor = conn.cursor()
                        
                        # Get table info
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = cursor.fetchall()
                        print(f"📋 Tables: {[t[0] for t in tables]}")
                        
                        cursor.execute("SELECT COUNT(*) FROM entries")
                        count = cursor.fetchone()[0]
                        
                        if count > 100000:  # FORCE VERIFICATION
                            print(f"💥 FORCED SUCCESS: {count} entries")
                            
                            # Get sample of complex words
                            cursor.execute("SELECT lemma, root, pos FROM entries WHERE LENGTH(lemma) > 6 LIMIT 10")
                            complex_words = cursor.fetchall()
                            
                            print("🔥 COMPLEX WORDS VERIFIED:")
                            for word, root, pos in complex_words:
                                print(f"   {word} (root: {root}, pos: {pos})")
                            
                            conn.close()
                            deployed_path = force_path
                            
                            # FORCE SYMLINKS TO ALL EXPECTED PATHS
                            force_paths = [
                                "/app/app/arabic_dict.db",
                                "/app/app/real_arabic_dict.db",
                                "/app/app/comprehensive_arabic_dict.db",
                                "app/arabic_dict.db",
                                "app/real_arabic_dict.db"
                            ]
                            
                            print("🔗 FORCING SYMLINKS...")
                            for target_path in force_paths:
                                try:
                                    # Ensure directory exists
                                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                                    
                                    # Remove if exists
                                    if os.path.exists(target_path):
                                        os.remove(target_path)
                                    
                                    # Try symlink first
                                    try:
                                        os.symlink(force_path, target_path)
                                        print(f"🔗 SYMLINKED: {target_path}")
                                    except:
                                        # Force copy if symlink fails
                                        shutil.copy2(force_path, target_path)
                                        print(f"📋 FORCE COPIED: {target_path}")
                                        
                                except Exception as e:
                                    print(f"⚠️  Could not force {target_path}: {e}")
                            
                            break
                        else:
                            conn.close()
                            print(f"❌ FORCED DB TOO SMALL: {count} entries")
                    else:
                        print(f"❌ DECOMPRESSED FILE TOO SMALL: {file_size:.1f}MB")
                        
                except Exception as e:
                    print(f"❌ FORCE DECOMPRESSION FAILED: {e}")
            else:
                print(f"❌ COMPRESSED FILE TOO SMALL: {compressed_size:.1f}MB")
    
    if deployed_path:
        # Create force signal files
        signal_files = [
            "/app/FORCE_COMPREHENSIVE_DB.txt",
            "/app/app/FORCE_COMPREHENSIVE_DB.txt",
            "FORCE_COMPREHENSIVE_DB.txt"
        ]
        
        print("📢 CREATING FORCE SIGNALS...")
        for signal_file in signal_files:
            try:
                os.makedirs(os.path.dirname(signal_file), exist_ok=True)
                with open(signal_file, 'w') as f:
                    f.write(f"{deployed_path}\n{timestamp}\n101331_ENTRIES_FORCED")
                print(f"📢 SIGNAL CREATED: {signal_file}")
            except Exception as e:
                print(f"⚠️  Signal failed: {signal_file} - {e}")
        
        print(f"🎉 NUCLEAR FORCE SUCCESS: {deployed_path}")
        return deployed_path
    else:
        print("💥 NUCLEAR FORCE FAILED")
        return None

if __name__ == "__main__":
    print("☢️  INITIATING NUCLEAR FORCE DEPLOYMENT...")
    result = nuclear_force_comprehensive_db()
    
    if result:
        print(f"✅ NUCLEAR SUCCESS: {result}")
        sys.exit(0)
    else:
        print("❌ NUCLEAR FAILURE")
        sys.exit(1)
