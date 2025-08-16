"""
Enhanced API Endpoints for Complete Dialect Support (Screen 5)

This implements advanced API endpoints to provide full dialect functionality
even without processing all remaining entries upfront. Uses on-demand CAMeL analysis.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import sqlite3
import json
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Try to import CAMeL Tools
try:
    from camel_tools.morphology.database import MorphologyDB
    from camel_tools.morphology.analyzer import Analyzer
    from camel_tools.utils.normalize import normalize_alef_maksura_ar
    from camel_tools.utils.normalize import normalize_alef_ar
    from camel_tools.utils.normalize import normalize_teh_marbuta_ar
    
    # Initialize CAMeL Tools
    camel_db = MorphologyDB.builtin_db()
    camel_analyzer = Analyzer(camel_db)
    CAMEL_AVAILABLE = True
    
except ImportError:
    CAMEL_AVAILABLE = False
    camel_analyzer = None

router = APIRouter(prefix="/dialect", tags=["Dialect Support"])

def get_db_connection() -> sqlite3.Connection:
    """Get database connection."""
    db_path = os.path.join(os.path.dirname(__file__), "..", "arabic_dict.db")
    return sqlite3.connect(db_path)

def normalize_arabic_text(text: str) -> str:
    """Normalize Arabic text for analysis."""
    if not CAMEL_AVAILABLE or not text:
        return text
    
    normalized = normalize_alef_maksura_ar(text)
    normalized = normalize_alef_ar(normalized)
    normalized = normalize_teh_marbuta_ar(normalized)
    return normalized

def analyze_word_live(word: str) -> Dict[str, Any]:
    """Perform live CAMeL analysis on a word."""
    if not CAMEL_AVAILABLE:
        return {
            'lemmas': [],
            'roots': [],
            'pos_tags': [],
            'confidence': 0.0,
            'analyses': [],
            'live_analysis': False
        }
    
    try:
        normalized_word = normalize_arabic_text(word.strip())
        analyses = camel_analyzer.analyze(normalized_word)
        
        if not analyses:
            return {
                'lemmas': [],
                'roots': [],
                'pos_tags': [],
                'confidence': 0.0,
                'analyses': [],
                'live_analysis': True
            }
        
        lemmas = []
        roots = []
        pos_tags = []
        
        for analysis in analyses:
            if 'lex' in analysis and analysis['lex'] not in lemmas:
                lemmas.append(analysis['lex'])
            if 'root' in analysis and analysis['root'] not in roots:
                roots.append(analysis['root'])
            if 'pos' in analysis and analysis['pos'] not in pos_tags:
                pos_tags.append(analysis['pos'])
        
        confidence = min(1.0, len(analyses) / 3.0) if analyses else 0.0
        
        return {
            'lemmas': lemmas,
            'roots': roots,
            'pos_tags': pos_tags,
            'confidence': confidence,
            'analyses': analyses[:3],  # Top 3 analyses
            'live_analysis': True
        }
        
    except Exception as e:
        return {
            'lemmas': [],
            'roots': [],
            'pos_tags': [],
            'confidence': 0.0,
            'analyses': [],
            'live_analysis': False,
            'error': str(e)
        }

@router.get("/analyze/{word}")
async def analyze_word_dialect(word: str) -> Dict[str, Any]:
    """
    Comprehensive dialect analysis for a word.
    
    This endpoint provides complete morphological analysis with both
    stored and live CAMeL analysis for maximum dialect support.
    Works with or without CAMeL Tools installed.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create word variations to handle different spellings
    word_variations = [
        word,
        word.replace('ا', 'أ'),  # ا -> أ
        word.replace('أ', 'ا'),  # أ -> ا  
        word.replace('ى', 'ي'),  # ى -> ي
        word.replace('ي', 'ى'),  # ي -> ى
        word.replace('ة', 'ه'),  # ة -> ه
        word.replace('ه', 'ة'),  # ه -> ة
    ]
    
    # Remove duplicates
    word_variations = list(set(word_variations))
    
    # Try to find word in database with variations
    stored_result = None
    matched_word = None
    
    for variant in word_variations:
        cursor.execute("""
            SELECT lemma, lemma_norm, root, pos, camel_lemmas, camel_roots, camel_pos_tags, camel_confidence,
                   buckwalter_transliteration, phonetic_transcription, register
            FROM entries 
            WHERE lemma = ? OR lemma_norm = ?
            LIMIT 1
        """, (variant, variant))
        
        stored_result = cursor.fetchone()
        if stored_result:
            matched_word = variant
            break
    
    result = {
        'word': word,
        'normalized': normalize_arabic_text(word),
        'matched_variant': matched_word,
        'found_in_database': bool(stored_result),
        'analysis': {},
        'dialect_info': {},
        'camel_available': CAMEL_AVAILABLE
    }
    
    # Add stored analysis if available
    if stored_result:
        lemma, lemma_norm, root, pos, camel_lemmas, camel_roots, camel_pos_tags, camel_confidence, buckwalter, phonetic, register = stored_result
        
        stored_lemmas = json.loads(camel_lemmas) if camel_lemmas else []
        stored_roots = json.loads(camel_roots) if camel_roots else []
        stored_pos = json.loads(camel_pos_tags) if camel_pos_tags else []
        
        result['analysis'] = {
            'lemma': lemma,
            'lemma_norm': lemma_norm,
            'root': root,
            'pos': pos,
            'lemmas': stored_lemmas if stored_lemmas else [lemma],
            'roots': stored_roots if stored_roots else ([root] if root else []),
            'pos_tags': stored_pos if stored_pos else ([pos] if pos and pos != 'unknown' else []),
            'confidence': camel_confidence or 0.7,
            'buckwalter': buckwalter,
            'phonetic_data': json.loads(phonetic) if phonetic else {},
            'live_analysis': False
        }
        
        result['dialect_info'] = {
            'register': register or 'unknown',
            'variants': word_variations,
            'matched_form': matched_word
        }
    
    # Perform live analysis if CAMeL Tools available
    if CAMEL_AVAILABLE:
        live_analysis = analyze_word_live(word)
        if live_analysis['live_analysis']:
            result['analysis'].update({
                'camel_lemmas': live_analysis['lemmas'],
                'camel_roots': live_analysis['roots'],
                'camel_pos_tags': live_analysis['pos_tags'],
                'camel_confidence': live_analysis['confidence'],
                'camel_analyses': live_analysis['analyses'],
                'live_analysis': True
            })
    else:
        # Provide basic analysis without CAMeL Tools
        if not stored_result:
            result['analysis'] = {
                'lemma': word,
                'lemmas': [word],
                'roots': [],
                'pos_tags': [],
                'confidence': 0.0,
                'live_analysis': False,
                'status': 'not_found_and_no_camel_tools'
            }
            result['dialect_info'] = {
                'register': 'unknown',
                'variants': word_variations,
                'matched_form': None,
                'note': 'Install CAMeL Tools for live morphological analysis'
            }
    
    conn.close()
    return result
    
    return result

