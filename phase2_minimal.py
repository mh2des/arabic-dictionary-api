#!/usr/bin/env python3
"""
COMPREHENSIVE PHASE 2 ARABIC DICTIONARY ENHANCEMENT - MINIMAL VERSION
====================================================================
Enhanced morphological analysis with available CAMeL Tools

Features:
- Basic morphological analysis
- Phonetic transcription (Buckwalter)
- Semantic feature extraction
- Multi-format analysis support
"""

import sqlite3
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

# Configure logging without emoji characters for Windows
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
        self.analyzer = None
        self.stats = {
            'processed': 0,
            'morphology': 0,
            'phonetic': 0,
            'semantic': 0
        }
        
    def initialize_camel_tools(self):
        """Initialize available CAMeL Tools"""
        logger.info("Initializing available CAMeL Tools...")
        
        try:
            from camel_tools.morphology.database import MorphologyDB
            from camel_tools.morphology.analyzer import Analyzer
            
            # Try different database names
            db_names = [
                'morphology-db-msa-r13',
                'calima-msa-r13',
                'msa-r13',
                'msa'
            ]
            
            for db_name in db_names:
                try:
                    logger.info(f"Trying database: {db_name}")
                    db = MorphologyDB(db_name)
                    self.analyzer = Analyzer(db)
                    logger.info(f"Successfully loaded: {db_name}")
                    break
                except Exception as e:
                    logger.warning(f"Database {db_name} unavailable: {e}")
            
            if self.analyzer:
                logger.info("CAMeL Tools morphological analyzer initialized")
                return True
            else:
                logger.warning("No morphology database available - proceeding with basic features")
                return True  # Continue without morphology
                
        except ImportError as e:
            logger.warning(f"CAMeL Tools not available: {e}")
            return True  # Continue without CAMeL Tools
        except Exception as e:
            logger.error(f"Error initializing CAMeL Tools: {e}")
            return True  # Continue without CAMeL Tools

    def ensure_phase2_columns(self):
        """Ensure all Phase 2 columns exist in the database"""
        logger.info("Ensuring Phase 2 enhancement columns exist...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Phase 2 columns to add
        phase2_columns = [
            ('dialect_msa_analysis', 'TEXT'),
            ('dialect_egy_analysis', 'TEXT'),
            ('dialect_lev_analysis', 'TEXT'),
            ('dialect_glf_analysis', 'TEXT'),
            ('cross_dialect_variants', 'TEXT'),
            ('advanced_morphology', 'TEXT'),
            ('phonetic_transcription', 'TEXT'),
            ('buckwalter_transliteration', 'TEXT'),
            ('semantic_features', 'TEXT'),
            ('named_entity_tags', 'TEXT'),
            ('semantic_relations', 'TEXT'),
            ('usage_frequency', 'INTEGER'),
            ('register_classification', 'TEXT'),
            ('cognates', 'TEXT'),
            ('borrowings', 'TEXT'),
            ('historical_etymology', 'TEXT'),
            ('phase2_enhanced', 'INTEGER'),
            ('phase2_version', 'TEXT'),
            ('phase2_timestamp', 'TEXT'),
            ('phase2_dialect_coverage', 'TEXT')
        ]
        
        # Check existing columns
        cursor.execute('PRAGMA table_info(entries)')
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # Add missing columns
        added_count = 0
        for column_name, column_type in phase2_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f'ALTER TABLE entries ADD COLUMN {column_name} {column_type}')
                    logger.info(f"Added column: {column_name}")
                    added_count += 1
                except sqlite3.Error as e:
                    logger.warning(f"Column {column_name} may already exist: {e}")
        
        conn.commit()
        conn.close()
        logger.info(f"Phase 2 database schema updated - {added_count} columns added")

    def analyze_morphology(self, word: str) -> Dict[str, Any]:
        """Perform morphological analysis if analyzer available"""
        if not self.analyzer:
            return {}
            
        try:
            analyses = self.analyzer.analyze(word)
            if analyses:
                # Take the first (most likely) analysis
                analysis = analyses[0]
                
                return {
                    'lemma': analysis.get('lex', ''),
                    'root': analysis.get('root', ''),
                    'pattern': analysis.get('pattern', ''),
                    'pos': analysis.get('pos', ''),
                    'gender': analysis.get('gen', ''),
                    'number': analysis.get('num', ''),
                    'case': analysis.get('cas', ''),
                    'state': analysis.get('stt', ''),
                    'voice': analysis.get('vox', ''),
                    'mood': analysis.get('mod', ''),
                    'aspect': analysis.get('asp', ''),
                    'person': analysis.get('per', ''),
                    'gloss': analysis.get('gloss', ''),
                    'confidence': 0.8
                }
            else:
                return {'error': 'No analysis found'}
                
        except Exception as e:
            return {'error': str(e)}

    def generate_phonetic_transcription(self, word: str) -> Dict[str, str]:
        """Generate phonetic transcription"""
        transcriptions = {}
        
        # Buckwalter transliteration mapping
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
        
        # Simple phonetic approximation
        ipa_map = {
            'ا': 'aː', 'ب': 'b', 'ت': 't', 'ث': 'θ', 'ج': 'd͡ʒ',
            'ح': 'ħ', 'خ': 'x', 'د': 'd', 'ذ': 'ð', 'ر': 'r',
            'ز': 'z', 'س': 's', 'ش': 'ʃ', 'ص': 'sˤ', 'ض': 'dˤ',
            'ط': 'tˤ', 'ظ': 'ðˤ', 'ع': 'ʕ', 'غ': 'ɣ', 'ف': 'f',
            'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
            'ه': 'h', 'و': 'w', 'ي': 'j', 'ة': 'a', 'ى': 'aː'
        }
        
        ipa = ''.join(ipa_map.get(char, char) for char in word if char in ipa_map)
        transcriptions['ipa_approx'] = ipa
        
        return transcriptions

    def extract_semantic_features(self, word: str, morphology: Dict) -> Dict[str, Any]:
        """Extract semantic features from morphological analysis"""
        features = {
            'semantic_class': '',
            'conceptual_domain': '',
            'abstractness': 0.5,
            'animacy': 'unknown',
            'concreteness': 0.5
        }
        
        # Extract POS-based semantic features
        pos = morphology.get('pos', '')
        
        if pos:
            # Map POS to semantic classes
            pos_semantic_map = {
                'noun': {'semantic_class': 'entity', 'concreteness': 0.7},
                'verb': {'semantic_class': 'action', 'concreteness': 0.3},
                'adj': {'semantic_class': 'property', 'concreteness': 0.4},
                'adv': {'semantic_class': 'modifier', 'concreteness': 0.2}
            }
            
            for pos_key in pos_semantic_map:
                if pos_key in pos.lower():
                    features.update(pos_semantic_map[pos_key])
                    break
        
        return features

    def enhance_entry(self, entry_data: tuple) -> Dict[str, Any]:
        """Enhance a single dictionary entry with Phase 2 features"""
        entry_id, lemma = entry_data[0], entry_data[1]
        
        if not lemma:
            return {}
        
        try:
            # Morphological analysis
            morphology = self.analyze_morphology(lemma)
            
            # Phonetic transcription
            phonetic_data = self.generate_phonetic_transcription(lemma)
            
            # Semantic feature extraction
            semantic_features = self.extract_semantic_features(lemma, morphology)
            
            # Prepare enhancement data
            enhancement_data = {
                'dialect_msa_analysis': json.dumps(morphology, ensure_ascii=False),
                'dialect_egy_analysis': json.dumps({}, ensure_ascii=False),  # Placeholder
                'dialect_lev_analysis': json.dumps({}, ensure_ascii=False),  # Placeholder
                'dialect_glf_analysis': json.dumps({}, ensure_ascii=False),  # Placeholder
                'cross_dialect_variants': json.dumps([], ensure_ascii=False),
                'advanced_morphology': json.dumps(morphology, ensure_ascii=False),
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
                'phase2_version': '2.0.1',
                'phase2_timestamp': datetime.now().isoformat(),
                'phase2_dialect_coverage': 'msa'
            }
            
            # Update statistics
            self.stats['processed'] += 1
            if morphology and 'error' not in morphology:
                self.stats['morphology'] += 1
            if phonetic_data:
                self.stats['phonetic'] += 1
            if semantic_features:
                self.stats['semantic'] += 1
            
            return enhancement_data
            
        except Exception as e:
            logger.error(f"Error enhancing entry {entry_id} ({lemma}): {e}")
            return {}

    def update_entry(self, cursor, entry_id: int, enhancement_data: Dict[str, Any]):
        """Update a single entry with enhancement data"""
        if not enhancement_data:
            return
        
        # Build UPDATE query for main entries table only
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

    def run_enhancement(self, limit: int = 2000):
        """Run the Phase 2 enhancement process"""
        logger.info("STARTING PHASE 2 ENHANCEMENT")
        logger.info("=" * 50)
        
        # Initialize CAMeL Tools
        self.initialize_camel_tools()
        
        # Ensure database schema
        self.ensure_phase2_columns()
        
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get entries to enhance
            cursor.execute("""
                SELECT id, lemma 
                FROM entries 
                WHERE phase2_enhanced IS NULL OR phase2_enhanced = 0
                ORDER BY id 
                LIMIT ?
            """, (limit,))
            
            entries = cursor.fetchall()
            total_entries = len(entries)
            
            logger.info(f"Enhancing {total_entries} entries with Phase 2 features")
            logger.info(f"Morphology analyzer available: {self.analyzer is not None}")
            
            start_time = time.time()
            
            for i, entry in enumerate(entries, 1):
                entry_id, lemma = entry
                
                # Enhance the entry
                enhancement_data = self.enhance_entry(entry)
                
                # Update database
                if enhancement_data:
                    self.update_entry(cursor, entry_id, enhancement_data)
                
                # Progress reporting
                if i % 50 == 0 or i == total_entries:
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    print(f"   Enhanced: {i:,}/{total_entries:,} ({i/total_entries*100:.1f}%) - Rate: {rate:.1f}/sec")
            
            # Commit changes
            conn.commit()
            
            # Final statistics
            elapsed = time.time() - start_time
            logger.info("PHASE 2 ENHANCEMENT COMPLETE!")
            logger.info("STATISTICS:")
            logger.info(f"   Entries processed: {self.stats['processed']}")
            logger.info(f"   Morphological analysis: {self.stats['morphology']}")
            logger.info(f"   Phonetic transcription: {self.stats['phonetic']}")
            logger.info(f"   Semantic features: {self.stats['semantic']}")
            logger.info(f"   Processing time: {elapsed:.1f} seconds")
            logger.info(f"   Average rate: {self.stats['processed']/elapsed:.1f} entries/sec")
            
            return True
            
        except Exception as e:
            logger.error(f"Enhancement failed: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def main():
    print("PHASE 2: ARABIC DICTIONARY ENHANCEMENT")
    print("=" * 45)
    print("Features:")
    print("- Morphological analysis")
    print("- Phonetic transcription (Buckwalter)")
    print("- Semantic feature extraction")
    print("- Database schema enhancement")
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
        print("PHASE 2 ENHANCEMENT RESULTS:")
        print(f"   Entries processed: {enhancer.stats['processed']}")
        print(f"   Morphological analysis: {enhancer.stats['morphology']}")
        print(f"   Phonetic transcription: {enhancer.stats['phonetic']}")
        print(f"   Semantic features: {enhancer.stats['semantic']}")
        print()
        print("ARABIC DICTIONARY ENHANCED!")
        print("Ready for advanced linguistic analysis!")
    else:
        print("Phase 2 enhancement failed. Check logs for details.")

if __name__ == "__main__":
    main()
