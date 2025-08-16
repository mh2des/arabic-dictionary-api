"""
Comprehensive Dialect Translation Service
Handles bidirectional translation between Arabic dialects and MSA (Fusha)
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from functools import lru_cache
import re
from difflib import SequenceMatcher

class ArabicDialectTranslator:
    """
    Comprehensive Arabic Dialect Translation Service
    
    Features:
    - Dialect -> MSA translation
    - MSA -> Dialect translation  
    - Multi-dialect support (Gulf, Egyptian, Levantine, Iraqi, etc.)
    - Semantic similarity matching
    - Category-based search (verbs, nouns, expressions, etc.)
    """
    
    def __init__(self, dialect_json_path: str, main_db_path: str):
        self.dialect_json_path = dialect_json_path
        self.main_db_path = main_db_path
        self.dialect_data = self._load_dialect_data()
        
        # Create reverse indices for fast lookup
        self.dialect_to_fusha_index = self._build_dialect_to_fusha_index()
        self.fusha_to_dialect_index = self._build_fusha_to_dialect_index()
        
        # Supported dialects
        self.supported_dialects = list(self.dialect_data['dialects'].keys())
        
    def _load_dialect_data(self) -> Dict[str, Any]:
        """Load the comprehensive dialect dictionary"""
        try:
            with open(self.dialect_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading dialect data: {e}")
            return {"dialects": {}, "metadata": {}}
    
    def _build_dialect_to_fusha_index(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build index: dialect_word -> [fusha_translations]"""
        index = {}
        
        for dialect_name, dialect_info in self.dialect_data['dialects'].items():
            for category, words in dialect_info['vocabulary'].items():
                for dialect_word, entry in words.items():
                    if dialect_word not in index:
                        index[dialect_word] = []
                    
                    index[dialect_word].append({
                        'fusha': entry['fusha'],
                        'english': entry['english'],
                        'dialect': dialect_name,
                        'category': category,
                        'pronunciation': entry.get('pronunciation', ''),
                        'usage': entry.get('usage', ''),
                        'examples': entry.get('examples', [])
                    })
        
        return index
    
    def _build_fusha_to_dialect_index(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build index: fusha_word -> [dialect_translations]"""
        index = {}
        
        for dialect_name, dialect_info in self.dialect_data['dialects'].items():
            for category, words in dialect_info['vocabulary'].items():
                for dialect_word, entry in words.items():
                    fusha = entry['fusha']
                    if fusha not in index:
                        index[fusha] = []
                    
                    index[fusha].append({
                        'dialect_word': dialect_word,
                        'dialect': dialect_name,
                        'category': category,
                        'english': entry['english'],
                        'pronunciation': entry.get('pronunciation', ''),
                        'usage': entry.get('usage', ''),
                        'examples': entry.get('examples', [])
                    })
        
        return index
    
    def _similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two Arabic strings"""
        return SequenceMatcher(None, a, b).ratio()
    
    def _find_similar_words(self, word: str, word_list: List[str], threshold: float = 0.6) -> List[Tuple[str, float]]:
        """Find words similar to the input word"""
        similar = []
        for candidate in word_list:
            similarity = self._similarity(word, candidate)
            if similarity >= threshold:
                similar.append((candidate, similarity))
        
        return sorted(similar, key=lambda x: x[1], reverse=True)
    
    def translate_dialect_to_fusha(self, dialect_word: str, target_dialects: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Translate dialect word to MSA (Fusha)
        
        Args:
            dialect_word: Word in dialect
            target_dialects: Specific dialects to search in (optional)
            
        Returns:
            Comprehensive translation data
        """
        
        # Direct lookup
        direct_matches = self.dialect_to_fusha_index.get(dialect_word, [])
        
        # Filter by target dialects if specified
        if target_dialects:
            direct_matches = [m for m in direct_matches if m['dialect'] in target_dialects]
        
        result = {
            'input_word': dialect_word,
            'found': len(direct_matches) > 0,
            'translations': direct_matches,
            'similar_words': [],
            'total_matches': len(direct_matches)
        }
        
        # If no direct match, find similar words
        if not direct_matches:
            all_dialect_words = list(self.dialect_to_fusha_index.keys())
            similar = self._find_similar_words(dialect_word, all_dialect_words, threshold=0.7)
            
            for similar_word, similarity in similar[:5]:  # Top 5 similar
                similar_matches = self.dialect_to_fusha_index[similar_word]
                if target_dialects:
                    similar_matches = [m for m in similar_matches if m['dialect'] in target_dialects]
                
                result['similar_words'].append({
                    'word': similar_word,
                    'similarity': similarity,
                    'translations': similar_matches
                })
        
        return result
    
    def translate_fusha_to_dialect(self, fusha_word: str, target_dialects: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Translate MSA (Fusha) word to dialects
        
        Args:
            fusha_word: Word in MSA
            target_dialects: Specific dialects to translate to (optional)
            
        Returns:
            Comprehensive translation data
        """
        
        # Direct lookup
        direct_matches = self.fusha_to_dialect_index.get(fusha_word, [])
        
        # Filter by target dialects if specified
        if target_dialects:
            direct_matches = [m for m in direct_matches if m['dialect'] in target_dialects]
        
        result = {
            'input_word': fusha_word,
            'found': len(direct_matches) > 0,
            'dialect_translations': direct_matches,
            'similar_words': [],
            'total_matches': len(direct_matches)
        }
        
        # If no direct match, find similar words
        if not direct_matches:
            all_fusha_words = list(self.fusha_to_dialect_index.keys())
            similar = self._find_similar_words(fusha_word, all_fusha_words, threshold=0.7)
            
            for similar_word, similarity in similar[:5]:  # Top 5 similar
                similar_matches = self.fusha_to_dialect_index[similar_word]
                if target_dialects:
                    similar_matches = [m for m in similar_matches if m['dialect'] in target_dialects]
                
                result['similar_words'].append({
                    'word': similar_word,
                    'similarity': similarity,
                    'dialect_translations': similar_matches
                })
        
        return result
    
    def get_word_meanings_and_synonyms(self, word: str, is_dialect: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive meaning and synonyms for a word
        
        Args:
            word: Input word
            is_dialect: True if word is in dialect, False if MSA
            
        Returns:
            Comprehensive analysis with meanings and synonyms
        """
        
        if is_dialect:
            # Dialect word -> get MSA equivalents and related words
            translation = self.translate_dialect_to_fusha(word)
            
            if translation['found']:
                # Get synonyms from main database
                synonyms = self._get_synonyms_from_main_db(translation['translations'][0]['fusha'])
                
                result = {
                    'input_word': word,
                    'word_type': 'dialect',
                    'primary_translation': translation['translations'][0],
                    'all_translations': translation['translations'],
                    'synonyms_in_msa': synonyms,
                    'related_dialect_words': self._find_related_dialect_words(word),
                    'usage_examples': translation['translations'][0].get('examples', [])
                }
            else:
                result = {
                    'input_word': word,
                    'word_type': 'dialect',
                    'found': False,
                    'similar_suggestions': translation['similar_words']
                }
        else:
            # MSA word -> get dialect equivalents and synonyms
            translation = self.translate_fusha_to_dialect(word)
            synonyms = self._get_synonyms_from_main_db(word)
            
            result = {
                'input_word': word,
                'word_type': 'msa',
                'dialect_translations': translation['dialect_translations'],
                'synonyms_in_msa': synonyms,
                'related_words': self._find_related_msa_words(word),
                'total_dialect_forms': len(translation['dialect_translations'])
            }
        
        return result
    
    def _get_synonyms_from_main_db(self, word: str) -> List[Dict[str, str]]:
        """Get synonyms from the main Arabic dictionary database"""
        try:
            conn = sqlite3.connect(self.main_db_path)
            cursor = conn.cursor()
            
            # Find words with same root or similar meaning
            cursor.execute("""
                SELECT DISTINCT lemma, root, pos 
                FROM entries 
                WHERE root IN (
                    SELECT root FROM entries WHERE lemma = ? OR lemma_norm = ?
                ) AND lemma != ?
                ORDER BY freq_rank ASC
                LIMIT 10
            """, (word, word, word))
            
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'word': result[0],
                    'root': result[1] or '',
                    'pos': result[2] or ''
                }
                for result in results
            ]
            
        except Exception as e:
            print(f"Error getting synonyms: {e}")
            return []
    
    def _find_related_dialect_words(self, word: str) -> List[Dict[str, Any]]:
        """Find related words in the same dialect"""
        related = []
        
        # Find words from same translation
        if word in self.dialect_to_fusha_index:
            fusha_equivalent = self.dialect_to_fusha_index[word][0]['fusha']
            dialect = self.dialect_to_fusha_index[word][0]['dialect']
            
            # Find other dialect words that translate to the same MSA word
            if fusha_equivalent in self.fusha_to_dialect_index:
                for translation in self.fusha_to_dialect_index[fusha_equivalent]:
                    if translation['dialect'] == dialect and translation['dialect_word'] != word:
                        related.append(translation)
        
        return related[:5]  # Limit to 5 related words
    
    def _find_related_msa_words(self, word: str) -> List[str]:
        """Find related MSA words"""
        try:
            conn = sqlite3.connect(self.main_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT lemma 
                FROM entries 
                WHERE root IN (
                    SELECT root FROM entries WHERE lemma = ?
                ) AND lemma != ?
                LIMIT 5
            """, (word, word))
            
            results = cursor.fetchall()
            conn.close()
            
            return [result[0] for result in results]
            
        except Exception:
            return []
    
    def search_by_category(self, category: str, dialect: Optional[str] = None) -> Dict[str, Any]:
        """
        Search words by category (verbs, family_terms, etc.)
        
        Args:
            category: Word category (verbs, adjectives, basic_words, etc.)
            dialect: Specific dialect (optional)
            
        Returns:
            Words in the specified category
        """
        
        results = {
            'category': category,
            'dialect': dialect or 'all',
            'words': [],
            'total_found': 0
        }
        
        dialects_to_search = [dialect] if dialect else self.supported_dialects
        
        for dialect_name in dialects_to_search:
            if dialect_name in self.dialect_data['dialects']:
                dialect_vocab = self.dialect_data['dialects'][dialect_name]['vocabulary']
                if category in dialect_vocab:
                    for word, entry in dialect_vocab[category].items():
                        results['words'].append({
                            'dialect_word': word,
                            'fusha': entry['fusha'],
                            'english': entry['english'],
                            'dialect': dialect_name,
                            'pronunciation': entry.get('pronunciation', ''),
                            'examples': entry.get('examples', [])
                        })
        
        results['total_found'] = len(results['words'])
        return results
    
    def get_dialect_info(self) -> Dict[str, Any]:
        """Get information about supported dialects"""
        return {
            'supported_dialects': self.supported_dialects,
            'total_entries': self.dialect_data['metadata'].get('total_entries', 0),
            'regions_included': self.dialect_data['metadata'].get('regions_included', []),
            'categories': ['basic_words', 'verbs', 'family_terms', 'adjectives', 'common_expressions', 'phrases', 'common_phrases'],
            'dialect_details': {
                name: {
                    'name': info['name'],
                    'countries': info['countries'],
                    'speakers': info['speakers'],
                    'word_count': sum(len(words) for words in info['vocabulary'].values())
                }
                for name, info in self.dialect_data['dialects'].items()
            }
        }
