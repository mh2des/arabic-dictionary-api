#!/usr/bin/env python3
"""
Simple CAMeL Enhancement for Remaining Entries

A lightweight approach to complete the CAMeL analysis for the remaining 22,962 entries.
Uses smaller batches and better lock handling to work around active servers.
"""

import os
import sys
import sqlite3
import json
import time
from typing import List, Dict, Any

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def init_camel():
    """Initialize CAMeL Tools."""
    try:
        from camel_tools.morphology.database import MorphologyDB
        from camel_tools.morphology.analyzer import Analyzer
        from camel_tools.utils.normalize import normalize_alef_maksura_ar
        from camel_tools.utils.normalize import normalize_alef_ar
        from camel_tools.utils.normalize import normalize_teh_marbuta_ar
        
        print("🔄 Initializing CAMeL Tools...")
        db = MorphologyDB.builtin_db()
        analyzer = Analyzer(db)
        print("✅ CAMeL Tools ready")
        
        return {
            'analyzer': analyzer,
            'normalize_alef_maksura': normalize_alef_maksura_ar,
            'normalize_alef': normalize_alef_ar,
            'normalize_teh_marbuta': normalize_teh_marbuta_ar,
            'available': True
        }
    except Exception as e:
        print(f"❌ CAMeL Tools failed: {e}")
        return {'available': False}

def normalize_arabic(text: str, camel_tools: dict) -> str:
    """Normalize Arabic text."""
    if not camel_tools['available'] or not text:
        return text
    
    normalized = camel_tools['normalize_alef_maksura'](text)
    normalized = camel_tools['normalize_alef'](normalized)
    normalized = camel_tools['normalize_teh_marbuta'](normalized)
    return normalized

def analyze_word(word: str, camel_tools: dict) -> Dict[str, Any]:
    """Analyze a single word with CAMeL Tools."""
    if not camel_tools['available'] or not word.strip():
        return {'lemmas': [], 'roots': [], 'pos_tags': [], 'confidence': 0.0}
    
    try:
        normalized_word = normalize_arabic(word.strip(), camel_tools)
        analyses = camel_tools['analyzer'].analyze(normalized_word)
        
        if not analyses:
            return {'lemmas': [], 'roots': [], 'pos_tags': [], 'confidence': 0.0}
        
        lemmas = []
        roots = []
        pos_tags = []
        
        for analysis in analyses:
            if 'lex' in analysis and analysis['lex'] not in lemmas:
                lemmas.append(analysis['lex'])
            if 'root' in analysis and analysis['root'] not in roots:
                roots.append(analysis['root'])
            if 'pos' in analysis and analysis['pos'] not in pos_tags:
                pos_tags.append(analysis['pos'])
        
        confidence = min(1.0, len(analyses) / 3.0) if analyses else 0.0
        
        return {
            'lemmas': lemmas,
            'roots': roots,
            'pos_tags': pos_tags,
            'confidence': confidence
        }
        
    except Exception as e:
        return {'lemmas': [], 'roots': [], 'pos_tags': [], 'confidence': 0.0}

def process_chunk(chunk_start: int, chunk_size: int, camel_tools: dict) -> int:
    """Process a small chunk of entries."""
    db_path = os.path.join(os.path.dirname(__file__), 'app', 'arabic_dict.db')
    processed = 0
    
    try:
        # Get entries to process
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, lemma, lemma_norm 
            FROM entries 
            WHERE (camel_lemmas IS NULL OR camel_lemmas = '' OR camel_lemmas = '[]')
            ORDER BY id
            LIMIT ? OFFSET ?
        """, (chunk_size, chunk_start))
        
        entries = cursor.fetchall()
        conn.close()
        
        if not entries:
            return 0
        
        # Process entries
        updates = []
        for entry_id, lemma, lemma_norm in entries:
            word = lemma_norm if lemma_norm else lemma
            camel_data = analyze_word(word, camel_tools)
            updates.append((
                json.dumps(camel_data['lemmas'], ensure_ascii=False),
                json.dumps(camel_data['roots'], ensure_ascii=False),
                json.dumps(camel_data['pos_tags'], ensure_ascii=False),
                camel_data['confidence'],
                entry_id
            ))
        
        # Update database with retry logic
        for retry in range(3):
            try:
                conn = sqlite3.connect(db_path, timeout=20.0)
                cursor = conn.cursor()
                
                cursor.executemany("""
                    UPDATE entries 
                    SET camel_lemmas = ?, camel_roots = ?, camel_pos_tags = ?, 
                        camel_confidence = ?, camel_analyzed = 1
                    WHERE id = ?
                """, updates)
                
                conn.commit()
                conn.close()
                processed = len(updates)
                break
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and retry < 2:
                    time.sleep(retry + 1)
                    continue
                else:
                    print(f"   ❌ Database error: {e}")
                    break
        
        return processed
        
    except Exception as e:
        print(f"   ❌ Chunk processing error: {e}")
        return 0

def main():
    """Main processing function."""
    print("🎯 Simple CAMeL Enhancement for Remaining Entries")
    print("=" * 50)
    
    # Initialize CAMeL Tools
    camel_tools = init_camel()
    if not camel_tools['available']:
        print("❌ Cannot proceed without CAMeL Tools")
        return False
    
    # Get total remaining count
    db_path = os.path.join(os.path.dirname(__file__), 'app', 'arabic_dict.db')
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM entries 
            WHERE (camel_lemmas IS NULL OR camel_lemmas = '' OR camel_lemmas = '[]')
        """)
        remaining = cursor.fetchone()[0]
        conn.close()
        
        print(f"📊 Remaining entries to process: {remaining:,}")
        
        if remaining == 0:
            print("✅ All entries already processed!")
            return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False
    
    # Process in small chunks
    chunk_size = 50  # Very small chunks to avoid locks
    total_processed = 0
    chunk_start = 0
    
    print(f"📊 Processing in chunks of {chunk_size} entries...")
    
    while chunk_start < remaining:
        print(f"\n🔄 Processing chunk {chunk_start + 1}-{min(chunk_start + chunk_size, remaining)}...")
        
        processed = process_chunk(chunk_start, chunk_size, camel_tools)
        total_processed += processed
        
        if processed > 0:
            progress = total_processed / remaining * 100
            print(f"✅ Processed {processed} entries (Total: {total_processed:,}/{remaining:,} - {progress:.1f}%)")
        else:
            print("⚠️  No entries processed in this chunk")
        
        chunk_start += chunk_size
        
        # Small pause to avoid overwhelming the database
        time.sleep(0.1)
    
    print(f"\n🎉 Completion Summary:")
    print(f"✅ Total processed: {total_processed:,} entries")
    
    # Final verification
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM entries')
        total = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM entries 
            WHERE camel_lemmas IS NOT NULL AND camel_lemmas != '' AND camel_lemmas != '[]'
        """)
        completed = cursor.fetchone()[0]
        
        conn.close()
        
        completion_rate = completed / total * 100
        print(f"📊 Final Status: {completed:,}/{total:,} entries have CAMeL analysis ({completion_rate:.1f}%)")
        
        if completion_rate >= 95.0:
            print("🎯 SUCCESS: Screen 5 (Dialect Support) is now functional!")
            return True
        else:
            remaining_final = total - completed
            print(f"⚠️  Still {remaining_final:,} entries need processing")
            return False
            
    except Exception as e:
        print(f"❌ Final verification failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
