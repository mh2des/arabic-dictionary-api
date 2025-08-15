#!/usr/bin/env python3
"""
Comprehensive Screen Coverage Enhancement Analysis
=================================================

Since we're having database update issues, let's focus on analyzing and 
improving other aspects of screen coverage that we CAN enhance without 
complex database modifications.
"""

import sqlite3
import json

def analyze_all_screen_coverage():
    """Analyze coverage across all screens and identify improvement opportunities"""
    
    conn = sqlite3.connect('app/arabic_dict.db')
    cursor = conn.cursor()
    
    print("=== COMPREHENSIVE SCREEN COVERAGE ANALYSIS ===")
    print("Identifying areas for maximum impact improvements...\n")
    
    # Get basic stats
    cursor.execute('SELECT COUNT(*) FROM entries')
    total = cursor.fetchone()[0]
    
    print(f"📊 DATABASE OVERVIEW:")
    print(f"   Total entries: {total:,}")
    print()
    
    # Screen 1: Info (lemma, root, pos, pattern, register)
    print("🎯 SCREEN 1 - WORD INFO:")
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE lemma IS NOT NULL')
    lemma_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE root IS NOT NULL AND root != ""')
    root_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE pos IS NOT NULL AND pos != ""')
    pos_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE pattern IS NOT NULL AND pattern != ""')
    pattern_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE register IS NOT NULL AND register != ""')
    register_count = cursor.fetchone()[0]
    
    print(f"   ✅ Lemma: {lemma_count:,}/{total:,} ({lemma_count/total*100:.1f}%)")
    print(f"   📚 Root: {root_count:,}/{total:,} ({root_count/total*100:.1f}%)")
    print(f"   🏷️ POS: {pos_count:,}/{total:,} ({pos_count/total*100:.1f}%)")
    print(f"   🔤 Pattern: {pattern_count:,}/{total:,} ({pattern_count/total*100:.1f}%)")
    print(f"   📋 Register: {register_count:,}/{total:,} ({register_count/total*100:.1f}%)")
    
    screen1_avg = (lemma_count + root_count + pos_count + pattern_count + register_count) / (5 * total) * 100
    print(f"   📈 Screen 1 Average: {screen1_avg:.1f}%")
    print()
    
    # Screen 2: Senses (definitions)
    print("🎯 SCREEN 2 - WORD SENSES:")
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE structured_senses IS NOT NULL AND structured_senses != ""')
    structured_senses_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE data IS NOT NULL AND data != ""')
    data_count = cursor.fetchone()[0]
    
    print(f"   📖 Structured senses: {structured_senses_count:,}/{total:,} ({structured_senses_count/total*100:.1f}%)")
    print(f"   📝 Data field: {data_count:,}/{total:,} ({data_count/total*100:.1f}%)")
    
    screen2_avg = max(structured_senses_count, data_count) / total * 100
    print(f"   📈 Screen 2 Readiness: {screen2_avg:.1f}%")
    print()
    
    # Screen 4: Relations (semantic)
    print("🎯 SCREEN 4 - WORD RELATIONS:")
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE semantic_relations IS NOT NULL AND semantic_relations != ""')
    semantic_relations_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE structured_relations IS NOT NULL AND structured_relations != ""')
    structured_relations_count = cursor.fetchone()[0]
    
    print(f"   🔗 Semantic relations: {semantic_relations_count:,}/{total:,} ({semantic_relations_count/total*100:.1f}%)")
    print(f"   🏗️ Structured relations: {structured_relations_count:,}/{total:,} ({structured_relations_count/total*100:.1f}%)")
    
    screen4_avg = max(semantic_relations_count, structured_relations_count) / total * 100
    print(f"   📈 Screen 4 Readiness: {screen4_avg:.1f}%")
    print()
    
    # Screen 5: Pronunciation
    print("🎯 SCREEN 5 - PRONUNCIATION:")
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE phonetic_transcription IS NOT NULL AND phonetic_transcription != ""')
    phonetic_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE buckwalter_transliteration IS NOT NULL AND buckwalter_transliteration != ""')
    buckwalter_count = cursor.fetchone()[0]
    
    print(f"   🔊 Phonetic: {phonetic_count:,}/{total:,} ({phonetic_count/total*100:.1f}%)")
    print(f"   🔤 Buckwalter: {buckwalter_count:,}/{total:,} ({buckwalter_count/total*100:.1f}%)")
    
    screen5_avg = max(phonetic_count, buckwalter_count) / total * 100
    print(f"   📈 Screen 5 Readiness: {screen5_avg:.1f}%")
    print()
    
    # Screen 6: Dialects
    print("🎯 SCREEN 6 - DIALECT VARIANTS:")
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE cross_dialect_variants IS NOT NULL AND cross_dialect_variants != ""')
    dialect_variants_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE camel_lemmas IS NOT NULL AND camel_lemmas != ""')
    camel_lemmas_count = cursor.fetchone()[0]
    
    print(f"   🌍 Cross-dialect variants: {dialect_variants_count:,}/{total:,} ({dialect_variants_count/total*100:.1f}%)")
    print(f"   🐪 CAMeL lemmas: {camel_lemmas_count:,}/{total:,} ({camel_lemmas_count/total*100:.1f}%)")
    
    screen6_avg = max(dialect_variants_count, camel_lemmas_count) / total * 100
    print(f"   📈 Screen 6 Readiness: {screen6_avg:.1f}%")
    print()
    
    # Screen 7: Morphology
    print("🎯 SCREEN 7 - MORPHOLOGY:")
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE advanced_morphology IS NOT NULL AND advanced_morphology != ""')
    adv_morph_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE camel_morphology IS NOT NULL AND camel_morphology != ""')
    camel_morph_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM entries WHERE enhanced_morphology IS NOT NULL AND enhanced_morphology != ""')
    enhanced_morph_count = cursor.fetchone()[0]
    
    print(f"   🧬 Advanced morphology: {adv_morph_count:,}/{total:,} ({adv_morph_count/total*100:.1f}%)")
    print(f"   🐪 CAMeL morphology: {camel_morph_count:,}/{total:,} ({camel_morph_count/total*100:.1f}%)")
    print(f"   ✨ Enhanced morphology: {enhanced_morph_count:,}/{total:,} ({enhanced_morph_count/total*100:.1f}%)")
    
    screen7_avg = max(adv_morph_count, camel_morph_count, enhanced_morph_count) / total * 100
    print(f"   📈 Screen 7 Readiness: {screen7_avg:.1f}%")
    print()
    
    # Overall summary
    print("📋 OVERALL SCREEN READINESS SUMMARY:")
    screens = [
        (1, screen1_avg),
        (2, screen2_avg),
        (4, screen4_avg),
        (5, screen5_avg),
        (6, screen6_avg),
        (7, screen7_avg)
    ]
    
    overall_avg = sum(avg for _, avg in screens) / len(screens)
    
    for screen_num, avg in screens:
        status = "🟢 EXCELLENT" if avg >= 90 else "🟡 GOOD" if avg >= 70 else "🔴 NEEDS WORK"
        print(f"   Screen {screen_num}: {avg:.1f}% {status}")
    
    print(f"\n🎯 OVERALL READINESS: {overall_avg:.1f}%")
    print()
    
    # Identify top improvement opportunities
    print("🚀 TOP IMPROVEMENT OPPORTUNITIES:")
    
    # Find screens with lowest coverage
    screens_sorted = sorted(screens, key=lambda x: x[1])
    
    print(f"1. 🎯 Screen {screens_sorted[0][0]} needs most improvement ({screens_sorted[0][1]:.1f}%)")
    
    if screens_sorted[0][0] == 1:
        print("   💡 Focus on: Root extraction (can improve to ~90%)")
        print("   💡 Focus on: Pattern recognition from existing morphology")
    elif screens_sorted[0][0] == 2:
        print("   💡 Focus on: Generate structured senses from existing data")
    elif screens_sorted[0][0] == 4:
        print("   💡 Focus on: Extract relations from semantic features")
    
    print(f"2. 🎯 Screen {screens_sorted[1][0]} second priority ({screens_sorted[1][1]:.1f}%)")
    print(f"3. 🎯 Screen {screens_sorted[2][0]} third priority ({screens_sorted[2][1]:.1f}%)")
    print()
    
    # Show what's already excellent
    excellent_screens = [s for s in screens if s[1] >= 90]
    if excellent_screens:
        print("✅ SCREENS ALREADY EXCELLENT:")
        for screen_num, avg in excellent_screens:
            print(f"   Screen {screen_num}: {avg:.1f}% - Production ready!")
    
    conn.close()
    
    print(f"\n🎉 CONCLUSION:")
    print(f"   Your Arabic Dictionary has {overall_avg:.1f}% overall screen readiness!")
    print(f"   {len(excellent_screens)}/6 screens are already production-ready!")
    
    return screens

if __name__ == "__main__":
    analyze_all_screen_coverage()
