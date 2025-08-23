# Arabic text normalization utilities (pure stdlib)
# - strip diacritics
# - unify alef/hamza variants
# - remove tatweel
# - normalize yaa/alef maqsura
# Keep two styles: 'safe' (minimal) and 'aggressive' (for search keys).

import re
import unicodedata

# Arabic diacritics and marks to remove
_DIACRITICS_RE = re.compile(
    "["
    "\u0610-\u061A"  # Arabic sign marks
    "\u064B-\u065F"  # harakat + small signs
    "\u0670"         # superscript alef
    "\u06D6-\u06ED"  # additional marks
    "]"
)

_TATWEEL_RE = re.compile("\u0640")

def strip_diacritics(text: str) -> str:
    return _DIACRITICS_RE.sub("", text or "")

def remove_tatweel(text: str) -> str:
    return _TATWEEL_RE.sub("", text or "")

def normalize_hamza_alef(text: str) -> str:
    # Map: \u0622, \u0623, \u0625, \u0671 -> \u0627
    if not text:
        return text
    return (text
            .replace("\u0622", "\u0627")  # ALEF WITH MADDA ABOVE -> ALEF
            .replace("\u0623", "\u0627")  # ALEF WITH HAMZA ABOVE -> ALEF
            .replace("\u0625", "\u0627")  # ALEF WITH HAMZA BELOW -> ALEF
            .replace("\u0671", "\u0627")) # ALEF WASLA -> ALEF

def normalize_yaa(text: str) -> str:
    # Map ALEF MAKSURA \u0649 -> YEH \u064A
    if not text:
        return text
    return text.replace("\u0649", "\u064A")

def safe_normalize(text: str) -> str:
    """Safe normalization: remove tatweel & diacritics; keep hamza/yaa as-is."""
    t = remove_tatweel(text)
    t = strip_diacritics(t)
    return t

def aggressive_normalize(text: str) -> str:
    """Aggressive normalization: remove diacritics & tatweel, unify alef/hamza & yaa/maqsura."""
    t = safe_normalize(text)
    t = normalize_hamza_alef(t)
    t = normalize_yaa(t)
    # NFC compose to keep indices stable
    return unicodedata.normalize("NFC", t)

def build_norm_forms(surface: str) -> dict:
    """Return both safe and aggressive normalized variants."""
    s = surface or ""
    return {
        "safe": safe_normalize(s),
        "aggr": aggressive_normalize(s),
    }
