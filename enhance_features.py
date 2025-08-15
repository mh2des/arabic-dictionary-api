#!/usr/bin/env python3
"""
Enhanced CAMeL Tools Features Update Script
Updates existing entries with the new morphological features.
"""

import sys
import sqlite3
import json
import time
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent / 'app'))

from services.camel_final import FinalCamelProcessor


def update_enhanced_features(limit=1000):
    """Update database with enhanced CAMeL features."""
    
    print("🔥 UPDATING DATABASE WITH ENHANCED CAMEL FEATURES")
    print("=" * 60)
    
    processor = FinalCamelProcessor()
    
    # Connect to database
    conn = sqlite3.connect("app/arabic_dict.db")
    cursor = conn.cursor()
    
    # Get entries that have basic CAMeL data but missing enhanced features
    cursor.execute("""
        SELECT id, lemma FROM entries 
        WHERE camel_lemmas IS NOT NULL 
        AND camel_lemmas != '' 
        AND (camel_genders IS NULL OR camel_english_glosses IS NULL)
        LIMIT ?
    """, (limit,))
    
    entries = cursor.fetchall()
    
    if not entries:
        print("ℹ️ No entries need enhancement updates")
        return
    
    print(f"📊 Updating {len(entries)} entries with enhanced features...")
    
    # Disable FTS triggers temporarily for performance
    cursor.execute("DROP TRIGGER IF EXISTS entries_ai")
    cursor.execute("DROP TRIGGER IF EXISTS entries_ad")
    cursor.execute("DROP TRIGGER IF EXISTS entries_au")
    
    updated = 0
    start_time = time.time()
    
    for entry_id, lemma in entries:
        try:
            # Get enhanced analysis
            analysis = processor.analyze_word(lemma)
            
            # Extract enhanced features
            genders = json.dumps(analysis.get('genders', []), ensure_ascii=False)
            numbers = json.dumps(analysis.get('numbers', []), ensure_ascii=False)
            cases = json.dumps(analysis.get('cases', []), ensure_ascii=False)
            states = json.dumps(analysis.get('states', []), ensure_ascii=False)
            voices = json.dumps(analysis.get('voices', []), ensure_ascii=False)
            moods = json.dumps(analysis.get('moods', []), ensure_ascii=False)
            aspects = json.dumps(analysis.get('aspects', []), ensure_ascii=False)
            english_glosses = json.dumps(analysis.get('english_glosses', []), ensure_ascii=False)
            patterns = json.dumps(analysis.get('patterns', []), ensure_ascii=False)
            
            # Update database
            cursor.execute("""
                UPDATE entries 
                SET camel_genders = ?, camel_numbers = ?, camel_cases = ?, 
                    camel_states = ?, camel_voices = ?, camel_moods = ?,
                    camel_aspects = ?, camel_english_glosses = ?, camel_patterns = ?
                WHERE id = ?
            """, (genders, numbers, cases, states, voices, moods, aspects, 
                  english_glosses, patterns, entry_id))
            
            updated += 1
            
            if updated % 100 == 0:
                elapsed = time.time() - start_time
                rate = updated / elapsed
                print(f"   Updated: {updated}/{len(entries)} ({updated/len(entries)*100:.1f}%) "
                      f"- Rate: {rate:.1f}/sec")
                conn.commit()
                
        except Exception as e:
            print(f"   ⚠️ Error updating '{lemma}': {e}")
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
    
    total_time = time.time() - start_time
    
    print(f"\n✅ ENHANCEMENT COMPLETE!")
    print(f"   Updated entries: {updated:,}")
    print(f"   Processing time: {total_time:.1f} seconds")
    print(f"   Average rate: {updated/total_time:.1f} entries/second")
    
    conn.close()


def test_enhanced_features():
    """Test the enhanced features."""
    print(f"\n🧪 Testing Enhanced Features:")
    print("=" * 40)
    
    processor = FinalCamelProcessor()
    
    test_words = ["كتاب", "مكتبة", "يكتب", "كاتب"]
    
    for word in test_words:
        print(f"\n📖 Enhanced analysis for: {word}")
        analysis = processor.analyze_word(word)
        
        print(f"   Lemmas: {analysis.get('possible_lemmas', [])}")
        print(f"   Roots: {analysis.get('roots', [])}")
        print(f"   POS: {analysis.get('pos_tags', [])}")
        print(f"   🆕 Genders: {analysis.get('genders', [])}")
        print(f"   🆕 Numbers: {analysis.get('numbers', [])}")
        print(f"   🆕 Cases: {analysis.get('cases', [])}")
        print(f"   🆕 English Glosses: {analysis.get('english_glosses', [])}")


if __name__ == "__main__":
    test_enhanced_features()
    
    response = input("\nUpdate database with enhanced features? (y/N): ")
    if response.lower() in ['y', 'yes']:
        update_enhanced_features(limit=5000)  # Update 5000 entries as a test
    else:
        print("Update cancelled.")
