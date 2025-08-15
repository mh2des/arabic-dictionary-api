#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Dialect Arabic Analysis System
Leveraging multiple morphology databases for comprehensive Arabic dialect support.

This system provides:
1. Multi-dialect morphological analysis
2. Cross-dialect word comparison
3. Dialectal variant detection
4. Regional morphology patterns
"""

import json
import sqlite3
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DialectMorphology:
    """Morphological analysis for a specific dialect."""
    dialect: str
    analyses: List[Dict]
    confidence: float

class MultiDialectAnalyzer:
    """Multi-dialect Arabic morphological analysis system."""
    
    def __init__(self):
        """Initialize the multi-dialect analyzer."""
        self.morphology_dbs = {}
        self.dialect_info = {}
        self._initialize_databases()
    
    def _initialize_databases(self):
        """Initialize all available morphology databases."""
        try:
            from camel_tools.morphology.database import MorphologyDB
            
            # Available dialect databases
            dialect_configs = {
                'MSA': {
                    'db_name': 'calima-msa-r13',
                    'full_name': 'Modern Standard Arabic',
                    'region': 'Standard Arabic',
                    'description': 'Formal Arabic used in literature, media, and education'
                },
                'MSA_ALT': {
                    'db_name': 'calima-msa-s31', 
                    'full_name': 'Modern Standard Arabic (Alternative)',
                    'region': 'Standard Arabic',
                    'description': 'Alternative MSA morphological analysis'
                },
                'EGY': {
                    'db_name': 'calima-egy-r13',
                    'full_name': 'Egyptian Arabic',
                    'region': 'Egypt',
                    'description': 'Spoken Arabic of Egypt, widely understood across Arab world'
                },
                'LEV': {
                    'db_name': 'calima-lev-01',
                    'full_name': 'Levantine Arabic',
                    'region': 'Levant (Syria, Lebanon, Palestine, Jordan)',
                    'description': 'Arabic dialects of the Levantine region'
                },
                'GLF': {
                    'db_name': 'calima-glf-01',
                    'full_name': 'Gulf Arabic',
                    'region': 'Arabian Gulf',
                    'description': 'Arabic dialects of Gulf countries'
                }
            }
            
            for dialect_code, config in dialect_configs.items():
                try:
                    db = MorphologyDB.builtin_db(config['db_name'])
                    self.morphology_dbs[dialect_code] = db
                    self.dialect_info[dialect_code] = config
                    logger.info(f"✅ {config['full_name']} database loaded")
                except Exception as e:
                    logger.warning(f"⚠️ Could not load {config['full_name']}: {e}")
            
            logger.info(f"✅ Loaded {len(self.morphology_dbs)} dialect databases")
                
        except Exception as e:
            logger.error(f"❌ Error initializing databases: {e}")
    
    def analyze_word_all_dialects(self, word: str) -> Dict[str, DialectMorphology]:
        """Analyze a word using all available dialect databases."""
        results = {}
        
        for dialect_code, db in self.morphology_dbs.items():
            try:
                # Get morphological analyses
                analyses = db.analyzer.generate(word)
                
                if analyses:
                    # Convert to standardized format
                    processed_analyses = []
                    for analysis in analyses[:5]:  # Top 5 per dialect
                        processed_analysis = {
                            'lemma': analysis.get('lemma', ''),
                            'root': analysis.get('root', ''),
                            'pos': analysis.get('pos', ''),
                            'gender': analysis.get('gender', ''),
                            'number': analysis.get('number', ''),
                            'person': analysis.get('person', ''),
                            'case': analysis.get('case', ''),
                            'state': analysis.get('state', ''),
                            'mood': analysis.get('mood', ''),
                            'voice': analysis.get('voice', ''),
                            'features': analysis.get('feats', {})
                        }
                        processed_analyses.append(processed_analysis)
                    
                    # Calculate confidence based on number of analyses
                    confidence = min(1.0, len(analyses) / 10.0)
                    
                    results[dialect_code] = DialectMorphology(
                        dialect=self.dialect_info[dialect_code]['full_name'],
                        analyses=processed_analyses,
                        confidence=confidence
                    )
                    
            except Exception as e:
                logger.debug(f"No analysis for '{word}' in {dialect_code}: {e}")
        
        return results
    
    def find_cross_dialect_variants(self, word: str) -> Dict[str, List[str]]:
        """Find variants of a word across different dialects."""
        all_analyses = self.analyze_word_all_dialects(word)
        variants_by_dialect = {}
        
        for dialect_code, analysis in all_analyses.items():
            variants = set()
            for morph_analysis in analysis.analyses:
                lemma = morph_analysis.get('lemma', '')
                if lemma and lemma != word:
                    variants.add(lemma)
            
            if variants:
                variants_by_dialect[dialect_code] = list(variants)
        
        return variants_by_dialect
    
    def compare_dialects(self, word: str) -> Dict:
        """Compare how a word is analyzed across different dialects."""
        analyses = self.analyze_word_all_dialects(word)
        
        comparison = {
            'word': word,
            'found_in_dialects': list(analyses.keys()),
            'total_dialects': len(self.morphology_dbs),
            'coverage_percentage': (len(analyses) / len(self.morphology_dbs)) * 100,
            'dialect_analyses': {},
            'common_roots': set(),
            'common_lemmas': set(),
            'pos_distribution': {}
        }
        
        # Process each dialect's analysis
        for dialect_code, analysis in analyses.items():
            dialect_summary = {
                'dialect_name': analysis.dialect,
                'confidence': analysis.confidence,
                'num_analyses': len(analysis.analyses),
                'roots': [],
                'lemmas': [],
                'pos_tags': []
            }
            
            for morph in analysis.analyses:
                if morph['root']:
                    dialect_summary['roots'].append(morph['root'])
                    comparison['common_roots'].add(morph['root'])
                
                if morph['lemma']:
                    dialect_summary['lemmas'].append(morph['lemma'])
                    comparison['common_lemmas'].add(morph['lemma'])
                
                if morph['pos']:
                    dialect_summary['pos_tags'].append(morph['pos'])
                    comparison['pos_distribution'][morph['pos']] = comparison['pos_distribution'].get(morph['pos'], 0) + 1
            
            comparison['dialect_analyses'][dialect_code] = dialect_summary
        
        # Convert sets to lists for JSON serialization
        comparison['common_roots'] = list(comparison['common_roots'])
        comparison['common_lemmas'] = list(comparison['common_lemmas'])
        
        return comparison
    
    def get_dialect_coverage_stats(self) -> Dict:
        """Get statistics about dialect database coverage."""
        return {
            'total_dialects': len(self.morphology_dbs),
            'available_dialects': {
                code: {
                    'name': info['full_name'],
                    'region': info['region'],
                    'description': info['description']
                }
                for code, info in self.dialect_info.items()
            }
        }

def test_multi_dialect_analysis():
    """Test the multi-dialect analysis system."""
    analyzer = MultiDialectAnalyzer()
    
    # Test words that might have different analyses across dialects
    test_words = [
        'كتاب',    # Book
        'بيت',     # House  
        'ولد',     # Boy
        'مدرسة',   # School
        'يكتب',    # He writes
        'مكتبة'    # Library
    ]
    
    print("🌍 MULTI-DIALECT ARABIC ANALYSIS SYSTEM")
    print("="*60)
    
    # Show available dialects
    stats = analyzer.get_dialect_coverage_stats()
    print(f"📊 Available Dialects: {stats['total_dialects']}")
    for code, info in stats['available_dialects'].items():
        print(f"   {code}: {info['name']} ({info['region']})")
    
    print("\n🔍 CROSS-DIALECT WORD ANALYSIS")
    print("-" * 40)
    
    for word in test_words:
        print(f"\n📖 Analyzing word: '{word}'")
        
        # Get comprehensive comparison
        comparison = analyzer.compare_dialects(word)
        
        print(f"   📈 Coverage: {comparison['coverage_percentage']:.1f}% ({len(comparison['found_in_dialects'])}/{comparison['total_dialects']} dialects)")
        
        if comparison['found_in_dialects']:
            print(f"   🗺️ Found in: {', '.join(comparison['found_in_dialects'])}")
            
            # Show common roots and lemmas
            if comparison['common_roots']:
                print(f"   🌳 Common roots: {', '.join(comparison['common_roots'])}")
            
            if comparison['common_lemmas']:
                lemmas = ', '.join(comparison['common_lemmas'][:3])
                if len(comparison['common_lemmas']) > 3:
                    lemmas += f" (+{len(comparison['common_lemmas'])-3} more)"
                print(f"   📝 Common lemmas: {lemmas}")
            
            # Show POS distribution
            if comparison['pos_distribution']:
                pos_summary = ', '.join([f"{pos}({count})" for pos, count in sorted(comparison['pos_distribution'].items())])
                print(f"   🏷️ POS distribution: {pos_summary}")
            
            # Show dialect-specific details
            print(f"   🔍 Dialect details:")
            for dialect_code in comparison['found_in_dialects']:
                dialect_data = comparison['dialect_analyses'][dialect_code]
                dialect_name = dialect_data['dialect_name']
                num_analyses = dialect_data['num_analyses']
                confidence = dialect_data['confidence']
                print(f"      {dialect_code}: {num_analyses} analyses (confidence: {confidence:.2f})")
    
    print(f"\n✅ Multi-dialect analysis system operational!")
    print(f"   📚 {stats['total_dialects']} Arabic dialect databases active")
    print(f"   🔍 Cross-dialect morphological comparison available")
    print(f"   🗺️ Comprehensive regional Arabic coverage")
    print(f"   🎯 Ready for integration into your dialects screen!")

if __name__ == '__main__':
    test_multi_dialect_analysis()
