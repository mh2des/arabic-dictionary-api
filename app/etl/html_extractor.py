"""
HTML Dictionary Extractor
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module extracts Arabic dictionary data from HTML files, including
specialized formats like Qamoos ul Muheet and other HTML-based dictionaries.
"""

from __future__ import annotations

import os
import re
from typing import Iterator, Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from bs4 import BeautifulSoup

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    BeautifulSoup = None

# Import from local modules
from ..models import Entry, Info  
from ..services.normalize import normalize_ar

from ..models import Entry, Info, QualityMeta
from ..services.normalize import normalize_ar


def extract_from_html_files(html_dir: str) -> Iterator[Entry]:
    """Extract dictionary entries from HTML files.
    
    Args:
        html_dir: Directory containing HTML files
        
    Yields:
        Entry objects extracted from HTML content
    """
    if not BS4_AVAILABLE:
        print("Warning: BeautifulSoup4 not available, skipping HTML extraction")
        return
    
    for root, dirs, files in os.walk(html_dir):
        for filename in files:
            if filename.endswith(('.html', '.htm')):
                filepath = os.path.join(root, filename)
                try:
                    yield from _extract_from_html_file(filepath)
                except Exception as e:
                    print(f"Error processing HTML file {filepath}: {e}")
                    continue


def _extract_from_html_file(html_path: str) -> Iterator[Entry]:
    """Extract entries from a single HTML file."""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with different encodings
        for encoding in ['latin-1', 'cp1256', 'iso-8859-1']:
            try:
                with open(html_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            print(f"Could not decode HTML file: {html_path}")
            return
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Try different extraction strategies based on file structure
    filename = os.path.basename(html_path).lower()
    
    if 'qamoos' in filename or 'muheet' in filename:
        yield from _extract_qamoos_muheet(soup, html_path)
    elif 'wiktionary' in filename:
        yield from _extract_wiktionary_html(soup, html_path)
    else:
        yield from _extract_generic_html(soup, html_path)


def _extract_qamoos_muheet(soup, filepath: str) -> Iterator[Entry]:
    """Extract entries from Qamoos ul Muheet HTML format (OCR processed)."""
    print(f"Processing Qamoos ul Muheet: {filepath}")
    
    # Look for OCR-specific structure
    ocr_pages = soup.find_all('div', class_='ocr_page')
    if not ocr_pages:
        # Fallback to any div with Arabic content
        ocr_pages = soup.find_all('div')
    
    entry_count = 0
    for page in ocr_pages:
        # Get all text content and try to reconstruct it
        text_content = page.get_text()
        
        # Clean up OCR artifacts - join scattered characters
        lines = []
        for line in text_content.split('\n'):
            line = line.strip()
            if line and len(line) > 2:  # Skip very short lines
                # Remove excessive whitespace and join characters
                cleaned_line = re.sub(r'\s+', ' ', line)
                if re.search(r'[\u0600-\u06FF]', cleaned_line):  # Contains Arabic
                    lines.append(cleaned_line)
        
        # Try to reconstruct dictionary entries from the text
        full_text = ' '.join(lines)
        
        # Look for potential word definitions using common Arabic dictionary patterns
        # Common patterns: word followed by colon, or word at start of sentence
        word_patterns = [
            r'([^\s:]+)\s*:\s*([^.]+)',  # word: definition
            r'([^\s]+)\s+([^.]{10,})',   # word followed by longer text
        ]
        
        for pattern in word_patterns:
            matches = re.finditer(pattern, full_text)
            for match in matches:
                word = match.group(1).strip()
                definition = match.group(2).strip()
                
                # Validate that word looks like Arabic
                if re.search(r'[\u0600-\u06FF]{2,}', word) and len(definition) > 5:
                    try:
                        # Create normalized version
                        word_norm = normalize_ar(word)
                        
                        # Create entry
                        entry = Entry(
                            info=Info(
                                lemma=word,
                                lemma_norm=word_norm,
                                pos=['noun']  # Default to noun for Qamoos
                            ),
                            definition=definition,
                            meaning=definition
                        )
                        entry_count += 1
                        yield entry
                        
                        if entry_count >= 100:  # Limit for performance testing
                            print(f"Extracted {entry_count} entries from Qamoos ul Muheet")
                            return
                            
                    except Exception as e:
                        continue  # Skip problematic entries
    
    print(f"Extracted {entry_count} entries from Qamoos ul Muheet")


def _extract_wiktionary_html(soup, filepath: str) -> Iterator[Entry]:
    """Extract entries from Wiktionary HTML exports."""
    # Wiktionary has specific structure with headings and sections
    
    # Look for main word entries
    word_headers = soup.find_all(['h1', 'h2', 'h3'], class_=lambda x: x and 'mw-headline' in x)
    
    for header in word_headers:
        try:
            # Extract the word from the header
            word_text = header.get_text().strip()
            if not word_text or not _is_arabic_word(word_text):
                continue
            
            # Find the content section for this word
            content_section = header.find_next_sibling()
            if content_section:
                entry = _parse_wiktionary_section(word_text, content_section, filepath)
                if entry:
                    yield entry
        except Exception as e:
            print(f"Error parsing Wiktionary entry in {filepath}: {e}")
            continue


def _extract_generic_html(soup, filepath: str) -> Iterator[Entry]:
    """Extract entries from generic HTML dictionary files."""
    
    # Try to find Arabic text in various HTML elements
    text_elements = soup.find_all(['p', 'div', 'span', 'td', 'li'])
    
    for elem in text_elements:
        text_content = elem.get_text().strip()
        if text_content and _contains_arabic_dictionary_pattern(text_content):
            try:
                entry = _parse_generic_text_entry(text_content, 'HTML Dictionary', filepath)
                if entry:
                    yield entry
            except Exception as e:
                continue


def _parse_html_entry_element(elem, source_name: str, filepath: str) -> Optional[Entry]:
    """Parse a single HTML element that represents a dictionary entry."""
    text_content = elem.get_text().strip()
    
    if not text_content or not _contains_arabic(text_content):
        return None
    
    # Try to extract word and definition
    lines = text_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Look for patterns like "word: definition" or "word - definition"
        patterns = [
            r'^([^\s:]+)\s*:\s*(.+)$',
            r'^([^\s-]+)\s*-\s*(.+)$', 
            r'^([^\s]+)\s+(.+)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match and _is_arabic_word(match.group(1)):
                word = match.group(1).strip()
                definition = match.group(2).strip()
                return _create_entry_from_text(word, definition, source_name, filepath)
    
    return None


def _parse_wiktionary_section(word: str, content_elem, filepath: str) -> Optional[Entry]:
    """Parse a Wiktionary section for a specific word."""
    if not _is_arabic_word(word):
        return None
    
    content_text = content_elem.get_text() if content_elem else ""
    
    # Extract definition (look for lines that start with numbers or bullets)
    definition_lines = []
    for line in content_text.split('\n'):
        line = line.strip()
        if re.match(r'^\d+\.', line) or line.startswith('•') or line.startswith('-'):
            definition_lines.append(line)
    
    definition = '; '.join(definition_lines) if definition_lines else content_text[:200]
    
    return _create_entry_from_text(word, definition, 'Wiktionary HTML', filepath)


def _parse_text_for_entries(text: str, source_name: str, filepath: str) -> Iterator[Entry]:
    """Parse plain text content for dictionary entries."""
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        
        # Look for dictionary entry patterns
        patterns = [
            r'^([^\s:]{2,})\s*:\s*(.{10,})$',
            r'^([^\s-]{2,})\s*-\s*(.{10,})$',
            r'^([^\s]{2,})\s+(.{20,})$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match and _is_arabic_word(match.group(1)):
                word = match.group(1).strip()
                definition = match.group(2).strip()
                entry = _create_entry_from_text(word, definition, source_name, filepath)
                if entry:
                    yield entry
                break


def _parse_generic_text_entry(text: str, source_name: str, filepath: str) -> Optional[Entry]:
    """Parse a generic text line that might contain a dictionary entry."""
    # Similar to _parse_text_for_entries but for single entries
    patterns = [
        r'^([^\s:]{2,})\s*:\s*(.{5,})$',
        r'^([^\s-]{2,})\s*-\s*(.{5,})$'
    ]
    
    for pattern in patterns:
        match = re.match(pattern, text)
        if match and _is_arabic_word(match.group(1)):
            word = match.group(1).strip()
            definition = match.group(2).strip()
            return _create_entry_from_text(word, definition, source_name, filepath)
    
    return None


def _create_entry_from_text(word: str, definition: str, source_name: str, filepath: str) -> Optional[Entry]:
    """Create an Entry object from extracted word and definition."""
    if not word or not definition:
        return None
    
    lemma_norm = normalize_ar(word)
    if not lemma_norm:
        return None
    
    # Create Info object
    info = Info(
        lemma=word,
        lemma_norm=lemma_norm,
        pos=['unknown'],
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
    
    entry_data = {
        'info': info_dict,
        'senses': [{
            'id': f"{lemma_norm}_html_1",
            'gloss_ar': definition if _contains_arabic(definition) else None,
            'gloss_en': definition if not _contains_arabic(definition) else None,
            'confidence': 0.6
        }],
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
            'format': 'HTML'
        }]
    }
    
    import json
    return Entry(
        info=info,
        data=json.dumps(entry_data, ensure_ascii=False)
    )


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


def _contains_arabic_dictionary_pattern(text: str) -> bool:
    """Check if text looks like it might contain dictionary entries."""
    if not _contains_arabic(text):
        return False
    
    # Look for patterns that suggest dictionary entries
    patterns = [
        r'[^\s:]{2,}\s*:\s*.{5,}',  # word: definition
        r'[^\s-]{2,}\s*-\s*.{5,}',  # word - definition
        r'[^\s]{2,}\s+.{20,}'       # word long definition
    ]
    
    return any(re.search(pattern, text) for pattern in patterns)
