"""
Robust CAMeL Tools integration for Arabic dictionary enhancement.
Handles Windows compatibility issues gracefully.
"""
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import core components with fallbacks
try:
    from camel_tools.morphology.database import MorphologyDB
    from camel_tools.morphology.analyzer import Analyzer
    from camel_tools.morphology.generator import Generator
    MORPHOLOGY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CAMeL Tools morphology not available: {e}")
    MORPHOLOGY_AVAILABLE = False

# Try normalization functions
try:
    from camel_tools.utils.normalize import normalize_alef_maksura_ar
    from camel_tools.utils.normalize import normalize_alef_ar
    from camel_tools.utils.normalize import normalize_teh_marbuta_ar
    NORMALIZATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CAMeL Tools normalization not available: {e}")
    NORMALIZATION_AVAILABLE = False

# Try tokenizer with fallback
try:
    from camel_tools.tokenizers.word import SimpleWordTokenizer
    TOKENIZER_AVAILABLE = True
except ImportError:
    try:
        # Try alternative import path
        from camel_tools.tokenizers import SimpleWordTokenizer
        TOKENIZER_AVAILABLE = True
    except ImportError:
        TOKENIZER_AVAILABLE = False

class RobustCamelProcessor:
    """Robust Arabic text processor with graceful fallbacks."""
    
    def __init__(self):
        self.available = False
        self.analyzer = None
        self.generator = None
        self.tokenizer = None
        
        # Initialize what we can
        self._init_morphology()
        self._init_tokenizer()
        
        # Set availability based on core morphology
        self.available = self.analyzer is not None
        
        if self.available:
            logger.info("CAMeL Tools morphology initialized successfully")
        else:
            logger.warning("CAMeL Tools morphology not available")
    
    def _init_morphology(self):
        """Initialize morphological analyzer and generator."""
        if not MORPHOLOGY_AVAILABLE:
            return
            
        try:
            # Try to initialize the morphology database
            logger.info("Initializing CAMeL morphology database...")
            self.morph_db = MorphologyDB.builtin_db(db_name='calima-msa-r13')
            self.analyzer = Analyzer(self.morph_db)
            self.generator = Generator(self.morph_db)
            logger.info("Morphological analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Morphology initialization failed: {e}")
            logger.info("Trying to download morphology database...")
            try:
                # Try downloading the database first
                import camel_tools
                camel_tools.data.download('morphology')
                # Try again after download
                self.morph_db = MorphologyDB.builtin_db(db_name='calima-msa-r13')
                self.analyzer = Analyzer(self.morph_db)
                self.generator = Generator(self.morph_db)
                logger.info("Morphological analyzer initialized after download")
            except Exception as e2:
                logger.error(f"Failed to download or initialize morphology: {e2}")
                self.morph_db = None
                self.analyzer = None
                self.generator = None
    
    def _init_tokenizer(self):
        """Initialize word tokenizer with fallback."""
        if not TOKENIZER_AVAILABLE:
            return
            
        try:
            self.tokenizer = SimpleWordTokenizer()
            logger.info("Tokenizer initialized")
        except Exception as e:
            logger.warning(f"Tokenizer initialization failed: {e}")
            self.tokenizer = None
    
    def simple_tokenize(self, text: str) -> List[str]:
        """Simple fallback tokenizer."""
        if self.tokenizer:
            try:
                return self.tokenizer.tokenize(text)
            except:
                pass
        # Fallback to simple split
        return text.split()
    
    def analyze_word(self, word: str) -> Dict[str, Any]:
        """
        Analyze an Arabic word using available CAMeL Tools components.
        
        Args:
            word: Arabic word to analyze
            
        Returns:
            Dictionary with analysis results
        """
        # Normalize the word
        normalized = self.normalize_text(word)
        
        result = {
            "original": word,
            "normalized": normalized,
            "morphology": [],
            "possible_lemmas": [],
            "roots": [],
            "patterns": [],
            "pos_tags": [],
            "available": self.available
        }
        
        if not self.available or not self.analyzer:
            result["error"] = "Morphological analyzer not available"
            return result
        
        # Morphological analysis
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
            result["error"] = f"Analysis failed: {str(e)}"
        
        return result
    
    def generate_forms(self, lemma: str, target_features: Dict[str, str]) -> List[str]:
        """Generate word forms from a lemma with specified features."""
        if not self.available or not self.generator:
            return []
        
        try:
            generated = self.generator.generate(lemma, target_features)
            return [form.get('diac', form.get('form', '')) for form in generated]
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
        """Normalize Arabic text using available normalization functions."""
        if not NORMALIZATION_AVAILABLE:
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
            "morphology": self.analyzer is not None,
            "generation": self.generator is not None,
            "normalization": NORMALIZATION_AVAILABLE,
            "tokenization": self.tokenizer is not None
        }

# Global instance
camel_processor = RobustCamelProcessor()

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
    
    print(f"\nOverall availability: {'✓' if camel_processor.available else '✗'}")
    
    if camel_processor.available:
        print("\n=== Testing with Arabic words ===")
        test_words = ["كتاب", "يكتب", "مكتبة", "الكتاب", "كاتب"]
        
        for word in test_words:
            print(f"\n--- Analysis for: {word} ---")
            analysis = camel_processor.analyze_word(word)
            print(f"Normalized: {analysis.get('normalized', 'N/A')}")
            print(f"Lemmas: {analysis.get('possible_lemmas', [])}")
            print(f"Roots: {analysis.get('roots', [])}")
            print(f"POS: {analysis.get('pos_tags', [])}")
            print(f"Patterns: {analysis.get('patterns', [])}")
            print(f"Morphological analyses: {len(analysis.get('morphology', []))}")
            
            if analysis.get('error'):
                print(f"Error: {analysis['error']}")
    else:
        print("\nCAMeL Tools not available for testing.")
        print("You may need to install additional data files.")
        print("Try running: python -m camel_tools.data download all")
