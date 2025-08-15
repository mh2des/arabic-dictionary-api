"""
SQLite Database Extractor
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module extracts Arabic dictionary data from SQLite databases,
including the arabicdictionary.sqlite found in some linguistic resources.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Iterator, Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..models import Entry, Info, QualityMeta
from ..services.normalize import normalize_ar


def extract_from_sqlite_files(sqlite_dir: str) -> Iterator[Entry]:
    """Extract dictionary entries from SQLite database files.
    
    Args:
        sqlite_dir: Directory containing SQLite files
        
    Yields:
        Entry objects extracted from database content
    """
    for root, dirs, files in os.walk(sqlite_dir):
        for filename in files:
            if filename.endswith(('.sqlite', '.sqlite3', '.db')):
                filepath = os.path.join(root, filename)
                try:
                    yield from _extract_from_sqlite_file(filepath)
                except Exception as e:
                    print(f"Error processing SQLite file {filepath}: {e}")
                    continue


def _extract_from_sqlite_file(db_path: str) -> Iterator[Entry]:
    """Extract entries from a single SQLite database file."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found tables in {os.path.basename(db_path)}: {tables}")
        
        # Try to extract from different table patterns
        for table in tables:
            try:
                yield from _extract_from_table(cursor, table, db_path)
            except Exception as e:
                print(f"Error extracting from table {table}: {e}")
                continue
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"SQLite error in {db_path}: {e}")
    except Exception as e:
        print(f"Error reading SQLite file {db_path}: {e}")


def _extract_from_table(cursor: sqlite3.Cursor, table_name: str, db_path: str) -> Iterator[Entry]:
    """Extract entries from a specific table."""
    
    # Get table schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    
    print(f"Table {table_name} columns: {columns}")
    
    # Identify likely columns for word, definition, etc.
    word_columns = _identify_columns(columns, ['word', 'lemma', 'entry', 'headword', 'term', 'arabic', 'ar'])
    definition_columns = _identify_columns(columns, ['definition', 'meaning', 'gloss', 'translation', 'desc', 'english', 'en'])
    pos_columns = _identify_columns(columns, ['pos', 'part_of_speech', 'category', 'type', 'class', 'gram'])
    root_columns = _identify_columns(columns, ['root', 'radical', 'stem', 'base'])
    
    if not word_columns:
        print(f"No word columns found in table {table_name}")
        return
    
    # Build SELECT query
    select_columns = list(set(word_columns + definition_columns + pos_columns + root_columns))
    query = f"SELECT {', '.join(select_columns)} FROM {table_name}"
    
    try:
        cursor.execute(query)
        
        count = 0
        for row in cursor.fetchall():
            try:
                entry = _parse_sqlite_row(dict(row), word_columns, definition_columns, 
                                        pos_columns, root_columns, table_name, db_path)
                if entry:
                    yield entry
                    count += 1
            except Exception as e:
                continue
        
        print(f"Extracted {count} entries from table {table_name}")
        
    except sqlite3.Error as e:
        print(f"Error querying table {table_name}: {e}")


def _identify_columns(columns: List[str], keywords: List[str]) -> List[str]:
    """Identify columns that match given keywords."""
    matches = []
    columns_lower = [col.lower() for col in columns]
    
    for keyword in keywords:
        for i, col_lower in enumerate(columns_lower):
            if keyword in col_lower and columns[i] not in matches:
                matches.append(columns[i])
    
    return matches


def _parse_sqlite_row(row: Dict[str, Any], word_cols: List[str], def_cols: List[str], 
                     pos_cols: List[str], root_cols: List[str], table_name: str, db_path: str) -> Optional[Entry]:
    """Parse a database row into an Entry object."""
    
    # Extract word/lemma
    lemma = None
    for col in word_cols:
        if col in row and row[col]:
            text = str(row[col]).strip()
            if _is_arabic_word(text):
                lemma = text
                break
    
    if not lemma:
        return None
    
    # Extract definition
    definition = None
    for col in def_cols:
        if col in row and row[col]:
            definition = str(row[col]).strip()
            break
    
    # Extract POS
    pos = 'unknown'
    for col in pos_cols:
        if col in row and row[col]:
            pos = _normalize_pos(str(row[col]).strip())
            break
    
    # Extract root
    root = None
    for col in root_cols:
        if col in row and row[col]:
            root_text = str(row[col]).strip()
            if _is_arabic_word(root_text):
                root = normalize_ar(root_text)
                break
    
    return _create_sqlite_entry(lemma, definition, pos, root, table_name, db_path)


def _create_sqlite_entry(lemma: str, definition: Optional[str], pos: str, root: Optional[str], 
                        table_name: str, db_path: str) -> Optional[Entry]:
    """Create an Entry object from SQLite-extracted data."""
    
    if not lemma:
        return None
    
    lemma_norm = normalize_ar(lemma)
    if not lemma_norm:
        return None
    
    # Create Info object
    info = Info(
        lemma=lemma,
        lemma_norm=lemma_norm,
        root=root,
        pos=[pos] if pos else ['unknown'],
        quality=QualityMeta(confidence=0.8, reviewed=False, source_count=1),
        updated_at=datetime.now().isoformat()
    )
    
    # Create entry data
    info_dict = info.dict() if hasattr(info, 'dict') else info.__dict__
    if 'quality' in info_dict and info_dict['quality']:
        if hasattr(info_dict['quality'], 'dict'):
            info_dict['quality'] = info_dict['quality'].dict()
        elif hasattr(info_dict['quality'], '__dict__'):
            info_dict['quality'] = info_dict['quality'].__dict__
    
    senses = []
    if definition:
        senses.append({
            'id': f"{lemma_norm}_sqlite_1",
            'gloss_ar': definition if _contains_arabic(definition) else None,
            'gloss_en': definition if not _contains_arabic(definition) else None,
            'confidence': 0.8
        })
    
    entry_data = {
        'info': info_dict,
        'senses': senses,
        'examples': [],
        'relations': {},
        'pronunciation': {},
        'dialects': [],
        'inflection': {},
        'derivations': {},
        'sources': [{
            'name': f'SQLite Database ({table_name})',
            'license': 'Unknown',
            'url': db_path,
            'format': 'SQLite'
        }]
    }
    
    import json
    return Entry(
        info=info,
        data=json.dumps(entry_data, ensure_ascii=False)
    )


def _normalize_pos(pos_text: str) -> str:
    """Normalize part-of-speech tags."""
    pos = pos_text.lower().strip()
    
    pos_mappings = {
        'n': 'noun',
        'noun': 'noun',
        'اسم': 'noun',
        'v': 'verb',
        'verb': 'verb',
        'فعل': 'verb',
        'adj': 'adjective',
        'adjective': 'adjective',
        'صفة': 'adjective',
        'adv': 'adverb',
        'adverb': 'adverb',
        'ظرف': 'adverb',
        'prep': 'preposition',
        'preposition': 'preposition',
        'حرف جر': 'preposition',
        'conj': 'conjunction',
        'conjunction': 'conjunction',
        'حرف عطف': 'conjunction'
    }
    
    return pos_mappings.get(pos, pos)


def _is_arabic_word(text: str) -> bool:
    """Check if text contains Arabic characters and looks like a word."""
    if not text or len(text) < 2:
        return False
    
    # Check for Arabic Unicode range
    arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
    return arabic_chars >= 2 and arabic_chars / len(text) > 0.5


def _contains_arabic(text: str) -> bool:
    """Check if text contains any Arabic characters."""
    return any('\u0600' <= char <= '\u06FF' for char in text)
