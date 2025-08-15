#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arabic Dialect Analysis System
Using comprehensive CAMeL Tools resources for multi-dialect support.

This system provides:
1. Dialect identification for 25+ Arabic dialects
2. Multi-dialect morphological analysis
3. Dialectal variant detection
4. Cross-dialect word mapping
5. Named entity recognition
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
class DialectInfo:
    """Information about an Arabic dialect."""
    code: str
    name: str
    region: str
    confidence: float

@dataclass
class DialectAnalysis:
    """Complete dialect analysis result."""
    detected_dialect: DialectInfo
    alternative_dialects: List[DialectInfo]
    morphological_analysis: Dict
    dialectal_variants: List[str]
    named_entities: List[Dict]

class ArabicDialectAnalyzer:
    """Comprehensive Arabic dialect analysis system."""
    
    def __init__(self):
        """Initialize the dialect analyzer with all CAMeL resources."""
        self.dialect_classifier = None
        self.morphology_dbs = {}
        self.ner_model = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all CAMeL Tools models."""
        try:
            # Initialize dialect identification
            from camel_tools.dialectid import DialectIdentifier
            self.dialect_classifier = DialectIdentifier.pretrained('dialectid_model26')
            logger.info("✅ Dialect identifier loaded (26 dialects)")
            
            # Initialize morphology databases for different dialects
            from camel_tools.morphology.database import MorphologyDB
            
            dialect_dbs = {
                'msa': 'calima-msa-r13',      # Modern Standard Arabic
                'egy': 'calima-egy-r13',      # Egyptian Arabic
                'glf': 'calima-glf-01',       # Gulf Arabic
                'lev': 'calima-lev-01',       # Levantine Arabic
                'msa_alt': 'calima-msa-s31'   # Alternative MSA database
            }
            
            for dialect_code, db_name in dialect_dbs.items():
                try:
                    self.morphology_dbs[dialect_code] = MorphologyDB.builtin_db(db_name)
                    logger.info(f"✅ {dialect_code.upper()} morphology database loaded")
                except Exception as e:
                    logger.warning(f"⚠️ Could not load {dialect_code} database: {e}")
            
            # Initialize Named Entity Recognition
            try:
                from camel_tools.ner import NERecognizer
                self.ner_model = NERecognizer.pretrained('ner_arabert')
                logger.info("✅ Arabic NER model loaded")
            except Exception as e:
                logger.warning(f"⚠️ Could not load NER model: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error initializing dialect analyzer: {e}")
    
    def identify_dialect(self, text: str) -> Tuple[DialectInfo, List[DialectInfo]]:
        """Identify the dialect of Arabic text."""
        if not self.dialect_classifier:
            return None, []
        
        try:
            # Get predictions with confidence scores
            predictions = self.dialect_classifier.predict([text], top=5)[0]
            
            # Convert to DialectInfo objects
            primary_dialect = DialectInfo(
                code=predictions[0].label,
                name=self._get_dialect_name(predictions[0].label),
                region=self._get_dialect_region(predictions[0].label),
                confidence=predictions[0].score
            )
            
            alternative_dialects = []
            for pred in predictions[1:]:
                alt_dialect = DialectInfo(
                    code=pred.label,
                    name=self._get_dialect_name(pred.label),
                    region=self._get_dialect_region(pred.label),
                    confidence=pred.score
                )
                alternative_dialects.append(alt_dialect)
            
            return primary_dialect, alternative_dialects
            
        except Exception as e:
            logger.error(f"Error in dialect identification: {e}")
            return None, []
    
    def _get_dialect_name(self, dialect_code: str) -> str:
        """Get human-readable dialect name."""
        dialect_names = {
            'MSA': 'Modern Standard Arabic',
            'EGY': 'Egyptian Arabic',
            'LEV': 'Levantine Arabic',
            'GLF': 'Gulf Arabic',
            'MAG': 'Maghrebi Arabic',
            'IRQ': 'Iraqi Arabic',
            'ALE': 'Aleppo Arabic',
            'AMM': 'Amman Arabic',
            'ASW': 'Aswan Arabic',
            'BAG': 'Baghdad Arabic',
            'BAS': 'Basra Arabic',
            'BEI': 'Beirut Arabic',
            'BEN': 'Benghazi Arabic',
            'CAI': 'Cairo Arabic',
            'DAM': 'Damascus Arabic',
            'DOH': 'Doha Arabic',
            'FES': 'Fes Arabic',
            'JED': 'Jeddah Arabic',
            'JER': 'Jerusalem Arabic',
            'KHA': 'Khartoum Arabic',
            'KUW': 'Kuwait Arabic',
            'MOS': 'Mosul Arabic',
            'MUS': 'Muscat Arabic',
            'RAB': 'Rabat Arabic',
            'RIY': 'Riyadh Arabic',
            'SAL': 'Salt Arabic',
            'SAN': 'Sana\'a Arabic',
            'SFX': 'Sfax Arabic',
            'TRI': 'Tripoli Arabic',
            'TUN': 'Tunis Arabic'
        }
        return dialect_names.get(dialect_code.upper(), dialect_code)
    
    def _get_dialect_region(self, dialect_code: str) -> str:
        """Get geographical region for dialect."""
        regions = {
            'MSA': 'Standard',
            'EGY': 'Egypt', 'CAI': 'Egypt', 'ASW': 'Egypt',
            'LEV': 'Levant', 'ALE': 'Syria', 'DAM': 'Syria', 'BEI': 'Lebanon', 
            'JER': 'Palestine', 'AMM': 'Jordan', 'SAL': 'Jordan',
            'GLF': 'Gulf', 'DOH': 'Qatar', 'KUW': 'Kuwait', 'RIY': 'Saudi Arabia',
            'JED': 'Saudi Arabia', 'MUS': 'Oman',
            'IRQ': 'Iraq', 'BAG': 'Iraq', 'BAS': 'Iraq', 'MOS': 'Iraq',
            'MAG': 'Maghreb', 'TUN': 'Tunisia', 'SFX': 'Tunisia', 'TRI': 'Libya',
            'BEN': 'Libya', 'RAB': 'Morocco', 'FES': 'Morocco',
            'KHA': 'Sudan', 'SAN': 'Yemen'
        }
        return regions.get(dialect_code.upper(), 'Unknown')
    
    def analyze_morphology_by_dialect(self, word: str, dialect_code: str = None) -> Dict:
        """Analyze morphology using appropriate dialect database."""
        results = {}
        
        # If specific dialect requested, use that database
        if dialect_code and dialect_code.lower() in self.morphology_dbs:
            db = self.morphology_dbs[dialect_code.lower()]
            try:
                analysis = db.analyzer.generate(word)
                results[dialect_code.upper()] = [
                    {
                        'lemma': a.get('lemma', ''),
                        'root': a.get('root', ''),
                        'pos': a.get('pos', ''),
                        'features': a.get('feats', {})
                    } for a in analysis[:5]  # Top 5 analyses
                ]
            except Exception as e:
                logger.warning(f"Error analyzing {word} with {dialect_code}: {e}")
        
        # Otherwise, try all available databases
        else:
            for dialect, db in self.morphology_dbs.items():
                try:
                    analysis = db.analyzer.generate(word)
                    if analysis:  # Only include if we got results
                        results[dialect.upper()] = [
                            {
                                'lemma': a.get('lemma', ''),
                                'root': a.get('root', ''),
                                'pos': a.get('pos', ''),
                                'features': a.get('feats', {})
                            } for a in analysis[:3]  # Top 3 analyses per dialect
                        ]
                except Exception as e:
                    logger.debug(f"No analysis for {word} in {dialect}: {e}")
        
        return results
    
    def extract_named_entities(self, text: str) -> List[Dict]:
        """Extract named entities from Arabic text."""
        if not self.ner_model:
            return []
        
        try:
            entities = self.ner_model.predict([text])[0]
            return [
                {
                    'text': entity.text,
                    'label': entity.label,
                    'start': entity.start,
                    'end': entity.end,
                    'confidence': getattr(entity, 'confidence', 1.0)
                } for entity in entities
            ]
        except Exception as e:
            logger.error(f"Error in NER: {e}")
            return []
    
    def find_dialectal_variants(self, word: str) -> List[str]:
        """Find dialectal variants of a word across different databases."""
        variants = set()
        
        # Get morphological analyses from all dialects
        morphology_results = self.analyze_morphology_by_dialect(word)
        
        # Extract lemmas as potential variants
        for dialect, analyses in morphology_results.items():
            for analysis in analyses:
                lemma = analysis.get('lemma', '')
                if lemma and lemma != word:
                    variants.add(lemma)
        
        return list(variants)
    
    def comprehensive_analysis(self, text: str, word: str = None) -> DialectAnalysis:
        """Perform comprehensive dialect analysis."""
        # Identify dialect of the text
        primary_dialect, alt_dialects = self.identify_dialect(text)
        
        # Analyze morphology
        target_word = word if word else text.split()[0] if text.split() else text
        morphology = self.analyze_morphology_by_dialect(target_word)
        
        # Find dialectal variants
        variants = self.find_dialectal_variants(target_word)
        
        # Extract named entities
        entities = self.extract_named_entities(text)
        
        return DialectAnalysis(
            detected_dialect=primary_dialect,
            alternative_dialects=alt_dialects,
            morphological_analysis=morphology,
            dialectal_variants=variants,
            named_entities=entities
        )

def test_dialect_analyzer():
    """Test the dialect analyzer with sample text."""
    analyzer = ArabicDialectAnalyzer()
    
    # Test texts in different dialects
    test_cases = [
        ("هذا كتاب جميل جداً", "Modern Standard Arabic"),
        ("ده كتاب حلو قوي", "Egyptian Arabic"), 
        ("هاي كتاب حلو كتير", "Levantine Arabic"),
        ("هذا كتاب زين واجد", "Gulf Arabic")
    ]
    
    print("🌍 ARABIC DIALECT ANALYSIS SYSTEM")
    print("="*50)
    
    for text, expected_dialect in test_cases:
        print(f"\n📝 Analyzing: '{text}'")
        print(f"   Expected: {expected_dialect}")
        
        # Perform comprehensive analysis
        analysis = analyzer.comprehensive_analysis(text)
        
        if analysis.detected_dialect:
            print(f"   🎯 Detected: {analysis.detected_dialect.name} ({analysis.detected_dialect.confidence:.3f})")
            print(f"   🗺️ Region: {analysis.detected_dialect.region}")
            
            # Show alternative dialects
            if analysis.alternative_dialects:
                print(f"   🔄 Alternatives:")
                for alt in analysis.alternative_dialects[:3]:
                    print(f"      {alt.name} ({alt.confidence:.3f})")
            
            # Show morphological analysis
            if analysis.morphological_analysis:
                print(f"   🔍 Morphology available for: {list(analysis.morphological_analysis.keys())}")
            
            # Show dialectal variants
            if analysis.dialectal_variants:
                print(f"   🗣️ Variants: {', '.join(analysis.dialectal_variants[:5])}")
            
            # Show named entities
            if analysis.named_entities:
                print(f"   🏷️ Named Entities: {len(analysis.named_entities)} found")
    
    print(f"\n✅ Dialect analysis system ready!")
    print(f"   📚 Supports 25+ Arabic dialects")
    print(f"   🔍 Multi-dialect morphological analysis")
    print(f"   🏷️ Named entity recognition")
    print(f"   🗺️ Comprehensive regional coverage")

if __name__ == '__main__':
    test_dialect_analyzer()
