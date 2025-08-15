"""
CAMeL Tools enhancement that handles FTS triggers correctly.
Uses a temporary approach to avoid FTS trigger conflicts.
"""
import sqlite3
import json
import sys
import os

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.camel_final import camel_processor

def enhance_with_camel_safe():
    """Safely enhance database by temporarily disabling triggers."""
    if not camel_processor.available:
        print("CAMeL Tools not available!")
        return
    
    print("Starting safe CAMeL Tools enhancement...")
    
    # Connect to database
    conn = sqlite3.connect('app/arabic_dict.db')
    cursor = conn.cursor()
    
    try:
        # Temporarily disable FTS triggers to avoid conflicts
        print("Temporarily disabling FTS triggers...")
        cursor.execute("DROP TRIGGER IF EXISTS entries_ai")
        cursor.execute("DROP TRIGGER IF EXISTS entries_ad") 
        cursor.execute("DROP TRIGGER IF EXISTS entries_au")
        
        # Add CAMeL columns if they don't exist
        columns = {
            'camel_lemmas': 'TEXT',
            'camel_roots': 'TEXT', 
            'camel_pos': 'TEXT',
            'camel_confidence': 'REAL',
            'camel_analyzed': 'INTEGER DEFAULT 0'
        }
        
        for col_name, col_type in columns.items():
            try:
                cursor.execute(f"ALTER TABLE entries ADD COLUMN {col_name} {col_type}")
                print(f"Added column: {col_name}")
            except sqlite3.OperationalError:
                pass  # Column already exists
        
        # Get entries to process (limit to first 100 for safety)
        cursor.execute("""
            SELECT id, lemma FROM entries 
            WHERE (camel_analyzed IS NULL OR camel_analyzed = 0) 
            AND lemma IS NOT NULL 
            LIMIT 100
        """)
        entries = cursor.fetchall()
        
        print(f"Processing {len(entries)} entries...")
        
        enhanced_count = 0
        for i, (entry_id, lemma) in enumerate(entries):
            try:
                # Analyze with CAMeL Tools
                analysis = camel_processor.analyze_word(lemma)
                
                # Extract key data
                camel_lemmas = analysis.get("possible_lemmas", [])
                camel_roots = analysis.get("roots", [])
                camel_pos = analysis.get("pos_tags", [])
                
                # Calculate confidence
                morphology = analysis.get("morphology", [])
                confidence = min(1.0, len(morphology) / 10.0) if morphology else 0.0
                
                # Update database with explicit column names
                cursor.execute("""
                    UPDATE entries SET 
                        camel_lemmas = ?,
                        camel_roots = ?,
                        camel_pos = ?,
                        camel_confidence = ?,
                        camel_analyzed = 1
                    WHERE id = ?
                """, (
                    json.dumps(camel_lemmas, ensure_ascii=False),
                    json.dumps(camel_roots, ensure_ascii=False),
                    json.dumps(camel_pos, ensure_ascii=False),
                    confidence,
                    entry_id
                ))
                
                enhanced_count += 1
                
                # Show sample results for first few
                if i < 3:
                    print(f"  {lemma} → lemmas: {camel_lemmas[:2]}, roots: {camel_roots}")
                
                # Progress update
                if (i + 1) % 20 == 0:
                    print(f"Processed {i + 1}/{len(entries)} entries...")
                    conn.commit()
                    
            except Exception as e:
                print(f"Error processing entry {entry_id} ('{lemma}'): {e}")
        
        # Final commit
        conn.commit()
        print(f"Enhancement complete! Enhanced {enhanced_count} entries.")
        
        # Now recreate the FTS triggers
        print("Recreating FTS triggers...")
        
        # Recreate INSERT trigger
        cursor.execute("""
            CREATE TRIGGER entries_ai AFTER INSERT ON entries BEGIN
                INSERT INTO entries_fts(rowid, lemma_norm, root, pattern, pos, definition, source)
                VALUES (new.id, new.lemma_norm, new.root, new.pattern, new.pos, 
                        COALESCE(json_extract(new.data, '$.definition'), ''), new.source);
            END
        """)
        
        # Recreate DELETE trigger
        cursor.execute("""
            CREATE TRIGGER entries_ad AFTER DELETE ON entries BEGIN
                DELETE FROM entries_fts WHERE rowid = old.id;
            END
        """)
        
        # Recreate UPDATE trigger
        cursor.execute("""
            CREATE TRIGGER entries_au AFTER UPDATE ON entries BEGIN
                DELETE FROM entries_fts WHERE rowid = old.id;
                INSERT INTO entries_fts(rowid, lemma_norm, root, pattern, pos, definition, source)
                VALUES (new.id, new.lemma_norm, new.root, new.pattern, new.pos, 
                        COALESCE(json_extract(new.data, '$.definition'), ''), new.source);
            END
        """)
        
        conn.commit()
        print("FTS triggers recreated successfully.")
        
        return enhanced_count
        
    except Exception as e:
        print(f"Error during enhancement: {e}")
        return 0
        
    finally:
        conn.close()

def show_camel_results():
    """Show enhanced entries with CAMeL data."""
    conn = sqlite3.connect('app/arabic_dict.db')
    cursor = conn.cursor()
    
    # Check if we have any enhanced entries
    cursor.execute("""
        SELECT COUNT(*) FROM entries 
        WHERE camel_analyzed = 1 AND camel_lemmas IS NOT NULL
    """)
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("No enhanced entries found. Run enhancement first.")
        conn.close()
        return
    
    print(f"Found {count} enhanced entries. Showing samples:")
    
    # Get sample enhanced entries
    cursor.execute("""
        SELECT lemma, camel_lemmas, camel_roots, camel_pos, camel_confidence
        FROM entries 
        WHERE camel_analyzed = 1 AND camel_lemmas IS NOT NULL
        ORDER BY camel_confidence DESC 
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    
    for lemma, lemmas_json, roots_json, pos_json, confidence in results:
        try:
            lemmas = json.loads(lemmas_json) if lemmas_json else []
            roots = json.loads(roots_json) if roots_json else []
            pos_tags = json.loads(pos_json) if pos_json else []
            
            print(f"\n{lemma} (confidence: {confidence:.2f})")
            print(f"  Lemmas: {lemmas[:3]}")
            print(f"  Roots: {roots}")
            print(f"  POS: {pos_tags}")
        except Exception as e:
            print(f"  {lemma} → Error parsing: {e}")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "enhance":
        enhanced = enhance_with_camel_safe()
        if enhanced > 0:
            print("\nShowing enhanced results:")
            show_camel_results()
    elif len(sys.argv) > 1 and sys.argv[1] == "show":
        show_camel_results()
    else:
        print("CAMeL Tools Safe Enhancement")
        print("Commands:")
        print("  python camel_safe.py enhance  - Enhance database safely")
        print("  python camel_safe.py show     - Show enhanced results")
        print(f"\nCAMeL Tools available: {'✓' if camel_processor.available else '✗'}")
