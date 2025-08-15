"""
Search Engine for Arabic Dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

High-performance search engine with full-text search, fuzzy matching,
and advanced Arabic text processing capabilities.
"""

import asyncio
import json
import sqlite3
import random
from typing import List, Optional, Dict, Any, Tuple, Iterable
from dataclasses import dataclass
from datetime import datetime

from .normalize import normalize_ar, normalize_search_query, get_orthographic_variants
from ..models import Entry, Info


@dataclass
class SearchResult:
    """Individual search result."""
    lemma: str
    lemma_norm: str
    data: Dict[str, Any]
    confidence: float
    sources: List[Dict[str, str]]
    rank_score: float = 0.0


@dataclass
class SearchResults:
    """Collection of search results with metadata."""
    results: List[SearchResult]
    total_count: int
    search_time_ms: float = 0.0


def simple_search(entries: Iterable[Entry], query: str) -> List[Info]:
    """Perform a naive search over the given entries.

    The search matches the query against the normalised lemma and
    glosses.  It returns the ``Info`` objects for each matching entry.
    """
    norm_q = normalize_ar(query)
    results: List[Info] = []
    for entry in entries:
        if norm_q in normalize_ar(entry.info.lemma_norm):
            results.append(entry.info)
            continue
        for sense in entry.senses or []:
            if (
                sense.gloss_ar_short and norm_q in normalize_ar(sense.gloss_ar_short)
            ) or (
                sense.gloss_en and norm_q.lower() in sense.gloss_en.lower()
            ):
                results.append(entry.info)
                break
    return results


