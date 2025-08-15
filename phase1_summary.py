#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 1 Enhancement Summary - Show the complete impact."""

import sqlite3

def phase1_summary():
    """Generate comprehensive Phase 1 enhancement summary."""
    
    db = sqlite3.connect('app/arabic_dict.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    print('🚀 PHASE 1 ENHANCEMENT COMPLETE!')
    print('='*50)
    
    # Basic statistics
    cursor.execute('SELECT COUNT(*) as count FROM entries')
    total_entries = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM entries WHERE camel_lemmas IS NOT NULL')
    camel_analyzed = cursor.fetchone()['count']
    
    print(f'📊 BASIC STATISTICS')
    print(f'   Total dictionary entries: {total_entries:,}')
    print(f'   CAMeL analyzed entries: {camel_analyzed:,} ({camel_analyzed/total_entries*100:.1f}%)')
    
    # Enhancement features
    print(f'\n🆕 NEW FEATURES ADDED:')
    features = [
        ('camel_genders', 'Gender information'),
        ('camel_numbers', 'Number (singular/plural)'),
        ('camel_cases', 'Grammatical cases'),
        ('camel_states', 'Definiteness states'),
        ('camel_voices', 'Voice (active/passive)'),
        ('camel_moods', 'Verb moods'),
        ('camel_aspects', 'Verb aspects'),
        ('camel_english_glosses', 'English translations')
    ]
    
    for column, description in features:
        cursor.execute(f'SELECT COUNT(*) as count FROM entries WHERE {column} IS NOT NULL AND {column} != ""')
        feature_count = cursor.fetchone()['count']
        percentage = (feature_count / camel_analyzed * 100) if camel_analyzed > 0 else 0
        print(f'   {description:25}: {feature_count:5,} entries ({percentage:5.1f}%)')
    
    # Sample enhanced entries
    print(f'\n📖 SAMPLE ENHANCED ENTRIES:')
    cursor.execute('''
        SELECT lemma, camel_pos, camel_genders, camel_numbers, camel_english_glosses
        FROM entries 
        WHERE camel_genders IS NOT NULL 
        AND camel_genders != ''
        AND camel_english_glosses IS NOT NULL
        AND camel_english_glosses != ''
        LIMIT 5
    ''')
    
    for i, row in enumerate(cursor.fetchall(), 1):
        print(f'\n   {i}. {row["lemma"]}')
        print(f'      POS: {row["camel_pos"]}')
        print(f'      Gender: {row["camel_genders"]}')
        print(f'      Number: {row["camel_numbers"]}')
        glosses = row['camel_english_glosses'][:60] + '...' if len(row['camel_english_glosses']) > 60 else row['camel_english_glosses']
        print(f'      English: {glosses}')
    
    # Coverage improvement
    print(f'\n📈 COVERAGE IMPROVEMENT:')
    
    # Before Phase 1 - basic CAMeL features (4 features)
    basic_features = 4  # lemmas, roots, pos, patterns
    
    # After Phase 1 - enhanced CAMeL features (8 additional features)
    enhanced_features = 8  # genders, numbers, cases, states, voices, moods, aspects, english
    
    cursor.execute('SELECT COUNT(*) as count FROM entries WHERE camel_genders IS NOT NULL AND camel_genders != ""')
    enhanced_count = cursor.fetchone()['count']
    
    before_coverage = (camel_analyzed * basic_features) / (total_entries * 12)  # 12 total possible features
    after_coverage = ((camel_analyzed * basic_features) + (enhanced_count * enhanced_features)) / (total_entries * 12)
    
    print(f'   Before Phase 1: {before_coverage*100:.1f}% feature coverage')
    print(f'   After Phase 1:  {after_coverage*100:.1f}% feature coverage')
    print(f'   Improvement:    +{(after_coverage-before_coverage)*100:.1f} percentage points')
    
    # Impact on different word types
    print(f'\n🔍 IMPACT BY WORD TYPE:')
    word_types = ['noun', 'verb', 'adj']
    for word_type in word_types:
        cursor.execute(f'SELECT COUNT(*) as count FROM entries WHERE camel_pos LIKE "%{word_type}%"')
        type_total = cursor.fetchone()['count']
        
        cursor.execute(f'''SELECT COUNT(*) as count FROM entries 
                          WHERE camel_pos LIKE "%{word_type}%" 
                          AND camel_genders IS NOT NULL 
                          AND camel_genders != ""''')
        type_enhanced = cursor.fetchone()['count']
        
        if type_total > 0:
            percentage = (type_enhanced / type_total * 100)
            print(f'   {word_type.capitalize()}s: {type_enhanced:,} / {type_total:,} enhanced ({percentage:.1f}%)')

    print(f'\n✅ Phase 1 enhancement successfully completed!')
    print(f'   Ready for Phase 2: External resources integration')
    
    db.close()

if __name__ == '__main__':
    phase1_summary()
