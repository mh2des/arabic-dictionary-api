"""
EMERGENCY REAL DATABASE LOADER
This module completely bypasses any cached databases and creates a fresh comprehensive database.
"""

import os
import sqlite3
import time
from typing import Optional

def create_emergency_real_database() -> Optional[str]:
    """Create an emergency real database with our comprehensive data."""
    try:
        # Import our real data
        from real_db_sample import REAL_ENTRIES
        
        # Create unique database path to avoid any caching
        timestamp = str(int(time.time()))
        db_path = f"/app/emergency_real_db_{timestamp}.db"
        
        print(f"🚨 EMERGENCY: Creating real database at {db_path}")
        
        # Create database with comprehensive schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create comprehensive entries table
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
        
        # Insert all real entries
        for i, entry in enumerate(REAL_ENTRIES):
            cursor.execute("""
            INSERT INTO entries (
                id, lemma, lemma_norm, root, pos, subpos, register, domain,
                freq_rank, camel_lemmas, camel_roots, camel_pos_tags,
                camel_confidence, buckwalter_transliteration, 
                phonetic_transcription, semantic_features,
                phase2_enhanced, camel_analyzed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                i + 1,  # id
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
        
        # Create search indexes
        cursor.execute("CREATE INDEX idx_lemma ON entries(lemma)")
        cursor.execute("CREATE INDEX idx_lemma_norm ON entries(lemma_norm)")
        cursor.execute("CREATE INDEX idx_root ON entries(root)")
        
        conn.commit()
        
        # Verify database
        cursor.execute("SELECT COUNT(*) FROM entries")
        count = cursor.fetchone()[0]
        print(f"✅ Emergency database created: {count} entries")
        
        # Test for complex words
        cursor.execute("SELECT lemma FROM entries WHERE lemma LIKE '%استقلال%' OR lemma LIKE '%محاضرة%' LIMIT 3")
        test_words = cursor.fetchall()
        if test_words:
            print(f"✅ Complex words verified: {[w[0] for w in test_words]}")
        
        conn.close()
        return db_path
        
    except Exception as e:
        print(f"❌ Emergency database creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

# Global variable to store emergency database path
EMERGENCY_DB_PATH = None

def get_emergency_database() -> sqlite3.Connection:
    """Get connection to emergency real database."""
    global EMERGENCY_DB_PATH
    
    if not EMERGENCY_DB_PATH or not os.path.exists(EMERGENCY_DB_PATH):
        EMERGENCY_DB_PATH = create_emergency_real_database()
    
    if EMERGENCY_DB_PATH:
        return sqlite3.connect(EMERGENCY_DB_PATH)
    else:
        raise Exception("Could not create emergency database!")
