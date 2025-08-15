"""
Enhanced API endpoints using CAMeL Tools for advanced Arabic NLP features.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import sqlite3
import json
import logging

from services.camel_processor import camel_processor, enhance_dictionary_entry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/camel", tags=["CAMeL Tools"])

class CamelAnalysisResponse(BaseModel):
    original: str
    normalized: str
    morphology: List[Dict[str, Any]]
    possible_lemmas: List[str]
    roots: List[str]
    patterns: List[str]
    pos_tags: List[str]
    dialect: Optional[Dict[str, Any]] = None
    sentiment: Optional[Dict[str, Any]] = None
    entities: List[Dict[str, str]]

class EnhancedSearchResponse(BaseModel):
    word: str
    entries: List[Dict[str, Any]]
    camel_analysis: Optional[CamelAnalysisResponse] = None
    suggestions: List[str]

@router.get("/analyze", response_model=CamelAnalysisResponse)
async def analyze_word(
    word: str = Query(..., description="Arabic word to analyze"),
    db_path: str = "app/arabic_dict.db"
):
    """
    Perform comprehensive morphological analysis using CAMeL Tools.
    """
    if not camel_processor.available:
        raise HTTPException(status_code=503, detail="CAMeL Tools not available")
    
    try:
        analysis = camel_processor.analyze_word(word)
        
        return CamelAnalysisResponse(
            original=analysis["original"],
            normalized=analysis["normalized"],
            morphology=analysis["morphology"],
            possible_lemmas=analysis["possible_lemmas"],
            roots=analysis["roots"],
            patterns=analysis["patterns"],
            pos_tags=analysis["pos_tags"],
            dialect=analysis.get("dialect"),
            sentiment=analysis.get("sentiment"),
            entities=analysis["entities"]
        )
    
    except Exception as e:
        logger.error(f"Analysis failed for '{word}': {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/search", response_model=EnhancedSearchResponse)
async def enhanced_search(
    query: str = Query(..., description="Search query"),
    use_morphology: bool = Query(True, description="Use morphological analysis for search"),
    include_dialects: bool = Query(False, description="Include dialectal variations"),
    db_path: str = "app/arabic_dict.db"
):
    """
    Enhanced search using CAMeL Tools morphological analysis.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get CAMeL analysis of the query
        camel_analysis = None
        search_terms = [query]
        
        if camel_processor.available and use_morphology:
            analysis = camel_processor.analyze_word(query)
            camel_analysis = CamelAnalysisResponse(
                original=analysis["original"],
                normalized=analysis["normalized"],
                morphology=analysis["morphology"],
                possible_lemmas=analysis["possible_lemmas"],
                roots=analysis["roots"],
                patterns=analysis["patterns"],
                pos_tags=analysis["pos_tags"],
                dialect=analysis.get("dialect"),
                sentiment=analysis.get("sentiment"),
                entities=analysis["entities"]
            )
            
            # Add morphological variations to search
            search_terms.extend(analysis["possible_lemmas"])
            search_terms.extend(analysis["roots"])
            
            # Normalize the original query
            normalized_query = camel_processor.normalize_text(query)
            if normalized_query != query:
                search_terms.append(normalized_query)
        
        # Remove duplicates while preserving order
        search_terms = list(dict.fromkeys(search_terms))
        
        # Build search query
        entries = []
        suggestions = []
        
        for term in search_terms:
            # Search in main entries
            cursor.execute("""
                SELECT e.*, 
                       COALESCE(e.camel_lemmas, '[]') as camel_lemmas,
                       COALESCE(e.camel_roots, '[]') as camel_roots,
                       COALESCE(e.camel_pos_tags, '[]') as camel_pos_tags,
                       COALESCE(e.camel_patterns, '[]') as camel_patterns,
                       e.camel_morphology,
                       e.camel_dialect,
                       e.camel_confidence
                FROM entries e
                WHERE e.lemma LIKE ? OR e.root LIKE ? OR e.definition LIKE ?
                   OR e.normalized_lemma LIKE ? OR e.camel_normalized LIKE ?
                ORDER BY 
                    CASE WHEN e.lemma = ? THEN 1
                         WHEN e.lemma LIKE ? THEN 2
                         WHEN e.root = ? THEN 3
                         ELSE 4 END,
                    COALESCE(e.camel_confidence, 0) DESC
                LIMIT 50
            """, (f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%",
                  term, f"{term}%", term))
            
            rows = cursor.fetchall()
            
            for row in rows:
                entry = {
                    "id": row[0],
                    "lemma": row[1],
                    "root": row[2],
                    "pos": row[3],
                    "gender": row[4],
                    "number": row[5],
                    "pattern": row[6],
                    "conjugation": row[7],
                    "normalized_lemma": row[8],
                    "definition": row[9],
                    "source": row[10],
                    "camel_data": {
                        "lemmas": json.loads(row[11]) if row[11] else [],
                        "roots": json.loads(row[12]) if row[12] else [],
                        "pos_tags": json.loads(row[13]) if row[13] else [],
                        "patterns": json.loads(row[14]) if row[14] else [],
                        "morphology": json.loads(row[15]) if row[15] else None,
                        "dialect": json.loads(row[16]) if row[16] else None,
                        "confidence": row[17]
                    }
                }
                
                # Avoid duplicates
                if not any(e["id"] == entry["id"] for e in entries):
                    entries.append(entry)
        
        # Generate suggestions based on CAMeL analysis
        if camel_analysis:
            # Suggest lemmas and roots as alternatives
            suggestions.extend(camel_analysis.possible_lemmas)
            suggestions.extend(camel_analysis.roots)
            
            # Generate morphological variations
            if camel_processor.available:
                for lemma in camel_analysis.possible_lemmas[:2]:  # Limit to top 2
                    # Generate plural forms
                    plural_forms = camel_processor.generate_forms(lemma, {"num": "p"})
                    suggestions.extend(plural_forms[:3])  # Limit suggestions
                    
                    # Generate feminine forms
                    fem_forms = camel_processor.generate_forms(lemma, {"gen": "f"})
                    suggestions.extend(fem_forms[:3])
        
        # Remove duplicates from suggestions and filter out the original query
        suggestions = [s for s in list(dict.fromkeys(suggestions)) 
                      if s and s != query and len(s) > 1][:10]
        
        conn.close()
        
        return EnhancedSearchResponse(
            word=query,
            entries=entries,
            camel_analysis=camel_analysis,
            suggestions=suggestions
        )
    
    except Exception as e:
        logger.error(f"Enhanced search failed for '{query}': {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/lemmatize")