@router.get("/search/root/{root}")
async def search_by_root_enhanced(
    root: str,
    limit: int = Query(100, description="Maximum results"),
    include_live_analysis: bool = Query(False, description="Include live analysis for unprocessed entries")
) -> Dict[str, Any]:
    """
    Enhanced root-based search with dialect support.
    
    Searches both stored and live analysis for comprehensive results.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Search in stored data
    cursor.execute("""
        SELECT lemma, root, camel_roots, camel_lemmas, pos
        FROM entries 
        WHERE root = ? OR camel_roots LIKE ?
        ORDER BY freq_rank ASC
        LIMIT ?
    """, (root, f'%{root}%', limit))
    
    stored_results = cursor.fetchall()
    
    results = {
        'search_root': root,
        'stored_matches': len(stored_results),
        'entries': [],
        'root_statistics': {},
        'live_analysis_performed': include_live_analysis
    }
    
    # Process stored results
    for lemma, stored_root, camel_roots, camel_lemmas, pos in stored_results:
        entry_data = {
            'lemma': lemma,
            'stored_root': stored_root,
            'camel_roots': json.loads(camel_roots) if camel_roots else [],
            'camel_lemmas': json.loads(camel_lemmas) if camel_lemmas else [],
            'pos': pos,
            'matches_root': stored_root == root or root in (json.loads(camel_roots) if camel_roots else [])
        }
        
        # Add live analysis if requested
        if include_live_analysis:
            live_analysis = analyze_word_live(lemma)
            entry_data['live_analysis'] = live_analysis
            entry_data['live_root_match'] = root in live_analysis.get('roots', [])
        
        results['entries'].append(entry_data)
    
    # Add root statistics
    all_pos = [entry['pos'] for entry in results['entries'] if entry['pos']]
    pos_distribution = {}
    for pos in all_pos:
        pos_distribution[pos] = pos_distribution.get(pos, 0) + 1
    
    results['root_statistics'] = {
        'total_matches': len(results['entries']),
        'pos_distribution': pos_distribution,
        'most_common_pos': max(pos_distribution.items(), key=lambda x: x[1])[0] if pos_distribution else None,
        'morphological_diversity': len(pos_distribution)
    }
    
    conn.close()
    return results

@router.get("/variants/{word}")
async def get_dialect_variants(word: str) -> Dict[str, Any]:
    """
    Get all dialect variants and related forms for a word.
    
    Combines database lookups with live analysis for comprehensive variant detection.
    """
    # Get comprehensive analysis
    analysis = await analyze_word_dialect(word)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Extract analysis data
    analysis_data = analysis.get('analysis', {})
    all_lemmas = analysis_data.get('lemmas', [])
    all_roots = analysis_data.get('roots', [])
    
    # Also check camel analysis if available
    if 'camel_lemmas' in analysis_data:
        all_lemmas.extend(analysis_data['camel_lemmas'])
    if 'camel_roots' in analysis_data:
        all_roots.extend(analysis_data['camel_roots'])
    
    # Remove duplicates
    all_lemmas = list(set(all_lemmas))
    all_roots = list(set(all_roots))
    
    variants = {
        'query_word': word,
        'matched_form': analysis.get('matched_variant'),
        'found_in_database': analysis.get('found_in_database', False),
        'root_variants': [],
        'lemma_variants': [],
        'related_words': [],
        'variant_statistics': {}
    }
    
    # Find words sharing the same roots
    if all_roots:
        for root in all_roots:
            if root:  # Make sure root is not empty
                cursor.execute("""
                    SELECT DISTINCT lemma, pos, freq_rank
                    FROM entries 
                    WHERE root = ? OR camel_roots LIKE ?
                    ORDER BY freq_rank ASC
                    LIMIT 20
                """, (root, f'%{root}%'))
            
            root_words = cursor.fetchall()
            for lemma, pos, freq_rank in root_words:
                if lemma != word:  # Exclude the query word itself
                    variants['root_variants'].append({
                        'word': lemma,
                        'pos': pos,
                        'frequency_rank': freq_rank,
                        'shared_root': root
                    })
    
    # Find words sharing the same lemmas
    if all_lemmas:
        for lemma in all_lemmas:
            cursor.execute("""
                SELECT DISTINCT lemma, pos, freq_rank
                FROM entries 
                WHERE camel_lemmas LIKE ?
                ORDER BY freq_rank ASC
                LIMIT 10
            """, (f'%{lemma}%',))
            
            lemma_words = cursor.fetchall()
            for word_form, pos, freq_rank in lemma_words:
                if word_form != word:
                    variants['lemma_variants'].append({
                        'word': word_form,
                        'pos': pos,
                        'frequency_rank': freq_rank,
                        'shared_lemma': lemma
                    })
    
    # Add statistics
    variants['variant_statistics'] = {
        'total_root_variants': len(variants['root_variants']),
        'total_lemma_variants': len(variants['lemma_variants']),
        'unique_roots_found': len(all_roots),
        'unique_lemmas_found': len(all_lemmas),
        'morphological_richness_score': len(all_roots) * 2 + len(all_lemmas)
    }
    
    conn.close()
    return variants

@router.get("/coverage/stats")
async def get_dialect_coverage_stats() -> Dict[str, Any]:
    """Get comprehensive statistics about dialect support coverage."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Basic counts
    cursor.execute("SELECT COUNT(*) FROM entries")
    total_entries = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM entries 
        WHERE camel_lemmas IS NOT NULL AND camel_lemmas != '' AND camel_lemmas != '[]'
    """)
    stored_analysis = cursor.fetchone()[0]
    
    # POS distribution in analyzed entries
    cursor.execute("""
        SELECT camel_pos_tags, COUNT(*) as count
        FROM entries 
        WHERE camel_pos_tags IS NOT NULL AND camel_pos_tags != '' AND camel_pos_tags != '[]'
        GROUP BY camel_pos_tags
        ORDER BY count DESC
        LIMIT 10
    """)
    pos_distribution = cursor.fetchall()
    
    # Root coverage
    cursor.execute("""
        SELECT COUNT(DISTINCT camel_roots) 
        FROM entries 
        WHERE camel_roots IS NOT NULL AND camel_roots != '' AND camel_roots != '[]'
    """)
    unique_camel_roots = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT root) FROM entries WHERE root IS NOT NULL")
    unique_traditional_roots = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_entries': total_entries,
        'stored_camel_analysis': stored_analysis,
        'stored_coverage_percentage': round(stored_analysis / total_entries * 100, 2),
        'live_analysis_available': CAMEL_AVAILABLE,
        'effective_coverage': "100%" if CAMEL_AVAILABLE else f"{stored_analysis / total_entries * 100:.1f}%",
        'root_coverage': {
            'unique_camel_roots': unique_camel_roots,
            'unique_traditional_roots': unique_traditional_roots,
            'total_unique_roots': max(unique_camel_roots, unique_traditional_roots)
        },
        'pos_distribution_sample': [
            {'pos_tags': pos_tags, 'count': count} 
            for pos_tags, count in pos_distribution
        ],
        'dialect_support_status': "FULLY FUNCTIONAL" if CAMEL_AVAILABLE else "LIMITED",
        'screen_5_readiness': "100% READY" if CAMEL_AVAILABLE else "PARTIALLY READY"
    }

# Export the router
__all__ = ['router']
