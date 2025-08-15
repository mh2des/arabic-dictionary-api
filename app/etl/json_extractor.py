"""
JSON Dictionary Extractor
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module extracts Arabic dictionary data from JSON files,
supporting various JSON schemas for linguistic resources.
"""

from __future__ import annotations

import os
import json
from typing import Iterator, Dict, List, Optional, Any, Union
from datetime import datetime

from ..models import Entry, Info, QualityMeta
from ..services.normalize import normalize_ar


def extract_from_json_files(json_dir: str) -> Iterator[Entry]:
    """Extract dictionary entries from JSON files.
    
    Args:
        json_dir: Directory containing JSON files
        
    Yields:
        Entry objects extracted from JSON content
    """
    for root, dirs, files in os.walk(json_dir):
        for filename in files:
            if filename.endswith(('.json', '.jsonl')):
                filepath = os.path.join(root, filename)
                try:
                    if filename.endswith('.jsonl'):
                        yield from _extract_from_jsonl_file(filepath)
                    else:
                        yield from _extract_from_json_file(filepath)
                except Exception as e:
                    print(f"Error processing JSON file {filepath}: {e}")
                    continue


def _extract_from_json_file(json_path: str) -> Iterator[Entry]:
    """Extract entries from a single JSON file."""
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error in {json_path}: {e}")
        return
    except Exception as e:
        print(f"Error reading JSON file {json_path}: {e}")
        return
    
    # Handle different JSON structures
    if isinstance(data, list):
        # Array of entries
        for item in data:
            entry = _parse_json_entry(item, json_path)
            if entry:
                yield entry
    
    elif isinstance(data, dict):
        # Could be a single entry or object with entries
        if _looks_like_single_entry(data):
            entry = _parse_json_entry(data, json_path)
            if entry:
                yield entry
        else:
            # Look for entries in various keys
            entries_keys = ['entries', 'words', 'dictionary', 'lexicon', 'data', 'items']
            
            for key in entries_keys:
                if key in data and isinstance(data[key], list):
                    for item in data[key]:
                        entry = _parse_json_entry(item, json_path)
                        if entry:
                            yield entry
                    break
            else:
                # Try to iterate over all values
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        if isinstance(value, dict):
                            entry = _parse_json_entry(value, json_path)
                            if entry:
                                yield entry
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict):
                                    entry = _parse_json_entry(item, json_path)
                                    if entry:
                                        yield entry


def _extract_from_jsonl_file(jsonl_path: str) -> Iterator[Entry]:
    """Extract entries from a JSONL (JSON Lines) file."""
    
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    entry = _parse_json_entry(data, jsonl_path)
                    if entry:
                        yield entry
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error at line {line_num} in {jsonl_path}: {e}")
                    continue
                
    except Exception as e:
        print(f"Error reading JSONL file {jsonl_path}: {e}")


def _looks_like_single_entry(data: Dict[str, Any]) -> bool:
    """Check if a JSON object looks like a single dictionary entry."""
    
    # Look for common entry fields
    entry_indicators = ['word', 'lemma', 'headword', 'entry', 'term', 'arabic']
    definition_indicators = ['definition', 'meaning', 'gloss', 'translation', 'senses']
    
    has_word = any(key.lower() in entry_indicators for key in data.keys())
    has_definition = any(key.lower() in definition_indicators for key in data.keys())
    
    return has_word or has_definition


def _parse_json_entry(data: Dict[str, Any], filepath: str) -> Optional[Entry]:
    """Parse a JSON object into an Entry."""
    
    if not isinstance(data, dict):
        return None
    
    # Extract word/lemma
    lemma = _extract_word_from_json(data)
    if not lemma or not _is_arabic_word(lemma):
        return None
    
    # Extract definition/senses
    definition = _extract_definition_from_json(data)
    
    # Extract POS
    pos = _extract_pos_from_json(data)
    
    # Extract root
    root = _extract_root_from_json(data)
    
    # Extract additional metadata
    metadata = _extract_metadata_from_json(data)
    
    return _create_json_entry(lemma, definition, pos, root, metadata, filepath)


def _extract_word_from_json(data: Dict[str, Any]) -> Optional[str]:
    """Extract the main word/lemma from JSON data."""
    
    word_keys = [
        'word', 'lemma', 'headword', 'entry', 'term', 'arabic', 'ar',
        'vocalized', 'unvocalized', 'surface', 'orthography'
    ]
    
    for key in word_keys:
        if key in data and data[key]:
            word = str(data[key]).strip()
            if _is_arabic_word(word):
                return word
    
    return None


