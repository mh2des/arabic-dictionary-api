#!/usr/bin/env python3
"""
Test the Enhanced Screen API endpoints directly
"""

import sqlite3
import os
import json
from typing import Dict, Any

# Database connection
def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), "app/arabic_dict.db")
    return sqlite3.connect(db_path)

# Test Screen 1: Word Info
def test_screen_1_info(lemma: str):
    """Test Screen 1: Basic word information"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT lemma, root, pos, pattern, register
        FROM entries 
        WHERE lemma = ?
        LIMIT 1
    ''', (lemma,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return {"error": "Word not found"}
    
    lemma_db, root, pos, pattern, register = result
    
    return {
        "screen": 1,
        "lemma": lemma_db,
        "root": root,
        "pos": pos or "unknown",
        "pattern": pattern,
        "register": register,
        "script": "Arabic",
        "quality": "verified"
    }

# Test Screen 2: Word Senses
def test_screen_2_senses(lemma: str):
    """Test Screen 2: Word senses/definitions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT lemma, data, structured_senses
        FROM entries 
        WHERE lemma = ?
        LIMIT 1
    ''', (lemma,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return {"error": "Word not found"}
    
    lemma_db, data, structured_senses = result
    
    # Parse JSON data
    senses = []
    if structured_senses:
        try:
            sense_data = json.loads(structured_senses)
            senses = sense_data if isinstance(sense_data, list) else [sense_data]
        except:
            pass
    
    if not senses:
        # Create default sense
        senses = [{
            "sense_id": 1,
            "definition_ar": f"تعريف للكلمة {lemma}",
            "definition_en": f"Definition for word: {lemma}",
            "domain": "general",
            "frequency": "common"
        }]
    
    return {
        "screen": 2,
        "lemma": lemma_db,
        "senses": senses
    }

# Test Screen 5: Pronunciation
def test_screen_5_pronunciation(lemma: str):
    """Test Screen 5: Pronunciation data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT lemma, phonetic_transcription, buckwalter_transliteration
        FROM entries 
        WHERE lemma = ?
        LIMIT 1
    ''', (lemma,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return {"error": "Word not found"}
    
    lemma_db, phonetic, buckwalter = result
    
    return {
        "screen": 5,
        "lemma": lemma_db,
        "buckwalter": buckwalter,
        "ipa": phonetic,
        "simplified": buckwalter,
        "alternatives": []
    }

def main():
    """Test all enhanced screen endpoints"""
    print("=== Enhanced Arabic Dictionary Screen API Test ===")
    
    # Test with sample words from database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get 3 sample words
    cursor.execute("SELECT lemma FROM entries LIMIT 3")
    words = cursor.fetchall()
    conn.close()
    
    if not words:
        print("ERROR: No words found in database!")
        return
    
    print(f"Testing with {len(words)} sample words...")
    
    for i, (word,) in enumerate(words, 1):
        print(f"\n--- Test {i}: Word '{word}' ---")
        
        # Test Screen 1: Info
        info_result = test_screen_1_info(word)
        print(f"Screen 1 (Info): {json.dumps(info_result, ensure_ascii=False, indent=2)}")
        
        # Test Screen 2: Senses
        senses_result = test_screen_2_senses(word)
        print(f"Screen 2 (Senses): {json.dumps(senses_result, ensure_ascii=False, indent=2)}")
        
        # Test Screen 5: Pronunciation
        pronunciation_result = test_screen_5_pronunciation(word)
        print(f"Screen 5 (Pronunciation): {json.dumps(pronunciation_result, ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    main()
