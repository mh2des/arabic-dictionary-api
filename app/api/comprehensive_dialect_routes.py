"""
Comprehensive Dialect Translation API Routes
Uses the enriched Arabic dialects JSON data for bidirectional translation
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.dialect_translator import ArabicDialectTranslator

# Initialize the router
router = APIRouter(prefix="/dialect/translate", tags=["Comprehensive Dialect Translation"])

# Initialize the translator
dialect_json_path = os.path.join(os.path.dirname(__file__), "..", "data", "arabic_dialect_dictionary_enriched (1).json")
main_db_path = os.path.join(os.path.dirname(__file__), "..", "arabic_dict.db")

try:
    translator = ArabicDialectTranslator(dialect_json_path, main_db_path)
    TRANSLATOR_AVAILABLE = True
    print(f"✅ Comprehensive dialect translator initialized with {len(translator.supported_dialects)} dialects")
except Exception as e:
    print(f"❌ Dialect translator initialization failed: {e}")
    TRANSLATOR_AVAILABLE = False
    translator = None

@router.get("/ammiya-to-fusha/{word}")
async def translate_ammiya_to_fusha(
    word: str,
    dialects: Optional[str] = Query(None, description="Comma-separated dialect names (gulf,egyptian,levantine,etc.)")
) -> Dict[str, Any]:
    """
    🔄 Translate dialect word (Ammiya) to MSA (Fusha)
    
    Examples:
    - ابغى -> أريد (Gulf: I want)
    - عايز -> أريد (Egyptian: I want)  
    - بدي -> أريد (Levantine: I want)
    - شلون -> كيف (Gulf: How)
    - إزيك -> كيف حالك (Egyptian: How are you)
    """
    
    if not TRANSLATOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dialect translator service not available")
    
    target_dialects = None
    if dialects:
        target_dialects = [d.strip() for d in dialects.split(',')]
    
    try:
        result = translator.translate_dialect_to_fusha(word, target_dialects)
        
        return {
            "input_word": word,
            "input_type": "ammiya_dialect",
            "target_type": "fusha_msa",
            "success": result['found'],
            "translations": result['translations'],
            "alternatives": result['similar_words'],
            "match_count": result['total_matches'],
            "dialects_searched": target_dialects or translator.supported_dialects,
            "service": "comprehensive_dialect_translator"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@router.get("/fusha-to-ammiya/{word}")
async def translate_fusha_to_ammiya(
    word: str,
    dialects: Optional[str] = Query(None, description="Target dialects (gulf,egyptian,levantine,etc.)")
) -> Dict[str, Any]:
    """
    🔄 Translate MSA (Fusha) word to dialect forms (Ammiya)
    
    Examples:
    - أريد -> ابغى (Gulf), عايز (Egyptian), بدي (Levantine)
    - كيف -> شلون (Gulf), إزاي (Egyptian), كيف (Levantine)
    - ماذا -> شنو (Gulf), إيه (Egyptian), شو (Levantine)
    """
    
    if not TRANSLATOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dialect translator service not available")
    
    target_dialects = None
    if dialects:
        target_dialects = [d.strip() for d in dialects.split(',')]
    
    try:
        result = translator.translate_fusha_to_dialect(word, target_dialects)
        
        # Group translations by dialect for better presentation
        by_dialect = {}
        for translation in result['dialect_translations']:
            dialect = translation['dialect']
            if dialect not in by_dialect:
                by_dialect[dialect] = []
            by_dialect[dialect].append(translation)
        
        return {
            "input_word": word,
            "input_type": "fusha_msa",
            "target_type": "ammiya_dialect",
            "success": result['found'],
            "translations_by_dialect": by_dialect,
            "all_translations": result['dialect_translations'],
            "alternatives": result['similar_words'],
            "total_variants": result['total_matches'],
            "dialect_coverage": f"{len(by_dialect)}/{len(translator.supported_dialects)} dialects",
            "service": "comprehensive_dialect_translator"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@router.get("/comprehensive/{word}")
async def comprehensive_word_analysis(
    word: str,
    is_dialect: bool = Query(True, description="True if input is dialect, False if MSA")
) -> Dict[str, Any]:
    """
    📚 Complete word analysis with meanings, synonyms, and cross-dialect translations
    
    Perfect for the dialect screen! Returns:
    - Primary translation
    - Synonyms in MSA
    - Related dialect words
    - Usage examples
    - Pronunciation guide
    """
    
    if not TRANSLATOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dialect translator service not available")
    
    try:
        analysis = translator.get_word_meanings_and_synonyms(word, is_dialect)
        
        return {
            "word": word,
            "analysis_type": "dialect_word" if is_dialect else "msa_word",
            "comprehensive_data": analysis,
            "for_flutter_screen": {
                "title": f"Analysis: {word}",
                "primary_meaning": analysis.get('primary_translation', {}).get('english', 'Unknown'),
                "fusha_equivalent": analysis.get('primary_translation', {}).get('fusha', word),
                "synonyms_count": len(analysis.get('synonyms_in_msa', [])),
                "dialect_forms_count": len(analysis.get('dialect_translations', [])),
                "has_examples": len(analysis.get('usage_examples', [])) > 0
            },
            "timestamp": "2025-08-16"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/browse/category/{category}")
async def browse_by_category(
    category: str,
    dialect: Optional[str] = Query(None, description="Specific dialect filter"),
    limit: int = Query(default=30, le=100, description="Number of words to return")
) -> Dict[str, Any]:
    """
    📋 Browse words by category - perfect for learning!
    
    Categories:
    - basic_words: Everyday essentials
    - verbs: Action words
    - family_terms: Family relationships  
    - adjectives: Descriptive words
    - common_expressions: Useful phrases
    - phrases: Conversation starters
    - common_phrases: Frequently used
    """
    
    if not TRANSLATOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dialect translator service not available")
    
    valid_categories = ['basic_words', 'verbs', 'family_terms', 'adjectives', 'common_expressions', 'phrases', 'common_phrases']
    
    if category not in valid_categories:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid category. Choose from: {', '.join(valid_categories)}"
        )
    
    try:
        result = translator.search_by_category(category, dialect)
        
        # Limit results
        limited_words = result['words'][:limit]
        
        return {
            "category": category,
            "dialect_filter": dialect or "all_dialects",
            "words": limited_words,
            "total_in_category": result['total_found'],
            "showing": len(limited_words),
            "for_flutter_list": [
                {
                    "dialect_word": word['dialect_word'],
                    "fusha": word['fusha'],
                    "english": word['english'],
                    "dialect": word['dialect'],
                    "subtitle": f"{word['fusha']} • {word['english']}"
                }
                for word in limited_words
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Category browse failed: {str(e)}")

@router.get("/info/dialects")
async def get_dialect_information() -> Dict[str, Any]:
    """
    ℹ️ Get comprehensive information about supported dialects
    """
    
    if not TRANSLATOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dialect translator service not available")
    
    try:
        info = translator.get_dialect_info()
        
        return {
            "service_status": "active",
            "total_entries": info['total_entries'],
            "supported_dialects": info['supported_dialects'],
            "regions_covered": info['regions_included'],
            "categories_available": info['categories'],
            "dialect_details": info['dialect_details'],
            "for_flutter_dropdown": [
                {
                    "value": dialect,
                    "label": details['name'],
                    "subtitle": f"{details['speakers']} speakers • {details['word_count']} words"
                }
                for dialect, details in info['dialect_details'].items()
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dialect info: {str(e)}")

@router.get("/examples/{dialect}")
async def get_dialect_examples(
    dialect: str,
    category: Optional[str] = Query(default="basic_words", description="Word category"),
    limit: int = Query(default=20, le=50, description="Number of examples")
) -> Dict[str, Any]:
    """
    📝 Get example words from a specific dialect
    
    Dialects: gulf, egyptian, levantine, iraqi, yemeni, sudanese, palestinian
    """
    
    if not TRANSLATOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dialect translator service not available")
    
    if dialect not in translator.supported_dialects:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported dialect '{dialect}'. Available: {', '.join(translator.supported_dialects)}"
        )
    
    try:
        examples = translator.search_by_category(category, dialect)
        limited_examples = examples['words'][:limit]
        
        return {
            "dialect": dialect,
            "category": category,
            "examples": limited_examples,
            "total_available": examples['total_found'],
            "showing": len(limited_examples),
            "dialect_info": {
                "name": translator.dialect_data['dialects'][dialect]['name'],
                "countries": translator.dialect_data['dialects'][dialect]['countries'],
                "speakers": translator.dialect_data['dialects'][dialect]['speakers']
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get examples: {str(e)}")

@router.get("/popular-words")
async def get_popular_words(
    dialect: Optional[str] = Query(None, description="Filter by dialect"),
    limit: int = Query(default=50, le=100, description="Number of words")
) -> Dict[str, Any]:
    """
    🔥 Get most popular/common dialect words across all dialects
    
    Perfect for a "Popular Words" section in your app!
    """
    
    if not TRANSLATOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dialect translator service not available")
    
    try:
        # Get basic words from all or specific dialect
        popular = translator.search_by_category('basic_words', dialect)
        
        # Filter for "very common" usage words
        very_common = [
            word for word in popular['words'] 
            if word.get('usage') == 'very common'
        ]
        
        # If not enough "very common", include regular words
        if len(very_common) < limit:
            all_words = popular['words']
            result_words = very_common + [
                word for word in all_words 
                if word not in very_common
            ]
        else:
            result_words = very_common
        
        final_words = result_words[:limit]
        
        return {
            "popular_words": final_words,
            "total_showing": len(final_words),
            "criteria": "most_common_usage",
            "dialect_filter": dialect or "all_dialects",
            "for_popular_list": [
                {
                    "dialect_word": word['dialect_word'],
                    "meaning": word['english'],
                    "fusha": word['fusha'],
                    "dialect": word['dialect'],
                    "pronunciation": word.get('pronunciation', ''),
                    "badge": "🔥 Popular"
                }
                for word in final_words
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get popular words: {str(e)}")

@router.get("/quick-translate")
async def quick_translate(
    q: str = Query(..., description="Word to translate"),
    source: str = Query(default="auto", description="Source type: auto, dialect, fusha")
) -> Dict[str, Any]:
    """
    ⚡ Quick translation endpoint - auto-detects if word is dialect or MSA
    
    Perfect for a quick search/translate feature in your app!
    """
    
    if not TRANSLATOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dialect translator service not available")
    
    try:
        if source == "auto":
            # Try both directions and return the one with results
            dialect_result = translator.translate_dialect_to_fusha(q)
            fusha_result = translator.translate_fusha_to_dialect(q)
            
            if dialect_result['found'] and not fusha_result['found']:
                # It's a dialect word
                return {
                    "query": q,
                    "detected_type": "dialect_word",
                    "translation": dialect_result['translations'][0] if dialect_result['translations'] else None,
                    "fusha_equivalent": dialect_result['translations'][0]['fusha'] if dialect_result['translations'] else None,
                    "dialect": dialect_result['translations'][0]['dialect'] if dialect_result['translations'] else None,
                    "quick_result": f"{q} → {dialect_result['translations'][0]['fusha']}" if dialect_result['translations'] else "No translation found"
                }
            elif fusha_result['found'] and not dialect_result['found']:
                # It's an MSA word
                return {
                    "query": q,
                    "detected_type": "msa_word",
                    "dialect_forms": fusha_result['dialect_translations'][:3],  # Top 3
                    "total_dialect_forms": len(fusha_result['dialect_translations']),
                    "quick_result": f"{q} → {', '.join([t['dialect_word'] for t in fusha_result['dialect_translations'][:3]])}"
                }
            elif dialect_result['found'] and fusha_result['found']:
                # Word exists in both
                return {
                    "query": q,
                    "detected_type": "ambiguous",
                    "as_dialect": dialect_result['translations'][0] if dialect_result['translations'] else None,
                    "as_fusha": fusha_result['dialect_translations'][:2],
                    "quick_result": f"{q} has multiple meanings"
                }
            else:
                # Not found in either
                return {
                    "query": q,
                    "detected_type": "unknown",
                    "found": False,
                    "suggestions": dialect_result['similar_words'][:3] + fusha_result['similar_words'][:3],
                    "quick_result": "Word not found - check suggestions"
                }
        
        elif source == "dialect":
            result = translator.translate_dialect_to_fusha(q)
            return {
                "query": q,
                "source_type": "dialect",
                "translation": result['translations'][0] if result['translations'] else None,
                "found": result['found']
            }
        
        elif source == "fusha":
            result = translator.translate_fusha_to_dialect(q)
            return {
                "query": q,
                "source_type": "fusha",
                "dialect_forms": result['dialect_translations'][:5],
                "found": result['found']
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick translate failed: {str(e)}")
