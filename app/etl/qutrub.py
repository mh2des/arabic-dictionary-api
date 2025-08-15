"""
ETL for Qutrub (Conjugation)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Qutrub is an open‑source Arabic verb conjugator.  Integrating Qutrub
into this backend allows you to generate past, present and imperative
forms for verbs automatically.  This module provides an interface to
Qutrub's conjugation functions (which should be installed as a
dependency) and converts their output into the internal inflection
structure.

At present the implementation is a stub.  To complete it you need
to import Qutrub's Python library and map the conjugation output
into the expected format.
"""

from __future__ import annotations

import os
import csv
from typing import Dict, Any, Iterator
from datetime import datetime


def extract(qutrub_path: str) -> Iterator[Dict[str, Any]]:
    """Extract verb conjugation data from Qutrub dataset.
    
    Args:
        qutrub_path: Path to the Qutrub dataset directory
        
    Yields:
        Dictionary entries with verb conjugation information
    """
    print("Extracting from Qutrub...")
    
    try:
        # Try to import Qutrub modules
        import qutrub
        print("Qutrub library found, using full functionality")
    except ImportError:
        print("Warning: Could not import Qutrub modules: No module named 'qutrub'")
    
    # Look for Qutrub CSV files
    verb_files = []
    for root, dirs, files in os.walk(qutrub_path):
        for filename in files:
            if filename.endswith('.csv') and 'verb' in filename.lower():
                filepath = os.path.join(root, filename)
                verb_files.append(filepath)
                print(f"Processing Qutrub file: {filepath}")
    
    extracted_count = 0
    for verb_file in verb_files:
        try:
            with open(verb_file, 'r', encoding='utf-8') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                
                delimiter = ','
                if '\t' in sample:
                    delimiter = '\t'
                elif ';' in sample:
                    delimiter = ';'
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for row in reader:
                    try:
                        entry = _parse_qutrub_row(row)
                        if entry:
                            extracted_count += 1
                            yield entry
                    except Exception as e:
                        # Skip problematic rows
                        continue
                        
        except Exception as e:
            print(f"Error processing Qutrub file {verb_file}: {e}")
            continue
    
    print(f"Extracted {extracted_count} verb conjugations from Qutrub")


def _parse_qutrub_row(row: Dict[str, str]) -> Dict[str, Any]:
    """Parse a single row from Qutrub CSV data.
    
    Args:
        row: Dictionary representing a CSV row
        
    Returns:
        Entry dictionary or None if parsing fails
    """
    # Common field names in Qutrub datasets
    verb_fields = ['verb', 'lemma', 'root', 'word', 'unvocalized']
    
    # Extract verb lemma
    verb = None
    for field in verb_fields:
        if field in row and row[field].strip():
            verb = row[field].strip()
            break
    
    if not verb:
        return None
    
    # Import normalize function dynamically to avoid import issues
    try:
        from ..services.normalize import normalize_ar
        verb_norm = normalize_ar(verb)
    except ImportError:
        # Basic fallback normalization
        verb_norm = verb.strip()
    
    if not verb_norm:
        return None
    
    # Extract root if available
    root = None
    if 'root' in row and row['root'].strip():
        try:
            from ..services.normalize import normalize_ar
            root = normalize_ar(row['root'].strip())
        except ImportError:
            root = row['root'].strip()
    
    # Create entry data
    entry = {
        'info': {
            'lemma': verb,
            'lemma_norm': verb_norm,
            'root': root,
            'pos': ['verb'],
            'quality': {
                'confidence': 0.8,
                'reviewed': False,
                'source_count': 1
            },
            'updated_at': datetime.now().isoformat()
        },
        'senses': [{
            'id': f"{verb_norm}_qut_1",
            'gloss_ar_short': 'فعل',
            'confidence': 0.8
        }],
        'examples': [],
        'relations': {},
        'pronunciation': {},
        'dialects': [],
        'inflection': {
            'conjugations': _extract_conjugations(row)
        },
        'derivations': {},
        'sources': [{
            'name': 'Qutrub',
            'license': 'GPL',
            'url': 'https://github.com/linuxscout/qutrub'
        }]
    }
    
    return entry


def _extract_conjugations(row: Dict[str, str]) -> Dict[str, Any]:
    """Extract conjugation data from a Qutrub row."""
    conjugations = {}
    
    # Map common conjugation field names
    conj_mapping = {
        'past_1s': ['past_1s', 'ماضي_أنا'],
        'past_2s': ['past_2s', 'ماضي_أنت'],
        'past_3s_m': ['past_3s_m', 'ماضي_هو'],
        'past_3s_f': ['past_3s_f', 'ماضي_هي'],
        'present_1s': ['present_1s', 'مضارع_أنا'],
        'present_2s': ['present_2s', 'مضارع_أنت'],
        'present_3s_m': ['present_3s_m', 'مضارع_هو'],
        'present_3s_f': ['present_3s_f', 'مضارع_هي'],
    }
    
    for tense_person, field_variants in conj_mapping.items():
        for field in field_variants:
            if field in row and row[field].strip():
                conjugations[tense_person] = row[field].strip()
                break
    
    return conjugations


def conjugate(lemma: str) -> Dict[str, Any]:
    """Return conjugation tables for the given verb.

    Returns a dictionary with keys such as 'past', 'present' and
    'imperative', each mapping person keys (e.g. '1sg', '2sg_m') to
    conjugated forms.  See the ``Inflection`` model for the expected
    shape.
    """
    raise NotImplementedError("Qutrub conjugation not yet integrated")
