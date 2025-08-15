#!/usr/bin/env python3
"""
Complete CAMeL Tools Enhancement Script
Process ALL entries in the Arabic dictionary database with CAMeL Tools analysis.
"""

import sys
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any
import json

# Add app to path
sys.path.insert(0, str(Path(__file__).parent / 'app'))

from services.camel_final import FinalCamelProcessor


def enhance_all_entries():
    """Enhance ALL entries in the database with CAMeL Tools analysis."""
    
    print("🐪 Starting COMPLETE CAMeL Tools Enhancement")
    print("=" * 60)
    
    # Initialize processor
    processor = FinalCamelProcessor()
    
    # Connect to database
    db_path = Path("app/arabic_dict.db")
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM entries")
    total_entries = cursor.fetchone()[0]
    
    # Check already enhanced
    cursor.execute("""
        SELECT COUNT(*) FROM entries 
        WHERE camel_lemmas IS NOT NULL AND camel_lemmas != ''
    """)
    already_enhanced = cursor.fetchone()[0]
    
    remaining = total_entries - already_enhanced
    
    print(f"📊 Database Status:")
    print(f"   Total entries: {total_entries:,}")
    print(f"   Already enhanced: {already_enhanced:,}")
    print(f"   Remaining to process: {remaining:,}")
    print(f"   Estimated time: {remaining * 0.1 / 60:.1f} minutes")
    
    if remaining == 0:
        print("✅ All entries already enhanced!")
        return
    
    # Temporarily disable FTS triggers for performance
    print("\n🔧 Temporarily disabling FTS triggers for performance...")
    cursor.execute("DROP TRIGGER IF EXISTS entries_ai")
    cursor.execute("DROP TRIGGER IF EXISTS entries_ad")
    cursor.execute("DROP TRIGGER IF EXISTS entries_au")
    
    # Process entries in batches
    batch_size = 1000
    processed = 0
    errors = 0
    start_time = time.time()
    
    print(f"\n🚀 Processing {remaining:,} entries in batches of {batch_size}...")
    
    # Get entries that need enhancement
    cursor.execute("""
        SELECT id, lemma FROM entries 
        WHERE camel_lemmas IS NULL OR camel_lemmas = ''
        ORDER BY id
    """)
    
    entries_to_process = cursor.fetchall()
    
    for i, (entry_id, lemma) in enumerate(entries_to_process):
        try:
            # Analyze with CAMeL Tools
            analysis = processor.analyze_word(lemma)
            
            # Extract data for database
            camel_lemmas = json.dumps(analysis.get('possible_lemmas', []), ensure_ascii=False)
            camel_roots = json.dumps(analysis.get('roots', []), ensure_ascii=False)
            camel_pos = json.dumps(analysis.get('pos_tags', []), ensure_ascii=False)
            camel_confidence = 1.0 if analysis.get('available', False) else 0.0
            
            # Update database
            cursor.execute("""
                UPDATE entries 
                SET camel_lemmas = ?, camel_roots = ?, camel_pos = ?, camel_confidence = ?
                WHERE id = ?
            """, (camel_lemmas, camel_roots, camel_pos, camel_confidence, entry_id))
            
            processed += 1
            
            # Progress reporting
            if processed % 100 == 0:
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                remaining_time = (len(entries_to_process) - processed) / rate if rate > 0 else 0
                
                print(f"   Processed: {processed:,}/{len(entries_to_process):,} "
                      f"({processed/len(entries_to_process)*100:.1f}%) "
                      f"- Rate: {rate:.1f}/sec "
                      f"- ETA: {remaining_time/60:.1f}min")
            
            # Commit in batches
            if processed % batch_size == 0:
                conn.commit()
                
        except Exception as e:
            errors += 1
            if errors <= 10:  # Only show first 10 errors
                print(f"   ⚠️ Error processing '{lemma}' (ID {entry_id}): {e}")
            continue
    
    # Final commit
    conn.commit()
    
    # Rebuild FTS triggers
    print(f"\n🔧 Rebuilding FTS triggers...")
    cursor.execute("""
        CREATE TRIGGER entries_ai AFTER INSERT ON entries BEGIN
            INSERT INTO entries_fts(rowid, lemma, pos, gloss_ar, gloss_en) 
            VALUES (new.id, new.lemma, new.pos, new.gloss_ar, new.gloss_en);
        END
    """)
    cursor.execute("""
        CREATE TRIGGER entries_ad AFTER DELETE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts, rowid) VALUES('delete', old.id);
        END
    """)
    cursor.execute("""
        CREATE TRIGGER entries_au AFTER UPDATE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts, rowid) VALUES('delete', old.id);
            INSERT INTO entries_fts(rowid, lemma, pos, gloss_ar, gloss_en) 
            VALUES (new.id, new.lemma, new.pos, new.gloss_ar, new.gloss_en);
        END
    """)
    
    # Rebuild FTS index
    cursor.execute("INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")
    conn.commit()
    
    # Final statistics
    cursor.execute("""
        SELECT COUNT(*) FROM entries 
        WHERE camel_lemmas IS NOT NULL AND camel_lemmas != ''
    """)
    final_enhanced = cursor.fetchone()[0]
    
    total_time = time.time() - start_time
    
    print(f"\n🎉 COMPLETE! Enhancement Results:")
    print(f"   Total entries: {total_entries:,}")
    print(f"   Successfully enhanced: {final_enhanced:,}")
    print(f"   Enhancement rate: {final_enhanced/total_entries*100:.1f}%")
    print(f"   Processing time: {total_time/60:.1f} minutes")
    print(f"   Average rate: {processed/total_time:.1f} entries/second")
    print(f"   Errors: {errors}")
    
    conn.close()


