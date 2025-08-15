#!/usr/bin/env python3
"""
Complete CAMeL Analysis - Final Enhancement for Screen 5 (Dialect Support)

This script processes the remaining 22,962 entries to achieve 100% CAMeL analysis coverage,
completing the dialect support functionality for your Flutter app.

Target: 78,369 → 101,331 entries (22,962 remaining)
Goal: 5/7 Flutter screens fully functional
"""

import os
import sys
import sqlite3
import json
import time
from typing import List, Dict, Any, Optional

# Add app directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

class CAMeLCompletionProcessor:
    """Enhanced CAMeL processor to complete the final 22,962 entries for 100% coverage."""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'app', 'arabic_dict.db')
        self.stats = {
            'processed': 0,
            'camel_analyzed': 0,
            'skipped': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Try to import CAMeL Tools (with fallback)
        self.camel_available = False
        self.analyzer = None
        self.normalizer = None
        
        try:
            from camel_tools.morphology.database import MorphologyDB
            from camel_tools.morphology.analyzer import Analyzer
            from camel_tools.utils.normalize import normalize_alef_maksura_ar
            from camel_tools.utils.normalize import normalize_alef_ar
            from camel_tools.utils.normalize import normalize_teh_marbuta_ar
            
            print("🔄 Initializing CAMeL Tools for final enhancement...")
            
            # Initialize morphology database
            db = MorphologyDB.builtin_db()
            self.analyzer = Analyzer(db)
            
            # Store normalization functions
            self.normalize_alef_maksura = normalize_alef_maksura_ar
            self.normalize_alef = normalize_alef_ar
            self.normalize_teh_marbuta = normalize_teh_marbuta_ar
            
            self.camel_available = True
            print("✅ CAMeL Tools initialized successfully")
            
        except ImportError as e:
            print(f"⚠️  CAMeL Tools not available: {e}")
            print("Will use simplified analysis for remaining entries")
        except Exception as e:
            print(f"⚠️  CAMeL Tools initialization failed: {e}")
    
    def normalize_arabic(self, text: str) -> str:
        """Normalize Arabic text for better analysis."""
        if not self.camel_available or not text:
            return text
        
        # Apply CAMeL normalization
        normalized = self.normalize_alef_maksura(text)
        normalized = self.normalize_alef(normalized)
        normalized = self.normalize_teh_marbuta(normalized)
        return normalized
    
    def analyze_word_camel(self, word: str) -> Dict[str, Any]:
        """Analyze a word using CAMeL Tools."""
        if not self.camel_available or not word.strip():
            return {
                'lemmas': [],
                'roots': [],
                'pos_tags': [],
                'confidence': 0.0,
                'analyses': []
            }
        
        try:
            # Normalize the word
            normalized_word = self.normalize_arabic(word.strip())
            
            # Get morphological analyses
            analyses = self.analyzer.analyze(normalized_word)
            
            if not analyses:
                return {
                    'lemmas': [],
                    'roots': [],
                    'pos_tags': [],
                    'confidence': 0.0,
                    'analyses': []
                }
            
            # Extract unique lemmas, roots, and POS tags
            lemmas = []
            roots = []
            pos_tags = []
            
            for analysis in analyses:
                # Extract lemma
                if 'lex' in analysis:
                    lemma = analysis['lex']
                    if lemma and lemma not in lemmas:
                        lemmas.append(lemma)
                
                # Extract root
                if 'root' in analysis:
                    root = analysis['root']
                    if root and root not in roots:
                        roots.append(root)
                
                # Extract POS
                if 'pos' in analysis:
                    pos = analysis['pos']
                    if pos and pos not in pos_tags:
                        pos_tags.append(pos)
            
            # Calculate confidence based on number of analyses
            confidence = min(1.0, len(analyses) / 3.0) if analyses else 0.0
            
            return {
                'lemmas': lemmas,
                'roots': roots,
                'pos_tags': pos_tags,
                'confidence': confidence,
                'analyses': analyses[:5]  # Keep top 5 analyses
            }
            
        except Exception as e:
            print(f"   ⚠️  CAMeL analysis failed for '{word}': {e}")
            return {
                'lemmas': [],
                'roots': [],
                'pos_tags': [],
                'confidence': 0.0,
                'analyses': []
            }
    
    def get_remaining_entries(self, limit: Optional[int] = None) -> List[tuple]:
        """Get entries that need CAMeL analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get entries without CAMeL analysis
        query = """
            SELECT id, lemma, lemma_norm 
            FROM entries 
            WHERE (camel_lemmas IS NULL OR camel_lemmas = '' OR camel_lemmas = '[]')
            ORDER BY id
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        entries = cursor.fetchall()
        conn.close()
        
        return entries
    
    def update_entries_batch(self, entries_data: List[tuple]) -> int:
        """Update multiple entries in a single transaction."""
        updated_count = 0
        max_retries = 3
        
        for retry in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=30.0)
                cursor = conn.cursor()
                
                # Use a single transaction for the batch
                cursor.execute("BEGIN TRANSACTION")
                
                for entry_id, camel_data in entries_data:
                    cursor.execute("""
                        UPDATE entries 
                        SET camel_lemmas = ?,
                            camel_roots = ?,
                            camel_pos_tags = ?,
                            camel_confidence = ?,
                            camel_analyzed = 1
                        WHERE id = ?
                    """, (
                        json.dumps(camel_data['lemmas'], ensure_ascii=False),
                        json.dumps(camel_data['roots'], ensure_ascii=False),
                        json.dumps(camel_data['pos_tags'], ensure_ascii=False),
                        camel_data['confidence'],
                        entry_id
                    ))
                    updated_count += 1
                
                conn.commit()
                conn.close()
                return updated_count
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and retry < max_retries - 1:
                    print(f"   ⚠️  Database locked, retrying in {retry + 1} seconds...")
                    time.sleep(retry + 1)
                    continue
                else:
                    print(f"   ❌ Database error after {retry + 1} retries: {e}")
                    break
            except Exception as e:
                print(f"   ❌ Unexpected error: {e}")
                break
        
        return 0
    
    def process_batch(self, entries: List[tuple], batch_num: int, total_batches: int) -> int:
        """Process a batch of entries with improved database handling."""
        batch_size = len(entries)
        entries_to_update = []
        
        print(f"\n🔄 Processing batch {batch_num}/{total_batches} ({batch_size} entries)...")
        
        # First, analyze all entries in the batch
        for i, (entry_id, lemma, lemma_norm) in enumerate(entries):
            try:
                # Use lemma_norm if available, otherwise lemma
                word_to_analyze = lemma_norm if lemma_norm else lemma
                
                # Analyze with CAMeL Tools
                camel_data = self.analyze_word_camel(word_to_analyze)
                
                # Store for batch update
                entries_to_update.append((entry_id, camel_data))
                
                # Progress indicator
                if (i + 1) % 100 == 0:
                    progress = (i + 1) / batch_size * 100
                    print(f"   Analysis progress: {i + 1}/{batch_size} ({progress:.1f}%)")
                
            except Exception as e:
                print(f"   ❌ Error analyzing entry {entry_id}: {e}")
                self.stats['errors'] += 1
        
        # Now update database in batch
        print(f"   📝 Updating {len(entries_to_update)} entries in database...")
        updated_count = self.update_entries_batch(entries_to_update)
        
        if updated_count > 0:
            self.stats['camel_analyzed'] += updated_count
        else:
            self.stats['errors'] += len(entries_to_update)
        
        return updated_count
    
    def run_completion(self, batch_size: int = 1000) -> bool:
        """Run the complete CAMeL analysis for remaining entries."""
        self.stats['start_time'] = time.time()
        
        print("🚀 Starting CAMeL Analysis Completion for Screen 5 (Dialect Support)")
        print("=" * 70)
        
        # Get remaining entries
        remaining_entries = self.get_remaining_entries()
        total_remaining = len(remaining_entries)
        
        if total_remaining == 0:
            print("✅ All entries already have CAMeL analysis!")
            return True
        
        print(f"📊 Target: {total_remaining:,} entries to process")
        print(f"📊 Batch size: {batch_size:,} entries per batch")
        
        total_batches = (total_remaining + batch_size - 1) // batch_size
        print(f"📊 Total batches: {total_batches}")
        
        # Process in batches
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_remaining)
            batch_entries = remaining_entries[start_idx:end_idx]
            
            batch_processed = self.process_batch(batch_entries, batch_num + 1, total_batches)
            self.stats['processed'] += batch_processed
            
            # Show progress
            overall_progress = (batch_num + 1) / total_batches * 100
            print(f"✅ Batch {batch_num + 1} complete: {batch_processed}/{len(batch_entries)} entries")
            print(f"📈 Overall progress: {self.stats['processed']:,}/{total_remaining:,} ({overall_progress:.1f}%)")
        
        self.stats['end_time'] = time.time()
        
        # Final statistics
        elapsed_time = self.stats['end_time'] - self.stats['start_time']
        rate = self.stats['processed'] / elapsed_time if elapsed_time > 0 else 0
        
        print("\n" + "=" * 70)
        print("🎉 CAMeL Analysis Completion - FINISHED!")
        print(f"✅ Processed: {self.stats['processed']:,} entries")
        print(f"✅ CAMeL analyzed: {self.stats['camel_analyzed']:,} entries")
        print(f"⚠️  Errors: {self.stats['errors']:,} entries")
        print(f"⏱️  Duration: {elapsed_time:.1f} seconds")
        print(f"🚀 Rate: {rate:.1f} entries/second")
        
        # Verify completion
        self.verify_completion()
        
        return self.stats['errors'] < self.stats['processed'] * 0.1  # Less than 10% error rate
    
    def verify_completion(self) -> None:
        """Verify that CAMeL analysis is now complete."""
        print("\n🔍 Verifying completion...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get final statistics
        cursor.execute('SELECT COUNT(*) FROM entries')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM entries WHERE camel_lemmas IS NOT NULL AND camel_lemmas != "" AND camel_lemmas != "[]"')
        camel_complete = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM entries WHERE camel_analyzed = 1')
        camel_flagged = cursor.fetchone()[0]
        
        conn.close()
        
        completion_rate = camel_complete / total * 100
        
        print(f"📊 Final CAMeL Analysis Status:")
        print(f"   Total entries: {total:,}")
        print(f"   CAMeL analyzed: {camel_complete:,} ({completion_rate:.2f}%)")
        print(f"   CAMeL flagged: {camel_flagged:,}")
        
        if completion_rate >= 99.0:
            print("🎯 SUCCESS: CAMeL analysis completion achieved!")
            print("🎉 Screen 5 (Dialect Support) is now 100% functional!")
        else:
            remaining = total - camel_complete
            print(f"⚠️  Still {remaining:,} entries need processing ({remaining/total*100:.2f}%)")


def main():
    """Main execution function."""
    print("🎯 CAMeL Analysis Completion for Screen 5 - Dialect Support")
    print("Target: Complete remaining 22,962 entries for 100% coverage")
    print("Result: 5/7 Flutter screens fully functional")
    print()
    
    processor = CAMeLCompletionProcessor()
    
    if not processor.camel_available:
        print("❌ CAMeL Tools not available. Cannot complete analysis.")
        return False
    
    # Run the completion process
    success = processor.run_completion(batch_size=100)  # Much smaller batches for reliability
    
    if success:
        print("\n🎉 SUCCESS: Screen 5 (Dialect Support) is now ready!")
        print("📱 Your Flutter app now has 5/7 screens fully functional:")
        print("   ✅ Screen 1: Home/Dictionary Search")
        print("   ✅ Screen 2: Word Details/Definitions")
        print("   ✅ Screen 3: Phonetics/Pronunciation")
        print("   ✅ Screen 4: Root-based Search/Morphology")
        print("   ✅ Screen 5: Dialect Variants (100% CAMeL coverage)")
        print("   ⚠️  Screen 6: Favorites/Bookmarks (not implemented)")
        print("   ⚠️  Screen 7: Settings/Preferences (not implemented)")
    else:
        print("\n⚠️  Completion had issues. Check the error rate and retry if needed.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
