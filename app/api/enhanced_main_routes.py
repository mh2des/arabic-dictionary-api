"""
Enhanced main routes using the fully enhanced SQLite database.
Replaces the in-memory JSON approach with database integration.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import sqlite3
import json
from ..services.normalize import normalize_ar

router = APIRouter()

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect("app/arabic_dict.db")

@router.get("/search/enhanced")
async def enhanced_search(
    q: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(50, description="Maximum results"),
    include_phonetics: bool = Query(True, description="Include phonetic data"),
    include_camel: bool = Query(True, description="Include CAMeL analysis")
):
    """Enhanced search using the fully processed database."""
    
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build query with all enhanced features
    base_query = """
        SELECT 
            lemma, root, pos, 
            buckwalter_transliteration, phonetic_transcription, semantic_features,
            camel_roots, camel_lemmas, camel_pos_tags,
            phase2_enhanced, camel_analyzed
        FROM entries 
        WHERE lemma LIKE ? OR lemma_norm LIKE ?
    """
    
    search_term = f"%{q}%"
    cursor.execute(f"{base_query} LIMIT ?", (search_term, search_term, limit))
    
    results = []
    for row in cursor.fetchall():
        result = {
            "lemma": row[0],
            "root": row[1], 
            "pos": row[2],
            "phonetics": {
                "buckwalter": row[3],
                "transcription": json.loads(row[4]) if row[4] else None,
                "semantic": json.loads(row[5]) if row[5] else None
            } if include_phonetics else None,
            "camel_analysis": {
                "roots": json.loads(row[6]) if row[6] else [],
                "lemmas": json.loads(row[7]) if row[7] else [], 
                "pos_tags": json.loads(row[8]) if row[8] else []
            } if include_camel else None,
            "enhanced": {
                "phase2": bool(row[9]),
                "camel": bool(row[10])
            }
        }
        results.append(result)
    
    conn.close()
    
    return {
        "query": q,
        "results": results,
        "total": len(results),
        "enhanced_features": {
            "phonetics_available": include_phonetics,
            "camel_analysis_available": include_camel
        }
    }

@router.get("/dialects/phonetics/{word}")
async def get_phonetics(word: str):
    """Get all phonetic representations for a word."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT lemma, buckwalter_transliteration, phonetic_transcription, semantic_features
        FROM entries 
        WHERE lemma = ? AND phase2_enhanced = 1
    """, (word,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"No phonetic data found for '{word}'")
    
    phonetic_data = json.loads(row[2]) if row[2] else {}
    semantic_data = json.loads(row[3]) if row[3] else {}
    
    return {
        "word": word,
        "original_lemma": row[0],
        "phonetic_representations": {
            "buckwalter": row[1],
            "ipa_approximation": phonetic_data.get("ipa_approx"),
            "romanization": phonetic_data.get("romanization"),
            "buckwalter_detailed": phonetic_data.get("buckwalter")
        },
        "semantic_analysis": semantic_data,
        "available_scripts": ["arabic", "buckwalter", "ipa", "latin"]
    }

@router.get("/stats/comprehensive")
async def comprehensive_stats():
    """Get comprehensive statistics about the enhanced database."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get various statistics
    stats = {}
    
    # Total entries
    cursor.execute("SELECT COUNT(*) FROM entries")
    stats["total_entries"] = cursor.fetchone()[0]
    
    # Enhanced entries
    cursor.execute("SELECT COUNT(*) FROM entries WHERE phase2_enhanced = 1")
    stats["phase2_enhanced"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM entries WHERE camel_analyzed = 1")
    stats["camel_enhanced"] = cursor.fetchone()[0]
    
    # Phonetic coverage
    cursor.execute("SELECT COUNT(*) FROM entries WHERE buckwalter_transliteration IS NOT NULL")
    stats["buckwalter_coverage"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM entries WHERE phonetic_transcription IS NOT NULL")
    stats["phonetic_coverage"] = cursor.fetchone()[0]
    
    # Root analysis
    cursor.execute("SELECT COUNT(DISTINCT camel_roots) FROM entries WHERE camel_roots IS NOT NULL")
    stats["unique_roots"] = cursor.fetchone()[0]
    
    # POS distribution
    cursor.execute("""
        SELECT COUNT(*) as count, pos 
        FROM entries 
        WHERE pos IS NOT NULL 
        GROUP BY pos 
        ORDER BY count DESC 
        LIMIT 10
    """)
    stats["pos_distribution"] = dict(cursor.fetchall())
    
    conn.close()
    
    return {
        "database_stats": stats,
        "enhancement_rates": {
            "phase2_coverage": f"{stats['phase2_enhanced']/stats['total_entries']*100:.1f}%",
            "camel_coverage": f"{stats['camel_enhanced']/stats['total_entries']*100:.1f}%",
            "phonetic_coverage": f"{stats['phonetic_coverage']/stats['total_entries']*100:.1f}%"
        },
        "capabilities": [
            "Multi-script phonetic representation",
            "CAMeL Tools morphological analysis", 
            "Comprehensive semantic analysis",
            "Root-based search",
            "POS tagging",
            "Cross-dialect analysis ready"
        ]
    }
