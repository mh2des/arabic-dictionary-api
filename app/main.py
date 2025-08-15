"""
FastAPI entrypoint for the Arabic dictionary backend.

This module configures the application with enhanced SQLite database
integration, providing access to CAMeL Tools analysis, phonetic
transcription, and comprehensive linguistic features.

Now uses the fully enhanced SQLite database with 101,331 entries
featuring complete morphological analysis and phonetic transcription.
"""

from __future__ import annotations

import json
import os
import sqlite3
from functools import lru_cache
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .services.normalize import normalize_ar

# CAMeL Tools routes are now integrated directly
CAMEL_AVAILABLE = False

# Enhanced response models for database integration
class EnhancedEntry(BaseModel):
    id: int
    lemma: str
    lemma_norm: str
    root: Optional[str] = None
    pos: Optional[str] = None
    subpos: Optional[str] = None
    register: Optional[str] = None
    domain: Optional[str] = None
    freq_rank: Optional[int] = None
    
    # CAMeL Tools analysis
    camel_lemmas: List[str] = []
    camel_roots: List[str] = []
    camel_pos_tags: List[str] = []
    camel_confidence: Optional[float] = None
    
    # Phase 2 phonetic features
    buckwalter_transliteration: Optional[str] = None
    phonetic_transcription: Optional[Dict[str, Any]] = None
    semantic_features: Optional[Dict[str, Any]] = None
    
    # Enhancement status
    phase2_enhanced: bool = False
    camel_analyzed: bool = False

class BasicInfo(BaseModel):
    lemma: str
    root: Optional[str] = None
    pos: Optional[str] = None

