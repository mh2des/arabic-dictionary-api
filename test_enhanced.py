#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the enhanced CAMeL features after Phase 1 implementation."""

import sqlite3
import json

def test_enhanced_features():
    """Test the enhanced morphological features."""
    
    db = sqlite3.connect('app/arabic_dict.db')
    db.row_factory = sqlite3.Row

    # Test enhanced features for a few words
    words = ['كتاب', 'مكتبة', 'يكتب', 'كاتب']

    print('🚀 PHASE 1 ENHANCEMENT RESULTS')
    print('='*50)

    for word in words:
        cursor = db.cursor()
        cursor.execute('''
            SELECT 
                lemma, 
                camel_lemmas, camel_roots, camel_pos,
                camel_genders, camel_numbers, camel_cases, 
                camel_states, camel_voices, camel_moods, 
                camel_aspects, camel_english_glosses
            FROM entries 
            WHERE lemma = ?
            LIMIT 1
        ''', (word,))
        
        result = cursor.fetchone()
        if result:
            print(f'\n📖 Word: {result["lemma"]}')
            print(f'   🔍 Lemmas: {result["camel_lemmas"]}')
            print(f'   🌳 Roots: {result["camel_roots"]}')
            print(f'   📝 POS: {result["camel_pos"]}')
            print(f'   ♂♀ Genders: {result["camel_genders"]}')
            print(f'   🔢 Numbers: {result["camel_numbers"]}')
            print(f'   📋 Cases: {result["camel_cases"]}')
            print(f'   🔄 States: {result["camel_states"]}')
            print(f'   🗣️ Voices: {result["camel_voices"]}')
            print(f'   😊 Moods: {result["camel_moods"]}')
            print(f'   ⏰ Aspects: {result["camel_aspects"]}')
            if result['camel_english_glosses']:
                glosses = result['camel_english_glosses'][:200] + '...' if len(result['camel_english_glosses']) > 200 else result['camel_english_glosses']
                print(f'   🇬🇧 English: {glosses}')

    # Coverage analysis
    print('\n\n📊 COVERAGE ANALYSIS')
    print('='*30)
    
    cursor = db.cursor()
    
    # Total entries with CAMeL analysis
    cursor.execute('SELECT COUNT(*) as count FROM entries WHERE camel_lemmas IS NOT NULL')
    total_analyzed = cursor.fetchone()['count']
    
    # Entries with each new feature
    features = [
        ('camel_genders', 'Genders'),
        ('camel_numbers', 'Numbers'), 
        ('camel_cases', 'Cases'),
        ('camel_english_glosses', 'English Glosses')
    ]
    
    for column, name in features:
        cursor.execute(f'SELECT COUNT(*) as count FROM entries WHERE {column} IS NOT NULL AND {column} != ""')
        feature_count = cursor.fetchone()['count']
        percentage = (feature_count / total_analyzed * 100) if total_analyzed > 0 else 0
        print(f'{name:15}: {feature_count:6,} / {total_analyzed:6,} ({percentage:5.1f}%)')

    db.close()

if __name__ == '__main__':
    test_enhanced_features()