async def lemmatize_text(
    text: str = Query(..., description="Arabic text to lemmatize"),
    return_analysis: bool = Query(False, description="Return full morphological analysis")
):
    """
    Lemmatize Arabic text using CAMeL Tools.
    """
    if not camel_processor.available:
        raise HTTPException(status_code=503, detail="CAMeL Tools not available")
    
    try:
        # Tokenize the text
        words = text.split()
        results = []
        
        for word in words:
            if return_analysis:
                analysis = camel_processor.analyze_word(word)
                results.append({
                    "word": word,
                    "lemmas": analysis["possible_lemmas"],
                    "best_lemma": analysis["possible_lemmas"][0] if analysis["possible_lemmas"] else word,
                    "morphology": analysis["morphology"]
                })
            else:
                best_lemma = camel_processor.get_best_lemma(word) or word
                results.append({
                    "word": word,
                    "lemma": best_lemma
                })
        
        return {
            "original_text": text,
            "lemmatized": results
        }
    
    except Exception as e:
        logger.error(f"Lemmatization failed for '{text}': {e}")
        raise HTTPException(status_code=500, detail=f"Lemmatization failed: {str(e)}")

@router.get("/dialect")
async def identify_dialect(
    text: str = Query(..., description="Arabic text to analyze for dialect")
):
    """
    Identify the dialect of Arabic text.
    """
    if not camel_processor.available:
        raise HTTPException(status_code=503, detail="CAMeL Tools not available")
    
    try:
        dialect_info = camel_processor.identify_dialect(text)
        
        if dialect_info:
            return {
                "text": text,
                "dialect": dialect_info["top_dialect"],
                "confidence": dialect_info["confidence"],
                "all_scores": dialect_info["all_scores"]
            }
        else:
            return {
                "text": text,
                "dialect": "unknown",
                "confidence": 0.0,
                "all_scores": {}
            }
    
    except Exception as e:
        logger.error(f"Dialect identification failed for '{text}': {e}")
        raise HTTPException(status_code=500, detail=f"Dialect identification failed: {str(e)}")

@router.get("/sentiment")
async def analyze_sentiment(
    text: str = Query(..., description="Arabic text to analyze for sentiment")
):
    """
    Analyze sentiment of Arabic text.
    """
    if not camel_processor.available:
        raise HTTPException(status_code=503, detail="CAMeL Tools not available")
    
    try:
        sentiment_info = camel_processor.analyze_sentiment(text)
        
        if sentiment_info:
            return {
                "text": text,
                "sentiment": sentiment_info["sentiment"],
                "confidence": sentiment_info["confidence"],
                "all_scores": sentiment_info["all_scores"]
            }
        else:
            return {
                "text": text,
                "sentiment": "neutral",
                "confidence": 0.0,
                "all_scores": {}
            }
    
    except Exception as e:
        logger.error(f"Sentiment analysis failed for '{text}': {e}")
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")

@router.get("/entities")
async def extract_entities(
    text: str = Query(..., description="Arabic text to extract entities from")
):
    """
    Extract named entities from Arabic text.
    """
    if not camel_processor.available:
        raise HTTPException(status_code=503, detail="CAMeL Tools not available")
    
    try:
        entities = camel_processor.extract_entities(text)
        
        return {
            "text": text,
            "entities": entities,
            "entity_count": len(entities)
        }
    
    except Exception as e:
        logger.error(f"Entity extraction failed for '{text}': {e}")
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")

@router.get("/stats")
async def get_camel_stats(db_path: str = "app/arabic_dict.db"):
    """
    Get statistics about CAMeL Tools enhancement in the database.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if CAMeL columns exist
        cursor.execute("PRAGMA table_info(entries)")
        columns = [col[1] for col in cursor.fetchall()]
        has_camel_data = "camel_analyzed" in columns
        
        if not has_camel_data:
            return {
                "camel_enhanced": False,
                "message": "Dictionary not yet enhanced with CAMeL Tools. Run enhancement first."
            }
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM entries")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM entries WHERE camel_analyzed = 1")
        analyzed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM entries WHERE camel_roots IS NOT NULL AND camel_roots != '[]'")
        with_roots = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM entries WHERE camel_pos_tags IS NOT NULL AND camel_pos_tags != '[]'")
        with_pos = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(camel_confidence) FROM entries WHERE camel_confidence IS NOT NULL")
        avg_confidence = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "camel_enhanced": True,
            "total_entries": total,
            "analyzed_entries": analyzed,
            "analysis_percentage": (analyzed / total * 100) if total > 0 else 0,
            "entries_with_roots": with_roots,
            "entries_with_pos": with_pos,
            "average_confidence": avg_confidence,
            "camel_tools_available": camel_processor.available
        }
    
    except Exception as e:
        logger.error(f"Stats generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats generation failed: {str(e)}")
