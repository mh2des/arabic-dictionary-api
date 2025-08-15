#!/usr/bin/env python3
"""
Simple Root Enhancement using existing CAMeL data
===============================================

Extract roots from the CAMeL data we already have in the database
without complex updates that might cause SQL locking issues.
"""

import sqlite3
import json
import re

def extract_roots_from_camel():
    """Extract roots from existing CAMeL data"""
    conn = sqlite3.connect('app/arabic_dict.db')
    cursor = conn.cursor()
    
    print("=== SIMPLE ROOT ENHANCEMENT ===")
    print("Extracting roots from existing CAMeL Tools data...")
    
    # Get entries with CAMeL roots but missing main root field
    cursor.execute("""
        SELECT id, lemma, camel_roots 
        FROM entries 
        WHERE (root IS NULL OR root = '') 
        AND camel_roots IS NOT NULL 
        AND camel_roots != ''
        AND camel_roots != '[]'
        LIMIT 10000
    """)
    
    entries = cursor.fetchall()
    print(f"Found {len(entries)} entries with CAMeL roots but missing main root field")
    
    successful_updates = 0
    
    for entry_id, lemma, camel_roots in entries:
        # Try to extract clean root
        extracted_root = None
        
        try:
            # Parse JSON if it looks like JSON
            if camel_roots.startswith('[') and camel_roots.endswith(']'):
                roots_list = json.loads(camel_roots)
                if roots_list:
                    extracted_root = roots_list[0].strip()
            else:
                # Use as-is if not JSON
                extracted_root = camel_roots.strip()
            
            # Clean and format the root
            if extracted_root:
                # Remove unwanted characters
                extracted_root = re.sub(r'[\[\]\"\'()]', '', extracted_root)
                
                # Add spaces between Arabic letters if needed
                if len(extracted_root) >= 3 and ' ' not in extracted_root:
                    # Check if it's Arabic
                    arabic_letters = 'ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأإ'
                    if all(c in arabic_letters for c in extracted_root):
                        extracted_root = ' '.join(extracted_root)
                
                # Update in a separate transaction to avoid locks
                update_conn = sqlite3.connect('app/arabic_dict.db')
                update_cursor = update_conn.cursor()
                
                update_cursor.execute("""
                    UPDATE entries 
                    SET root = ?
                    WHERE id = ?
                """, (extracted_root, entry_id))
                
                update_conn.commit()
                update_conn.close()
                
                successful_updates += 1
                
                if successful_updates % 100 == 0:
                    print(f"   Updated {successful_updates} entries...")
                    
        except Exception as e:
            print(f"   Warning: Could not process entry {entry_id}: {e}")
            continue
    
    conn.close()
    
    print(f"✅ Successfully added {successful_updates} roots from CAMeL data!")
    
    # Check new coverage
    conn = sqlite3.connect('app/arabic_dict.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM entries')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE root IS NOT NULL AND root != ""')
    with_roots = cursor.fetchone()[0]
    
    print(f"\n📊 NEW ROOT COVERAGE:")
    print(f"   Total entries: {total:,}")
    print(f"   With roots: {with_roots:,}")
    print(f"   Coverage: {with_roots/total*100:.1f}%")
    print(f"   Improvement: +{successful_updates:,} roots")
    
    conn.close()

if __name__ == "__main__":
    extract_roots_from_camel()
