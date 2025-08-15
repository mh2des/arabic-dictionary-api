#!/usr/bin/env python3
"""
Batch Root Enhancement Script
============================

Extract and apply root improvements in batches to avoid database locks.
This will dramatically improve root coverage from 47.1% to ~90%+
"""

import sqlite3
import json
import re
import time

def enhance_roots_batch():
    """Enhance roots in manageable batches"""
    print("=== BATCH ROOT ENHANCEMENT ===")
    print("Improving root coverage from 47.1% to 90%+...")
    
    # First, let's wait a moment for any locks to clear
    time.sleep(2)
    
    conn = sqlite3.connect('app/arabic_dict.db', timeout=30.0)
    cursor = conn.cursor()
    
    # Get the data we need to process
    print("📊 Loading entries that need root enhancement...")
    cursor.execute("""
        SELECT id, lemma, camel_roots 
        FROM entries 
        WHERE (root IS NULL OR root = '') 
        AND camel_roots IS NOT NULL 
        AND camel_roots != '' 
        AND camel_roots != '[]'
        LIMIT 5000
    """)
    
    entries = cursor.fetchall()
    print(f"   Found {len(entries)} entries to enhance")
    
    # Process in smaller batches
    batch_size = 100
    successful_updates = 0
    
    for i in range(0, len(entries), batch_size):
        batch = entries[i:i+batch_size]
        print(f"   Processing batch {i//batch_size + 1}/{(len(entries)-1)//batch_size + 1}...")
        
        # Prepare all updates for this batch
        updates = []
        for entry_id, lemma, camel_roots in batch:
            try:
                # Extract root from CAMeL data
                extracted_root = None
                
                if camel_roots.startswith('[') and camel_roots.endswith(']'):
                    # JSON format
                    roots_list = json.loads(camel_roots)
                    if roots_list:
                        extracted_root = str(roots_list[0]).strip()
                else:
                    # Direct format
                    extracted_root = camel_roots.strip()
                
                if extracted_root:
                    # Clean the root
                    extracted_root = re.sub(r'[\[\]\"\'()]', '', extracted_root)
                    
                    # Format as spaced root if it's Arabic letters
                    arabic_letters = 'ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأإ'
                    if len(extracted_root) >= 2 and ' ' not in extracted_root:
                        if all(c in arabic_letters or c in '.#' for c in extracted_root):
                            if '.' in extracted_root or '#' in extracted_root:
                                # Already formatted with separators
                                pass
                            elif len(extracted_root) == 3:
                                # Add spaces for 3-letter roots
                                extracted_root = ' '.join(extracted_root)
                    
                    updates.append((extracted_root, entry_id))
                    
            except Exception as e:
                print(f"      Warning: Could not process {lemma}: {e}")
                continue
        
        # Execute batch update
        if updates:
            try:
                cursor.executemany("""
                    UPDATE entries 
                    SET root = ?
                    WHERE id = ?
                """, updates)
                
                conn.commit()
                successful_updates += len(updates)
                print(f"      ✅ Updated {len(updates)} entries")
                
            except Exception as e:
                print(f"      ❌ Batch update failed: {e}")
                # Try individual updates as fallback
                for root, entry_id in updates:
                    try:
                        cursor.execute("UPDATE entries SET root = ? WHERE id = ?", (root, entry_id))
                        conn.commit()
                        successful_updates += 1
                    except:
                        pass
        
        # Small delay between batches
        time.sleep(0.1)
    
    conn.close()
    
    print(f"\n✅ ROOT ENHANCEMENT COMPLETED!")
    print(f"   Successfully enhanced: {successful_updates:,} entries")
    
    # Check final coverage
    time.sleep(1)
    conn = sqlite3.connect('app/arabic_dict.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM entries')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE root IS NOT NULL AND root != ""')
    with_roots = cursor.fetchone()[0]
    
    new_coverage = with_roots/total*100
    
    print(f"\n📊 FINAL ROOT COVERAGE:")
    print(f"   Total entries: {total:,}")
    print(f"   With roots: {with_roots:,}")
    print(f"   Coverage: {new_coverage:.1f}%")
    print(f"   Improvement: +{successful_updates:,} roots")
    
    if new_coverage > 70:
        print(f"   🎉 EXCELLENT! Root coverage improved to {new_coverage:.1f}%")
    elif new_coverage > 60:
        print(f"   👍 GOOD! Root coverage improved to {new_coverage:.1f}%")
    else:
        print(f"   📈 Progress made: {new_coverage:.1f}% coverage")
    
    conn.close()
    return successful_updates > 0

if __name__ == "__main__":
    enhance_roots_batch()
