"""
Nuclear Force Emergency API Routes
"""

import os
import sys
import sqlite3
import gzip
import shutil
import time
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.post("/nuclear/force-comprehensive-db")
async def nuclear_force_comprehensive_db() -> Dict[str, Any]:
    """NUCLEAR OPTION: Force deploy comprehensive database bypassing all caches."""
    
    try:
        print("💥 NUCLEAR FORCE DEPLOYMENT INITIATED")
        
        # Step 1: Nuke all cached databases
        cache_locations = [
            "/app/app/arabic_dict.db",
            "/app/app/real_arabic_dict.db", 
            "/app/app/comprehensive_arabic_dict.db",
            "app/arabic_dict.db",
            "app/real_arabic_dict.db",
            "app/comprehensive_arabic_dict.db"
        ]
        
        nuked_files = []
        for cache_path in cache_locations:
            if os.path.exists(cache_path):
                try:
                    file_size = os.path.getsize(cache_path) / (1024 * 1024)
                    os.remove(cache_path)
                    nuked_files.append(f"{cache_path} ({file_size:.1f}MB)")
                except Exception as e:
                    print(f"Could not nuke {cache_path}: {e}")
        
        # Step 2: Force decompress with timestamp
        compressed_paths = [
            "/app/arabic_dict.db.gz",
            "arabic_dict.db.gz"
        ]
        
        for compressed_path in compressed_paths:
            if os.path.exists(compressed_path):
                compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)
                
                if compressed_size > 15:  # Our 18MB compressed DB
                    # Create timestamped database
                    timestamp = int(time.time())
                    os.makedirs("/app/app", exist_ok=True)
                    os.makedirs("app", exist_ok=True)
                    
                    nuclear_path = f"/app/app/NUCLEAR_FORCE_{timestamp}.db"
                    
                    # Force decompress
                    with gzip.open(compressed_path, 'rb') as f_in:
                        with open(nuclear_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Verify
                    file_size = os.path.getsize(nuclear_path) / (1024 * 1024)
                    
                    if file_size > 100:
                        conn = sqlite3.connect(nuclear_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM entries")
                        count = cursor.fetchone()[0]
                        
                        if count > 100000:
                            # Get sample words for verification
                            cursor.execute("SELECT lemma, root, pos FROM entries WHERE LENGTH(lemma) > 6 LIMIT 5")
                            sample_words = cursor.fetchall()
                            conn.close()
                            
                            # Force symlinks to all expected paths
                            force_paths = [
                                "/app/app/arabic_dict.db",
                                "/app/app/real_arabic_dict.db",
                                "/app/app/comprehensive_arabic_dict.db",
                                "app/arabic_dict.db",
                                "app/real_arabic_dict.db",
                                "app/comprehensive_arabic_dict.db"
                            ]
                            
                            created_links = []
                            for target_path in force_paths:
                                try:
                                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                                    if os.path.exists(target_path):
                                        os.remove(target_path)
                                    
                                    try:
                                        os.symlink(nuclear_path, target_path)
                                        created_links.append(f"symlink: {target_path}")
                                    except:
                                        shutil.copy2(nuclear_path, target_path)
                                        created_links.append(f"copy: {target_path}")
                                except Exception as e:
                                    print(f"Could not create {target_path}: {e}")
                            
                            # Create nuclear force signal
                            signal_files = [
                                "/app/NUCLEAR_FORCE_ACTIVE.txt",
                                "/app/app/NUCLEAR_FORCE_ACTIVE.txt"
                            ]
                            
                            for signal_file in signal_files:
                                try:
                                    os.makedirs(os.path.dirname(signal_file), exist_ok=True)
                                    with open(signal_file, 'w') as f:
                                        f.write(f"{nuclear_path}\n{timestamp}\n{count}_ENTRIES_NUCLEAR_FORCED\n")
                                except:
                                    pass
                            
                            return {
                                "status": "NUCLEAR_SUCCESS",
                                "message": "💥 NUCLEAR FORCE DEPLOYMENT SUCCESSFUL",
                                "database_path": nuclear_path,
                                "entries": count,
                                "file_size_mb": round(file_size, 1),
                                "compressed_size_mb": round(compressed_size, 1),
                                "nuked_files": nuked_files,
                                "created_links": created_links,
                                "sample_words": [{"lemma": w[0], "root": w[1], "pos": w[2]} for w in sample_words],
                                "timestamp": timestamp
                            }
                        else:
                            conn.close()
                            raise HTTPException(status_code=500, detail=f"Nuclear database too small: {count} entries")
                    else:
                        raise HTTPException(status_code=500, detail=f"Decompressed file too small: {file_size:.1f}MB")
                else:
                    raise HTTPException(status_code=500, detail=f"Compressed file too small: {compressed_size:.1f}MB")
        
        raise HTTPException(status_code=404, detail="No compressed database found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nuclear force failed: {str(e)}")

@router.get("/nuclear/status")
async def nuclear_status() -> Dict[str, Any]:
    """Check nuclear force deployment status."""
    
    signal_files = [
        "/app/NUCLEAR_FORCE_ACTIVE.txt",
        "/app/app/NUCLEAR_FORCE_ACTIVE.txt"
    ]
    
    for signal_file in signal_files:
        if os.path.exists(signal_file):
            try:
                with open(signal_file, 'r') as f:
                    lines = f.read().strip().split('\n')
                    if len(lines) >= 3:
                        nuclear_path = lines[0]
                        timestamp = lines[1]
                        entries_info = lines[2]
                        
                        if os.path.exists(nuclear_path):
                            file_size = os.path.getsize(nuclear_path) / (1024 * 1024)
                            
                            # Quick verification
                            conn = sqlite3.connect(nuclear_path)
                            cursor = conn.cursor()
                            cursor.execute("SELECT COUNT(*) FROM entries")
                            current_count = cursor.fetchone()[0]
                            conn.close()
                            
                            return {
                                "status": "NUCLEAR_ACTIVE",
                                "message": "💥 Nuclear force database is active",
                                "nuclear_path": nuclear_path,
                                "entries": current_count,
                                "file_size_mb": round(file_size, 1),
                                "timestamp": timestamp,
                                "entries_info": entries_info
                            }
            except Exception as e:
                print(f"Error reading nuclear signal: {e}")
    
    return {
        "status": "NUCLEAR_INACTIVE",
        "message": "No nuclear force deployment detected"
    }

@router.get("/nuclear/verify")
async def nuclear_verify() -> Dict[str, Any]:
    """Verify nuclear database with sample queries."""
    
    # Check current database connection
    db_paths = [
        "/app/app/arabic_dict.db",
        "/app/app/comprehensive_arabic_dict.db",
        "app/arabic_dict.db"
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get entry count
                cursor.execute("SELECT COUNT(*) FROM entries")
                count = cursor.fetchone()[0]
                
                # Test complex Arabic words
                test_queries = ["كتب", "علم", "استقلال"]
                results = {}
                
                for query in test_queries:
                    cursor.execute("SELECT lemma, root, pos FROM entries WHERE lemma LIKE ? LIMIT 3", (f"%{query}%",))
                    results[query] = [{"lemma": r[0], "root": r[1], "pos": r[2]} for r in cursor.fetchall()]
                
                conn.close()
                
                file_size = os.path.getsize(db_path) / (1024 * 1024)
                
                return {
                    "status": "VERIFICATION_SUCCESS",
                    "database_path": db_path,
                    "entries": count,
                    "file_size_mb": round(file_size, 1),
                    "test_results": results,
                    "is_comprehensive": count > 100000
                }
                
            except Exception as e:
                continue
    
    return {
        "status": "VERIFICATION_FAILED",
        "message": "No accessible database found"
    }
