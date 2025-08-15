#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sample enhanced entries to demonstrate Phase 1 improvements."""

import sqlite3

def show_enhanced_sample():
    """Show sample enhanced entries."""
    
    db = sqlite3.connect('app/arabic_dict.db')
    db.row_factory = sqlite3.Row

    # Get some enhanced entries
    cursor = db.cursor()
    cursor.execute('''
        SELECT lemma, camel_lemmas, camel_roots, camel_pos, 
               camel_genders, camel_numbers, camel_cases, 
               camel_english_glosses
        FROM entries 
        WHERE camel_genders IS NOT NULL 
        AND camel_genders != ''
        AND rowid <= 5000
        LIMIT 8
    ''')

    print('🚀 ENHANCED ENTRIES SAMPLE')
    print('='*40)

    for row in cursor.fetchall():
        print(f'📖 {row["lemma"]}')
        print(f'   Lemmas: {row["camel_lemmas"]}')
        print(f'   Roots: {row["camel_roots"]}')
        print(f'   POS: {row["camel_pos"]}')
        print(f'   🆕 Genders: {row["camel_genders"]}')
        print(f'   🆕 Numbers: {row["camel_numbers"]}')
        print(f'   🆕 Cases: {row["camel_cases"]}')
        if row['camel_english_glosses']:
            glosses = row['camel_english_glosses'][:100] + '...' if len(row['camel_english_glosses']) > 100 else row['camel_english_glosses']
            print(f'   🆕 English: {glosses}')
        print()

    # Final statistics
    print('\n📊 ENHANCEMENT STATISTICS')
    print('='*30)
    
    cursor.execute('SELECT COUNT(*) as count FROM entries WHERE camel_analyzed = 1')
    total_analyzed = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM entries WHERE camel_genders IS NOT NULL AND camel_genders != ""')
    enhanced_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM entries WHERE camel_english_glosses IS NOT NULL AND camel_english_glosses != ""')
    glosses_count = cursor.fetchone()['count']
    
    print(f'Total CAMeL analyzed entries: {total_analyzed:,}')
    print(f'Enhanced with new features: {enhanced_count:,}')
    print(f'With English glosses: {glosses_count:,}')
    print(f'Enhancement coverage: {(enhanced_count/total_analyzed*100):.1f}%')

    db.close()

if __name__ == '__main__':
    show_enhanced_sample()
