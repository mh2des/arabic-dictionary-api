"""
Emergency database diagnostic and deployment endpoint.
This bypasses all caching and creates a fresh comprehensive database.
"""

from fastapi import APIRouter, HTTPException
import sqlite3
import os
import time
from typing import Dict, Any

router = APIRouter()

@router.get("/emergency/deploy-real-db")
async def emergency_deploy_real_database() -> Dict[str, Any]:
    """Emergency endpoint to deploy real comprehensive database."""
    try:
        # Import our real comprehensive data
        import sys
        sys.path.append('/app')
        from real_db_sample import REAL_ENTRIES
        
        # Create unique database with timestamp to avoid caching
        timestamp = str(int(time.time()))
        emergency_db_path = f"/app/emergency_comprehensive_{timestamp}.db"
        
        # Create database
        conn = sqlite3.connect(emergency_db_path)
        cursor = conn.cursor()
        
        # Create schema
        cursor.execute("""
        CREATE TABLE entries (
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
        
        # Insert real comprehensive data
        for i, entry in enumerate(REAL_ENTRIES):
            # entry is a tuple: (lemma, lemma_norm, root, pos, subpos, register, domain, freq_rank)
            cursor.execute("""
            INSERT INTO entries (
                id, lemma, lemma_norm, root, pos, subpos, register, domain,
                freq_rank, camel_lemmas, camel_roots, camel_pos_tags,
                camel_confidence, buckwalter_transliteration, 
                phonetic_transcription, semantic_features,
                phase2_enhanced, camel_analyzed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                i + 1,                  # id
                entry[0],              # lemma
                entry[1] if len(entry) > 1 else None,  # lemma_norm
                entry[2] if len(entry) > 2 else None,  # root
                entry[3] if len(entry) > 3 else None,  # pos
                entry[4] if len(entry) > 4 else None,  # subpos
                entry[5] if len(entry) > 5 else None,  # register
                entry[6] if len(entry) > 6 else None,  # domain
                entry[7] if len(entry) > 7 else None,  # freq_rank
                "",                     # camel_lemmas
                "",                     # camel_roots
                "",                     # camel_pos_tags
                None,                   # camel_confidence
                None,                   # buckwalter_transliteration
                None,                   # phonetic_transcription
                None,                   # semantic_features
                0,                      # phase2_enhanced
                0                       # camel_analyzed
            ))
        
        conn.commit()
        
        # Get database stats
        cursor.execute("SELECT COUNT(*) FROM entries")
        total_count = cursor.fetchone()[0]
        
        # Test for complex words
        cursor.execute("SELECT lemma FROM entries WHERE lemma LIKE '%استقلال%' OR lemma LIKE '%محاضرة%' OR lemma LIKE '%اقتصاد%'")
        complex_words = [row[0] for row in cursor.fetchall()]
        
        # Get sample of entries
        cursor.execute("SELECT lemma, root, pos FROM entries LIMIT 10")
        sample_entries = [{"lemma": row[0], "root": row[1], "pos": row[2]} for row in cursor.fetchall()]
        
        conn.close()
        
        # Store path for main app to use
        with open("/app/emergency_db_path.txt", "w") as f:
            f.write(emergency_db_path)
        
        return {
            "status": "SUCCESS",
            "message": "Emergency comprehensive database deployed",
            "database_path": emergency_db_path,
            "total_entries": total_count,
            "complex_words_found": complex_words,
            "sample_entries": sample_entries,
            "timestamp": timestamp
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "FAILED",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/emergency/force-restart")
async def force_restart_database() -> Dict[str, Any]:
    """Force the main app to restart its database connection."""
    try:
        # Check if emergency database exists
        if not os.path.exists("/app/emergency_db_path.txt"):
            return {"status": "NO_EMERGENCY_DB", "message": "No emergency database deployed yet"}
        
        with open("/app/emergency_db_path.txt", "r") as f:
            emergency_path = f.read().strip()
        
        if not os.path.exists(emergency_path):
            return {"status": "DB_NOT_FOUND", "path": emergency_path}
        
        # Test the emergency database
        conn = sqlite3.connect(emergency_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM entries")
        count = cursor.fetchone()[0]
        conn.close()
        
        # Create a signal file to force main app to use emergency database
        with open("/app/force_emergency_db.txt", "w") as f:
            f.write(emergency_path)
        
        return {
            "status": "SUCCESS",
            "message": "Emergency database activated",
            "emergency_db_path": emergency_path,
            "entries_count": count,
            "action": "Main app will use emergency database on next request"
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e)
        }

@router.get("/emergency/test-real-db")
async def test_emergency_database() -> Dict[str, Any]:
    """Test the emergency database for complex Arabic words."""
    try:
        # Check if emergency database exists
        if not os.path.exists("/app/emergency_db_path.txt"):
            return {"status": "NO_EMERGENCY_DB", "message": "No emergency database deployed yet"}
        
        with open("/app/emergency_db_path.txt", "r") as f:
            db_path = f.read().strip()
        
        if not os.path.exists(db_path):
            return {"status": "DB_NOT_FOUND", "path": db_path}
        
        # Connect and test
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test complex Arabic searches
        test_words = ["استقلال", "محاضرة", "اقتصاد", "مهندس"]
        results = {}
        
        for word in test_words:
            cursor.execute("SELECT lemma, root, pos FROM entries WHERE lemma LIKE ? LIMIT 5", (f"%{word}%",))
            matches = [{"lemma": row[0], "root": row[1], "pos": row[2]} for row in cursor.fetchall()]
            results[word] = matches
        
        cursor.execute("SELECT COUNT(*) FROM entries")
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "status": "SUCCESS",
            "database_path": db_path,
            "total_entries": total,
            "search_results": results
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e)
        }
