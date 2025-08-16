"""
Arabic Dialect Mapping Service
Handles Ammiya (Colloquial) <-> Fusha (MSA) translation and synonym detection
"""

import json
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

@dataclass
class DialectMapping:
    ammiya_word: str
    fusha_equivalents: List[str]
    meaning: str
    dialect_region: str  # gulf, levantine, egyptian, maghrebi
    pos: str
    confidence: float

class ArabicDialectMapper:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # Core Gulf Arabic -> MSA mappings
        self.gulf_to_msa = {
            # Common Gulf Words
            "ابغى": ["أريد", "أرغب", "أود"],  # I want
            "اشلون": ["كيف"],  # How
            "شنو": ["ماذا", "ما"],  # What
            "وين": ["أين"],  # Where
            "متى": ["متى"],  # When (same)
            "ليش": ["لماذا", "لم"],  # Why
            "شگد": ["كم", "كم من"],  # How much/many
            "هسه": ["الآن", "حالياً"],  # Now
            "گلت": ["قلت"],  # I said
            "گال": ["قال"],  # He said
            "گاعد": ["جالس", "قاعد"],  # Sitting
            "يالله": ["هيا", "تعال"],  # Come on
            "زين": ["جيد", "حسن"],  # Good
            "خوش": ["جميل", "لطيف"],  # Nice/Good
            "كشخة": ["أنيق", "جميل"],  # Elegant
            "حلو": ["جميل", "لطيف"],  # Sweet/Nice
            "شايف": ["أرى", "أشاهد"],  # Seeing
            "ماشي": ["موافق", "حسناً"],  # OK/Agreed
            "خلاص": ["انتهى", "كفى"],  # Finished/Enough
            "بعدين": ["بعد ذلك", "لاحقاً"],  # Later
            "توني": ["للتو", "حديثاً"],  # Just now
            "اشوي": ["قليلاً", "نوعاً ما"],  # A little
            "وايد": ["كثير", "كثيراً"],  # A lot
            "شوية": ["قليل", "بعض"],  # A little/Some
            "ماكو": ["لا يوجد", "ليس هناك"],  # There isn't
            "اكو": ["يوجد", "هناك"],  # There is
            "هاي": ["هذه"],  # This (feminine)
            "هذا": ["هذا"],  # This (masculine) - same
            "الحين": ["الآن", "حالياً"],  # Now
            "طلعت": ["خرجت", "ذهبت"],  # I went out
            "رحت": ["ذهبت"],  # I went
            "جيت": ["جئت", "أتيت"],  # I came
            "شربت": ["شربت"],  # I drank - same
            "اكلت": ["أكلت"],  # I ate
            "نمت": ["نمت"],  # I slept - same
            "صحيت": ["استيقظت"],  # I woke up
            "تعال": ["تعال"],  # Come - same
            "روح": ["اذهب"],  # Go
            "قعد": ["جلس"],  # Sit
            "قوم": ["قم", "انهض"],  # Stand up
            "نزل": ["انزل", "اهبط"],  # Go down
            "طلع": ["اصعد", "ارتق"],  # Go up
            
            # Verbs - Gulf to MSA
            "اسوي": ["أفعل", "أعمل"],  # I do
            "اشتغل": ["أعمل"],  # I work - same
            "اقرا": ["أقرأ"],  # I read
            "اكتب": ["أكتب"],  # I write - same
            "اسمع": ["أسمع"],  # I hear - same
            "اشوف": ["أرى", "أنظر"],  # I see
            "اتكلم": ["أتحدث", "أتكلم"],  # I speak
            "افهم": ["أفهم"],  # I understand - same
            "اعرف": ["أعرف"],  # I know - same
            "احب": ["أحب"],  # I love - same
            "اكره": ["أكره"],  # I hate - same
            "اخاف": ["أخاف"],  # I fear - same
            "افرح": ["أفرح"],  # I'm happy - same
            "ازعل": ["أحزن", "أغضب"],  # I'm upset
            
            # Family terms
            "اهلي": ["أهلي", "عائلتي"],  # My family
            "امي": ["أمي", "والدتي"],  # My mother
            "ابوي": ["أبي", "والدي"],  # My father
            "اخوي": ["أخي"],  # My brother - same
            "اختي": ["أختي"],  # My sister - same
            "يدي": ["جدي"],  # My grandfather
            "يدتي": ["جدتي"],  # My grandmother
            "عمي": ["عمي"],  # My uncle - same
            "خالي": ["خالي"],  # My uncle (maternal) - same
            "عمتي": ["عمتي"],  # My aunt - same
            "خالتي": ["خالتي"],  # My aunt (maternal) - same
            
            # Food terms
            "مشخول": ["مشغول"],  # Busy - same concept
            "جوعان": ["جائع"],  # Hungry
            "عطشان": ["عطش"],  # Thirsty
            "شبعان": ["شبع"],  # Full (from eating)
            "تعبان": ["متعب"],  # Tired
            "مريض": ["مريض"],  # Sick - same
            
            # Time expressions
            "بكرة": ["غداً"],  # Tomorrow
            "امس": ["أمس"],  # Yesterday - same
            "اليوم": ["اليوم"],  # Today - same
            "الليلة": ["الليلة"],  # Tonight - same
            "الصبح": ["الصباح"],  # Morning
            "الظهر": ["الظهر"],  # Noon - same
            "العصر": ["العصر"],  # Afternoon - same
            "المغرب": ["المغرب"],  # Sunset - same
            "العشا": ["العشاء"],  # Dinner
        }
        
        # Egyptian Arabic -> MSA mappings
        self.egyptian_to_msa = {
            "ايه": ["ماذا", "ما"],  # What
            "فين": ["أين"],  # Where  
            "ازيك": ["كيف حالك"],  # How are you
            "كدة": ["هكذا"],  # Like this
            "علشان": ["لأن", "من أجل"],  # Because/For
            "عايز": ["أريد"],  # I want
            "عاوز": ["أريد"],  # I want
            "مش": ["لست", "ليس"],  # Not
            "برضو": ["أيضاً"],  # Also
            "يلا": ["هيا", "تعال"],  # Come on
            "خلاص": ["انتهى", "كفى"],  # Finished
            "كمان": ["أيضاً"],  # Also
            "شوية": ["قليل"],  # A little
            "كتير": ["كثير"],  # A lot
        }
        
        # Levantine Arabic -> MSA mappings  
        self.levantine_to_msa = {
            "شو": ["ماذا", "ما"],  # What
            "وين": ["أين"],  # Where
            "كيف": ["كيف"],  # How - same
            "ليش": ["لماذا"],  # Why
            "بدي": ["أريد"],  # I want
            "مش": ["لست", "ليس"],  # Not
            "كمان": ["أيضاً"],  # Also
            "هيك": ["هكذا"],  # Like this
            "هلق": ["الآن"],  # Now
            "بكرا": ["غداً"],  # Tomorrow
        }
        
        # Combine all dialects
        self.dialect_to_msa = {
            **self.gulf_to_msa,
            **self.egyptian_to_msa, 
            **self.levantine_to_msa
        }
        
        # Create reverse mapping (MSA -> Dialect)
        self.msa_to_dialect = {}
        for dialect_word, msa_words in self.dialect_to_msa.items():
            for msa_word in msa_words:
                if msa_word not in self.msa_to_dialect:
                    self.msa_to_dialect[msa_word] = []
                self.msa_to_dialect[msa_word].append(dialect_word)
    
    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def find_msa_equivalents(self, ammiya_word: str) -> List[Dict[str, Any]]:
        """Find MSA equivalents for a dialect word."""
        results = []
        
        # Direct mapping lookup
        if ammiya_word in self.dialect_to_msa:
            msa_words = self.dialect_to_msa[ammiya_word]
            
            # Get detailed info from database for each MSA word
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            for msa_word in msa_words:
                cursor.execute("""
                    SELECT lemma, lemma_norm, root, pos, subpos, 
                           buckwalter_transliteration, phonetic_transcription
                    FROM entries 
                    WHERE lemma = ? OR lemma_norm = ?
                    LIMIT 1
                """, (msa_word, msa_word))
                
                db_result = cursor.fetchone()
                
                result = {
                    "ammiya_input": ammiya_word,
                    "fusha_equivalent": msa_word,
                    "confidence": 0.9,  # High confidence for direct mappings
                    "mapping_type": "direct_dialect_mapping",
                    "database_info": None
                }
                
                if db_result:
                    lemma, lemma_norm, root, pos, subpos, buckwalter, phonetic = db_result
                    result["database_info"] = {
                        "lemma": lemma,
                        "lemma_norm": lemma_norm,
                        "root": root,
                        "pos": pos,
                        "subpos": subpos,
                        "buckwalter": buckwalter,
                        "phonetic": json.loads(phonetic) if phonetic else None
                    }
                    result["confidence"] = 0.95  # Higher confidence with DB confirmation
                
                results.append(result)
            
            conn.close()
        
        # If no direct mapping, try fuzzy matching
        if not results:
            results.extend(self._fuzzy_search_msa(ammiya_word))
        
        return results
    
    def find_dialect_equivalents(self, msa_word: str) -> List[Dict[str, Any]]:
        """Find dialect equivalents for an MSA word."""
        results = []
        
        # Direct reverse mapping lookup
        if msa_word in self.msa_to_dialect:
            dialect_words = self.msa_to_dialect[msa_word]
            
            for dialect_word in dialect_words:
                results.append({
                    "fusha_input": msa_word,
                    "ammiya_equivalent": dialect_word,
                    "dialect_region": self._detect_dialect_region(dialect_word),
                    "confidence": 0.9,
                    "mapping_type": "direct_msa_mapping"
                })
        
        # Also search database for the MSA word
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT lemma, lemma_norm, root, pos, subpos, 
                   buckwalter_transliteration, phonetic_transcription
            FROM entries 
            WHERE lemma = ? OR lemma_norm = ?
            LIMIT 1
        """, (msa_word, msa_word))
        
        db_result = cursor.fetchone()
        if db_result:
            lemma, lemma_norm, root, pos, subpos, buckwalter, phonetic = db_result
            
            # Add database info to existing results
            for result in results:
                result["fusha_database_info"] = {
                    "lemma": lemma,
                    "lemma_norm": lemma_norm,
                    "root": root,
                    "pos": pos,
                    "subpos": subpos,
                    "buckwalter": buckwalter,
                    "phonetic": json.loads(phonetic) if phonetic else None
                }
        
        conn.close()
        
        # If no results, try related words from same root
        if not results and db_result and db_result[2]:  # has root
            results.extend(self._find_root_based_dialect_matches(db_result[2], msa_word))
        
        return results
    
    def _fuzzy_search_msa(self, ammiya_word: str) -> List[Dict[str, Any]]:
        """Fuzzy search for similar MSA words."""
        results = []
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Try different normalization approaches
        normalized_variants = [
            ammiya_word,
            ammiya_word.replace('ا', 'أ'),
            ammiya_word.replace('أ', 'ا'),
            ammiya_word.replace('ى', 'ي'),
            ammiya_word.replace('ي', 'ى'),
            ammiya_word.replace('ة', 'ه'),
            ammiya_word.replace('ه', 'ة'),
        ]
        
        for variant in set(normalized_variants):
            cursor.execute("""
                SELECT lemma, lemma_norm, root, pos, subpos, 
                       buckwalter_transliteration, phonetic_transcription
                FROM entries 
                WHERE lemma LIKE ? OR lemma_norm LIKE ?
                ORDER BY freq_rank ASC
                LIMIT 5
            """, (f"%{variant}%", f"%{variant}%"))
            
            fuzzy_results = cursor.fetchall()
            
            for result in fuzzy_results:
                lemma, lemma_norm, root, pos, subpos, buckwalter, phonetic = result
                
                results.append({
                    "ammiya_input": ammiya_word,
                    "fusha_equivalent": lemma,
                    "confidence": 0.6,  # Lower confidence for fuzzy matches
                    "mapping_type": "fuzzy_search",
                    "database_info": {
                        "lemma": lemma,
                        "lemma_norm": lemma_norm,
                        "root": root,
                        "pos": pos,
                        "subpos": subpos,
                        "buckwalter": buckwalter,
                        "phonetic": json.loads(phonetic) if phonetic else None
                    }
                })
        
        conn.close()
        return results[:5]  # Limit results
    
    def _find_root_based_dialect_matches(self, root: str, msa_word: str) -> List[Dict[str, Any]]:
        """Find dialect words that might relate to the same root."""
        results = []
        
        # Look for dialect words in our mappings that might share meaning
        for dialect_word, msa_equivalents in self.dialect_to_msa.items():
            # Check if any equivalent shares meaning concept
            if any(equiv in msa_word or msa_word in equiv for equiv in msa_equivalents):
                results.append({
                    "fusha_input": msa_word,
                    "ammiya_equivalent": dialect_word,
                    "dialect_region": self._detect_dialect_region(dialect_word),
                    "confidence": 0.7,
                    "mapping_type": "semantic_similarity"
                })
        
        return results[:3]  # Limit results
    
    def _detect_dialect_region(self, dialect_word: str) -> str:
        """Detect which dialect region a word belongs to."""
        if dialect_word in self.gulf_to_msa:
            return "gulf"
        elif dialect_word in self.egyptian_to_msa:
            return "egyptian"
        elif dialect_word in self.levantine_to_msa:
            return "levantine"
        else:
            return "unknown"
    
    def get_synonyms_and_meaning(self, word: str, is_dialect: bool = True) -> Dict[str, Any]:
        """Get comprehensive word analysis with synonyms and meanings."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        result = {
            "query_word": word,
            "is_dialect": is_dialect,
            "translations": [],
            "synonyms": [],
            "meanings": [],
            "related_words": []
        }
        
        if is_dialect:
            # Ammiya -> Fusha
            translations = self.find_msa_equivalents(word)
            result["translations"] = translations
            
            # For each translation, find synonyms
            for translation in translations:
                if translation.get("database_info") and translation["database_info"].get("root"):
                    root = translation["database_info"]["root"]
                    
                    # Find words with same root
                    cursor.execute("""
                        SELECT DISTINCT lemma, pos, freq_rank
                        FROM entries 
                        WHERE root = ?
                        ORDER BY freq_rank ASC
                        LIMIT 10
                    """, (root,))
                    
                    root_words = cursor.fetchall()
                    result["synonyms"].extend([
                        {"word": rw[0], "pos": rw[1], "freq_rank": rw[2]}
                        for rw in root_words
                    ])
        else:
            # Fusha -> Ammiya
            translations = self.find_dialect_equivalents(word)
            result["translations"] = translations
            
            # Find MSA synonyms
            cursor.execute("""
                SELECT lemma, lemma_norm, root, pos
                FROM entries 
                WHERE lemma = ? OR lemma_norm = ?
                LIMIT 1
            """, (word, word))
            
            msa_result = cursor.fetchone()
            if msa_result and msa_result[2]:  # has root
                root = msa_result[2]
                
                cursor.execute("""
                    SELECT DISTINCT lemma, pos, freq_rank
                    FROM entries 
                    WHERE root = ?
                    ORDER BY freq_rank ASC
                    LIMIT 10
                """, (root,))
                
                root_words = cursor.fetchall()
                result["synonyms"].extend([
                    {"word": rw[0], "pos": rw[1], "freq_rank": rw[2]}
                    for rw in root_words
                ])
        
        conn.close()
        return result
