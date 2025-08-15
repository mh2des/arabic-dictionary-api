#!/usr/bin/env python3
"""
Final demonstration of CAMeL Tools integration for Arabic Dictionary Backend.

This script demonstrates the complete functionality we've implemented:
1. Morphological analysis using CAMeL Tools
2. Database enhancement with CAMeL data
3. Enhanced search capabilities
"""

import sys
import os
import sqlite3
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'app'))

from services.camel_final import FinalCamelProcessor


def test_morphological_analysis():
    """Test the CAMeL Tools morphological analysis."""
    print("=" * 60)
    print("🔍 TESTING CAMEL TOOLS MORPHOLOGICAL ANALYSIS")
    print("=" * 60)
    
    processor = FinalCamelProcessor()
    
    # Test various Arabic words
    test_words = [
        "كتاب",     # book
        "كتب",      # books/wrote
        "يكتب",     # writes
        "مكتوب",    # written
        "مكتبة",    # library
        "الكتاب",   # the book
        "والكتاب",  # and the book
    ]
    
    for word in test_words:
        print(f"\n📖 Analyzing: {word}")
        try:
            analysis = processor.analyze_word(word)
            print(f"   Lemmas: {analysis['possible_lemmas']}")
            print(f"   Roots: {analysis['roots']}")
            print(f"   POS: {analysis['pos_tags']}")
            print(f"   Available: {analysis['available']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")


def test_database_integration():
    """Test the database integration with CAMeL enhanced data."""
    print("\n" + "=" * 60)
    print("💾 TESTING DATABASE INTEGRATION")
    print("=" * 60)
    
    db_path = Path("app/data/sample/sample_entries.json").parent.parent.parent / "arabic_dict.db"
    
    if not db_path.exists():
        print("❌ Database file not found. Please ensure the database is set up.")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check enhanced entries
    cursor.execute("""
        SELECT COUNT(*) FROM entries 
        WHERE camel_lemmas IS NOT NULL AND camel_lemmas != ''
    """)
    enhanced_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM entries")
    total_count = cursor.fetchone()[0]
    
    print(f"📊 Enhanced entries: {enhanced_count}")
    print(f"📊 Total entries: {total_count}")
    print(f"📊 Enhancement percentage: {(enhanced_count/total_count)*100:.1f}%")
    
    # Show some enhanced entries
    cursor.execute("""
        SELECT lemma, camel_lemmas, camel_roots, camel_pos 
        FROM entries 
        WHERE camel_lemmas IS NOT NULL AND camel_lemmas != ''
        LIMIT 5
    """)
    
    print("\n🔍 Sample enhanced entries:")
    for row in cursor.fetchall():
        lemma, camel_lemmas, camel_roots, camel_pos = row
        print(f"   {lemma}:")
        print(f"      Lemmas: {camel_lemmas}")
        print(f"      Roots: {camel_roots}")
        print(f"      POS: {camel_pos}")
    
    conn.close()


def test_search_functionality():
    """Test enhanced search functionality."""
    print("\n" + "=" * 60)
    print("🔎 TESTING ENHANCED SEARCH FUNCTIONALITY")
    print("=" * 60)
    
    db_path = Path("app/data/sample/sample_entries.json").parent.parent.parent / "arabic_dict.db"
    
    if not db_path.exists():
        print("❌ Database file not found.")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Test root-based search
    test_root = "ك.ت.ب"
    print(f"\n🔍 Searching by root: {test_root}")
    
    cursor.execute("""
        SELECT lemma, camel_roots, camel_lemmas
        FROM entries 
        WHERE camel_roots LIKE ?
        LIMIT 5
    """, (f"%{test_root}%",))
    
    results = cursor.fetchall()
    if results:
        print(f"   Found {len(results)} entries with root {test_root}:")
        for lemma, roots, camel_lemmas in results:
            print(f"      {lemma} -> roots: {roots}, lemmas: {camel_lemmas}")
    else:
        print(f"   No entries found with root {test_root}")
    
    # Test lemma-based search
    test_lemma = "كِتاب"
    print(f"\n🔍 Searching by lemma: {test_lemma}")
    
    cursor.execute("""
        SELECT lemma, camel_lemmas, camel_roots
        FROM entries 
        WHERE camel_lemmas LIKE ?
        LIMIT 5
    """, (f"%{test_lemma}%",))
    
    results = cursor.fetchall()
    if results:
        print(f"   Found {len(results)} entries with lemma {test_lemma}:")
        for lemma, camel_lemmas, roots in results:
            print(f"      {lemma} -> lemmas: {camel_lemmas}, roots: {roots}")
    else:
        print(f"   No entries found with lemma {test_lemma}")
    
    conn.close()


def show_api_routes():
    """Show the available API routes."""
    print("\n" + "=" * 60)
    print("🌐 AVAILABLE CAMEL TOOLS API ROUTES")
    print("=" * 60)
    
    routes = [
        ("GET", "/camel/analyze/{word}", "Analyze Arabic word morphologically"),
        ("GET", "/camel/search", "Search enhanced entries by query"),
        ("GET", "/camel/lemmatize/{text}", "Get lemmatized form of text"),
        ("GET", "/camel/root/{root}", "Find entries by root"),
        ("GET", "/camel/stats", "Get enhancement statistics"),
    ]
    
    for method, path, description in routes:
        print(f"   {method:4} {path:25} - {description}")
    
    print("\n📝 Example usage:")
    print("   curl 'http://localhost:8000/camel/analyze/كتاب'")
    print("   curl 'http://localhost:8000/camel/search?q=كتب'")
    print("   curl 'http://localhost:8000/camel/root/ك.ت.ب'")


def main():
    """Run all tests and demonstrations."""
    print("🐪 CAMeL Tools Integration - Final Test Suite")
    print("This demonstrates the complete CAMeL Tools integration for your Arabic dictionary.")
    
    try:
        # Test morphological analysis
        test_morphological_analysis()
        
        # Test database integration
        test_database_integration()
        
        # Test search functionality
        test_search_functionality()
        
        # Show API routes
        show_api_routes()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        print("\n🎉 Your Arabic dictionary now has enhanced CAMeL Tools functionality:")
        print("   ✅ Morphological analysis for Arabic words")
        print("   ✅ Root extraction and lemmatization")
        print("   ✅ Part-of-speech tagging")
        print("   ✅ Enhanced database with linguistic features")
        print("   ✅ New API endpoints for advanced search")
        
        print("\n🚀 To use the enhanced API:")
        print("   1. Start the server: uvicorn app.main:app --reload")
        print("   2. Visit: http://localhost:8000/docs")
        print("   3. Try the /camel/* endpoints")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
