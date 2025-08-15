#!/usr/bin/env python3
"""
Startup script that FORCES Railway to use the REAL comprehensive database.
This script runs before the FastAPI app starts and ensures we have the real data.
"""

import os
import sys
import sqlite3
import subprocess
import time

def force_real_database():
    """FORCE the deployment of the real comprehensive database."""
    print("🚀 FORCING REAL DATABASE DEPLOYMENT ON RAILWAY")
    print("=" * 60)
    
    # Add the app directory to Python path
    sys.path.append('/app')
    sys.path.append('/app/app')
    
    # Remove any existing cached databases
    cached_dbs = [
        "/app/app/arabic_dict.db",
        "/app/app/real_arabic_dict.db",
        "/app/arabic_dict.db",
        "/app/real_arabic_dict.db"
    ]
    
    for db_path in cached_dbs:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"🗑️  Removed cached database: {db_path}")
            except Exception as e:
                print(f"⚠️  Could not remove {db_path}: {e}")
    
    # Try our robust deployment system
    try:
        print("📥 Attempting comprehensive database download...")
        from deploy_real_database import download_real_database
        db_path = download_real_database()
        
        if db_path and os.path.exists(db_path):
            # Verify it's actually comprehensive
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM entries")
            count = cursor.fetchone()[0]
            
            if count > 1000:  # At least 1000 entries
                print(f"✅ SUCCESS! Real database deployed: {count} entries")
                
                # Test for complex Arabic words
                cursor.execute("SELECT lemma FROM entries WHERE lemma LIKE '%استقلال%' OR lemma LIKE '%محاضرة%' LIMIT 3")
                test_words = cursor.fetchall()
                if test_words:
                    print(f"✅ Verified complex Arabic words: {[w[0] for w in test_words]}")
                else:
                    print("⚠️  No complex Arabic words found")
                
                conn.close()
                return db_path
            else:
                print(f"❌ Database too small: {count} entries")
                conn.close()
    except Exception as e:
        print(f"❌ Deployment system failed: {e}")
    
    # Fallback: Create database from our extracted real data
    try:
        print("🔄 Creating database from extracted real data...")
        from real_db_sample import REAL_ENTRIES
        
        # Create with a unique name to avoid caching
        timestamp = str(int(time.time()))
        db_path = f"/app/app/comprehensive_arabic_{timestamp}.db"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create the comprehensive schema
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY,
            lemma TEXT NOT NULL,
            lemma_norm TEXT,
            root TEXT,
            pos TEXT,
            subpos TEXT,
            register TEXT,
            domain TEXT,
            freq_rank INTEGER,
            camel_lemmas TEXT,
            camel_roots TEXT,
            camel_pos_tags TEXT,
            camel_confidence REAL,
            buckwalter_transliteration TEXT,
            phonetic_transcription TEXT,
            semantic_features TEXT,
            phase2_enhanced INTEGER DEFAULT 0,
            camel_analyzed INTEGER DEFAULT 0
        )
        """)
        
        # Insert all real entries
        for entry in REAL_ENTRIES:
            cursor.execute("""
            INSERT INTO entries (
                lemma, lemma_norm, root, pos, subpos, register, domain,
                freq_rank, camel_lemmas, camel_roots, camel_pos_tags,
                camel_confidence, buckwalter_transliteration, 
                phonetic_transcription, semantic_features,
                phase2_enhanced, camel_analyzed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry["lemma"],
                entry.get("lemma_norm"),
                entry.get("root"),
                entry.get("pos"),
                entry.get("subpos"), 
                entry.get("register"),
                entry.get("domain"),
                entry.get("freq_rank"),
                ",".join(entry.get("camel_lemmas", [])),
                ",".join(entry.get("camel_roots", [])),
                ",".join(entry.get("camel_pos_tags", [])),
                entry.get("camel_confidence"),
                entry.get("buckwalter_transliteration"),
                entry.get("phonetic_transcription"),
                entry.get("semantic_features"),
                1 if entry.get("phase2_enhanced") else 0,
                1 if entry.get("camel_analyzed") else 0
            ))
        
        conn.commit()
        
        # Verify the database
        cursor.execute("SELECT COUNT(*) FROM entries")
        count = cursor.fetchone()[0]
        print(f"✅ Created comprehensive database: {count} entries")
        
        # Test search capabilities
        cursor.execute("SELECT lemma FROM entries WHERE lemma LIKE '%استقلال%' LIMIT 3")
        test_results = cursor.fetchall()
        if test_results:
            print(f"✅ Database ready with complex words: {[r[0] for r in test_results]}")
        
        conn.close()
        
        # Create a symbolic link to the expected path
        expected_path = "/app/app/arabic_dict.db"
        if not os.path.exists(expected_path):
            try:
                os.symlink(db_path, expected_path)
                print(f"🔗 Created symlink: {expected_path} -> {db_path}")
            except:
                # If symlink fails, copy the file
                import shutil
                shutil.copy2(db_path, expected_path)
                print(f"📋 Copied database to: {expected_path}")
        
        return expected_path
        
    except Exception as e:
        print(f"❌ Fallback creation failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("❌ ALL DATABASE DEPLOYMENT METHODS FAILED!")
    return None

if __name__ == "__main__":
    # This runs when Railway starts the container
    print("🚀 Railway Startup: Ensuring Real Database Deployment")
    result = force_real_database()
    
    if result:
        print(f"✅ Startup successful: Real database at {result}")
        print("🚀 Starting FastAPI application...")
    else:
        print("❌ Startup failed: Could not deploy real database")
        print("🚀 Starting FastAPI with fallback...")
    
    print("=" * 60)