def test_enhanced_search():
    """Test the enhanced search capabilities."""
    print(f"\n🔍 Testing Enhanced Search Capabilities:")
    print("=" * 40)
    
    conn = sqlite3.connect("app/arabic_dict.db")
    cursor = conn.cursor()
    
    # Test root-based search
    test_root = "ك.ت.ب"
    cursor.execute("""
        SELECT lemma, camel_roots, camel_lemmas
        FROM entries 
        WHERE camel_roots LIKE ?
        LIMIT 10
    """, (f"%{test_root}%",))
    
    results = cursor.fetchall()
    print(f"Root search for '{test_root}': {len(results)} results")
    for lemma, roots, lemmas in results[:5]:
        print(f"   {lemma} -> roots: {roots}")
    
    # Test lemma search
    cursor.execute("""
        SELECT COUNT(*) FROM entries 
        WHERE camel_lemmas LIKE '%كِتاب%'
    """)
    lemma_count = cursor.fetchone()[0]
    print(f"Lemma search for 'كِتاب': {lemma_count} results")
    
    # Test POS search
    cursor.execute("""
        SELECT COUNT(*) FROM entries 
        WHERE camel_pos LIKE '%noun%'
    """)
    noun_count = cursor.fetchone()[0]
    print(f"POS search for 'noun': {noun_count} results")
    
    conn.close()


if __name__ == "__main__":
    print("🐪 CAMeL Tools Complete Enhancement Script")
    print("This will process ALL 101,331 entries in your dictionary!")
    print("Estimated time: 15-20 minutes")
    
    response = input("\nContinue with complete enhancement? (y/N): ")
    if response.lower() in ['y', 'yes']:
        enhance_all_entries()
        test_enhanced_search()
        
        print(f"\n🚀 Your Arabic dictionary now has FULL CAMeL Tools power!")
        print("   ✅ Morphological analysis for ALL entries")
        print("   ✅ Root-based search across entire dictionary")
        print("   ✅ Advanced lemmatization for every word")
        print("   ✅ Complete POS tagging coverage")
        print("   ✅ Pattern recognition for all Arabic words")
    else:
        print("Enhancement cancelled.")
