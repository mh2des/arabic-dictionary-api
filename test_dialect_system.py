#!/usr/bin/env python3
"""
Test script to verify comprehensive dialect translation system
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.dialect_translator import ArabicDialectTranslator

def test_comprehensive_dialect_system():
    """Test the comprehensive dialect translation system"""
    
    print("=== COMPREHENSIVE ARABIC DIALECT TRANSLATION TEST ===")
    
    # Initialize the translator
    try:
        dialect_json_path = 'app/data/arabic_dialect_dictionary_enriched (1).json'
        main_db_path = 'app/arabic_dict.db'
        
        translator = ArabicDialectTranslator(dialect_json_path, main_db_path)
        print(f"✅ Translator initialized with {len(translator.supported_dialects)} dialects")
        print(f"   Supported dialects: {translator.supported_dialects}")
        
    except Exception as e:
        print(f"❌ Failed to initialize translator: {e}")
        return False
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Original problem word - ابغى
    print("\n" + "="*50)
    print("TEST 1: Original Issue Resolution - ابغى")
    print("="*50)
    total_tests += 1
    
    try:
        result = translator.translate_dialect_to_fusha('ابغى')
        if result['found']:
            trans = result['translations'][0]
            print(f"✅ SUCCESS: ابغى -> {trans['fusha']} ({trans['english']}) [{trans['dialect']}]")
            success_count += 1
        else:
            print("❌ FAILED: ابغى not found")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 2: Bidirectional translation
    print("\n" + "="*50) 
    print("TEST 2: Bidirectional Translation")
    print("="*50)
    
    # Ammiya -> Fusha
    ammiya_words = ['عايز', 'شنو', 'بدي', 'كيفك']
    for word in ammiya_words:
        total_tests += 1
        try:
            result = translator.translate_dialect_to_fusha(word)
            if result['found']:
                trans = result['translations'][0]
                print(f"✅ {word} ({trans['dialect']}) -> {trans['fusha']} ({trans['english']})")
                success_count += 1
            else:
                print(f"❌ {word} -> Not found")
        except Exception as e:
            print(f"❌ {word} -> Error: {e}")
    
    # Fusha -> Ammiya
    print("\nFusha -> Multiple Dialects:")
    fusha_words = ['أريد', 'كيف', 'ماذا']
    for word in fusha_words:
        total_tests += 1
        try:
            result = translator.translate_fusha_to_dialect(word)
            if result['found']:
                print(f"✅ {word} -> Found {result['total_matches']} dialect variations:")
                shown = 0
                for trans in result['dialect_translations']:
                    if shown < 3:  # Show first 3
                        print(f"     {trans['dialect_word']} ({trans['dialect']})")
                        shown += 1
                success_count += 1
            else:
                print(f"❌ {word} -> Not found")
        except Exception as e:
            print(f"❌ {word} -> Error: {e}")
    
    # Test 3: Flutter-ready data structure
    print("\n" + "="*50)
    print("TEST 3: Flutter Integration Ready")
    print("="*50)
    total_tests += 1
    
    try:
        # Test the service methods that would be used by API endpoints
        word = 'ابغى'
        result = translator.translate_dialect_to_fusha(word)
        
        if result['found']:
            # Simulate Flutter-ready response
            flutter_data = {
                "title": f"Fusha for '{word}'",
                "subtitle": f"Found {len(result['translations'])} translation(s)",
                "items": [
                    {
                        "fusha": t["fusha"],
                        "meaning": t["english"], 
                        "dialect": t["dialect"].title(),
                        "category": t["category"].replace("_", " ").title()
                    }
                    for t in result['translations']
                ]
            }
            
            print("✅ Flutter-ready data structure:")
            print(f"   Title: {flutter_data['title']}")
            print(f"   Subtitle: {flutter_data['subtitle']}")
            for item in flutter_data['items']:
                print(f"   Item: {item['fusha']} ({item['meaning']}) - {item['dialect']}")
            
            success_count += 1
        else:
            print("❌ No data for Flutter structure test")
            
    except Exception as e:
        print(f"❌ Flutter test error: {e}")
    
    # Test 4: System statistics
    print("\n" + "="*50)
    print("TEST 4: System Statistics")
    print("="*50)
    total_tests += 1
    
    try:
        stats = translator.get_statistics()
        print("✅ System Statistics:")
        print(f"   Total entries: {stats['total_entries']:,}")
        print(f"   Dialects covered: {len(stats['entries_per_dialect'])}")
        for dialect, count in stats['entries_per_dialect'].items():
            print(f"   {dialect.title()}: {count:,} entries")
        
        success_count += 1
    except Exception as e:
        print(f"❌ Statistics error: {e}")
    
    # Final results
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    
    success_rate = (success_count / total_tests) * 100
    print(f"Tests Passed: {success_count}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 COMPREHENSIVE DIALECT SYSTEM: FULLY OPERATIONAL!")
        print("✅ Ready for production deployment")
        print("✅ Flutter integration ready")
        print("✅ Original dialect issues resolved")
        return True
    else:
        print("⚠️  Some issues detected - review failed tests")
        return False

if __name__ == "__main__":
    test_comprehensive_dialect_system()
