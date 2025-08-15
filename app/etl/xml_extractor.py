"""
XML Dictionary Extractor
~~~~~~~~~~~~~~~~~~~~~~~~~

This module extracts Arabic dictionary data from XML files, supporting
various XML schemas commonly used for linguistic resources.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from typing import Iterator, Dict, List, Optional, Any
from datetime import datetime

from ..models import Entry, Info, QualityMeta
from ..services.normalize import normalize_ar


def extract_from_xml_files(xml_dir: str) -> Iterator[Entry]:
    """Extract dictionary entries from XML files.
    
    Args:
        xml_dir: Directory containing XML files
        
    Yields:
        Entry objects extracted from XML content
    """
    for root, dirs, files in os.walk(xml_dir):
        for filename in files:
            if filename.endswith(('.xml', '.XML')):
                filepath = os.path.join(root, filename)
                try:
                    yield from _extract_from_xml_file(filepath)
                except Exception as e:
                    print(f"Error processing XML file {filepath}: {e}")
                    continue


def _extract_from_xml_file(xml_path: str) -> Iterator[Entry]:
    """Extract entries from a single XML file."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"XML parsing error in {xml_path}: {e}")
        return
    except Exception as e:
        print(f"Error reading XML file {xml_path}: {e}")
        return
    
    # Try different XML schema patterns
    filename = os.path.basename(xml_path).lower()
    
    if 'tei' in filename or root.tag.endswith('TEI'):
        yield from _extract_tei_xml(root, xml_path)
    elif 'lexicon' in filename or 'dict' in filename:
        yield from _extract_lexicon_xml(root, xml_path)
    else:
        yield from _extract_generic_xml(root, xml_path)


def _extract_tei_xml(root: ET.Element, filepath: str) -> Iterator[Entry]:
    """Extract entries from TEI (Text Encoding Initiative) XML format."""
    # TEI format typically has <entry> elements within <body>
    
    # Define namespace if present
    ns = {}
    if root.tag.startswith('{'):
        ns_uri = root.tag.split('}')[0][1:]
        ns['tei'] = ns_uri
    
    # Look for entry elements
    entry_xpath = './/entry' if not ns else './/tei:entry'
    entry_elements = root.findall(entry_xpath, ns)
    
    if not entry_elements:
        # Try alternative paths
        alternative_paths = [
            './/item',
            './/lemma',
            './/word',
            './/lex'
        ]
        
        for path in alternative_paths:
            if ns:
                path = path.replace('//', '//tei:')
            entry_elements.extend(root.findall(path, ns))
    
    for entry_elem in entry_elements:
        try:
            entry = _parse_tei_entry(entry_elem, filepath, ns)
            if entry:
                yield entry
        except Exception as e:
            print(f"Error parsing TEI entry in {filepath}: {e}")
            continue


def _extract_lexicon_xml(root: ET.Element, filepath: str) -> Iterator[Entry]:
    """Extract entries from generic lexicon XML format."""
    # Common lexicon XML patterns
    entry_tags = ['entry', 'word', 'lemma', 'item', 'record']
    
    for tag in entry_tags:
        entry_elements = root.findall(f'.//{tag}')
        if entry_elements:
            for entry_elem in entry_elements:
                try:
                    entry = _parse_lexicon_entry(entry_elem, filepath)
                    if entry:
                        yield entry
                except Exception as e:
                    continue


def _extract_generic_xml(root: ET.Element, filepath: str) -> Iterator[Entry]:
    """Extract entries from generic XML files."""
    # Try to find any elements that might contain dictionary data
    
    # Get all elements with text content
    for elem in root.iter():
        if elem.text and elem.text.strip():
            text = elem.text.strip()
            if _contains_arabic_word(text):
                try:
                    entry = _parse_xml_text_entry(elem, filepath)
                    if entry:
                        yield entry
                except Exception as e:
                    continue


