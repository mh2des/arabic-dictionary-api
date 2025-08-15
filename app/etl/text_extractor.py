"""
Text File Extractor
~~~~~~~~~~~~~~~~~~~

This module extracts Arabic dictionary data from various text file formats,
including plain text, dictionary format files, and other structured text formats.
"""

from __future__ import annotations

import os
import re
import json
from typing import Iterator, Dict, List, Optional, Any
from datetime import datetime

from ..models import Entry, Info, QualityMeta
from ..services.normalize import normalize_ar


def extract_from_text_files(text_dir: str) -> Iterator[Entry]:
    """Extract dictionary entries from text files.
    
    Args:
        text_dir: Directory containing text files
        
    Yields:
        Entry objects extracted from text content
    """
    for root, dirs, files in os.walk(text_dir):
        for filename in files:
            if filename.endswith(('.txt', '.dict', '.tab', '.tsv')):
                filepath = os.path.join(root, filename)
                try:
                    yield from _extract_from_text_file(filepath)
                except Exception as e:
                    print(f"Error processing text file {filepath}: {e}")
                    continue


def _extract_from_text_file(file_path: str) -> Iterator[Entry]:
    """Extract entries from a single text file."""
    
    # Try different encodings
    content = None
    for encoding in ['utf-8', 'utf-16', 'cp1256', 'latin-1']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        print(f"Could not decode text file: {file_path}")
        return
    
    filename = os.path.basename(file_path).lower()
    
    # Choose extraction strategy based on file format
    if filename.endswith('.dict'):
        yield from _extract_dict_format(content, file_path)
    elif filename.endswith(('.tab', '.tsv')):
        yield from _extract_tabular_format(content, file_path)
    elif 'freq' in filename:
        yield from _extract_frequency_format(content, file_path)
    else:
        yield from _extract_generic_text(content, file_path)


def _extract_dict_format(content: str, filepath: str) -> Iterator[Entry]:
    """Extract from dictionary format files (.dict)."""
    
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        try:
            # Dictionary format often uses tab separation
            if '\t' in line:
                parts = line.split('\t')
            else:
                # Try colon separation
                parts = line.split(':', 1) if ':' in line else line.split(' ', 1)
            
            if len(parts) >= 2:
                word = parts[0].strip()
                definition = parts[1].strip()
                
                if _is_arabic_word(word):
                    entry = _create_text_entry(word, definition, 'Dict Format', filepath)
                    if entry:
                        yield entry
            
        except Exception as e:
            print(f"Error parsing line {line_num} in {filepath}: {e}")
            continue


def _extract_tabular_format(content: str, filepath: str) -> Iterator[Entry]:
    """Extract from tabular format files (.tab, .tsv)."""
    
    lines = content.split('\n')
    if not lines:
        return
    
    # Try to detect header
    header = lines[0].strip().split('\t')
    data_lines = lines[1:] if len(header) > 1 else lines
    
    # Identify columns
    word_col = _find_column_index(header, ['word', 'lemma', 'arabic', 'ar', 'entry'])
    def_col = _find_column_index(header, ['definition', 'meaning', 'english', 'en', 'gloss'])
    pos_col = _find_column_index(header, ['pos', 'category', 'type', 'class'])
    root_col = _find_column_index(header, ['root', 'radical', 'stem'])
    
    for line_num, line in enumerate(data_lines, 2):
        line = line.strip()
        if not line:
            continue
        
        try:
            parts = line.split('\t')
            
            word = parts[word_col].strip() if word_col < len(parts) else None
            definition = parts[def_col].strip() if def_col < len(parts) else None
            pos = parts[pos_col].strip() if pos_col < len(parts) else 'unknown'
            root = parts[root_col].strip() if root_col < len(parts) else None
            
            if word and _is_arabic_word(word):
                entry = _create_text_entry(word, definition, 'Tabular Format', filepath, pos, root)
                if entry:
                    yield entry
            
        except Exception as e:
            continue