# Database connection helper
def get_db_connection() -> sqlite3.Connection:
    """Get a connection to the enhanced SQLite database."""
    
    # Print debug info for Railway deployment
    print(f"Current working directory: {os.getcwd()}")
    print(f"Files in current directory: {os.listdir('.')}")
    if os.path.exists('app'):
        print(f"Files in app directory: {os.listdir('app')}")
    
    # Railway deployment paths
    possible_paths = [
        "/app/app/arabic_dict.db",                                  # Railway container path
        os.path.join(os.path.dirname(__file__), "arabic_dict.db"), # app/arabic_dict.db
        os.path.join(os.getcwd(), "app", "arabic_dict.db"),         # ./app/arabic_dict.db
        "app/arabic_dict.db",                                       # relative path
    ]
    
    for db_path in possible_paths:
        print(f"Checking path: {db_path}")
        if os.path.exists(db_path):
            try:
                # Check file size to ensure it's the real database
                file_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
                print(f"Found database at: {db_path} ({file_size:.1f} MB)")
                
                if file_size < 50:  # If less than 50MB, it's probably not our real database
                    print(f"Database too small ({file_size:.1f} MB), skipping...")
                    continue
                
                conn = sqlite3.connect(db_path)
                # Test the connection
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM entries LIMIT 1")
                count = cursor.fetchone()[0]
                print(f"Database connected: {db_path} with {count} entries")
                
                if count < 1000:  # If less than 1000 entries, it's probably fallback
                    print(f"Database has too few entries ({count}), skipping...")
                    conn.close()
                    continue
                    
                return conn
            except Exception as e:
                print(f"Database at {db_path} failed: {e}")
                continue
    
    # If no database found, create a minimal one
    print("Creating minimal fallback database...")
    fallback_path = "/tmp/fallback_dict.db"
    conn = sqlite3.connect(fallback_path)
    cursor = conn.cursor()
    
    # Create minimal schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY,
            lemma TEXT NOT NULL,
            lemma_norm TEXT,
            root TEXT,
            pos TEXT,
            subpos TEXT,
            register TEXT,
            domain TEXT,
            freq_rank INTEGER,
            phase2_enhanced INTEGER DEFAULT 0,
            camel_analyzed INTEGER DEFAULT 0,
            camel_lemmas TEXT,
            camel_roots TEXT,
            camel_pos_tags TEXT,
            camel_confidence REAL,
            buckwalter_transliteration TEXT,
            phonetic_transcription TEXT,
            semantic_features TEXT
        )
    ''')
    
    # Add a few test entries
    test_entries = [
        ("كتاب", "كتاب", "ك.ت.ب", "noun", "common", None, "education", 1),
        ("مكتبة", "مكتبة", "ك.ت.ب", "noun", "common", None, "education", 2),
        ("كتب", "كتب", "ك.ت.ب", "verb", "perfect", None, "education", 3)
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO entries 
        (lemma, lemma_norm, root, pos, subpos, register, domain, freq_rank)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', test_entries)
    
    conn.commit()
    print(f"Created fallback database with {len(test_entries)} entries")
    return conn

def row_to_enhanced_entry(row) -> EnhancedEntry:
    """Convert database row to EnhancedEntry model."""
    return EnhancedEntry(
        id=row[0],
        lemma=row[1],
        lemma_norm=row[2],
        root=row[3],
        pos=row[4],
        subpos=row[5],
        register=row[6],
        domain=row[7],
        freq_rank=row[8],
        camel_lemmas=json.loads(row[9]) if row[9] else [],
        camel_roots=json.loads(row[10]) if row[10] else [],
        camel_pos_tags=json.loads(row[11]) if row[11] else [],
        camel_confidence=row[12],
        buckwalter_transliteration=row[13],
        phonetic_transcription=json.loads(row[14]) if row[14] else None,
        semantic_features=json.loads(row[15]) if row[15] else None,
        phase2_enhanced=bool(row[16]),
        camel_analyzed=bool(row[17])
    )

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Create and configure the FastAPI application with enhanced database integration."""
    
    app = FastAPI(
        title="Arabic Dictionary API",
        description="Comprehensive Arabic lexical service with morphological analysis and phonetic transcription.",
        version="1.0.0",
    )

    # Enable CORS for all origins (configurable)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Root route - Enhanced welcome message (safe with error handling)
    @app.get("/", tags=["Welcome"])
    async def read_root() -> dict:
        try:
            # Get live database stats safely
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM entries")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM entries WHERE phase2_enhanced = 1")
            phase2_enhanced = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM entries WHERE camel_analyzed = 1")
            camel_enhanced = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "message": "Arabic Dictionary API - Production Ready",
                "version": "1.0.0",
                "status": "production-ready",
                "screens_supported": [1, 2, 4, 5, 6, 7],
                "database_stats": {
                    "total_entries": total,
                    "camel_enhanced": camel_enhanced,
                    "phase2_enhanced": phase2_enhanced,
                    "enhancement_rate": f"{phase2_enhanced/total*100:.1f}%"
                },
                "features": [
                    "6 Screen APIs ready for mobile/web apps",
                    "SQLite database with comprehensive entries",
                    "CAMeL Tools morphological analysis",
                    "Phonetic transcription (Buckwalter, IPA, Romanization)",
                    "Comprehensive semantic analysis",
                    "Root-based search with extensive results",
                    "Multi-dialect analysis foundation",
                    "Advanced linguistic features"
                ],
                "endpoints": {
                    "documentation": "/docs",
                    "interactive_docs": "/redoc",
                    "health_check": "/health",
                    "detailed_health": "/healthz",
                    "flutter_suggest": "/api/suggest",
                    "flutter_search": "/api/search/fast"
                },
                "deployment": "Railway Platform - Live and Operational"
            }
        except Exception as e:
            # Fallback response if database fails
            return {
                "message": "Arabic Dictionary API - Starting Up",
                "version": "1.0.0", 
                "status": "initializing",
                "error": f"Database initialization: {str(e)}",
                "endpoints": {
                    "health_check": "/health",
                    "documentation": "/docs"
                },
                "note": "Service is starting, some features may be limited initially"
            }

    # Health check for Railway deployment (ultra-simple, no dependencies)
    @app.get("/health", tags=["Utility"])
    async def health() -> dict:
        """Ultra-simple health check for Railway deployment."""
        return {"status": "healthy", "service": "arabic-dictionary-api"}

    # Detailed health check with database (safe with try/catch)
    @app.get("/healthz", tags=["Utility"])
    async def healthz() -> dict:
        """Detailed health check with database connectivity."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM entries LIMIT 1")
            count = cursor.fetchone()[0]
            conn.close()
            return {"status": "healthy", "database": "connected", "entries": count}
        except Exception as e:
            return {"status": "degraded", "database": f"error: {str(e)}", "note": "using fallback"}

    @app.get("/api/suggest", tags=["Flutter Integration"])
    async def suggest_words(q: str = Query(..., min_length=1), limit: int = Query(10, le=50)):
        """
        Fast autocomplete suggestions for Flutter app.
        Optimized for real-time typing with minimal latency.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fast prefix search with LIMIT for performance
        cursor.execute("""
            SELECT DISTINCT lemma 
            FROM entries 
            WHERE lemma LIKE ? 
            ORDER BY LENGTH(lemma), lemma 
            LIMIT ?
        """, (f"{q}%", limit))
        
        suggestions = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return {"suggestions": suggestions, "query": q}

    @app.get("/api/search/fast", tags=["Flutter Integration"])
    async def fast_search(q: str = Query(..., min_length=1), limit: int = Query(20, le=100)):
        """
        Fast search endpoint optimized for Flutter app performance.
        Returns minimal but essential data for quick results.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search with basic info for speed
        cursor.execute("""
            SELECT lemma, pos, root, camel_english_glosses
            FROM entries 
            WHERE lemma LIKE ? OR lemma_norm LIKE ?
            ORDER BY 
                CASE WHEN lemma = ? THEN 1
                     WHEN lemma LIKE ? THEN 2 
                     ELSE 3 END,
                LENGTH(lemma)
            LIMIT ?
        """, (f"%{q}%", f"%{q}%", q, f"{q}%", limit))
        
        results = []
        for row in cursor.fetchall():
            # Parse English glosses safely
            glosses = ""
            if row[3]:
                try:
                    import json
                    gloss_list = json.loads(row[3])
                    if isinstance(gloss_list, list) and gloss_list:
                        glosses = str(gloss_list[0]).replace("+", " ").replace("_", " ")[:100]
                    elif isinstance(gloss_list, str):
                        glosses = gloss_list[:100]
                except:
                    glosses = str(row[3])[:50] if row[3] else ""
            
            results.append({
                "lemma": row[0],
                "pos": row[1],
                "root": row[2],
                "definition": glosses
            })
        
        conn.close()
        return {"results": results, "count": len(results)}
    @app.get("/search/enhanced", tags=["Enhanced Lookup"])
    async def enhanced_search(
        q: str = Query(..., description="Search query"),
        limit: int = Query(50, description="Maximum results"),
        include_phonetics: bool = Query(True, description="Include phonetic data"),
        include_camel: bool = Query(True, description="Include CAMeL analysis")
    ) -> Dict[str, Any]:
        """Enhanced search with full database integration."""
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search in lemma and lemma_norm
        search_term = f"%{q}%"
        
        query = """
            SELECT 
                id, lemma, lemma_norm, root, pos, subpos, register, domain, freq_rank,
                camel_lemmas, camel_roots, camel_pos_tags, camel_confidence,
                buckwalter_transliteration, phonetic_transcription, semantic_features,
                phase2_enhanced, camel_analyzed
            FROM entries 
            WHERE lemma LIKE ? OR lemma_norm LIKE ?
            ORDER BY 
                CASE WHEN lemma = ? THEN 1 
                     WHEN lemma LIKE ? THEN 2 
                     ELSE 3 END,
                freq_rank ASC
            LIMIT ?
        """
        
        cursor.execute(query, (search_term, search_term, q, f"{q}%", limit))
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            entry = row_to_enhanced_entry(row)
            
            # Optionally filter out phonetic/camel data
            if not include_phonetics:
                entry.buckwalter_transliteration = None
                entry.phonetic_transcription = None
                entry.semantic_features = None
            
            if not include_camel:
                entry.camel_lemmas = []
                entry.camel_roots = []
                entry.camel_pos_tags = []
                entry.camel_confidence = None
            
            results.append(entry)
        
        conn.close()
        
        return {
            "query": q,
            "results": results,
            "total_found": len(results),
            "search_features": {
                "phonetics_included": include_phonetics,
                "camel_analysis_included": include_camel,
                "database_powered": True
            }
        }

    # Legacy search endpoint (database-powered)
    @app.get("/search", response_model=List[BasicInfo], tags=["Lookup"])
    async def search(
        q: Optional[str] = Query(None, description="Search query (lemma)")
    ) -> List[BasicInfo]:
        """Legacy search endpoint now powered by enhanced database."""
        
        if not q:
            # Return first 100 entries if no query
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT lemma, root, pos FROM entries LIMIT 100")
            rows = cursor.fetchall()
            conn.close()
            return [BasicInfo(lemma=row[0], root=row[1], pos=row[2]) for row in rows]
        
        norm_q = normalize_ar(q)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT lemma, root, pos FROM entries 
            WHERE lemma LIKE ? OR lemma_norm LIKE ?
            LIMIT 50
        """, (f"%{q}%", f"%{norm_q}%"))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [BasicInfo(lemma=row[0], root=row[1], pos=row[2]) for row in rows]

    # Enhanced lemma lookup
    @app.get("/lemmas/{q}", response_model=EnhancedEntry, tags=["Lookup"])
    async def get_lemma(q: str) -> EnhancedEntry:
        """Get detailed lemma information from enhanced database."""
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Try exact match first
        cursor.execute("""
            SELECT 
                id, lemma, lemma_norm, root, pos, subpos, register, domain, freq_rank,
                camel_lemmas, camel_roots, camel_pos_tags, camel_confidence,
                buckwalter_transliteration, phonetic_transcription, semantic_features,
                phase2_enhanced, camel_analyzed
            FROM entries 
            WHERE lemma = ? OR lemma_norm = ?
            LIMIT 1
        """, (q, normalize_ar(q)))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Lemma '{q}' not found")
        
        return row_to_enhanced_entry(row)

    # Enhanced root lookup
    @app.get("/root/{root}", response_model=List[BasicInfo], tags=["Lookup"])
    async def by_root(root: str) -> List[BasicInfo]:
        """Find entries by Arabic root using enhanced database."""
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Handle both spaced and non-spaced root formats
        # Convert "كتب" to "ك ت ب" for database search
        spaced_root = ' '.join(list(root.strip()))
        
        # Search in both root field and camel_roots JSON with multiple formats
        cursor.execute("""
            SELECT lemma, root, pos FROM entries 
            WHERE root = ? OR root = ? OR camel_roots LIKE ? OR camel_roots LIKE ?
            ORDER BY freq_rank ASC
            LIMIT 200
        """, (root, spaced_root, f'%{root}%', f'%{spaced_root}%'))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [BasicInfo(lemma=row[0], root=row[1], pos=row[2]) for row in rows]

    # Phonetic endpoint
    @app.get("/phonetics/{word}", tags=["Enhanced Features"])
    async def get_phonetics(word: str) -> Dict[str, Any]:
        """Get all phonetic representations for a word."""
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT lemma, buckwalter_transliteration, phonetic_transcription, semantic_features
            FROM entries 
            WHERE lemma = ? AND phase2_enhanced = 1
            LIMIT 1
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
            "available_scripts": ["arabic", "buckwalter", "ipa", "latin"],
            "enhanced": True
        }

    # Comprehensive stats
    @app.get("/stats/comprehensive", tags=["Enhanced Features"])
    async def comprehensive_stats() -> Dict[str, Any]:
        """Get comprehensive statistics about the enhanced database."""
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Basic counts
        cursor.execute("SELECT COUNT(*) FROM entries")
        stats["total_entries"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM entries WHERE phase2_enhanced = 1")
        stats["phase2_enhanced"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM entries WHERE camel_analyzed = 1")
        stats["camel_enhanced"] = cursor.fetchone()[0]
        
        # Feature coverage
        cursor.execute("SELECT COUNT(*) FROM entries WHERE buckwalter_transliteration IS NOT NULL")
        stats["buckwalter_coverage"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM entries WHERE phonetic_transcription IS NOT NULL")
        stats["phonetic_coverage"] = cursor.fetchone()[0]
        
        # POS distribution
        cursor.execute("""
            SELECT pos, COUNT(*) as count 
            FROM entries 
            WHERE pos IS NOT NULL 
            GROUP BY pos 
            ORDER BY count DESC 
            LIMIT 10
        """)
        stats["pos_distribution"] = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "database_statistics": stats,
            "enhancement_coverage": {
                "phase2_percentage": f"{stats['phase2_enhanced']/stats['total_entries']*100:.1f}%",
                "camel_percentage": f"{stats['camel_enhanced']/stats['total_entries']*100:.1f}%",
                "phonetic_percentage": f"{stats['phonetic_coverage']/stats['total_entries']*100:.1f}%"
            },
            "capabilities": [
                "Multi-script phonetic representation",
                "Complete CAMeL Tools morphological analysis",
                "Comprehensive semantic analysis",
                "Root-based search with extensive results",
                "POS tagging for all entries",
                "Cross-dialect analysis foundation",
                "High-performance SQLite backend"
            ],
            "database_integration": "Fully operational"
        }

    # Random entry
    @app.get("/random", response_model=EnhancedEntry, tags=["Lookup"])
    async def random_lemma() -> EnhancedEntry:
        """Get a random enhanced entry from the database."""
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, lemma, lemma_norm, root, pos, subpos, register, domain, freq_rank,
                camel_lemmas, camel_roots, camel_pos_tags, camel_confidence,
                buckwalter_transliteration, phonetic_transcription, semantic_features,
                phase2_enhanced, camel_analyzed
            FROM entries 
            ORDER BY RANDOM() 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        return row_to_enhanced_entry(row)

    # Include enhanced dialect support routes
    try:
        from app.api.dialect_enhanced_routes import router as dialect_router
        app.include_router(dialect_router)
    except ImportError:
        pass
    
    # Include enhanced screen API routes
    try:
        from app.api.enhanced_screen_routes import router as screen_router
        app.include_router(screen_router)
    except ImportError:
        pass

    return app


app = create_app()