class SearchEngine:
    """High-performance Arabic dictionary search engine."""
    
    def __init__(self, db_path: str, backend: str = "sqlite", db_url: Optional[str] = None):
        """
        Initialize search engine.
        
        Args:
            db_path: Path to SQLite database
            backend: Search backend type
            db_url: Database URL (optional)
        """
        self.db_path = db_path
        self.backend = backend
        self.db_url = db_url
        self.connection_pool = None
    
    async def initialize(self):
        """Initialize the search engine."""
        # Test database connection
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("SELECT COUNT(*) FROM entries LIMIT 1")
            print(f"Search engine initialized with database: {self.db_path}")
        except Exception as e:
            print(f"Warning: Could not connect to database {self.db_path}: {e}")
    
    async def close(self):
        """Close the search engine and cleanup resources."""
        pass
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def index(self, entries: Iterable[Entry]) -> None:
        """Index the provided entries into the search backend."""
        # TODO: implement indexing for SQLite FTS5 or PostgreSQL
        pass
    
    def query(self, query: str, limit: int = 10) -> List[Info]:
        """Run a search query and return ranked results."""
        # TODO: implement ranking logic
        raise NotImplementedError("Full search engine not yet implemented")
    
    async def search_exact(self, lemma_norm: str) -> List[SearchResult]:
        """
        Search for exact lemma matches.
        
        Args:
            lemma_norm: Normalized lemma to search for
            
        Returns:
            List of exact matches
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT lemma, lemma_norm, data, quality_confidence
                FROM entries 
                WHERE lemma_norm = ?
                ORDER BY quality_confidence DESC, freq_rank ASC
            """, (lemma_norm,))
            
            results = []
            for row in cursor.fetchall():
                try:
                    data = json.loads(row['data'])
                    result = SearchResult(
                        lemma=row['lemma'],
                        lemma_norm=row['lemma_norm'],
                        data=data,
                        confidence=row['quality_confidence'],
                        sources=data.get('sources', [])
                    )
                    results.append(result)
                except Exception as e:
                    print(f"Error parsing entry data: {e}")
                    continue
            
            return results
    
    async def search(
        self,
        query: str,
        pos_filter: Optional[str] = None,
        dialect_filter: Optional[str] = None,
        domain_filter: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResults:
        """
        Perform comprehensive search with filters.
        
        Args:
            query: Search query (normalized)
            pos_filter: Part of speech filter
            dialect_filter: Dialect filter
            domain_filter: Domain filter
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Search results with metadata
        """
        start_time = datetime.now()
        
        # Build search conditions
        conditions = []
        params = []
        
        # FTS search on multiple fields
        if query:
            conditions.append("""
                entries.id IN (
                    SELECT rowid FROM entries_fts 
                    WHERE entries_fts MATCH ?
                )
            """)
            # Create FTS query with field boosting
            fts_query = f'lemma_norm:{query}^3 OR gloss_en:{query}^2 OR gloss_ar_short:{query}^2 OR {query}'
            params.append(fts_query)
        
        # POS filter
        if pos_filter:
            conditions.append("pos LIKE ?")
            params.append(f"%{pos_filter}%")
        
        # Additional filters would be added here
        if domain_filter:
            conditions.append("domain = ?")
            params.append(domain_filter)
        
        # Build final query
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Count total results
        count_query = f"""
            SELECT COUNT(*) FROM entries 
            WHERE {where_clause}
        """
        
        # Main search query
        main_query = f"""
            SELECT lemma, lemma_norm, data, quality_confidence, freq_rank
            FROM entries 
            WHERE {where_clause}
            ORDER BY 
                quality_confidence DESC,
                freq_rank ASC,
                lemma_norm ASC
            LIMIT ? OFFSET ?
        """
        
        with self._get_connection() as conn:
            try:
                # Get total count
                total_count = conn.execute(count_query, params).fetchone()[0]
                
                # Get results
                cursor = conn.execute(main_query, params + [limit, offset])
                
                results = []
                for row in cursor.fetchall():
                    try:
                        data = json.loads(row['data'])
                        result = SearchResult(
                            lemma=row['lemma'],
                            lemma_norm=row['lemma_norm'],
                            data=data,
                            confidence=row['quality_confidence'],
                            sources=data.get('sources', []),
                            rank_score=self._calculate_rank_score(row, query)
                        )
                        results.append(result)
                    except Exception as e:
                        print(f"Error parsing search result: {e}")
                        continue
            except Exception as e:
                print(f"Search error: {e}")
                return SearchResults(results=[], total_count=0)
        
        # Re-sort by rank score
        results.sort(key=lambda x: x.rank_score, reverse=True)
        
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return SearchResults(
            results=results,
            total_count=total_count,
            search_time_ms=search_time
        )
    
    def _calculate_rank_score(self, row: sqlite3.Row, query: str) -> float:
        """Calculate ranking score for search result."""
        score = 0.0
        
        # Boost exact matches
        if row['lemma_norm'] == query:
            score += 10.0
        elif query in row['lemma_norm']:
            score += 5.0
        
        # Boost by confidence
        score += row['quality_confidence'] * 3.0
        
        # Boost by frequency (inverse of rank)
        if row['freq_rank']:
            score += max(0, 5.0 - (row['freq_rank'] / 1000))
        
        return score
    
    async def search_by_root(self, root: str, limit: int = 50) -> List[SearchResult]:
        """
        Search for lemmas by Arabic root.
        
        Args:
            root: Arabic root
            limit: Maximum number of results
            
        Returns:
            List of lemmas with the specified root
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT lemma, lemma_norm, data, quality_confidence
                FROM entries 
                WHERE root = ?
                ORDER BY quality_confidence DESC, freq_rank ASC
                LIMIT ?
            """, (root, limit))
            
            results = []
            for row in cursor.fetchall():
                try:
                    data = json.loads(row['data'])
                    result = SearchResult(
                        lemma=row['lemma'],
                        lemma_norm=row['lemma_norm'],
                        data=data,
                        confidence=row['quality_confidence'],
                        sources=data.get('sources', [])
                    )
                    results.append(result)
                except Exception as e:
                    print(f"Error parsing root search result: {e}")
                    continue
            
            return results
    
    async def get_random(
        self,
        pos_filter: Optional[str] = None,
        dialect_filter: Optional[str] = None
    ) -> Optional[SearchResult]:
        """
        Get a random lemma with optional filters.
        
        Args:
            pos_filter: Optional POS filter
            dialect_filter: Optional dialect filter
            
        Returns:
            Random lemma or None if no matches
        """
        conditions = []
        params = []
        
        if pos_filter:
            conditions.append("pos LIKE ?")
            params.append(f"%{pos_filter}%")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        with self._get_connection() as conn:
            # Get total count
            count = conn.execute(f"SELECT COUNT(*) FROM entries WHERE {where_clause}", params).fetchone()[0]
            
            if count == 0:
                return None
            
            # Get random offset
            random_offset = random.randint(0, count - 1)
            
            cursor = conn.execute(f"""
                SELECT lemma, lemma_norm, data, quality_confidence
                FROM entries 
                WHERE {where_clause}
                LIMIT 1 OFFSET ?
            """, params + [random_offset])
            
            row = cursor.fetchone()
            if row:
                try:
                    data = json.loads(row['data'])
                    return SearchResult(
                        lemma=row['lemma'],
                        lemma_norm=row['lemma_norm'],
                        data=data,
                        confidence=row['quality_confidence'],
                        sources=data.get('sources', [])
                    )
                except Exception as e:
                    print(f"Error parsing random result: {e}")
                    return None
            
            return None
    
    async def search_dialect(
        self,
        query: str,
        dialect_code: str,
        limit: int = 20
    ) -> SearchResults:
        """
        Search for lemmas in a specific dialect.
        
        Args:
            query: Search query
            dialect_code: Dialect code
            limit: Maximum number of results
            
        Returns:
            Search results filtered by dialect
        """
        # This is a simplified implementation
        # In practice, you'd want to search within dialect-specific fields
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT lemma, lemma_norm, data, quality_confidence
                FROM entries 
                WHERE lemma_norm LIKE ? OR lemma LIKE ?
                ORDER BY quality_confidence DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            results = []
            for row in cursor.fetchall():
                try:
                    data = json.loads(row['data'])
                    
                    # Check if entry has the requested dialect
                    dialects = data.get('dialects', [])
                    has_dialect = any(d.get('dialect') == dialect_code for d in dialects)
                    
                    if has_dialect or not dialects:  # Include if no dialect info
                        result = SearchResult(
                            lemma=row['lemma'],
                            lemma_norm=row['lemma_norm'],
                            data=data,
                            confidence=row['quality_confidence'],
                            sources=data.get('sources', [])
                        )
                        results.append(result)
                except Exception as e:
                    print(f"Error parsing dialect search result: {e}")
                    continue
            
            return SearchResults(
                results=results,
                total_count=len(results)
            )
