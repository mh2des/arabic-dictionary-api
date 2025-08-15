"""
Simplified CAMeL Tools dictionary enhancement script.
Works with the existing database schema.
"""
import sqlite3
import json
import logging
from pathlib import Path
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Use the final working CAMeL processor
from services.camel_final import camel_processor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enhance_dictionary_with_camel(db_path: str = "app/arabic_dict.db", max_entries: int = 100):
    """
    Enhance dictionary entries with CAMeL Tools morphological analysis.
    """
    if not camel_processor.available:
        logger.error("CAMeL Tools not available!")
        return
    
    logger.info("Starting CAMeL Tools enhancement...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add CAMeL columns if they don't exist
    camel_columns = [
        "camel_lemmas TEXT",
        "camel_roots TEXT", 
        "camel_pos TEXT",
        "camel_patterns TEXT",
        "camel_morphology TEXT",
        "camel_confidence REAL",
        "camel_analyzed INTEGER DEFAULT 0"
    ]
    
    for column in camel_columns:
        try:
            cursor.execute(f"ALTER TABLE entries ADD COLUMN {column}")
        except sqlite3.OperationalError:
            pass  # Column already exists
    
    # Get entries to process
    query = "SELECT id, lemma, root, pos FROM entries WHERE camel_analyzed IS NULL OR camel_analyzed = 0 LIMIT ?"
    cursor.execute(query, (max_entries,))
    entries = cursor.fetchall()
    
    logger.info(f"Processing {len(entries)} entries...")
    
    enhanced_count = 0
    for i, (entry_id, lemma, existing_root, existing_pos) in enumerate(entries):
        if not lemma:
            continue
            
        try:
            # Analyze with CAMeL Tools
            analysis = camel_processor.analyze_word(lemma)
            
            # Extract data
            camel_lemmas = analysis.get("possible_lemmas", [])
            camel_roots = analysis.get("roots", [])
            camel_pos = analysis.get("pos_tags", [])
            camel_patterns = analysis.get("patterns", [])
            camel_morphology = analysis.get("morphology", [])
            
            # Calculate confidence
            confidence = min(1.0, len(camel_morphology) / 10.0) if camel_morphology else 0.0
            
            # Update database
            cursor.execute("""
                UPDATE entries SET 
                    camel_lemmas = ?,
                    camel_roots = ?,
                    camel_pos = ?,
                    camel_patterns = ?,
                    camel_morphology = ?,
                    camel_confidence = ?,
                    camel_analyzed = 1
                WHERE id = ?
            """, (
                json.dumps(camel_lemmas, ensure_ascii=False),
                json.dumps(camel_roots, ensure_ascii=False),
                json.dumps(camel_pos, ensure_ascii=False),
                json.dumps(camel_patterns, ensure_ascii=False),
                json.dumps(camel_morphology, ensure_ascii=False),
                confidence,
                entry_id
            ))
            
            # Update main fields if empty and CAMeL provides data
            if not existing_root and camel_roots:
                cursor.execute("UPDATE entries SET root = ? WHERE id = ?", (camel_roots[0], entry_id))
            
            if not existing_pos and camel_pos:
                cursor.execute("UPDATE entries SET pos = ? WHERE id = ?", (camel_pos[0], entry_id))
            
            enhanced_count += 1
            
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{len(entries)} entries...")
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error processing entry {entry_id} ('{lemma}'): {e}")
    
    conn.commit()
    conn.close()
    
    logger.info(f"Enhancement complete! Enhanced {enhanced_count} entries.")

def test_camel_on_sample_words():
    """Test CAMeL Tools on common Arabic words."""
    if not camel_processor.available:
        print("CAMeL Tools not available!")
        return
    
    test_words = ["كتاب", "يكتب", "مكتبة", "بيت", "ماء", "قلم", "جميل", "كبير"]
    
    print("\n=== CAMeL Tools Analysis Results ===")
    for word in test_words:
        analysis = camel_processor.analyze_word(word)
        print(f"\nWord: {word}")
        print(f"  Lemmas: {analysis.get('possible_lemmas', [])[:3]}")  # Show first 3
        print(f"  Roots: {analysis.get('roots', [])}")
        print(f"  POS: {analysis.get('pos_tags', [])}")
        print(f"  Analyses found: {len(analysis.get('morphology', []))}")

def show_enhancement_stats(db_path: str = "app/arabic_dict.db"):
    """Show statistics about CAMeL Tools enhancement."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if camel columns exist
    cursor.execute("PRAGMA table_info(entries)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "camel_analyzed" not in columns:
        print("Dictionary not yet enhanced with CAMeL Tools.")
        conn.close()
        return
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) FROM entries")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM entries WHERE camel_analyzed = 1")
    analyzed = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM entries WHERE camel_roots IS NOT NULL AND camel_roots != '[]'")
    with_roots = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(camel_confidence) FROM entries WHERE camel_confidence IS NOT NULL")
    avg_confidence = cursor.fetchone()[0] or 0
    
    # Sample enhanced entries
    cursor.execute("""
        SELECT lemma, camel_lemmas, camel_roots, camel_pos, camel_confidence
        FROM entries 
        WHERE camel_analyzed = 1 AND camel_lemmas != '[]'
        ORDER BY camel_confidence DESC 
        LIMIT 5
    """)
    samples = cursor.fetchall()
    
    conn.close()
    
    print(f"\n=== CAMeL Tools Enhancement Statistics ===")
    print(f"Total entries: {total:,}")
    print(f"Analyzed with CAMeL: {analyzed:,} ({analyzed/total*100:.1f}%)")
    print(f"Entries with roots: {with_roots:,} ({with_roots/total*100:.1f}%)")
    print(f"Average confidence: {avg_confidence:.3f}")
    
    if samples:
        print("\nTop enhanced entries:")
        for lemma, lemmas_json, roots_json, pos_json, conf in samples:
            try:
                lemmas = json.loads(lemmas_json)
                roots = json.loads(roots_json)
                pos_tags = json.loads(pos_json)
                print(f"  {lemma} → lemmas: {lemmas[:2]}, roots: {roots}, POS: {pos_tags}, conf: {conf:.2f}")
            except:
                print(f"  {lemma} → (parsing error)")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CAMeL Tools dictionary enhancement")
    parser.add_argument("--test", action="store_true", help="Test CAMeL Tools on sample words")
    parser.add_argument("--enhance", action="store_true", help="Enhance dictionary entries")
    parser.add_argument("--stats", action="store_true", help="Show enhancement statistics")
    parser.add_argument("--max-entries", type=int, default=100, help="Maximum entries to enhance")
    parser.add_argument("--db", default="app/arabic_dict.db", help="Database path")
    
    args = parser.parse_args()
    
    if args.test:
        test_camel_on_sample_words()
    
    if args.enhance:
        enhance_dictionary_with_camel(args.db, args.max_entries)
    
    if args.stats:
        show_enhancement_stats(args.db)
    
    if not any([args.test, args.enhance, args.stats]):
        print("CAMeL Tools Dictionary Enhancement")
        print("Use --test, --enhance, or --stats")
        print(f"CAMeL Tools available: {'✓' if camel_processor.available else '✗'}")
        if camel_processor.available:
            caps = camel_processor.get_capabilities()
            for feature, available in caps.items():
                print(f"  {feature}: {'✓' if available else '✗'}")