def _extract_frequency_format(content: str, filepath: str) -> Iterator[Entry]:
    """Extract from frequency list format files."""
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Frequency format: "word frequency" or "frequency word"
        parts = line.split()
        if len(parts) >= 2:
            # Try both orders
            if _is_arabic_word(parts[0]):
                word = parts[0]
                freq = parts[1] if parts[1].isdigit() else None
            elif _is_arabic_word(parts[1]):
                word = parts[1]
                freq = parts[0] if parts[0].isdigit() else None
            else:
                continue
            
            entry = _create_frequency_entry(word, freq, filepath)
            if entry:
                yield entry


def _extract_generic_text(content: str, filepath: str) -> Iterator[Entry]:
    """Extract from generic text files."""
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        
        # Look for dictionary entry patterns
        patterns = [
            r'^([^\s:]{2,})\s*:\s*(.{5,})$',      # word: definition
            r'^([^\s-]{2,})\s*-\s*(.{5,})$',      # word - definition
            r'^([^\s=]{2,})\s*=\s*(.{5,})$',      # word = definition
            r'^([^\s]{2,})\s+(.{20,})$'           # word long_definition
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match and _is_arabic_word(match.group(1)):
                word = match.group(1).strip()
                definition = match.group(2).strip()
                
                entry = _create_text_entry(word, definition, 'Text Format', filepath)
                if entry:
                    yield entry
                break


def _find_column_index(header: List[str], keywords: List[str]) -> int:
    """Find the index of a column that matches keywords."""
    header_lower = [h.lower() for h in header]
    
    for keyword in keywords:
        for i, col in enumerate(header_lower):
            if keyword in col:
                return i
    
    return 0  # Default to first column


def _create_text_entry(word: str, definition: Optional[str], source_name: str, 
                      filepath: str, pos: str = 'unknown', root: Optional[str] = None) -> Optional[Entry]:
    """Create an Entry object from text-extracted data."""
    
    if not word:
        return None
    
    lemma_norm = normalize_ar(word)
    if not lemma_norm:
        return None
    
    # Create Info object
    info = Info(
        lemma=word,
        lemma_norm=lemma_norm,
        root=normalize_ar(root) if root else None,
        pos=[_normalize_pos(pos)] if pos else ['unknown'],
        quality=QualityMeta(confidence=0.6, reviewed=False, source_count=1),
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
            'id': f"{lemma_norm}_text_1",
            'gloss_ar': definition if _contains_arabic(definition) else None,
            'gloss_en': definition if not _contains_arabic(definition) else None,
            'confidence': 0.6
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
            'name': source_name,
            'license': 'Unknown',
            'url': filepath,
            'format': 'Text'
        }]
    }
    
    return Entry(
        info=info,
        data=json.dumps(entry_data, ensure_ascii=False)
    )


def _create_frequency_entry(word: str, frequency: Optional[str], filepath: str) -> Optional[Entry]:
    """Create an Entry object from frequency data."""
    
    if not word:
        return None
    
    lemma_norm = normalize_ar(word)
    if not lemma_norm:
        return None
    
    # Create frequency metadata
    freq_data = {}
    if frequency and frequency.isdigit():
        freq_data['corpus_frequency'] = int(frequency)
    
    # Create Info object
    info = Info(
        lemma=word,
        lemma_norm=lemma_norm,
        pos=['unknown'],
        freq=freq_data if freq_data else None,
        quality=QualityMeta(confidence=0.5, reviewed=False, source_count=1),
        updated_at=datetime.now().isoformat()
    )
    
    # Create entry data
    info_dict = info.dict() if hasattr(info, 'dict') else info.__dict__
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
            'name': 'Frequency List',
            'license': 'Unknown',
            'url': filepath,
            'format': 'Text'
        }]
    }
    
    return Entry(
        info=info,
        data=json.dumps(entry_data, ensure_ascii=False)
    )


def _normalize_pos(pos_text: str) -> str:
    """Normalize part-of-speech tags."""
    if not pos_text:
        return 'unknown'
    
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