def _extract_definition_from_json(data: Dict[str, Any]) -> Optional[str]:
    """Extract definition/meaning from JSON data."""
    
    # Check for simple definition fields
    definition_keys = [
        'definition', 'meaning', 'gloss', 'translation', 'desc', 'description',
        'english', 'en', 'arabic_def', 'ar_def'
    ]
    
    for key in definition_keys:
        if key in data and data[key]:
            return str(data[key]).strip()
    
    # Check for senses array
    if 'senses' in data and isinstance(data['senses'], list):
        definitions = []
        for sense in data['senses']:
            if isinstance(sense, dict):
                for def_key in definition_keys:
                    if def_key in sense and sense[def_key]:
                        definitions.append(str(sense[def_key]).strip())
                        break
        if definitions:
            return '; '.join(definitions)
    
    # Check for nested definition structures
    if 'definitions' in data and isinstance(data['definitions'], list):
        definitions = []
        for definition in data['definitions']:
            if isinstance(definition, str):
                definitions.append(definition.strip())
            elif isinstance(definition, dict) and 'text' in definition:
                definitions.append(str(definition['text']).strip())
        if definitions:
            return '; '.join(definitions)
    
    return None


def _extract_pos_from_json(data: Dict[str, Any]) -> str:
    """Extract part of speech from JSON data."""
    
    pos_keys = ['pos', 'part_of_speech', 'category', 'type', 'class', 'gram', 'grammatical_category']
    
    for key in pos_keys:
        if key in data and data[key]:
            return _normalize_pos(str(data[key]).strip())
    
    return 'unknown'


def _extract_root_from_json(data: Dict[str, Any]) -> Optional[str]:
    """Extract root from JSON data."""
    
    root_keys = ['root', 'radical', 'radicals', 'stem', 'base', 'morphological_root']
    
    for key in root_keys:
        if key in data and data[key]:
            root_text = str(data[key]).strip()
            if _is_arabic_word(root_text):
                return normalize_ar(root_text)
    
    return None


def _extract_metadata_from_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract additional metadata from JSON data."""
    
    metadata = {}
    
    # Extract frequency information
    freq_keys = ['frequency', 'freq', 'count', 'occurrences']
    for key in freq_keys:
        if key in data and data[key]:
            try:
                metadata['frequency'] = int(data[key])
                break
            except ValueError:
                pass
    
    # Extract pronunciation
    pron_keys = ['pronunciation', 'phonetic', 'ipa', 'phonetics']
    for key in pron_keys:
        if key in data and data[key]:
            metadata['pronunciation'] = str(data[key]).strip()
            break
    
    # Extract domain/field
    domain_keys = ['domain', 'field', 'subject', 'category']
    for key in domain_keys:
        if key in data and data[key]:
            metadata['domain'] = str(data[key]).strip()
            break
    
    # Extract dialect information
    dialect_keys = ['dialect', 'variety', 'regional']
    for key in dialect_keys:
        if key in data and data[key]:
            metadata['dialect'] = str(data[key]).strip()
            break
    
    return metadata


def _create_json_entry(lemma: str, definition: Optional[str], pos: str, root: Optional[str], 
                      metadata: Dict[str, Any], filepath: str) -> Optional[Entry]:
    """Create an Entry object from JSON-extracted data."""
    
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
        domain=metadata.get('domain'),
        freq={'corpus_frequency': metadata['frequency']} if 'frequency' in metadata else None,
        quality=QualityMeta(confidence=0.7, reviewed=False, source_count=1),
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
            'id': f"{lemma_norm}_json_1",
            'gloss_ar': definition if _contains_arabic(definition) else None,
            'gloss_en': definition if not _contains_arabic(definition) else None,
            'confidence': 0.7
        })
    
    pronunciation = {}
    if 'pronunciation' in metadata:
        pronunciation['ipa'] = metadata['pronunciation']
    
    dialects = []
    if 'dialect' in metadata:
        dialects.append({
            'variety': metadata['dialect'],
            'lemma': lemma
        })
    
    entry_data = {
        'info': info_dict,
        'senses': senses,
        'examples': [],
        'relations': {},
        'pronunciation': pronunciation,
        'dialects': dialects,
        'inflection': {},
        'derivations': {},
        'sources': [{
            'name': 'JSON Dictionary',
            'license': 'Unknown',
            'url': filepath,
            'format': 'JSON'
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