def _parse_tei_entry(entry_elem: ET.Element, filepath: str, ns: Dict[str, str]) -> Optional[Entry]:
    """Parse a TEI entry element."""
    
    # Extract lemma/headword
    lemma = None
    lemma_xpath = [
        'lem',
        'lemma', 
        'form/orth',
        'head',
        '@n'  # sometimes lemma is in 'n' attribute
    ]
    
    for xpath in lemma_xpath:
        if xpath.startswith('@'):
            # Attribute
            attr_name = xpath[1:]
            lemma = entry_elem.get(attr_name)
        else:
            # Element
            if ns:
                xpath = f"tei:{xpath}"
            elem = entry_elem.find(xpath, ns)
            if elem is not None and elem.text:
                lemma = elem.text.strip()
        
        if lemma and _is_arabic_word(lemma):
            break
    
    if not lemma or not _is_arabic_word(lemma):
        return None
    
    # Extract definition/sense
    definition = None
    definition_xpaths = [
        'def',
        'definition',
        'sense/def',
        'gloss',
        'trans',
        'translation'
    ]
    
    for xpath in definition_xpaths:
        if ns:
            xpath = f"tei:{xpath.replace('/', '/tei:')}"
        elem = entry_elem.find(xpath, ns)
        if elem is not None and elem.text:
            definition = elem.text.strip()
            break
    
    # Extract POS if available
    pos = 'unknown'
    pos_xpaths = ['pos', 'gram', 'gramGrp/pos']
    
    for xpath in pos_xpaths:
        if ns:
            xpath = f"tei:{xpath.replace('/', '/tei:')}"
        elem = entry_elem.find(xpath, ns)
        if elem is not None and elem.text:
            pos = _normalize_pos(elem.text.strip())
            break
    
    return _create_xml_entry(lemma, definition, pos, 'TEI XML', filepath)


def _parse_lexicon_entry(entry_elem: ET.Element, filepath: str) -> Optional[Entry]:
    """Parse a generic lexicon entry element."""
    
    # Try to extract word and definition from various child elements
    lemma = None
    definition = None
    pos = 'unknown'
    
    # Common element names for lemma
    lemma_tags = ['word', 'lemma', 'headword', 'entry_word', 'term']
    for tag in lemma_tags:
        elem = entry_elem.find(tag)
        if elem is not None and elem.text:
            lemma = elem.text.strip()
            if _is_arabic_word(lemma):
                break
    
    # If no lemma found in child elements, try attributes
    if not lemma:
        for attr in ['word', 'lemma', 'headword']:
            lemma = entry_elem.get(attr)
            if lemma and _is_arabic_word(lemma):
                break
    
    # If still no lemma, try the element text itself
    if not lemma and entry_elem.text:
        text = entry_elem.text.strip()
        if _is_arabic_word(text):
            lemma = text
    
    if not lemma:
        return None
    
    # Extract definition
    definition_tags = ['definition', 'meaning', 'gloss', 'translation', 'def', 'desc']
    for tag in definition_tags:
        elem = entry_elem.find(tag)
        if elem is not None and elem.text:
            definition = elem.text.strip()
            break
    
    # Extract POS
    pos_tags = ['pos', 'part_of_speech', 'category', 'type', 'class']
    for tag in pos_tags:
        elem = entry_elem.find(tag)
        if elem is not None and elem.text:
            pos = _normalize_pos(elem.text.strip())
            break
    
    return _create_xml_entry(lemma, definition, pos, 'Lexicon XML', filepath)


def _parse_xml_text_entry(elem: ET.Element, filepath: str) -> Optional[Entry]:
    """Parse an XML element that contains text that might be a dictionary entry."""
    
    text = elem.text.strip()
    
    # Try to parse text for word-definition patterns
    import re
    patterns = [
        r'^([^\s:]{2,})\s*:\s*(.+)$',
        r'^([^\s-]{2,})\s*-\s*(.+)$'
    ]
    
    for pattern in patterns:
        match = re.match(pattern, text)
        if match and _is_arabic_word(match.group(1)):
            word = match.group(1).strip()
            definition = match.group(2).strip()
            return _create_xml_entry(word, definition, 'unknown', 'Generic XML', filepath)
    
    return None


def _create_xml_entry(lemma: str, definition: Optional[str], pos: str, source_name: str, filepath: str) -> Optional[Entry]:
    """Create an Entry object from XML-extracted data."""
    
    if not lemma:
        return None
    
    lemma_norm = normalize_ar(lemma)
    if not lemma_norm:
        return None
    
    # Create Info object
    info = Info(
        lemma=lemma,
        lemma_norm=lemma_norm,
        pos=[pos] if pos else ['unknown'],
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
            'id': f"{lemma_norm}_xml_1",
            'gloss_ar': definition if _contains_arabic(definition) else None,
            'gloss_en': definition if not _contains_arabic(definition) else None,
            'confidence': 0.7
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
            'format': 'XML'
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


def _contains_arabic_word(text: str) -> bool:
    """Check if text contains Arabic words."""
    words = text.split()
    return any(_is_arabic_word(word) for word in words)


def _contains_arabic(text: str) -> bool:
    """Check if text contains any Arabic characters."""
    return any('\u0600' <= char <= '\u06FF' for char in text)
