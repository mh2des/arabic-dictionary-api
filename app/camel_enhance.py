"""
Dictionary enhancement script using CAMeL Tools.
Processes existing dictionary entries and enriches them with advanced morphological analysis.
"""
import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.camel_processor import camel_processor, enhance_dictionary_entry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DictionaryEnhancer:
    """Enhance dictionary entries with CAMeL Tools analysis."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.enhanced_count = 0
        self.error_count = 0
    
    def enhance_all_entries(self, batch_size: int = 100, max_entries: int = None):
        """
        Enhance all dictionary entries with CAMeL Tools analysis.
        
        Args:
            batch_size: Number of entries to process in each batch
            max_entries: Maximum number of entries to process (None for all)
        """
        logger.info("Starting dictionary enhancement with CAMeL Tools...")
        
        if not camel_processor.available:
            logger.error("CAMeL Tools not available. Cannot enhance dictionary.")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add new columns for CAMeL Tools data if they don't exist
        self._add_camel_columns(cursor)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM entries")
        total_entries = cursor.fetchone()[0]
        
        if max_entries:
            total_entries = min(total_entries, max_entries)
        
        logger.info(f"Processing {total_entries} entries in batches of {batch_size}")
        
        # Process entries in batches
        offset = 0
        while offset < total_entries:
            limit = min(batch_size, total_entries - offset)
            
            # Get batch of entries
            cursor.execute("""
                SELECT id, lemma, root, pos, gender, number, pattern, 
                       conjugation, normalized_lemma, definition
                FROM entries 
                ORDER BY id 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            entries = cursor.fetchall()
            
            logger.info(f"Processing batch {offset//batch_size + 1}: "
                       f"entries {offset+1} to {offset+len(entries)}")
            
            # Process each entry in the batch
            for entry in entries:
                try:
                    self._enhance_entry(cursor, entry)
                    self.enhanced_count += 1
                except Exception as e:
                    logger.error(f"Error enhancing entry {entry[0]}: {e}")
                    self.error_count += 1
            
            # Commit batch
            conn.commit()
            
            # Progress update
            progress = (offset + len(entries)) / total_entries * 100
            logger.info(f"Progress: {progress:.1f}% "
                       f"({self.enhanced_count} enhanced, {self.error_count} errors)")
            
            offset += len(entries)
        
        conn.close()
        logger.info(f"Enhancement complete. Enhanced: {self.enhanced_count}, "
                   f"Errors: {self.error_count}")
    
    def _add_camel_columns(self, cursor):
        """Add columns for CAMeL Tools analysis results."""
        columns_to_add = [
            ("camel_lemmas", "TEXT"),  # JSON array of possible lemmas
            ("camel_roots", "TEXT"),   # JSON array of possible roots
            ("camel_pos_tags", "TEXT"), # JSON array of POS tags
            ("camel_patterns", "TEXT"), # JSON array of patterns
            ("camel_morphology", "TEXT"), # JSON object with detailed morphology
            ("camel_dialect", "TEXT"),  # JSON object with dialect info
            ("camel_normalized", "TEXT"), # Normalized form
            ("camel_confidence", "REAL"), # Overall confidence score
            ("camel_analyzed", "INTEGER DEFAULT 0") # Flag indicating CAMeL analysis done
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE entries ADD COLUMN {col_name} {col_type}")
                logger.info(f"Added column: {col_name}")
            except sqlite3.OperationalError:
                # Column already exists
                pass
    
    def _enhance_entry(self, cursor, entry):
        """Enhance a single dictionary entry."""
        (entry_id, lemma, root, pos, gender, number, pattern, 
         conjugation, normalized_lemma, definition) = entry
        
        # Use lemma as the word to analyze
        word_to_analyze = lemma or normalized_lemma
        if not word_to_analyze:
            return
        
        # Get existing data
        existing_data = {
            "lemma": lemma,
            "root": root,
            "pos": pos,
            "gender": gender,
            "number": number,
            "pattern": pattern,
            "conjugation": conjugation,
            "definition": definition
        }
        
        # Enhance with CAMeL Tools
        enhanced = enhance_dictionary_entry(word_to_analyze, existing_data)
        
        # Extract CAMeL-specific data
        camel_analysis = camel_processor.analyze_word(word_to_analyze)
        
        # Calculate confidence based on number of analyses found
        confidence = 0.0
        if camel_analysis.get("morphology"):
            confidence = min(1.0, len(camel_analysis["morphology"]) / 5.0)
        
        # Update database with CAMeL analysis
        cursor.execute("""
            UPDATE entries SET
                camel_lemmas = ?,
                camel_roots = ?,
                camel_pos_tags = ?,
                camel_patterns = ?,
                camel_morphology = ?,
                camel_dialect = ?,
                camel_normalized = ?,
                camel_confidence = ?,
                camel_analyzed = 1
            WHERE id = ?
        """, (
            json.dumps(camel_analysis.get("possible_lemmas", []), ensure_ascii=False),
            json.dumps(camel_analysis.get("roots", []), ensure_ascii=False),
            json.dumps(camel_analysis.get("pos_tags", []), ensure_ascii=False),
            json.dumps(camel_analysis.get("patterns", []), ensure_ascii=False),
            json.dumps(camel_analysis.get("morphology", []), ensure_ascii=False),
            json.dumps(camel_analysis.get("dialect"), ensure_ascii=False) if camel_analysis.get("dialect") else None,
            camel_analysis.get("normalized", word_to_analyze),
            confidence,
            entry_id
        ))
        
        # Update main fields if CAMeL provides better data
        updates = []
        params = []
        
        if not root and camel_analysis.get("roots"):
            updates.append("root = ?")
            params.append(camel_analysis["roots"][0])
        
        if not pos and camel_analysis.get("pos_tags"):
            updates.append("pos = ?")
            params.append(camel_analysis["pos_tags"][0])
        
        if camel_analysis.get("patterns") and not pattern:
            updates.append("pattern = ?")
            params.append(camel_analysis["patterns"][0])
        
        if updates:
            params.append(entry_id)
            query = f"UPDATE entries SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
    
    def generate_statistics(self):
        """Generate statistics about CAMeL Tools enhancement."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total entries
        cursor.execute("SELECT COUNT(*) FROM entries")
        total = cursor.fetchone()[0]
        
        # Analyzed entries
        cursor.execute("SELECT COUNT(*) FROM entries WHERE camel_analyzed = 1")
        analyzed = cursor.fetchone()[0]
        
        # Entries with CAMeL roots
        cursor.execute("SELECT COUNT(*) FROM entries WHERE camel_roots IS NOT NULL AND camel_roots != '[]'")
        with_roots = cursor.fetchone()[0]
        
        # Entries with CAMeL POS
        cursor.execute("SELECT COUNT(*) FROM entries WHERE camel_pos_tags IS NOT NULL AND camel_pos_tags != '[]'")
        with_pos = cursor.fetchone()[0]
        
        # Average confidence
        cursor.execute("SELECT AVG(camel_confidence) FROM entries WHERE camel_confidence IS NOT NULL")
        avg_confidence = cursor.fetchone()[0] or 0
        
        # Dialect distribution
        cursor.execute("""
            SELECT camel_dialect, COUNT(*) 
            FROM entries 
            WHERE camel_dialect IS NOT NULL 
            GROUP BY camel_dialect 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        """)
        dialect_dist = cursor.fetchall()
        
        conn.close()
        
        print(f"\n=== CAMeL Tools Enhancement Statistics ===")
        print(f"Total entries: {total:,}")
        print(f"Analyzed with CAMeL: {analyzed:,} ({analyzed/total*100:.1f}%)")
        print(f"Entries with CAMeL roots: {with_roots:,} ({with_roots/total*100:.1f}%)")
        print(f"Entries with CAMeL POS: {with_pos:,} ({with_pos/total*100:.1f}%)")
        print(f"Average confidence: {avg_confidence:.3f}")
        
        if dialect_dist:
            print("\nTop dialect classifications:")
            for dialect, count in dialect_dist[:5]:
                try:
                    dialect_data = json.loads(dialect)
                    dialect_name = dialect_data.get("top_dialect", "unknown")
                    print(f"  {dialect_name}: {count:,}")
                except:
                    print(f"  {dialect}: {count:,}")

def test_camel_tools():
    """Test CAMeL Tools functionality."""
    logger.info("Testing CAMeL Tools functionality...")
    
    if not camel_processor.available:
        logger.error("CAMeL Tools not available!")
        return False
    
    test_words = ["كتاب", "يكتب", "مكتبة", "الكتاب", "كاتب"]
    
    for word in test_words:
        print(f"\n--- Testing: {word} ---")
        
        # Test analysis
        analysis = camel_processor.analyze_word(word)
        print(f"Lemmas: {analysis.get('possible_lemmas', [])}")
        print(f"Roots: {analysis.get('roots', [])}")
        print(f"POS: {analysis.get('pos_tags', [])}")
        print(f"Patterns: {analysis.get('patterns', [])}")
        
        # Test individual methods
        print(f"Best lemma: {camel_processor.get_best_lemma(word)}")
        print(f"Best root: {camel_processor.get_best_root(word)}")
        print(f"Best POS: {camel_processor.get_best_pos(word)}")
    
    logger.info("CAMeL Tools test completed successfully!")
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhance Arabic dictionary with CAMeL Tools")
    parser.add_argument("--db", default="app/arabic_dict.db", help="Database path")
    parser.add_argument("--test", action="store_true", help="Test CAMeL Tools functionality")
    parser.add_argument("--enhance", action="store_true", help="Enhance dictionary entries")
    parser.add_argument("--stats", action="store_true", help="Show enhancement statistics")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--max-entries", type=int, help="Maximum entries to process")
    
    args = parser.parse_args()
    
    if args.test:
        test_camel_tools()
    
    if args.enhance:
        enhancer = DictionaryEnhancer(args.db)
        enhancer.enhance_all_entries(args.batch_size, args.max_entries)
    
    if args.stats:
        enhancer = DictionaryEnhancer(args.db)
        enhancer.generate_statistics()
    
    if not any([args.test, args.enhance, args.stats]):
        print("Use --test, --enhance, or --stats. See --help for options.")
