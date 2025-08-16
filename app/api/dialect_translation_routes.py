"""
Dialect Translation API Endpoints
Ammiya (Colloquial) <-> Fusha (MSA) translation with synonyms
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any
from ..services.dialect_mapper import ArabicDialectMapper
import os

router = APIRouter(prefix="/dialect/translate", tags=["Dialect Translation"])

# Initialize dialect mapper
db_path = os.path.join(os.path.dirname(__file__), "..", "arabic_dict.db")
dialect_mapper = ArabicDialectMapper(db_path)

@router.get("/ammiya-to-fusha/{word}")
async def translate_ammiya_to_fusha(word: str) -> Dict[str, Any]:
    """
    Translate Ammiya (dialect) word to Fusha (MSA) with synonyms and meanings.
    
    Example: /dialect/translate/ammiya-to-fusha/ابغى
    Returns MSA equivalents: أريد, أرغب, أود with synonyms and root analysis
    """
    try:
        # Get MSA equivalents
        msa_equivalents = dialect_mapper.find_msa_equivalents(word)
        
        if not msa_equivalents:
            return {
                "ammiya_word": word,
                "found": False,
                "message": "No direct translation found. Try spelling variations.",
                "suggestions": _get_spelling_suggestions(word),
                "fusha_equivalents": [],
                "synonyms": []
            }
        
        # Get comprehensive analysis
        analysis = dialect_mapper.get_synonyms_and_meaning(word, is_dialect=True)
        
        # Format response
        result = {
            "ammiya_word": word,
            "found": True,
            "fusha_equivalents": [],
            "meanings": [],
            "synonyms": [],
            "root_analysis": {},
            "dialect_info": {
                "region": dialect_mapper._detect_dialect_region(word),
                "confidence": max([eq.get("confidence", 0) for eq in msa_equivalents])
            }
        }
        
        # Process each MSA equivalent
        for equiv in msa_equivalents:
            fusha_word = {
                "word": equiv["fusha_equivalent"],
                "confidence": equiv["confidence"],
                "mapping_type": equiv["mapping_type"]
            }
            
            # Add database info if available
            if equiv.get("database_info"):
                db_info = equiv["database_info"]
                fusha_word.update({
                    "root": db_info.get("root"),
                    "pos": db_info.get("pos"),
                    "pronunciation": {
                        "buckwalter": db_info.get("buckwalter"),
                        "phonetic": db_info.get("phonetic")
                    }
                })
                
                # Add meaning context
                result["meanings"].append({
                    "fusha_word": equiv["fusha_equivalent"],
                    "pos": db_info.get("pos"),
                    "root": db_info.get("root"),
                    "usage": "MSA equivalent"
                })
            
            result["fusha_equivalents"].append(fusha_word)
        
        # Add synonyms from analysis
        result["synonyms"] = analysis.get("synonyms", [])[:10]  # Limit to 10
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@router.get("/fusha-to-ammiya/{word}")
async def translate_fusha_to_ammiya(word: str) -> Dict[str, Any]:
    """
    Translate Fusha (MSA) word to Ammiya (dialect) with variants and meanings.
    
    Example: /dialect/translate/fusha-to-ammiya/أريد
    Returns dialect equivalents: ابغى, عايز, بدي with regional info
    """
    try:
        # Get dialect equivalents
        dialect_equivalents = dialect_mapper.find_dialect_equivalents(word)
        
        # Also search in database for the MSA word
        analysis = dialect_mapper.get_synonyms_and_meaning(word, is_dialect=False)
        
        result = {
            "fusha_word": word,
            "found": len(dialect_equivalents) > 0 or len(analysis["synonyms"]) > 0,
            "ammiya_equivalents": [],
            "regional_variants": {},
            "meanings": [],
            "msa_synonyms": [],
            "root_analysis": {}
        }
        
        # Process dialect equivalents
        regional_variants = {"gulf": [], "egyptian": [], "levantine": [], "other": []}
        
        for equiv in dialect_equivalents:
            ammiya_word = {
                "word": equiv["ammiya_equivalent"],
                "region": equiv["dialect_region"],
                "confidence": equiv["confidence"],
                "mapping_type": equiv["mapping_type"]
            }
            
            result["ammiya_equivalents"].append(ammiya_word)
            
            # Group by region
            region = equiv["dialect_region"]
            if region in regional_variants:
                regional_variants[region].append({
                    "word": equiv["ammiya_equivalent"],
                    "confidence": equiv["confidence"]
                })
            else:
                regional_variants["other"].append({
                    "word": equiv["ammiya_equivalent"], 
                    "confidence": equiv["confidence"]
                })
        
        result["regional_variants"] = {k: v for k, v in regional_variants.items() if v}
        
        # Add MSA synonyms
        result["msa_synonyms"] = analysis.get("synonyms", [])[:10]
        
        # Add meanings from database
        for translation in analysis.get("translations", []):
            if translation.get("fusha_database_info"):
                db_info = translation["fusha_database_info"]
                result["meanings"].append({
                    "word": word,
                    "pos": db_info.get("pos"),
                    "root": db_info.get("root"),
                    "pronunciation": {
                        "buckwalter": db_info.get("buckwalter"),
                        "phonetic": db_info.get("phonetic")
                    }
                })
                
                result["root_analysis"] = {
                    "root": db_info.get("root"),
                    "related_words_count": len(result["msa_synonyms"])
                }
        
        if not result["found"]:
            result["message"] = "No direct dialect translation found. Check MSA synonyms for alternatives."
            result["suggestions"] = _get_msa_suggestions(word)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@router.get("/bidirectional/{word}")
async def bidirectional_translate(
    word: str, 
    auto_detect: bool = Query(default=True, description="Auto-detect if word is dialect or MSA")
) -> Dict[str, Any]:
    """
    Smart bidirectional translation - automatically detects if input is Ammiya or Fusha.
    
    Returns both directions plus comprehensive analysis.
    """
    try:
        result = {
            "query_word": word,
            "detected_type": "unknown",
            "ammiya_to_fusha": {},
            "fusha_to_ammiya": {},
            "confidence": 0.0,
            "recommendations": []
        }
        
        # Try both directions
        ammiya_results = dialect_mapper.find_msa_equivalents(word)
        fusha_results = dialect_mapper.find_dialect_equivalents(word)
        
        ammiya_confidence = max([r.get("confidence", 0) for r in ammiya_results]) if ammiya_results else 0
        fusha_confidence = max([r.get("confidence", 0) for r in fusha_results]) if fusha_results else 0
        
        # Determine most likely type
        if ammiya_confidence > fusha_confidence:
            result["detected_type"] = "ammiya"
            result["confidence"] = ammiya_confidence
            result["ammiya_to_fusha"] = (await translate_ammiya_to_fusha(word))
            result["recommendations"].append("Word detected as Ammiya (dialect)")
        elif fusha_confidence > 0:
            result["detected_type"] = "fusha"
            result["confidence"] = fusha_confidence
            result["fusha_to_ammiya"] = (await translate_fusha_to_ammiya(word))
            result["recommendations"].append("Word detected as Fusha (MSA)")
        else:
            # Try both and return both
            result["detected_type"] = "ambiguous"
            result["ammiya_to_fusha"] = (await translate_ammiya_to_fusha(word))
            result["fusha_to_ammiya"] = (await translate_fusha_to_ammiya(word))
            result["recommendations"].append("Could not determine word type - showing both translations")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bidirectional translation failed: {str(e)}")

@router.get("/regions")
async def get_supported_regions() -> Dict[str, Any]:
    """Get information about supported dialect regions."""
    return {
        "supported_regions": [
            {
                "code": "gulf",
                "name": "Gulf Arabic",
                "countries": ["Saudi Arabia", "UAE", "Kuwait", "Qatar", "Bahrain", "Oman"],
                "sample_words": ["ابغى", "شلون", "وين", "هسه"],
                "coverage": "High"
            },
            {
                "code": "egyptian", 
                "name": "Egyptian Arabic",
                "countries": ["Egypt"],
                "sample_words": ["ايه", "فين", "عايز", "مش"],
                "coverage": "Medium"
            },
            {
                "code": "levantine",
                "name": "Levantine Arabic", 
                "countries": ["Syria", "Lebanon", "Jordan", "Palestine"],
                "sample_words": ["شو", "وين", "بدي", "هيك"],
                "coverage": "Medium"
            }
        ],
        "total_mappings": len(dialect_mapper.dialect_to_msa),
        "msa_database_entries": "101,331 comprehensive entries"
    }

def _get_spelling_suggestions(word: str) -> List[str]:
    """Get spelling suggestions for dialect words."""
    suggestions = []
    
    # Common spelling variations
    if 'ا' in word:
        suggestions.append(word.replace('ا', 'أ'))
    if 'أ' in word:
        suggestions.append(word.replace('أ', 'ا'))
    if 'ى' in word:
        suggestions.append(word.replace('ى', 'ي'))
    if 'ي' in word:
        suggestions.append(word.replace('ي', 'ى'))
        
    return list(set(suggestions))[:3]

def _get_msa_suggestions(word: str) -> List[str]:
    """Get MSA word suggestions."""
    # This would ideally connect to the database for suggestions
    return [
        f"Try variations of {word}",
        "Check root-based words",
        "Consider synonyms"
    ]
