"""
ETL for Qutrub Conjugation Engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module extracts Arabic verb conjugation data from the Qutrub
open-source conjugation system. Qutrub provides comprehensive verb
conjugation tables for Arabic verbs across different forms, voices,
and persons.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Iterator, Dict, List, Optional, Any
from datetime import datetime

# Add Qutrub to Python path if available
def _add_qutrub_to_path(qutrub_dir: str):
    """Add Qutrub library to Python path."""
    if os.path.exists(qutrub_dir):
        libqutrub_path = os.path.join(qutrub_dir, 'libqutrub')
        if os.path.exists(libqutrub_path) and libqutrub_path not in sys.path:
            sys.path.insert(0, libqutrub_path)


def extract_verb_conjugations(qutrub_dir: str) -> Iterator[Dict[str, Any]]:
    """Extract verb conjugation data from Qutrub.
    
    Args:
        qutrub_dir: Path to Qutrub source directory
        
    Yields:
        Dictionaries containing verb conjugation information
    """
    # Add Qutrub to path
    _add_qutrub_to_path(qutrub_dir)
    
    try:
        # Try to import Qutrub modules
        import qutrub.verb_db as vdb
        import qutrub.ar_verb as arverb
        import qutrub.ar_verb_const as arc
    except ImportError as e:
        print(f"Warning: Could not import Qutrub modules: {e}")
        # Fall back to parsing data files directly
        yield from _extract_from_data_files(qutrub_dir)
        return
    
    # Get verb database
    try:
        verb_db = vdb.VerbDB()
        verbs = verb_db.get_all_verbs()
        
        for verb_tuple in verbs:
            try:
                # verb_tuple typically contains (id, verb, vocalized, root, form, type)
                if len(verb_tuple) >= 4:
                    verb_id, verb, vocalized, root = verb_tuple[:4]
                    
                    # Generate conjugation
                    conj_result = arverb.conjugate(verb)
                    
                    if conj_result:
                        yield {
                            'verb_id': verb_id,
                            'verb': verb,
                            'vocalized': vocalized,
                            'root': root,
                            'conjugation': conj_result,
                            'source': 'Qutrub'
                        }
                        
            except Exception as e:
                print(f"Error processing verb {verb_tuple}: {e}")
                continue
                
    except Exception as e:
        print(f"Error accessing Qutrub verb database: {e}")
        # Fall back to data files
        yield from _extract_from_data_files(qutrub_dir)


def _extract_from_data_files(qutrub_dir: str) -> Iterator[Dict[str, Any]]:
    """Extract verb data from Qutrub data files directly.
    
    Args:
        qutrub_dir: Path to Qutrub source directory
        
    Yields:
        Verb data dictionaries
    """
    data_dir = os.path.join(qutrub_dir, 'data')
    if not os.path.exists(data_dir):
        print(f"Warning: Qutrub data directory not found: {data_dir}")
        return
    
    # Look for verb data files
    verb_files = []
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if 'verb' in file.lower() and file.endswith(('.txt', '.csv', '.sql')):
                verb_files.append(os.path.join(root, file))
    
    for verb_file in verb_files:
        print(f"Processing Qutrub file: {verb_file}")
        yield from _parse_verb_file(verb_file)


def conjugate(lemma: str) -> Dict[str, Any]:
    """Return conjugation tables for the given verb.

    Returns a dictionary with keys such as 'past', 'present' and
    'imperative', each mapping person keys (e.g. '1sg', '2sg_m') to
    conjugated forms.  See the ``Inflection`` model for the expected
    shape.
    """
    # This is a simplified interface - in production you'd call Qutrub directly
    try:
        import qutrub.ar_verb as arverb
        return arverb.conjugate(lemma)
    except ImportError:
        print("Warning: Qutrub not available for conjugation")
        return {}


def _parse_verb_file(file_path: str) -> Iterator[Dict[str, Any]]:
    """Parse a Qutrub verb data file.
    
    Args:
        file_path: Path to verb data file
        
    Yields:
        Parsed verb data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Handle different file formats
            if file_path.endswith('.sql'):
                yield from _parse_sql_verbs(content)
            elif file_path.endswith('.csv'):
                yield from _parse_csv_verbs(content)
            else:
                yield from _parse_txt_verbs(content)
                
    except Exception as e:
        print(f"Error parsing verb file {file_path}: {e}")


