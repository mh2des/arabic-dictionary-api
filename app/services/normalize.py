"""
Arabic text normalisation utilities for the dictionary backend.

This module provides comprehensive Arabic text normalization functions
including diacritic removal, character variant standardization, and
orthographic normalization for both storage and search purposes.
"""

import re
import unicodedata
from typing import List, Optional, Set

# Extended Arabic diacritics and marks pattern
ARABIC_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06ED\u08D3-\u08E1\u08E3-\u08FF]")

# Precompiled patterns for performance
SPACES_PATTERN = re.compile(r'\s+')
PUNCTUATION_PATTERN = re.compile(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\s\d\w]')

# Character normalization mappings
CHAR_MAPPINGS = {
    # Alef variants
    'أ': 'ا',  'إ': 'ا',  'آ': 'ا',  'ٱ': 'ا',
    # Yeh variants  
    'ى': 'ي',  'ئ': 'ي',  'يٰ': 'ي',
    # Waw variants
    'ؤ': 'و',
    # Teh marbuta
    'ة': 'ه',
    # Remove tatweel
    'ـ': '',
    # Lam-alef ligatures
    'ﻻ': 'لا', 'ﻷ': 'لا', 'ﻹ': 'لا', 'ﻵ': 'لا',
    'ﻼ': 'لا', 'ﻸ': 'لا', 'ﻺ': 'لا', 'ﻶ': 'لا',
}

# Common Arabic prefixes for root extraction
ARABIC_PREFIXES = ['ال', 'و', 'ف', 'ب', 'ك', 'ل', 'من', 'إلى', 'على', 'في', 'عن', 'مع', 'بعد', 'قبل']

# Common Arabic suffixes for root extraction  
ARABIC_SUFFIXES = ['ة', 'ه', 'ها', 'هم', 'هن', 'ك', 'كم', 'كن', 'ي', 'نا', 'ان', 'ين', 'ون', 'ات', 'ني', 'كما', 'هما']


def normalize_ar(s: Optional[str]) -> str:
    """Normalise an Arabic string for storage and indexing.

    Args:
        s: Input string or None.

    Returns:
        A normalised version of the string. Diacritics are removed,
        variant letters are unified and extraneous spacing is collapsed.
    """
    if s is None:
        return ""
    
    # Strip leading/trailing whitespace
    s = s.strip()
    if not s:
        return ""
    
    # Unicode normalization (NFC)
    s = unicodedata.normalize('NFC', s)
    
    # Remove diacritics
    s = ARABIC_DIACRITICS.sub("", s)
    
    # Apply character mappings
    for old_char, new_char in CHAR_MAPPINGS.items():
        s = s.replace(old_char, new_char)
    
    # Collapse multiple spaces
    s = SPACES_PATTERN.sub(" ", s)
    
    return s.strip()


def normalize_search_query(s: Optional[str]) -> str:
    """Normalize Arabic text specifically for search queries.
    
    More aggressive normalization that's suitable for matching.
    """
    normalized = normalize_ar(s)
    if not normalized:
        return ""
    
    # Additional search-specific normalizations
    # Remove punctuation except for essential Arabic punctuation
    normalized = PUNCTUATION_PATTERN.sub(' ', normalized)
    
    # Collapse spaces again after punctuation removal
    normalized = SPACES_PATTERN.sub(' ', normalized).strip()
    
    return normalized


def get_orthographic_variants(word: str) -> List[str]:
    """Generate orthographic variants of an Arabic word.
    
    Args:
        word: Arabic word
        
    Returns:
        List of common orthographic variants
    """
    if not word:
        return []
    
    variants: Set[str] = set()
    
    # Original word
    variants.add(word)
    
    # Normalized version
    normalized = normalize_ar(word)
    variants.add(normalized)
    
    # Alef variants
    for alef_form in ['ا', 'أ', 'إ', 'آ']:
        if 'ا' in normalized:
            variant = normalized.replace('ا', alef_form)
            variants.add(variant)
    
    # Yeh variants
    for yeh_form in ['ي', 'ى']:
        if 'ي' in normalized:
            variant = normalized.replace('ي', yeh_form)
            variants.add(variant)
    
    # Teh marbuta variants
    for teh_form in ['ة', 'ه']:
        if 'ه' in normalized:
            variant = normalized.replace('ه', teh_form)
            variants.add(variant)
    
    return [v for v in variants if v]


def extract_potential_roots(word: str) -> List[str]:
    """Extract potential root candidates from an Arabic word.
    
    Args:
        word: Arabic word
        
    Returns:
        List of potential root forms
    """
    if not word:
        return []
    
    word = normalize_ar(word)
    candidates: Set[str] = {word}
    
    # Remove common prefixes
    for prefix in ARABIC_PREFIXES:
        if word.startswith(prefix) and len(word) > len(prefix):
            candidates.add(word[len(prefix):])
    
    # Remove common suffixes
    for suffix in ARABIC_SUFFIXES:
        if word.endswith(suffix) and len(word) > len(suffix):
            candidates.add(word[:-len(suffix)])
    
    # Remove both prefix and suffix combinations
    for prefix in ARABIC_PREFIXES:
        for suffix in ARABIC_SUFFIXES:
            if (word.startswith(prefix) and word.endswith(suffix) and 
                len(word) > len(prefix) + len(suffix)):
                candidates.add(word[len(prefix):-len(suffix)])
    
    # Filter out very short candidates (roots are typically 3-4 letters)
    return [c for c in candidates if len(c) >= 2]


def is_arabic_text(text: str) -> bool:
    """Check if text contains Arabic characters.
    
    Args:
        text: Input text
        
    Returns:
        True if text contains Arabic characters
    """
    if not text:
        return False
    
    arabic_ranges = [
        (0x0600, 0x06FF),  # Arabic
        (0x0750, 0x077F),  # Arabic Supplement
        (0x08A0, 0x08FF),  # Arabic Extended-A
        (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
        (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
    ]
    
    for char in text:
        char_code = ord(char)
        for start, end in arabic_ranges:
            if start <= char_code <= end:
                return True
    
    return False


def clean_arabic_text(text: str, preserve_diacritics: bool = False) -> str:
    """Clean Arabic text for display purposes.
    
    Args:
        text: Input Arabic text
        preserve_diacritics: Whether to keep diacritics
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Unicode normalization
    text = unicodedata.normalize('NFC', text)
    
    if not preserve_diacritics:
        # Remove diacritics
        text = ARABIC_DIACRITICS.sub("", text)
    
    # Normalize spaces but keep structure
    text = SPACES_PATTERN.sub(" ", text).strip()
    
    return text
