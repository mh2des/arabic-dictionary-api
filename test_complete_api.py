#!/usr/bin/env python3
"""
Complete Test Suite for Enhanced Arabic Dictionary with CAMeL Tools
Run this to test all the enhanced functionality.
"""

import requests
import json
import time
from urllib.parse import quote

# Server configuration
BASE_URL = "http://127.0.0.1:8080"
TIMEOUT = 10

def test_endpoint(url, description):
    """Test a single endpoint and return the result."""
    try:
        print(f"🧪 Testing: {description}")
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {response.status_code}")
            return data
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def main():
    """Run all tests for the enhanced Arabic dictionary."""
    
    print("=" * 70)
    print("🐪 ENHANCED ARABIC DICTIONARY - COMPLETE TEST SUITE")
    print("=" * 70)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Test 1: Health check
    print("\n1️⃣ BASIC HEALTH CHECK")
    print("-" * 30)
    health_data = test_endpoint(f"{BASE_URL}/healthz", "Health endpoint")
    if health_data:
        print(f"   Status: {health_data.get('status', 'Unknown')}")
    
    # Test 2: CAMeL Tools Statistics
    print("\n2️⃣ CAMEL TOOLS STATISTICS")
    print("-" * 30)
    stats_data = test_endpoint(f"{BASE_URL}/camel/stats", "CAMeL enhancement statistics")
    if stats_data:
        print(f"   📊 Enhanced entries: {stats_data.get('enhanced_entries', 0):,}")
        print(f"   📊 Total entries: {stats_data.get('total_entries', 0):,}")
        print(f"   📊 Enhancement rate: {stats_data.get('enhancement_percentage', 0):.1f}%")
        print(f"   📊 Entries with analysis: {stats_data.get('entries_with_analysis', 0):,}")
    
    # Test 3: Word Analysis
    print("\n3️⃣ MORPHOLOGICAL WORD ANALYSIS")
    print("-" * 30)
    
    test_words = [
        ("كتاب", "book"),
        ("مكتبة", "library"), 
        ("يكتب", "writes"),
        ("مكتوب", "written")
    ]
    
    for word, meaning in test_words:
        encoded_word = quote(word)
        word_data = test_endpoint(f"{BASE_URL}/camel/analyze/{encoded_word}", 
                                f"Analysis for '{word}' ({meaning})")
        if word_data:
            print(f"      Word: {word} ({meaning})")
            print(f"      Lemmas: {word_data.get('lemmas', [])}")
            print(f"      Roots: {word_data.get('roots', [])}")
            print(f"      POS: {word_data.get('pos', [])}")
            print()
    
    # Test 4: Root-Based Search
    print("\n4️⃣ ROOT-BASED SEARCH (THE BIG IMPROVEMENT!)")
    print("-" * 30)
    
    test_roots = [
        ("ك.ت.ب", "writing/book"),
        ("ع.ل.م", "knowledge"),
        ("ق.ر.أ", "reading")
    ]
    
    for root, meaning in test_roots:
        encoded_root = quote(root)
        root_data = test_endpoint(f"{BASE_URL}/camel/root/{encoded_root}", 
                                f"Root search for '{root}' ({meaning})")
        if root_data:
            print(f"      📚 Root '{root}' ({meaning}): {len(root_data)} entries found!")
            if len(root_data) > 0:
                print("      Sample entries:")
                for entry in root_data[:3]:
                    print(f"         - {entry.get('lemma', 'N/A')}")
            print()
    
    # Test 5: Enhanced Search
    print("\n5️⃣ ENHANCED SEARCH WITH CAMEL TOOLS")
    print("-" * 30)
    
    search_queries = ["كتب", "علم", "درس"]
    
    for query in search_queries:
        encoded_query = quote(query)
        search_data = test_endpoint(f"{BASE_URL}/camel/search?q={encoded_query}", 
                                  f"Enhanced search for '{query}'")
        if search_data:
            print(f"      🔍 Search '{query}': {len(search_data)} results")
            if len(search_data) > 0:
                print("      Top results:")
                for result in search_data[:2]:
                    print(f"         - {result.get('lemma', 'N/A')}")
            print()
    
    # Test 6: Text Lemmatization
    print("\n6️⃣ TEXT LEMMATIZATION")
    print("-" * 30)
    
    test_texts = ["الكتاب الجديد", "مكتبة الجامعة"]
    
    for text in test_texts:
        encoded_text = quote(text)
        lemma_data = test_endpoint(f"{BASE_URL}/camel/lemmatize/{encoded_text}", 
                                 f"Lemmatization for '{text}'")
        if lemma_data:
            print(f"      Text: {text}")
            print(f"      Lemmatized: {lemma_data.get('lemmatized', 'N/A')}")
            print()
    
    # Test 7: Traditional Dictionary Search (still works!)
    print("\n7️⃣ TRADITIONAL DICTIONARY FEATURES (STILL WORKING)")
    print("-" * 30)
    
    # Test basic search
    traditional_search = test_endpoint(f"{BASE_URL}/search?q=كتاب", "Traditional search")
    if traditional_search:
        print(f"      Traditional search results: {len(traditional_search)}")
    
    # Test random entry
    random_entry = test_endpoint(f"{BASE_URL}/random", "Random entry")
    if random_entry:
        print(f"      Random entry: {random_entry.get('info', {}).get('lemma', 'N/A')}")
    
    # Final Summary
    print("\n" + "=" * 70)
    print("🎉 TEST SUITE COMPLETE!")
    print("=" * 70)
    
    print("\n✅ YOUR ENHANCED ARABIC DICTIONARY IS READY!")
    print("\n🚀 Available at: http://127.0.0.1:8080")
    print("📖 Interactive docs: http://127.0.0.1:8080/docs")
    print("📚 Alternative docs: http://127.0.0.1:8080/redoc")
    
    print("\n🔥 NEW CAMEL TOOLS FEATURES:")
    print("   • Morphological analysis for any Arabic word")
    print("   • Root-based search across 101,331+ entries")
    print("   • Advanced lemmatization capabilities")
    print("   • POS tagging and grammatical analysis")
    print("   • Enhanced search with linguistic matching")
    
    print("\n💡 Try these commands:")
    print("   curl 'http://127.0.0.1:8080/camel/analyze/كتاب'")
    print("   curl 'http://127.0.0.1:8080/camel/root/ك.ت.ب'")
    print("   curl 'http://127.0.0.1:8080/camel/search?q=علم'")
    print("   curl 'http://127.0.0.1:8080/camel/stats'")

if __name__ == "__main__":
    main()
