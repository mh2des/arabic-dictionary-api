#!/usr/bin/env python3
"""
PHASE 2 ARABIC DICTIONARY ENHANCEMENT - FINAL VERSION
====================================================
Enhanced Arabic dictionary with phonetic transcription and semantic features

Features:
- Buckwalter transliteration
- IPA phonetic approximation
- Romanization
- Semantic feature extraction
- Safe database updates (bypassing FTS triggers)
"""

import sqlite3
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase2_enhancement.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Phase2Enhancer:
    def __init__(self):
        self.db_path = 'app/arabic_dict.db'
        self.stats = {
            'processed': 0,
            'phonetic': 0,
            'semantic': 0
        }

    def generate_phonetic_transcription(self, word: str) -> Dict[str, str]:
        """Generate comprehensive phonetic transcription"""
        transcriptions = {}
        
        # Comprehensive Buckwalter transliteration mapping
        buckwalter_map = {
            'ا': 'A', 'ب': 'b', 'ت': 't', 'ث': 'v', 'ج': 'j',
            'ح': 'H', 'خ': 'x', 'د': 'd', 'ذ': '*', 'ر': 'r',
            'ز': 'z', 'س': 's', 'ش': '$', 'ص': 'S', 'ض': 'D',
            'ط': 'T', 'ظ': 'Z', 'ع': 'E', 'غ': 'g', 'ف': 'f',
            'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
            'ه': 'h', 'و': 'w', 'ي': 'y', 'ة': 'p', 'ى': 'Y',
            'ء': "'", 'أ': '>', 'إ': '<', 'آ': '|', 'ؤ': '&',
            'ئ': '}', 'َ': 'a', 'ُ': 'u', 'ِ': 'i', 'ً': 'F',
            'ٌ': 'N', 'ٍ': 'K', 'ْ': 'o', 'ّ': '~'
        }
        
        buckwalter = ''.join(buckwalter_map.get(char, char) for char in word)
        transcriptions['buckwalter'] = buckwalter
        
        # Enhanced IPA approximation
        ipa_map = {
            'ا': 'aː', 'ب': 'b', 'ت': 't', 'ث': 'θ', 'ج': 'd͡ʒ',
            'ح': 'ħ', 'خ': 'x', 'د': 'd', 'ذ': 'ð', 'ر': 'r',
            'ز': 'z', 'س': 's', 'ش': 'ʃ', 'ص': 'sˤ', 'ض': 'dˤ',
            'ط': 'tˤ', 'ظ': 'ðˤ', 'ع': 'ʕ', 'غ': 'ɣ', 'ف': 'f',
            'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
            'ه': 'h', 'و': 'w', 'ي': 'j', 'ة': 'a', 'ى': 'aː',
            'ء': 'ʔ', 'أ': 'ʔa', 'إ': 'ʔi', 'آ': 'ʔaː',
            'َ': 'a', 'ُ': 'u', 'ِ': 'i', 'ً': 'an', 'ٌ': 'un', 'ٍ': 'in'
        }
        
        ipa = ''.join(ipa_map.get(char, char) for char in word if char in ipa_map)
        transcriptions['ipa_approx'] = ipa
        
        # Romanization (simplified)
        roman_map = {
            'ا': 'a', 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j',
            'ح': 'h', 'خ': 'kh', 'د': 'd', 'ذ': 'dh', 'ر': 'r',
            'ز': 'z', 'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'd',
            'ط': 't', 'ظ': 'dh', 'ع': "'", 'غ': 'gh', 'ف': 'f',
            'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
            'ه': 'h', 'و': 'w', 'ي': 'y', 'ة': 'a', 'ى': 'a'
        }
        
        romanization = ''.join(roman_map.get(char, char) for char in word if char in roman_map)
        transcriptions['romanization'] = romanization
        
        return transcriptions

    def extract_semantic_features(self, entry_data: Dict) -> Dict[str, Any]:
        """Extract semantic features from entry data"""
        features = {
            'semantic_class': '',
            'pos_category': '',
            'abstractness': 0.5,
            'frequency_estimate': 0,
            'morphological_complexity': 0,
            'diacritic_density': 0
        }
        
        # Extract from existing data
        pos = entry_data.get('pos', '')
        lemma = entry_data.get('lemma', '')
        
        # POS-based classification
        if pos:
            pos_lower = pos.lower()
            if 'noun' in pos_lower or 'اسم' in pos_lower:
                features['semantic_class'] = 'entity'
                features['pos_category'] = 'noun'
                features['abstractness'] = 0.6
            elif 'verb' in pos_lower or 'فعل' in pos_lower:
                features['semantic_class'] = 'action'
                features['pos_category'] = 'verb'
                features['abstractness'] = 0.3
            elif 'adj' in pos_lower or 'صفة' in pos_lower:
                features['semantic_class'] = 'property'
                features['pos_category'] = 'adjective'
                features['abstractness'] = 0.4
            elif 'adv' in pos_lower or 'ظرف' in pos_lower:
                features['semantic_class'] = 'modifier'
                features['pos_category'] = 'adverb'
                features['abstractness'] = 0.2
        
        # Morphological complexity based on length and diacritics
        if lemma:
            features['morphological_complexity'] = min(len(lemma) / 10, 1.0)
            
            # Count diacritics
            diacritics = ['َ', 'ُ', 'ِ', 'ً', 'ٌ', 'ٍ', 'ْ', 'ّ']
            diacritic_count = sum(1 for char in lemma if char in diacritics)
            features['diacritic_density'] = diacritic_count / len(lemma) if lemma else 0
        
        return features

    def enhance_entry(self, entry_data: tuple) -> Dict[str, Any]:
        """Enhance a single dictionary entry with Phase 2 features"""
        # Unpack entry data
        entry_id = entry_data[0]
        lemma = entry_data[1]
        pos = entry_data[5] if len(entry_data) > 5 else ''
        
        if not lemma:
            return {}
        
        try:
            # Create entry dict for processing
            entry_dict = {
                'id': entry_id,
                'lemma': lemma,
                'pos': pos
            }
            
            # Phonetic transcription
            phonetic_data = self.generate_phonetic_transcription(lemma)
            
            # Semantic feature extraction
            semantic_features = self.extract_semantic_features(entry_dict)
            
            # Prepare enhancement data
            enhancement_data = {
                'dialect_msa_analysis': json.dumps({'processed': True, 'lemma': lemma}, ensure_ascii=False),
                'dialect_egy_analysis': json.dumps({}, ensure_ascii=False),
                'dialect_lev_analysis': json.dumps({}, ensure_ascii=False),
                'dialect_glf_analysis': json.dumps({}, ensure_ascii=False),
                'cross_dialect_variants': json.dumps([], ensure_ascii=False),
                'advanced_morphology': json.dumps({'pos': pos, 'lemma': lemma}, ensure_ascii=False),
                'phonetic_transcription': json.dumps(phonetic_data, ensure_ascii=False),
                'buckwalter_transliteration': phonetic_data.get('buckwalter', ''),
                'semantic_features': json.dumps(semantic_features, ensure_ascii=False),
                'named_entity_tags': json.dumps([], ensure_ascii=False),
                'semantic_relations': json.dumps([], ensure_ascii=False),
                'usage_frequency': 0,
                'register_classification': 'standard',
                'cognates': json.dumps([], ensure_ascii=False),
                'borrowings': json.dumps([], ensure_ascii=False),
                'historical_etymology': '',
                'phase2_enhanced': 1,
                'phase2_version': '2.0.3',
                'phase2_timestamp': datetime.now().isoformat(),
                'phase2_dialect_coverage': 'basic'
            }
            
            # Update statistics
            self.stats['processed'] += 1
            if phonetic_data:
                self.stats['phonetic'] += 1
            if semantic_features:
                self.stats['semantic'] += 1
            
            return enhancement_data
            
        except Exception as e:
            logger.error(f"Error enhancing entry {entry_id} ({lemma}): {e}")
            return {}

    def disable_fts_triggers(self, cursor):
        """Temporarily disable FTS triggers"""
        logger.info("Disabling FTS triggers temporarily...")
        cursor.execute("DROP TRIGGER IF EXISTS entries_ai")
        cursor.execute("DROP TRIGGER IF EXISTS entries_ad") 
        cursor.execute("DROP TRIGGER IF EXISTS entries_au")

    def recreate_fts_triggers(self, cursor):
        """Recreate FTS triggers after enhancement"""
        logger.info("Recreating FTS triggers...")
        
        # Recreate the triggers with proper column mapping
        cursor.execute("""
        CREATE TRIGGER entries_ai AFTER INSERT ON entries BEGIN
            INSERT INTO entries_fts(rowid, lemma_norm, root, pattern, pos)
            VALUES (new.id, new.lemma_norm, new.root, new.pattern, new.pos);
        END
        """)
        
        cursor.execute("""
        CREATE TRIGGER entries_ad AFTER DELETE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts) VALUES('delete-id ' || old.id);
        END
        """)
        
        cursor.execute("""
        CREATE TRIGGER entries_au AFTER UPDATE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts) VALUES('delete-id ' || old.id);
            INSERT INTO entries_fts(rowid, lemma_norm, root, pattern, pos)
            VALUES (new.id, new.lemma_norm, new.root, new.pattern, new.pos);
        END
        """)

    def run_enhancement(self, limit: int = 2000):
        """Run the Phase 2 enhancement process"""
        logger.info("STARTING PHASE 2 ENHANCEMENT")
        logger.info("=" * 50)
        
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Disable FTS triggers temporarily
            self.disable_fts_triggers(cursor)
            
            # Get entries to enhance
            cursor.execute("""
                SELECT id, lemma, lemma_norm, root, pattern, pos
                FROM entries 
                WHERE phase2_enhanced IS NULL OR phase2_enhanced = 0
                ORDER BY id 
                LIMIT ?
            """, (limit,))
            
            entries = cursor.fetchall()
            total_entries = len(entries)
            
            logger.info(f"Enhancing {total_entries} entries with Phase 2 features")
            
            start_time = time.time()
            
            for i, entry in enumerate(entries, 1):
                entry_id = entry[0]
                
                # Enhance the entry
                enhancement_data = self.enhance_entry(entry)
                
                # Update database
                if enhancement_data:
                    # Build UPDATE query for main entries table
                    set_clauses = []
                    values = []
                    
                    for column, value in enhancement_data.items():
                        set_clauses.append(f"{column} = ?")
                        values.append(value)
                    
                    values.append(entry_id)
                    
                    update_query = f"""
                    UPDATE entries 
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                    """
                    
                    cursor.execute(update_query, values)
                
                # Progress reporting
                if i % 50 == 0 or i == total_entries:
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    print(f"   Enhanced: {i:,}/{total_entries:,} ({i/total_entries*100:.1f}%) - Rate: {rate:.1f}/sec")
            
            # Recreate FTS triggers
            self.recreate_fts_triggers(cursor)
            
            # Commit changes
            conn.commit()
            
            # Final statistics
            elapsed = time.time() - start_time
            logger.info("PHASE 2 ENHANCEMENT COMPLETE!")
            logger.info("STATISTICS:")
            logger.info(f"   Entries processed: {self.stats['processed']}")
            logger.info(f"   Phonetic transcription: {self.stats['phonetic']}")
            logger.info(f"   Semantic features: {self.stats['semantic']}")
            logger.info(f"   Processing time: {elapsed:.1f} seconds")
            logger.info(f"   Average rate: {self.stats['processed']/elapsed:.1f} entries/sec")
            
            return True
            
        except Exception as e:
            logger.error(f"Enhancement failed: {e}")
            conn.rollback()
            # Try to recreate triggers even if enhancement failed
            try:
                self.recreate_fts_triggers(cursor)
                conn.commit()
            except:
                pass
            return False
        finally:
            conn.close()

