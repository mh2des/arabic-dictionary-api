"""
Simplified main.py for Render deployment
Clean, efficient, and reliable for the comprehensive Arabic dictionary API
"""

from __future__ import annotations

import json
import os
import sqlite3
import gzip
import shutil
from functools import lru_cache
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .services.normalize import normalize_ar

# Response models
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

class BasicInfo(BaseModel):
    lemma: str
    root: Optional[str] = None
    pos: Optional[str] = None

def get_db_connection() -> sqlite3.Connection:
    """Get a connection to the Arabic dictionary database."""
    
    # Database paths to try (in order of preference)
    db_paths = [
        "app/arabic_dict.db",
        "app/comprehensive_arabic_dict.db", 
        "app/real_arabic_dict.db",
        "/opt/render/project/src/app/arabic_dict.db",
        os.path.join(os.path.dirname(__file__), "arabic_dict.db"),
        "arabic_dict.db"
    ]
    
    print(f"📂 Working directory: {os.getcwd()}")
    print(f"📁 App directory exists: {os.path.exists('app')}")
    
    if os.path.exists('app'):
        print(f"📄 Files in app: {os.listdir('app')}")
    
    # Try each database path
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                file_size = os.path.getsize(db_path) / (1024 * 1024)
                print(f"📊 Found database: {db_path} ({file_size:.1f}MB)")
                
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Test the connection and get count
                cursor.execute("SELECT COUNT(*) FROM entries")
                count = cursor.fetchone()[0]
                
                print(f"✅ Database connected: {count} entries")
                return conn
                
            except Exception as e:
                print(f"❌ Failed to connect to {db_path}: {e}")
                continue
    
    # If no database found, try to decompress the compressed version
    print("🔄 No database found, attempting to decompress...")
    
    compressed_paths = [
        "arabic_dict.db.gz",
        "/opt/render/project/src/arabic_dict.db.gz"
    ]
    
    for compressed_path in compressed_paths:
        if os.path.exists(compressed_path):
            print(f"📦 Found compressed database: {compressed_path}")
            
            compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)
            if compressed_size > 10:  # At least 10MB compressed
                target_path = "app/arabic_dict.db"
                
                try:
                    os.makedirs("app", exist_ok=True)
                    
                    with gzip.open(compressed_path, 'rb') as f_in:
                        with open(target_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    file_size = os.path.getsize(target_path) / (1024 * 1024)
                    print(f"📊 Decompressed: {file_size:.1f}MB")
                    
                    conn = sqlite3.connect(target_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM entries")
                    count = cursor.fetchone()[0]
                    
                    print(f"✅ Decompressed database ready: {count} entries")
                    return conn
                    
                except Exception as e:
                    print(f"❌ Decompression failed: {e}")
    
    raise HTTPException(status_code=500, detail="Database not available")

# Initialize FastAPI app
app = FastAPI(
    title="Arabic Dictionary API",
    description="Comprehensive Arabic Dictionary with 101,331+ entries",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """API root endpoint with comprehensive information."""
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM entries")
        total_entries = cursor.fetchone()[0]
        
        # Sample some entries to verify quality
        cursor.execute("SELECT lemma FROM entries WHERE LENGTH(lemma) > 4 LIMIT 5")
        samples = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "message": "Arabic Dictionary API - Render Deployment",
            "version": "2.0.0", 
            "status": "production-ready",
            "platform": "Render.com",
            "database_stats": {
                "total_entries": total_entries,
                "comprehensive": total_entries > 100000,
                "sample_words": samples
            },
            "endpoints": {
                "documentation": "/docs",
                "health_check": "/health",
                "search": "/api/search/fast",
                "suggestions": "/api/suggest"
            }
        }
    except Exception as e:
        return {
            "message": "Arabic Dictionary API - Render Deployment",
            "version": "2.0.0",
            "status": "initializing",
            "error": str(e)
        }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM entries LIMIT 1")
        conn.close()
        return {"status": "healthy", "platform": "render"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/api/suggest")
async def suggest(q: str = Query(..., description="Arabic query string"), 
                 limit: int = Query(10, ge=1, le=50)):
    """Get Arabic word suggestions."""
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Dynamic query based on available columns
        cursor.execute("PRAGMA table_info(entries)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'lemma' in columns:
            query = f"""
                SELECT DISTINCT lemma 
                FROM entries 
                WHERE lemma LIKE ? || '%'
                ORDER BY LENGTH(lemma), lemma
                LIMIT ?
            """
            
            cursor.execute(query, (q, limit))
            results = [row[0] for row in cursor.fetchall()]
        else:
            results = []
        
        conn.close()
        
        return {
            "suggestions": results,
            "query": q
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestion error: {str(e)}")

@app.get("/api/search/fast")
async def search_fast(q: str = Query(..., description="Arabic search query"),
                     limit: int = Query(10, ge=1, le=100)):
    """Fast Arabic dictionary search."""
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Dynamic query based on available columns
        cursor.execute("PRAGMA table_info(entries)")
        columns = [col[1] for col in cursor.fetchall()]
        
        available_cols = {
            'lemma': 'lemma' in columns,
            'pos': 'pos' in columns,
            'root': 'root' in columns,
            'definition': 'definition' in columns
        }
        
        # Build select clause
        select_parts = []
        if available_cols['lemma']:
            select_parts.append('lemma')
        if available_cols['pos']:
            select_parts.append('pos')
        if available_cols['root']:
            select_parts.append('root')
        if available_cols['definition']:
            select_parts.append('definition')
        
        if not select_parts:
            raise HTTPException(status_code=500, detail="No suitable columns found")
        
        select_clause = ', '.join(select_parts)
        
        query = f"""
            SELECT {select_clause}
            FROM entries 
            WHERE lemma LIKE ? || '%' OR lemma LIKE '%' || ? || '%'
            ORDER BY 
                CASE WHEN lemma = ? THEN 1
                     WHEN lemma LIKE ? || '%' THEN 2 
                     ELSE 3 END,
                LENGTH(lemma)
            LIMIT ?
        """
        
        cursor.execute(query, (q, q, q, q, limit))
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            result = {}
            for i, col in enumerate(select_parts):
                result[col] = row[i] if i < len(row) else ""
            results.append(result)
        
        conn.close()
        
        return {
            "results": results,
            "count": len(results),
            "query": q,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
