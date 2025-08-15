"""
Windows-compatible CAMeL Tools integration for Arabic dictionary enhancement.
Focuses on morphological analysis which is the core feature we need.
"""
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

try:
    from camel_tools.morphology.database import MorphologyDB
    from camel_tools.morphology.analyzer import Analyzer
    from camel_tools.morphology.generator import Generator
    from camel_tools.tokenizers.word import SimpleWordTokenizer
    from camel_tools.utils.normalize import normalize_alef_maksura_ar
    from camel_tools.utils.normalize import normalize_alef_ar
    from camel_tools.utils.normalize import normalize_teh_marbuta_ar
    MORPHOLOGY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"CAMeL Tools morphology not available: {e}")
    MORPHOLOGY_AVAILABLE = False

# Try to import optional components (may not work on Windows)
try:
    from camel_tools.dialectid import DialectIdentifier
    DIALECT_ID_AVAILABLE = True
except ImportError:
    DIALECT_ID_AVAILABLE = False

try:
    from camel_tools.sentiment import SentimentAnalyzer
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False

try:
    from camel_tools.ner import NERecognizer
    NER_AVAILABLE = True
except ImportError:
    NER_AVAILABLE = False

logger = logging.getLogger(__name__)

class WindowsCamelProcessor:
    """Windows-compatible Arabic text processor using CAMeL Tools morphology."""
    
    def __init__(self):
        self.available = MORPHOLOGY_AVAILABLE
        if not self.available:
            logger.warning("CAMeL Tools morphology not available. Advanced features disabled.")
            return
            
        try:
            # Initialize core components that work on Windows
            self._init_morphology()
            self._init_tokenizer()
            
            # Try optional components
            self._init_optional_components()
            
            logger.info("CAMeL Tools initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CAMeL Tools: {e}")
            self.available = False
    
    def _init_morphology(self):
        """Initialize morphological analyzer and generator."""
        try:
            # Download and use CALIMA MSA database for morphological analysis
            logger.info("Initializing morphology database...")
            self.morph_db = MorphologyDB.builtin_db(db_name='calima-msa-r13')
            self.analyzer = Analyzer(self.morph_db)
            self.generator = Generator(self.morph_db)
            logger.info("Morphological analyzer initialized successfully")
        except Exception as e:
            logger.warning(f"Morphology initialization failed: {e}")
            self.morph_db = None
            self.analyzer = None
            self.generator = None
            self.available = False
    
    def _init_tokenizer(self):
        """Initialize word tokenizer."""
        try:
            self.tokenizer = SimpleWordTokenizer()
            logger.info("Tokenizer initialized")
        except Exception as e:
            logger.warning(f"Tokenizer initialization failed: {e}")
            self.tokenizer = None
    
    def _init_optional_components(self):
        """Initialize optional components that may not work on Windows."""
        # Dialect identification
        if DIALECT_ID_AVAILABLE:
            try:
                self.dialect_id = DialectIdentifier.pretrained()
                logger.info("Dialect identifier initialized")
            except Exception as e:
                logger.warning(f"Dialect ID initialization failed: {e}")
                self.dialect_id = None
        else:
            self.dialect_id = None
        
        # Sentiment analysis
        if SENTIMENT_AVAILABLE:
            try:
                self.sentiment = SentimentAnalyzer.pretrained()
                logger.info("Sentiment analyzer initialized")
            except Exception as e:
                logger.warning(f"Sentiment analyzer initialization failed: {e}")
                self.sentiment = None
        else:
            self.sentiment = None
        
        # Named Entity Recognition
        if NER_AVAILABLE:
            try:
                self.ner = NERecognizer.pretrained()
                logger.info("NER initialized")
            except Exception as e:
                logger.warning(f"NER initialization failed: {e}")
                self.ner = None
        else:
            self.ner = None
    
    def analyze_word(self, word: str) -> Dict[str, Any]:
        """
        Comprehensive analysis of an Arabic word using CAMeL Tools.
        
        Args:
            word: Arabic word to analyze
            
        Returns:
            Dictionary with morphological analysis and available features
        """
        if not self.available:
            return {"error": "CAMeL Tools not available"}
        
        # Normalize the word
        normalized = self.normalize_text(word)
        
        result = {
            "original": word,
            "normalized": normalized,
            "morphology": [],
            "dialect": None,
            "sentiment": None,
            "entities": [],
            "possible_lemmas": [],
            "roots": [],
            "patterns": [],
            "pos_tags": []
        }
        
        # Morphological analysis (core feature)
        if self.analyzer:
            try:
                analyses = self.analyzer.analyze(normalized)
                for analysis in analyses:
                    morph_data = {
                        "lemma": analysis.get('lex', ''),
                        "root": analysis.get('root', ''),
                        "pattern": analysis.get('pattern', ''),
                        "pos": analysis.get('pos', ''),
                        "gender": analysis.get('gen', ''),
                        "number": analysis.get('num', ''),
                        "person": analysis.get('per', ''),
                        "aspect": analysis.get('asp', ''),
                        "mood": analysis.get('mod', ''),
                        "voice": analysis.get('vox', ''),
                        "case": analysis.get('cas', ''),
                        "state": analysis.get('stt', ''),
                        "gloss": analysis.get('gloss', ''),
                        "source": "calima-msa-r13"
                    }
                    result["morphology"].append(morph_data)
                    
                    # Collect unique values
                    if morph_data["lemma"] and morph_data["lemma"] not in result["possible_lemmas"]:
                        result["possible_lemmas"].append(morph_data["lemma"])
                    if morph_data["root"] and morph_data["root"] not in result["roots"]:
                        result["roots"].append(morph_data["root"])
                    if morph_data["pattern"] and morph_data["pattern"] not in result["patterns"]:
                        result["patterns"].append(morph_data["pattern"])
                    if morph_data["pos"] and morph_data["pos"] not in result["pos_tags"]:
                        result["pos_tags"].append(morph_data["pos"])
                        
            except Exception as e:
                logger.warning(f"Morphological analysis failed for '{word}': {e}")
        
        # Optional features (may not work on Windows)
        try:
            if self.dialect_id:
                dialect_scores = self.dialect_id.predict([normalized])
                if dialect_scores:
                    result["dialect"] = {
                        "top_dialect": dialect_scores[0].top,
                        "scores": dict(dialect_scores[0].scores)
                    }
        except Exception as e:
            logger.debug(f"Dialect identification failed for '{word}': {e}")
        
        try:
            if self.sentiment:
                sentiment_result = self.sentiment.predict([normalized])
                if sentiment_result:
                    result["sentiment"] = {
                        "label": sentiment_result[0].top,
                        "scores": dict(sentiment_result[0].scores)
                    }
        except Exception as e:
            logger.debug(f"Sentiment analysis failed for '{word}': {e}")
        
        try:
            if self.ner and self.tokenizer:
                tokens = [normalized] if self.tokenizer is None else self.tokenizer.tokenize(normalized)
                entities = self.ner.predict(tokens)
                result["entities"] = [{"text": ent.text, "label": ent.label} for ent in entities]
        except Exception as e:
            logger.debug(f"NER failed for '{word}': {e}")
        
        return result
    
    def generate_forms(self, lemma: str, target_features: Dict[str, str]) -> List[str]:
        """Generate word forms from a lemma with specified features."""
        if not self.available or not self.generator:
            return []
        
        try:
            generated = self.generator.generate(lemma, target_features)
            return [form['diac'] for form in generated if 'diac' in form]
        except Exception as e:
            logger.warning(f"Generation failed for '{lemma}': {e}")
            return []
    
    def get_all_lemmas(self, word: str) -> List[str]:
        """Extract all possible lemmas for a word."""
        analysis = self.analyze_word(word)
        return analysis.get("possible_lemmas", [])
    
    def get_best_lemma(self, word: str) -> Optional[str]:
        """Get the most likely lemma for a word."""
        lemmas = self.get_all_lemmas(word)
        return lemmas[0] if lemmas else None
    
    def get_roots(self, word: str) -> List[str]:
        """Extract all possible roots for a word."""
        analysis = self.analyze_word(word)
        return analysis.get("roots", [])
    
    def get_best_root(self, word: str) -> Optional[str]:
        """Get the most likely root for a word."""
        roots = self.get_roots(word)
        return roots[0] if roots else None
    
    def get_pos_tags(self, word: str) -> List[str]:
        """Get all possible POS tags for a word."""
        analysis = self.analyze_word(word)
        return analysis.get("pos_tags", [])
    
    def get_best_pos(self, word: str) -> Optional[str]:
        """Get the most likely POS tag for a word."""
        pos_tags = self.get_pos_tags(word)
        return pos_tags[0] if pos_tags else None
    
    def normalize_text(self, text: str) -> str:
        """Normalize Arabic text using CAMeL Tools normalization."""
        if not self.available:
            return text
        
        try:
            # Apply CAMeL Tools normalizations
            normalized = normalize_alef_ar(text)
            normalized = normalize_alef_maksura_ar(normalized)
            normalized = normalize_teh_marbuta_ar(normalized)
            return normalized
        except Exception as e:
            logger.warning(f"Normalization failed: {e}")
            return text
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Return information about available capabilities."""
        return {
            "morphology": self.available and self.analyzer is not None,
            "generation": self.available and self.generator is not None,
            "normalization": self.available,
            "tokenization": self.tokenizer is not None,
            "dialect_id": self.dialect_id is not None,
            "sentiment": self.sentiment is not None,
            "ner": self.ner is not None
        }

# Global instance
camel_processor = WindowsCamelProcessor()

def enhance_dictionary_entry(word: str, existing_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Enhance a dictionary entry with CAMeL Tools analysis.
    
    Args:
        word: Arabic word to enhance
        existing_data: Existing dictionary data to merge with
        
    Returns:
        Enhanced dictionary entry
    """
    if existing_data is None:
        existing_data = {}
    
    # Get CAMeL analysis
    camel_analysis = camel_processor.analyze_word(word)
    
    # Merge with existing data, prioritizing CAMeL results where they exist
    enhanced = existing_data.copy()
    
    # Update lemma if CAMeL provides better one
    if camel_analysis.get("possible_lemmas"):
        enhanced["lemma"] = camel_analysis["possible_lemmas"][0]
        enhanced["alternative_lemmas"] = camel_analysis["possible_lemmas"][1:]
    
    # Update root if CAMeL provides one
    if camel_analysis.get("roots"):
        enhanced["root"] = camel_analysis["roots"][0]
        enhanced["alternative_roots"] = camel_analysis["roots"][1:]
    
    # Update POS if CAMeL provides one
    if camel_analysis.get("pos_tags"):
        enhanced["pos"] = camel_analysis["pos_tags"][0]
        enhanced["alternative_pos"] = camel_analysis["pos_tags"][1:]
    
    # Add morphological details
    if camel_analysis.get("morphology"):
        enhanced["morphology"] = camel_analysis["morphology"]
    
    # Add patterns
    if camel_analysis.get("patterns"):
        enhanced["patterns"] = camel_analysis["patterns"]
    
    # Add dialect information if available
    if camel_analysis.get("dialect"):
        enhanced["dialect"] = camel_analysis["dialect"]
    
    # Add sentiment if available
    if camel_analysis.get("sentiment"):
        enhanced["sentiment"] = camel_analysis["sentiment"]
    
    # Add entities if available
    if camel_analysis.get("entities"):
        enhanced["entities"] = camel_analysis["entities"]
    
    # Add normalized form
    enhanced["normalized"] = camel_analysis.get("normalized", word)
    
    return enhanced

if __name__ == "__main__":
    # Test the processor
    print("=== CAMeL Tools Capabilities ===")
    capabilities = camel_processor.get_capabilities()
    for feature, available in capabilities.items():
        status = "✓" if available else "✗"
        print(f"{status} {feature}")
    
    if camel_processor.available:
        print("\n=== Testing with Arabic words ===")
        test_words = ["كتاب", "يكتب", "مكتبة", "الكتاب", "كاتب"]
        
        for word in test_words:
            print(f"\n--- Analysis for: {word} ---")
            analysis = camel_processor.analyze_word(word)
            print(f"Lemmas: {analysis.get('possible_lemmas', [])}")
            print(f"Roots: {analysis.get('roots', [])}")
            print(f"POS: {analysis.get('pos_tags', [])}")
            print(f"Patterns: {analysis.get('patterns', [])}")
            print(f"Morphological analyses: {len(analysis.get('morphology', []))}")
    else:
        print("\nCAMeL Tools not available for testing.")
