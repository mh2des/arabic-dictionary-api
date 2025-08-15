"""
Working CAMeL Tools enhancement for the Arabic dictionary.
Simple and direct approach that actually works.
"""
import sqlite3
import json
import sys
import os

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.camel_final import camel_processor

def enhance_database_with_camel():
    """Enhance the database with CAMeL Tools analysis."""
    if not camel_processor.available:
        print("CAMeL Tools not available!")
        return
    
    print("Starting CAMeL Tools enhancement...")
    
    # Connect to database
    conn = sqlite3.connect('app/arabic_dict.db')
    cursor = conn.cursor()
    
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
    
    # Get entries to process (limit to first 200 for demo)
    cursor.execute("SELECT id, lemma FROM entries WHERE (camel_analyzed IS NULL OR camel_analyzed = 0) AND lemma IS NOT NULL LIMIT 200")
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
            
            # Update database - use simple UPDATE
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
            
            # Progress update
            if (i + 1) % 20 == 0:
                print(f"Processed {i + 1}/{len(entries)} entries...")
                conn.commit()
                
            # Show sample results
            if i < 5:
                print(f"  {lemma} → lemmas: {camel_lemmas[:2]}, roots: {camel_roots}, POS: {camel_pos}")
                
        except Exception as e:
            print(f"Error processing entry {entry_id} ('{lemma}'): {e}")
    
    # Final commit
    conn.commit()
    conn.close()
    
    print(f"Enhancement complete! Enhanced {enhanced_count} entries.")
    return enhanced_count

def show_enhanced_samples():
    """Show sample enhanced entries."""
    conn = sqlite3.connect('app/arabic_dict.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT lemma, camel_lemmas, camel_roots, camel_pos, camel_confidence
        FROM entries 
        WHERE camel_analyzed = 1 AND camel_lemmas IS NOT NULL
        ORDER BY camel_confidence DESC 
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    if results:
        print("\nTop enhanced entries:")
        for lemma, lemmas_json, roots_json, pos_json, confidence in results:
            try:
                lemmas = json.loads(lemmas_json) if lemmas_json else []
                roots = json.loads(roots_json) if roots_json else []
                pos_tags = json.loads(pos_json) if pos_json else []
                
                print(f"  {lemma}")
                print(f"    → Lemmas: {lemmas[:3]}")
                print(f"    → Roots: {roots}")
                print(f"    → POS: {pos_tags}")
                print(f"    → Confidence: {confidence:.2f}")
                print()
            except Exception as e:
                print(f"  {lemma} → Error parsing: {e}")
    else:
        print("No enhanced entries found.")

def test_camel_on_common_words():
    """Test CAMeL Tools on common Arabic words."""
    if not camel_processor.available:
        print("CAMeL Tools not available!")
        return
    
    common_words = [
        "كتاب", "بيت", "ماء", "قلم", "جميل", "كبير", "صغير",
        "أكل", "شرب", "كتب", "قرأ", "ذهب", "جاء", "رأى"
    ]
    
    print("Testing CAMeL Tools on common Arabic words:")
    print("=" * 50)
    
    for word in common_words:
        analysis = camel_processor.analyze_word(word)
        lemmas = analysis.get("possible_lemmas", [])
        roots = analysis.get("roots", [])
        pos_tags = analysis.get("pos_tags", [])
        
        print(f"{word}:")
        print(f"  Lemmas: {lemmas[:3]}")  # Show top 3
        print(f"  Roots: {roots}")
        print(f"  POS: {pos_tags}")
        print()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            test_camel_on_common_words()
        elif command == "enhance":
            enhanced = enhance_database_with_camel()
            if enhanced > 0:
                show_enhanced_samples()
        elif command == "samples":
            show_enhanced_samples()
        else:
            print("Unknown command. Use: test, enhance, or samples")
    else:
        print("CAMeL Tools Dictionary Enhancement")
        print("Commands:")
        print("  python camel_working.py test     - Test on common words")
        print("  python camel_working.py enhance  - Enhance database")
        print("  python camel_working.py samples  - Show enhanced samples")
        print(f"\nCAMeL Tools available: {'✓' if camel_processor.available else '✗'}")
