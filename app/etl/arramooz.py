"""
ETL for Arramooz AlWaseet
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module extracts morphological information from the open Arramooz 
AlWaseet database. Arramooz provides comprehensive Arabic morphological
data including roots, patterns, POS tags, and inflectional features.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Iterator, Dict, List, Optional
from datetime import datetime

from ..models import Info, Entry, QualityMeta
from ..services.normalize import normalize_ar


def extract_from_csv(csv_path: str) -> Iterator[Entry]:
    """Extract Arramooz data from CSV files.
    
    Args:
        csv_path: Path to the Arramooz CSV file
        
    Yields:
        Entry objects with morphological information
    """
    if not os.path.exists(csv_path):
        print(f"Warning: Arramooz CSV file not found: {csv_path}")
        return
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Try to detect delimiter
        sample = f.read(1024)
        f.seek(0)
        
        delimiter = ','
        if '\t' in sample:
            delimiter = '\t'
        elif ';' in sample:
            delimiter = ';'
        
        reader = csv.DictReader(f, delimiter=delimiter)
        
        for row_num, row in enumerate(reader, 1):
            try:
                entry = _parse_arramooz_row(row)
                if entry:
                    yield entry
            except Exception as e:
                print(f"Error parsing Arramooz row {row_num}: {e}")
                continue


def _parse_arramooz_row(row: Dict[str, str]) -> Optional[Entry]:
    """Parse a single row from Arramooz CSV data.
    
    Args:
        row: Dictionary representing a CSV row
        
    Returns:
        Entry object or None if parsing fails
    """
    # Common field names in Arramooz datasets
    lemma_fields = ['lemma', 'word', 'vocalized', 'unvocalized', 'surface']
    root_fields = ['root', 'radicals', 'stem']
    pos_fields = ['pos', 'category', 'type', 'class']
    pattern_fields = ['pattern', 'wazn', 'template']
    
    # Extract lemma
    lemma = None
    for field in lemma_fields:
        if field in row and row[field].strip():
            lemma = row[field].strip()
            break
    
    if not lemma:
        return None
    
    # Normalize lemma
    lemma_norm = normalize_ar(lemma)
    if not lemma_norm:
        return None
    
    # Extract root
    root = None
    for field in root_fields:
        if field in row and row[field].strip():
            root = normalize_ar(row[field].strip())
            break
    
    # Extract POS
    pos_list = []
    for field in pos_fields:
        if field in row and row[field].strip():
            pos_value = row[field].strip().lower()
            # Map Arabic/English POS tags to standard forms
            pos_mapped = _map_pos_tag(pos_value)
            if pos_mapped and pos_mapped not in pos_list:
                pos_list.append(pos_mapped)
    
    # Extract pattern
    pattern = None
    for field in pattern_fields:
        if field in row and row[field].strip():
            pattern = row[field].strip()
            break
    
    # Extract additional morphological features
    morph_features = {}
    
    # Gender
    if 'gender' in row or 'جنس' in row:
        gender = row.get('gender') or row.get('جنس', '')
        if gender:
            morph_features['gender'] = _map_gender(gender.strip())
    
    # Number
    if 'number' in row or 'عدد' in row:
        number = row.get('number') or row.get('عدد', '')
        if number:
            morph_features['number'] = _map_number(number.strip())
    
    # Verb form
    if 'form' in row or 'باب' in row:
        form = row.get('form') or row.get('باب', '')
        if form:
            morph_features['form'] = _map_verb_form(form.strip())
    
    # Create Info object
    info = Info(
        lemma=lemma,
        lemma_norm=lemma_norm,
        root=root,
        pattern=pattern,
        pos=pos_list if pos_list else ['unknown'],
        morph=morph_features if morph_features else None,
        quality=QualityMeta(confidence=0.8, reviewed=False, source_count=1),
        updated_at=datetime.now().isoformat()
    )
    
    # Create full entry data
    info_dict = info.dict() if hasattr(info, 'dict') else info.__dict__
    # Ensure quality is properly serialized 
    if 'quality' in info_dict and info_dict['quality']:
        if hasattr(info_dict['quality'], 'dict'):
            info_dict['quality'] = info_dict['quality'].dict()
        elif hasattr(info_dict['quality'], '__dict__'):
            info_dict['quality'] = info_dict['quality'].__dict__
    
    entry_data = {
        'info': info_dict,
        'senses': [],
        'examples': [],
        'relations': {},
        'pronunciation': {},
        'dialects': [],
        'inflection': {},
        'derivations': {},
        'sources': [{
            'name': 'Arramooz AlWaseet',
            'license': 'GPL',
            'url': 'https://github.com/linuxscout/arramooz'
        }]
    }
    
    return Entry(
        info=info,
        data=json.dumps(entry_data, ensure_ascii=False)
    )


def _map_pos_tag(pos: str) -> Optional[str]:
    """Map various POS tag formats to standard forms."""
    pos = pos.lower().strip()
    
    # Arabic POS mappings
    arabic_pos_map = {
        'اسم': 'noun',
        'فعل': 'verb', 
        'صفة': 'adjective',
        'ظرف': 'adverb',
        'حرف': 'particle',
        'ضمير': 'pronoun',
        'عدد': 'numeral',
        'حرف جر': 'preposition',
        'حرف عطف': 'conjunction',
        'تعجب': 'interjection'
    }
    
    # English POS mappings
    english_pos_map = {
        'noun': 'noun',
        'verb': 'verb',
        'adj': 'adjective',
        'adjective': 'adjective',
        'adv': 'adverb',
        'adverb': 'adverb',
        'prep': 'preposition',
        'preposition': 'preposition',
        'pron': 'pronoun',
        'pronoun': 'pronoun',
        'conj': 'conjunction',
        'conjunction': 'conjunction',
        'interj': 'interjection',
        'interjection': 'interjection',
        'part': 'particle',
        'particle': 'particle',
        'num': 'numeral',
        'numeral': 'numeral'
    }
    
    # Check Arabic mappings first
    if pos in arabic_pos_map:
        return arabic_pos_map[pos]
    
    # Check English mappings
    if pos in english_pos_map:
        return english_pos_map[pos]
    
    # Check partial matches
    for key, value in english_pos_map.items():
        if key in pos or pos in key:
            return value
    
    return None


def _map_gender(gender: str) -> Optional[str]:
    """Map gender values to standard forms."""
    gender = gender.lower().strip()
    
    gender_map = {
        'م': 'masculine',
        'مذكر': 'masculine',
        'masculine': 'masculine',
        'male': 'masculine',
        'ف': 'feminine', 
        'مؤنث': 'feminine',
        'feminine': 'feminine',
        'female': 'feminine',
        'مشترك': 'common',
        'common': 'common'
    }
    
    return gender_map.get(gender)


def _map_number(number: str) -> Optional[str]:
    """Map number values to standard forms."""
    number = number.lower().strip()
    
    number_map = {
        'مفرد': 'singular',
        'singular': 'singular',
        'مثنى': 'dual',
        'dual': 'dual',
        'جمع': 'plural',
        'plural': 'plural'
    }
    
    return number_map.get(number)


def _map_verb_form(form: str) -> Optional[str]:
    """Map verb form values to Roman numerals."""
    form = form.strip()
    
    # Arabic numerals to Roman
    arabic_to_roman = {
        '1': 'I', '2': 'II', '3': 'III', '4': 'IV', '5': 'V',
        '6': 'VI', '7': 'VII', '8': 'VIII', '9': 'IX', '10': 'X'
    }
    
    # Arabic number words
    arabic_words = {
        'الأول': 'I', 'الثاني': 'II', 'الثالث': 'III', 'الرابع': 'IV',
        'الخامس': 'V', 'السادس': 'VI', 'السابع': 'VII', 'الثامن': 'VIII',
        'التاسع': 'IX', 'العاشر': 'X'
    }
    
    if form in arabic_to_roman:
        return arabic_to_roman[form]
    
    if form in arabic_words:
        return arabic_words[form]
    
    # Already in Roman numeral format
    if form.upper() in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']:
        return form.upper()
    
    return None


def extract(source_dir: str) -> Iterator[Entry]:
    """Extract Arramooz data from source directory.
    
    Args:
        source_dir: Path to directory containing Arramooz data files
        
    Yields:
        Entry objects with morphological information
    """
    if not os.path.exists(source_dir):
        print(f"Warning: Arramooz source directory not found: {source_dir}")
        return
    
    # Look for CSV files in the directory
    csv_files = []
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.csv'):
                csv_files.append(os.path.join(root, file))
    
    if not csv_files:
        print(f"Warning: No CSV files found in Arramooz directory: {source_dir}")
        return
    
    # Process each CSV file
    for csv_file in csv_files:
        print(f"Processing Arramooz file: {csv_file}")
        yield from extract_from_csv(csv_file)