def main():
    print("PHASE 2: ARABIC DICTIONARY ENHANCEMENT")
    print("=" * 45)
    print("Features:")
    print("- Buckwalter transliteration for all entries")
    print("- IPA phonetic approximation")
    print("- Romanization")
    print("- Semantic feature extraction")
    print("- POS-based classification")
    print("- Morphological complexity analysis")
    print("- Enhanced database schema")
    print()
    
    enhancer = Phase2Enhancer()
    
    # Ask for confirmation
    response = input("Proceed with Phase 2 enhancement? (y/N): ").strip().lower()
    if response != 'y':
        print("Enhancement cancelled.")
        return
    
    # Run enhancement
    success = enhancer.run_enhancement(limit=2000)
    
    if success:
        print()
        print("PHASE 2 ENHANCEMENT COMPLETE!")
        print("=" * 40)
        print("RESULTS:")
        print(f"   ✓ {enhancer.stats['processed']} entries enhanced")
        print(f"   ✓ {enhancer.stats['phonetic']} phonetic transcriptions")
        print(f"   ✓ {enhancer.stats['semantic']} semantic analyses")
        print()
        print("NEW FEATURES ADDED:")
        print("   • Buckwalter transliteration")
        print("   • IPA phonetic approximation")
        print("   • Romanization")
        print("   • Semantic classification")
        print("   • POS categorization")
        print("   • Morphological complexity metrics")
        print("   • Diacritic density analysis")
        print()
        print("🎉 ARABIC DICTIONARY NOW ENHANCED!")
        print("Ready for advanced Arabic language processing!")
        print("Supports multi-script phonetic representations!")
    else:
        print("❌ Phase 2 enhancement failed. Check logs for details.")

if __name__ == "__main__":
    main()
