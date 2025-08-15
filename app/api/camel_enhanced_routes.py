"""
Enhanced API routes that utilize CAMeL Tools morphological analysis.
Provides advanced search and analysis capabilities.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import sqlite3
import json
import logging

# Import CAMeL processor
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.camel_final import camel_processor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/camel", tags=["CAMeL Tools Enhanced"])

class CamelAnalysisResponse(BaseModel):
    original: str
    normalized: str
    lemmas: List[str]
    roots: List[str]
    pos_tags: List[str]
    morphology_count: int
    available: bool

class EnhancedEntryResponse(BaseModel):
    id: int
    lemma: str
    root: Optional[str] = None
    pos: Optional[str] = None
    camel_lemmas: List[str] = []
    camel_roots: List[str] = []
    camel_pos: List[str] = []
    camel_confidence: Optional[float] = None
    camel_enhanced: bool = False

class EnhancedSearchResponse(BaseModel):
    query: str
    entries: List[EnhancedEntryResponse]
    camel_analysis: Optional[CamelAnalysisResponse] = None
    morphological_suggestions: List[str] = []
    total_found: int

@router.get("/analyze/{word}", response_model=CamelAnalysisResponse)
async def analyze_word(word: str):
    """
    Perform morphological analysis on an Arabic word using CAMeL Tools.
    """
    if not camel_processor.available:
        raise HTTPException(status_code=503, detail="CAMeL Tools not available")
    
    try:
        analysis = camel_processor.analyze_word(word)
        
        return CamelAnalysisResponse(
            original=analysis["original"],
            normalized=analysis["normalized"],
            lemmas=analysis.get("possible_lemmas", []),
            roots=analysis.get("roots", []),
            pos_tags=analysis.get("pos_tags", []),
            morphology_count=len(analysis.get("morphology", [])),
            available=True
        )
    
    except Exception as e:
        logger.error(f"Analysis failed for '{word}': {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/search", response_model=EnhancedSearchResponse)
async def enhanced_search(
    q: str = Query(..., description="Search query"),
    use_morphology: bool = Query(True, description="Use morphological analysis for search"),
    limit: int = Query(50, description="Maximum results to return")
):
    """
    Enhanced search using CAMeL Tools morphological analysis.
    """
    try:
        conn = sqlite3.connect('app/arabic_dict.db')
        cursor = conn.cursor()
        
        # Get CAMeL analysis of the query if available
        camel_analysis = None
        search_terms = [q]
        
        if camel_processor.available and use_morphology:
            analysis = camel_processor.analyze_word(q)
            camel_analysis = CamelAnalysisResponse(
                original=analysis["original"],
                normalized=analysis["normalized"], 
                lemmas=analysis.get("possible_lemmas", []),
                roots=analysis.get("roots", []),
                pos_tags=analysis.get("pos_tags", []),
                morphology_count=len(analysis.get("morphology", [])),
                available=True
            )
            
            # Add morphological variations to search
            search_terms.extend(analysis.get("possible_lemmas", []))
            search_terms.extend(analysis.get("roots", []))
            
            # Add normalized form
            normalized = camel_processor.normalize_text(q)
            if normalized != q:
                search_terms.append(normalized)
        
        # Remove duplicates while preserving order
        search_terms = list(dict.fromkeys(search_terms))
        
        # Build comprehensive search query
        entries = []
        all_entry_ids = set()
        
        for term in search_terms:
            # Search in main fields and CAMeL enhanced fields
            cursor.execute("""
                SELECT 
                    e.id, e.lemma, e.root, e.pos,
                    e.camel_lemmas, e.camel_roots, e.camel_pos, e.camel_confidence,
                    CASE WHEN e.camel_analyzed = 1 THEN 1 ELSE 0 END as camel_enhanced
                FROM entries e
                WHERE 
                    e.lemma LIKE ? OR
                    e.root LIKE ? OR
                    e.lemma_norm LIKE ? OR
                    (e.camel_lemmas IS NOT NULL AND e.camel_lemmas LIKE ?) OR
                    (e.camel_roots IS NOT NULL AND e.camel_roots LIKE ?)
                ORDER BY 
                    CASE 
                        WHEN e.lemma = ? THEN 1
                        WHEN e.lemma LIKE ? THEN 2
                        WHEN e.root = ? THEN 3
                        WHEN e.camel_roots LIKE ? THEN 4
                        ELSE 5 
                    END,
                    COALESCE(e.camel_confidence, 0) DESC
                LIMIT ?
            """, (
                f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%",
                term, f"{term}%", term, f"%{term}%", limit
            ))
            
            rows = cursor.fetchall()
            
            for row in rows:
                entry_id = row[0]
                if entry_id not in all_entry_ids:
                    all_entry_ids.add(entry_id)
                    
                    # Parse CAMeL data
                    camel_lemmas = []
                    camel_roots = []
                    camel_pos = []
                    
                    try:
                        if row[4]:  # camel_lemmas
                            camel_lemmas = json.loads(row[4])
                        if row[5]:  # camel_roots
                            camel_roots = json.loads(row[5])
                        if row[6]:  # camel_pos
                            camel_pos = json.loads(row[6])
                    except json.JSONDecodeError:
                        pass
                    
                    entry = EnhancedEntryResponse(
                        id=entry_id,
                        lemma=row[1],
                        root=row[2],
                        pos=row[3],
                        camel_lemmas=camel_lemmas,
                        camel_roots=camel_roots,
                        camel_pos=camel_pos,
                        camel_confidence=row[7],
                        camel_enhanced=bool(row[8])
                    )
                    
                    entries.append(entry)
        
        # Generate morphological suggestions
        suggestions = []
        if camel_analysis:
            suggestions.extend(camel_analysis.lemmas[:5])
            suggestions.extend(camel_analysis.roots)
            
            # Remove duplicates and filter out the original query
            suggestions = [s for s in list(dict.fromkeys(suggestions)) 
                          if s and s != q and len(s) > 1][:10]
        
        conn.close()
        
        return EnhancedSearchResponse(
            query=q,
            entries=entries[:limit],
            camel_analysis=camel_analysis,
            morphological_suggestions=suggestions,
            total_found=len(entries)
        )
    
    except Exception as e:
        logger.error(f"Enhanced search failed for '{q}': {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/lemmatize/{text}")
async def lemmatize_text(text: str):
    """
    Lemmatize Arabic text using CAMeL Tools.
    """
    if not camel_processor.available:
        raise HTTPException(status_code=503, detail="CAMeL Tools not available")
    
    try:
        words = text.split()
        results = []
        
        for word in words:
            lemmas = camel_processor.get_all_lemmas(word)
            best_lemma = lemmas[0] if lemmas else word
            
            results.append({
                "word": word,
                "lemma": best_lemma,
                "all_lemmas": lemmas[:5],  # Limit to top 5
                "root": camel_processor.get_best_root(word),
                "pos": camel_processor.get_best_pos(word)
            })
        
        return {
            "original_text": text,
            "lemmatized": results,
            "word_count": len(words)
        }
    
    except Exception as e:
        logger.error(f"Lemmatization failed for '{text}': {e}")
        raise HTTPException(status_code=500, detail=f"Lemmatization failed: {str(e)}")

@router.get("/root/{root}")
async def search_by_root(
    root: str,
    include_camel: bool = Query(True, description="Include CAMeL-enhanced results")
):
    """
    Search for words by Arabic root, including CAMeL-enhanced results.
    """
    try:
        conn = sqlite3.connect('app/arabic_dict.db')
        cursor = conn.cursor()
        
        if include_camel:
            # Search both original root field and CAMeL roots
            cursor.execute("""
                SELECT 
                    e.id, e.lemma, e.root, e.pos,
                    e.camel_lemmas, e.camel_roots, e.camel_pos, e.camel_confidence
                FROM entries e
                WHERE 
                    e.root = ? OR
                    (e.camel_roots IS NOT NULL AND e.camel_roots LIKE ?)
                ORDER BY COALESCE(e.camel_confidence, 0) DESC
                LIMIT 100
            """, (root, f'%"{root}"%'))
        else:
            # Search only original root field
            cursor.execute("""
                SELECT 
                    e.id, e.lemma, e.root, e.pos,
                    e.camel_lemmas, e.camel_roots, e.camel_pos, e.camel_confidence
                FROM entries e
                WHERE e.root = ?
                LIMIT 100
            """, (root,))
        
        rows = cursor.fetchall()
        
        entries = []
        for row in rows:
            # Parse CAMeL data
            camel_lemmas = []
            camel_roots = []
            camel_pos = []
            
            try:
                if row[4]:  # camel_lemmas
                    camel_lemmas = json.loads(row[4])
                if row[5]:  # camel_roots  
                    camel_roots = json.loads(row[5])
                if row[6]:  # camel_pos
                    camel_pos = json.loads(row[6])
            except json.JSONDecodeError:
                pass
            
            entry = EnhancedEntryResponse(
                id=row[0],
                lemma=row[1],
                root=row[2],
                pos=row[3],
                camel_lemmas=camel_lemmas,
                camel_roots=camel_roots,
                camel_pos=camel_pos,
                camel_confidence=row[7],
                camel_enhanced=bool(row[4] or row[5] or row[6])  # Has any CAMeL data
            )
            
            entries.append(entry)
        
        conn.close()
        
        return {
            "root": root,
            "entries": entries,
            "total_found": len(entries),
            "camel_enhanced": include_camel
        }
    
    except Exception as e:
        logger.error(f"Root search failed for '{root}': {e}")
        raise HTTPException(status_code=500, detail=f"Root search failed: {str(e)}")

@router.get("/stats")
async def get_enhancement_stats():
    """
    Get statistics about CAMeL Tools enhancement in the database.
    """
    try:
        conn = sqlite3.connect('app/arabic_dict.db')
        cursor = conn.cursor()
        
        # Total entries
        cursor.execute("SELECT COUNT(*) FROM entries")
        total = cursor.fetchone()[0]
        
        # Check if CAMeL columns exist
        cursor.execute("PRAGMA table_info(entries)")
        columns = [col[1] for col in cursor.fetchall()]
        has_camel = "camel_analyzed" in columns
        
        if not has_camel:
            return {
                "total_entries": total,
                "camel_enhanced": False,
                "message": "Dictionary not yet enhanced with CAMeL Tools"
            }
        
        # Enhanced entries
        cursor.execute("SELECT COUNT(*) FROM entries WHERE camel_analyzed = 1")
        enhanced = cursor.fetchone()[0]
        
        # Entries with roots
        cursor.execute("SELECT COUNT(*) FROM entries WHERE camel_roots IS NOT NULL AND camel_roots != '[]'")
        with_roots = cursor.fetchone()[0]
        
        # Entries with lemmas
        cursor.execute("SELECT COUNT(*) FROM entries WHERE camel_lemmas IS NOT NULL AND camel_lemmas != '[]'")
        with_lemmas = cursor.fetchone()[0]
        
        # Average confidence
        cursor.execute("SELECT AVG(camel_confidence) FROM entries WHERE camel_confidence IS NOT NULL")
        avg_confidence = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_entries": total,
            "camel_enhanced": True,
            "enhanced_entries": enhanced,
            "enhancement_percentage": (enhanced / total * 100) if total > 0 else 0,
            "entries_with_roots": with_roots,
            "entries_with_lemmas": with_lemmas,
            "average_confidence": avg_confidence,
            "camel_available": camel_processor.available
        }
    
    except Exception as e:
        logger.error(f"Stats generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats generation failed: {str(e)}")
