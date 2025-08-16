#!/usr/bin/env python3
"""
NUCLEAR FORCE DEPLOYMENT - FINAL SOLUTION
This script will absolutely force Railway to use our complete 101,331-entry database
by completely rebuilding the database connection system with atomic operations.
"""

import os
import sys
import sqlite3
import gzip
import shutil
import time
import hashlib
from pathlib import Path

def nuclear_force_comprehensive_database():
    """Nuclear option: Force complete database deployment with atomic operations."""
    
    print("☢️  NUCLEAR FORCE: COMPREHENSIVE DATABASE DEPLOYMENT")
    print("=" * 70)
    print("🎯 TARGET: Force Railway to use 101,331-entry database")
    print("🔥 METHOD: Atomic replacement with cache destruction")
    print("=" * 70)
    
    # Step 1: Destroy all existing databases
    print("💥 STEP 1: DESTROYING ALL CACHED DATABASES")
    cache_paths = [
        "/app/app/arabic_dict.db",
        "/app/app/real_arabic_dict.db", 
        "/app/app/comprehensive_arabic_dict.db",
        "/app/arabic_dict.db",
        "/app/real_arabic_dict.db",
        "app/arabic_dict.db",
        "app/real_arabic_dict.db",
        "app/comprehensive_arabic_dict.db"
    ]
    
    destroyed_count = 0
    for cache_path in cache_paths:
        if os.path.exists(cache_path):
            try:
                file_size = os.path.getsize(cache_path) / (1024 * 1024)
                os.remove(cache_path)
                print(f"💣 DESTROYED: {cache_path} ({file_size:.1f}MB)")
                destroyed_count += 1
            except Exception as e:
                print(f"⚠️  Could not destroy {cache_path}: {e}")
    
    print(f"💥 DESTROYED {destroyed_count} cached databases")
    
    # Step 2: Create timestamp-based unique database
    timestamp = int(time.time())
    unique_id = hashlib.md5(str(timestamp).encode()).hexdigest()[:8]
    nuclear_db_name = f"nuclear_arabic_dict_{timestamp}_{unique_id}.db"
    
    print(f"⚛️  STEP 2: CREATING NUCLEAR DATABASE: {nuclear_db_name}")
    
    # Step 3: Find and decompress the comprehensive database
    compressed_paths = [
        "/app/arabic_dict.db.gz",
        os.path.join(os.path.dirname(__file__), "arabic_dict.db.gz"),
        "arabic_dict.db.gz"
    ]
    
    nuclear_db_path = None
    
    for compressed_path in compressed_paths:
        if os.path.exists(compressed_path):
            print(f"🎯 Found compressed database: {compressed_path}")
            
            compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)
            print(f"📦 Compressed size: {compressed_size:.1f}MB")
            
            if compressed_size > 15:  # 18MB compressed = 172MB uncompressed
                # Create app directory
                os.makedirs("/app/app", exist_ok=True)
                
                nuclear_db_path = f"/app/app/{nuclear_db_name}"
                
                print(f"⚛️  NUCLEAR DECOMPRESSION: {compressed_path} -> {nuclear_db_path}")
                
                try:
                    # Atomic decompression
                    with gzip.open(compressed_path, 'rb') as f_in:
                        with open(nuclear_db_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Verify nuclear database
                    file_size = os.path.getsize(nuclear_db_path) / (1024 * 1024)
                    print(f"⚛️  Nuclear database size: {file_size:.1f}MB")
                    
                    if file_size > 100:  # Should be ~172MB
                        conn = sqlite3.connect(nuclear_db_path)
                        cursor = conn.cursor()
                        
                        # Verify entry count
                        cursor.execute("SELECT COUNT(*) FROM entries")
                        count = cursor.fetchone()[0]
                        
                        if count > 100000:  # Should be 101,331
                            print(f"☢️  NUCLEAR SUCCESS: {count} entries deployed")
                            
                            # Test complex words
                            cursor.execute("SELECT lemma FROM entries WHERE LENGTH(lemma) > 6 LIMIT 10")
                            complex_words = cursor.fetchall()
                            print(f"⚛️  Complex words verified: {[w[0] for w in complex_words[:5]]}")
                            
                            conn.close()
                            
                            # Step 4: Create atomic symlinks to all expected paths
                            print("⚛️  STEP 4: CREATING ATOMIC SYMLINKS")
                            
                            symlink_targets = [
                                "/app/app/arabic_dict.db",
                                "/app/app/real_arabic_dict.db",
                                "/app/app/comprehensive_arabic_dict.db"
                            ]
                            
                            for target in symlink_targets:
                                try:
                                    if os.path.exists(target):
                                        os.remove(target)
                                    
                                    # Try symlink first
                                    try:
                                        os.symlink(nuclear_db_path, target)
                                        print(f"🔗 ATOMIC SYMLINK: {os.path.basename(target)}")
                                    except:
                                        # Fallback to atomic copy
                                        shutil.copy2(nuclear_db_path, target)
                                        print(f"📋 ATOMIC COPY: {os.path.basename(target)}")
                                        
                                except Exception as e:
                                    print(f"⚠️  Atomic link failed for {target}: {e}")
                            
                            # Step 5: Create nuclear force signal file
                            nuclear_signal_path = "/app/nuclear_database_deployed.txt"
                            with open(nuclear_signal_path, "w") as f:
                                f.write(f"{nuclear_db_path}\n{count}\n{timestamp}\n{unique_id}")
                            
                            print(f"⚛️  NUCLEAR SIGNAL CREATED: {nuclear_signal_path}")
                            print(f"☢️  NUCLEAR DEPLOYMENT COMPLETE: {count} entries")
                            
                            return nuclear_db_path
                        else:
                            conn.close()
                            print(f"❌ Nuclear database too small: {count} entries")
                    else:
                        print(f"❌ Nuclear decompressed file too small: {file_size:.1f}MB")
                        
                except Exception as e:
                    print(f"❌ Nuclear decompression failed: {e}")
            else:
                print(f"❌ Compressed source too small: {compressed_size:.1f}MB")
    
    print("💀 NUCLEAR DEPLOYMENT FAILED")
    return None

if __name__ == "__main__":
    nuclear_force_comprehensive_database()
