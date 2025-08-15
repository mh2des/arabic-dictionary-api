#!/usr/bin/env python3
"""
Enhanced Root Analysis and Extraction
====================================

This script significantly improves root coverage by using multiple strategies:
1. CAMeL Tools root extraction from existing data
2. Pattern-based root extraction for Arabic words
3. Morphological analysis for root derivation
4. Cross-reference with existing roots for validation
"""

import sqlite3
import json
import re
from typing import Optional, List, Set
import unicodedata

class RootEnhancer:
    def __init__(self, db_path: str = "app/arabic_dict.db"):
        self.db_path = db_path
        self.stats = {
            "processed": 0,
            "roots_added": 0,
            "camel_roots": 0,
            "pattern_roots": 0,
            "morphological_roots": 0
        }
        
        # Common Arabic root patterns (traditional 3-letter roots)
        self.arabic_letters = set('ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأإ')
        
    def extract_root_from_camel_data(self, camel_roots: str) -> Optional[str]:
        """Extract clean root from CAMeL Tools data"""
        if not camel_roots:
            return None
            
        try:
            if camel_roots.startswith('[') and camel_roots.endswith(']'):
                roots_list = json.loads(camel_roots)
                if roots_list and len(roots_list) > 0:
                    # Get the first root and clean it
                    root = roots_list[0].strip()
                    if root and len(root) >= 3:
                        return self.normalize_root_format(root)
        except:
            # If JSON parsing fails, try direct processing
            if camel_roots and len(camel_roots) >= 3:
                return self.normalize_root_format(camel_roots)
        
        return None
    
    def normalize_root_format(self, root: str) -> str:
        """Normalize root to consistent format: 'ك ت ب'"""
        # Remove brackets, quotes, and extra spaces
        root = re.sub(r'[\[\]\"\'()]', '', root)
        root = root.strip()
        
        # If already spaced, return as is
        if ' ' in root and len(root.split()) >= 2:
            return root
        
        # Add spaces between Arabic letters
        if len(root) >= 3 and all(c in self.arabic_letters for c in root):
            return ' '.join(root)
            
        return root
    
    def extract_root_from_pattern(self, lemma: str) -> Optional[str]:
        """Extract root using morphological patterns"""
        if not lemma or len(lemma) < 3:
            return None
            
        # Remove diacritics
        lemma_clean = self.remove_diacritics(lemma)
        
        # Extract consonantal root (remove common prefixes/suffixes)
        root_candidates = self.extract_consonantal_root(lemma_clean)
        
        if root_candidates and len(root_candidates) >= 3:
            return self.normalize_root_format(root_candidates)
        
        return None
    
    def remove_diacritics(self, text: str) -> str:
        """Remove Arabic diacritical marks"""
        diacritics = 'ًٌٍَُِّْٰٱ'
        for diacritic in diacritics:
            text = text.replace(diacritic, '')
        return text
    
    def extract_consonantal_root(self, word: str) -> str:
        """Extract consonantal root by removing common patterns"""
        # Remove common prefixes
        prefixes = ['ال', 'و', 'ف', 'ب', 'ل', 'ك', 'أ', 'إ', 'م', 'ت', 'ي', 'ن']
        for prefix in prefixes:
            if word.startswith(prefix) and len(word) > len(prefix) + 2:
                word = word[len(prefix):]
                break
        
        # Remove common suffixes  
        suffixes = ['ة', 'ات', 'ان', 'ون', 'ين', 'ها', 'هم', 'هن', 'ه', 'ك', 'ت', 'ى']
        for suffix in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                word = word[:-len(suffix)]
                break
        
        # Remove weak letters in certain positions (advanced pattern)
        if len(word) >= 4:
            # Remove weak letters (و، ي، ا) in middle positions
            weak_letters = 'ويا'
            filtered = []
            for i, char in enumerate(word):
                if i == 0 or i == len(word)-1:  # Keep first and last
                    filtered.append(char)
                elif char not in weak_letters:  # Keep strong consonants
                    filtered.append(char)
                elif len(filtered) < 3:  # Keep if we need more letters
                    filtered.append(char)
            word = ''.join(filtered)
        
        return word[:4] if len(word) > 4 else word  # Limit to reasonable length
    
    def validate_root(self, root: str, existing_roots: Set[str]) -> bool:
        """Validate if extracted root makes sense"""
        if not root or len(root) < 3:
            return False
            
        # Check if similar roots exist
        root_letters = set(root.replace(' ', ''))
        for existing in existing_roots:
            existing_letters = set(existing.replace(' ', ''))
            if len(root_letters.intersection(existing_letters)) >= 2:
                return True
        
        # Check if it contains valid Arabic root letters
        clean_root = root.replace(' ', '')
        if len(clean_root) >= 3 and all(c in self.arabic_letters for c in clean_root):
            return True
            
        return False
    
    def enhance_roots(self, limit: int = None):
        """Main enhancement function"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("🔍 Loading existing roots for validation...")
        cursor.execute("SELECT DISTINCT root FROM entries WHERE root IS NOT NULL AND root != ''")
        existing_roots = {row[0] for row in cursor.fetchall()}
        print(f"   Found {len(existing_roots)} existing root patterns")
        
        # Get entries missing roots
        query = """
        SELECT id, lemma, camel_roots, pos
        FROM entries 
        WHERE root IS NULL OR root = ''
        """
        if limit:
            query += f" LIMIT {limit}"
            
        cursor.execute(query)
        entries = cursor.fetchall()
        
        print(f"🚀 Processing {len(entries)} entries without roots...")
        
        for entry_id, lemma, camel_roots, pos in entries:
            self.stats["processed"] += 1
            extracted_root = None
            method_used = None
            
            # Strategy 1: Extract from CAMeL data
            if camel_roots:
                extracted_root = self.extract_root_from_camel_data(camel_roots)
                if extracted_root:
                    method_used = "camel"
                    self.stats["camel_roots"] += 1
            
            # Strategy 2: Pattern-based extraction
            if not extracted_root:
                extracted_root = self.extract_root_from_pattern(lemma)
                if extracted_root and self.validate_root(extracted_root, existing_roots):
                    method_used = "pattern"
                    self.stats["pattern_roots"] += 1
                else:
                    extracted_root = None
            
            # Update database if we found a root
            if extracted_root:
                try:
                    cursor.execute("""
                        UPDATE entries 
                        SET root = ?
                        WHERE id = ?
                    """, (extracted_root, entry_id))
                    
                    self.stats["roots_added"] += 1
                    existing_roots.add(extracted_root)  # Add to validation set
                    
                    if self.stats["processed"] % 1000 == 0:
                        print(f"   Processed {self.stats['processed']:,} entries, added {self.stats['roots_added']:,} roots")
                        conn.commit()  # Commit periodically
                except Exception as e:
                    print(f"   Warning: Could not update entry {entry_id}: {e}")
                    continue
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Root enhancement completed!")
        print(f"   Processed: {self.stats['processed']:,} entries")
        print(f"   Roots added: {self.stats['roots_added']:,}")
        print(f"   From CAMeL: {self.stats['camel_roots']:,}")
        print(f"   From patterns: {self.stats['pattern_roots']:,}")
        
        return self.stats["roots_added"] > 0

def main():
    """Run root enhancement"""
    enhancer = RootEnhancer()
    
    print("=== ENHANCED ROOT EXTRACTION ===")
    print("Improving root coverage using multiple strategies...")
    
    # First, try a batch of 5000 to see results
    success = enhancer.enhance_roots(limit=5000)
    
    if success:
        # Check new coverage
        conn = sqlite3.connect("app/arabic_dict.db")
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM entries')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM entries WHERE root IS NOT NULL AND root != ""')
        with_roots = cursor.fetchone()[0]
        
        print(f"\n📊 NEW ROOT COVERAGE:")
        print(f"   Total entries: {total:,}")
        print(f"   With roots: {with_roots:,}")
        print(f"   Coverage: {with_roots/total*100:.1f}%")
        print(f"   Improvement: +{enhancer.stats['roots_added']:,} roots")
        
        conn.close()

if __name__ == "__main__":
    main()