def _parse_sql_verbs(content: str) -> Iterator[Dict[str, Any]]:
    """Parse SQL-format verb data."""
    import re
    
    # Look for INSERT statements
    insert_pattern = r"INSERT\s+INTO\s+\w+\s*\([^)]+\)\s*VALUES\s*\(([^)]+)\)"
    
    for match in re.finditer(insert_pattern, content, re.IGNORECASE):
        values_str = match.group(1)
        # Parse values (simplified - real implementation would need proper SQL parsing)
        values = [v.strip().strip("'\"") for v in values_str.split(',')]
        
        if len(values) >= 3:
            yield {
                'verb': values[0] if len(values) > 0 else '',
                'vocalized': values[1] if len(values) > 1 else '',
                'root': values[2] if len(values) > 2 else '',
                'source': 'Qutrub SQL'
            }


def _parse_csv_verbs(content: str) -> Iterator[Dict[str, Any]]:
    """Parse CSV-format verb data."""
    import csv
    import io
    
    reader = csv.reader(io.StringIO(content))
    
    # Skip header if present
    first_row = next(reader, None)
    if first_row and any('verb' in cell.lower() for cell in first_row):
        # This was a header row
        pass
    else:
        # Process first row as data
        if first_row and len(first_row) >= 3:
            yield {
                'verb': first_row[0],
                'vocalized': first_row[1] if len(first_row) > 1 else '',
                'root': first_row[2] if len(first_row) > 2 else '',
                'source': 'Qutrub CSV'
            }
    
    # Process remaining rows
    for row in reader:
        if len(row) >= 3:
            yield {
                'verb': row[0],
                'vocalized': row[1] if len(row) > 1 else '',
                'root': row[2] if len(row) > 2 else '',
                'source': 'Qutrub CSV'
            }


def _parse_txt_verbs(content: str) -> Iterator[Dict[str, Any]]:
    """Parse text-format verb data."""
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # Try different delimiters
        parts = None
        for delimiter in ['\t', '|', ';', ',']:
            if delimiter in line:
                parts = [p.strip() for p in line.split(delimiter)]
                break
        
        if parts and len(parts) >= 1:
            yield {
                'verb': parts[0],
                'vocalized': parts[1] if len(parts) > 1 else '',
                'root': parts[2] if len(parts) > 2 else '',
                'source': 'Qutrub TXT'
            }


def extract(source_dir: str) -> Iterator[Dict[str, Any]]:
    """Extract conjugation data from Qutrub source directory.
    
    Args:
        source_dir: Path to Qutrub source directory
        
    Yields:
        Entry dictionaries with inflection information
    """
    if not os.path.exists(source_dir):
        print(f"Warning: Qutrub source directory not found: {source_dir}")
        return
    
    count = 0
    for verb_data in extract_verb_conjugations(source_dir):
        entry = create_inflection_entry(verb_data)
        if entry:
            yield entry
            count += 1
            
            # Limit output for performance during development
            if count >= 1000:  # Remove this limit in production
                break
    
    print(f"Extracted {count} verb conjugations from Qutrub")


def create_inflection_entry(verb_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create an inflection entry from Qutrub verb data.
    
    Args:
        verb_data: Verb data dictionary from Qutrub
        
    Returns:
        Formatted entry with inflection information
    """
    from ..services.normalize import normalize_ar
    
    verb = verb_data.get('verb', '').strip()
    if not verb:
        return None
    
    verb_norm = normalize_ar(verb)
    root = normalize_ar(verb_data.get('root', ''))
    
    # Create basic info structure
    info = {
        'lemma': verb,
        'lemma_norm': verb_norm,
        'root': root,
        'pos': ['verb'],
        'quality': {
            'confidence': 0.7,
            'reviewed': False,
            'source_count': 1
        },
        'updated_at': datetime.now().isoformat()
    }
    
    # Create inflection data
    inflection = {}
    conjugation = verb_data.get('conjugation')
    
    if conjugation and isinstance(conjugation, dict):
        # Extract conjugation tables
        verb_tables = {}
        
        # Map Qutrub conjugation structure to our format
        if 'past' in conjugation:
            verb_tables['past'] = conjugation['past']
        if 'present' in conjugation:
            verb_tables['present'] = conjugation['present']
        if 'imperative' in conjugation:
            verb_tables['imperative'] = conjugation['imperative']
        
        if verb_tables:
            inflection['verb_tables'] = verb_tables
    
    # Create entry structure
    entry_data = {
        'info': info,
        'senses': [],
        'examples': [],
        'relations': {},
        'pronunciation': {},
        'dialects': [],
        'inflection': inflection,
        'derivations': {},
        'sources': [{
            'name': 'Qutrub',
            'license': 'GPL',
            'url': 'https://github.com/linuxscout/qutrub'
        }]
    }
    
    return entry_data
