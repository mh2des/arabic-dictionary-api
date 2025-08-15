#!/usr/bin/env python3
"""
Test script for Arabic Dictionary API
"""

import sqlite3
import json
import sys
import os

# Add app directory to path
sys.path.append('app')

def test_database():
    """Test the Arabic dictionary database."""
    
    print("=== Arabic Dictionary Database Test ===")
    
    # Connect to database
    db_path = 'app/arabic_dict.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get basic stats
    cursor.execute('SELECT COUNT(*) FROM entries')
    total_entries = cursor.fetchone()[0]
    print(f"✅ Total entries in database: {total_entries:,}")
    
    # Test different word types
    test_words = [
        ('كتب', 'Arabic word for books/write'),
        ('علم', 'Arabic word for science/knowledge'), 
        ('طبيب', 'Arabic word for doctor'),
        ('مدرسة', 'Arabic word for school'),
        ('بيت', 'Arabic word for house')
    ]
    
    print("\n=== Testing Word Searches ===")
    for word, description in test_words:
        print(f"\n🔍 Searching for '{word}' ({description}):")
        
        # Exact match search
        cursor.execute('''
            SELECT lemma, pos, root 
            FROM entries 
            WHERE lemma = ? OR lemma_norm = ?
            LIMIT 5
        ''', (word, word))
        
        exact_results = cursor.fetchall()
        
        # Partial match search  
        cursor.execute('''
            SELECT lemma, pos, root 
            FROM entries 
            WHERE lemma LIKE ? OR lemma_norm LIKE ?
            LIMIT 5
        ''', (f'%{word}%', f'%{word}%'))
        
        partial_results = cursor.fetchall()
        
        if exact_results:
            print(f"   ✅ Exact matches ({len(exact_results)}):")
            for i, (lemma, pos, root) in enumerate(exact_results, 1):
                print(f"      {i}. {lemma} ({pos or 'unknown'}) - Root: {root or 'N/A'}")
        
        if partial_results and len(partial_results) > len(exact_results):
            print(f"   📝 Partial matches ({len(partial_results) - len(exact_results)} additional):")
            for i, (lemma, pos, root) in enumerate(partial_results[len(exact_results):], 1):
                if i <= 3:  # Show max 3 additional
                    print(f"      {i}. {lemma} ({pos or 'unknown'}) - Root: {root or 'N/A'}")
        
        if not exact_results and not partial_results:
            print("   ❌ No matches found")
    
    # Test FTS search if available
    print("\n=== Testing Full-Text Search (FTS5) ===")
    try:
        cursor.execute('''
            SELECT e.lemma, e.pos, e.root
            FROM entries e
            JOIN entries_fts f ON e.id = f.rowid
            WHERE entries_fts MATCH 'كتب'
            LIMIT 5
        ''')
        
        fts_results = cursor.fetchall()
        print(f"✅ FTS search working - found {len(fts_results)} results for 'كتب'")
        for lemma, pos, root in fts_results[:3]:
            print(f"   - {lemma} ({pos or 'unknown'}) - Root: {root or 'N/A'}")
            
    except sqlite3.OperationalError as e:
        print(f"⚠️  FTS search issue: {e}")
    
    # Show sample entries from different sources
    print("\n=== Sample Entries by Source ===")
    cursor.execute('''
        SELECT json_extract(data, '$._source') as source, COUNT(*) as count
        FROM entries 
        WHERE json_extract(data, '$._source') IS NOT NULL
        GROUP BY source
        ORDER BY count DESC
        LIMIT 10
    ''')
    
    source_stats = cursor.fetchall()
    if source_stats:
        print("📊 Entries by data source:")
        for source, count in source_stats:
            print(f"   - {source}: {count:,} entries")
    
    # Show random sample
    print("\n=== Random Sample Entries ===")
    cursor.execute('''
        SELECT lemma, pos, root
        FROM entries 
        ORDER BY RANDOM()
        LIMIT 10
    ''')
    
    random_entries = cursor.fetchall()
    print("🎲 Random dictionary entries:")
    for i, (lemma, pos, root) in enumerate(random_entries, 1):
        print(f"   {i}. {lemma} ({pos or 'unknown'}) - Root: {root or 'N/A'}")
    
    conn.close()
    print("\n✅ Database test completed successfully!")

def test_api_endpoints():
    """Test API endpoints if server is running."""
    import requests
    
    print("\n=== Testing API Endpoints ===")
    base_url = "http://localhost:8000"
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            
            # Test search endpoint
            search_response = requests.get(f"{base_url}/search", params={"q": "كتب", "limit": 3}, timeout=5)
            if search_response.status_code == 200:
                results = search_response.json()
                print(f"✅ Search endpoint working - found {len(results.get('results', []))} results")
            else:
                print(f"⚠️  Search endpoint issue: {search_response.status_code}")
        else:
            print(f"⚠️  Health endpoint issue: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  API server not running - start with: uvicorn app.main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ API test error: {e}")

if __name__ == "__main__":
    test_database()
    test_api_endpoints()
