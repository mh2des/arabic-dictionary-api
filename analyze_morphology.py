#!/usr/bin/env python3
"""
Analyze morphological data in the Arabic dictionary
"""

import sqlite3
import json

def analyze_morphological_data():
    """Analyze what morphological information we have."""
    
    conn = sqlite3.connect('app/arabic_dict.db')
    cursor = conn.cursor()
    
    print("=== ADVANCED MORPHOLOGICAL DATA ANALYSIS ===")
    
    # Sample entries with morphological data
    cursor.execute('''
        SELECT lemma, pos, root, data 
        FROM entries 
        WHERE root IS NOT NULL AND root != "N/A" AND root != ""
        LIMIT 10
    ''')
    
    entries_with_roots = cursor.fetchall()
    
    print("Sample entries with morphological data:")
    morphological_features = set()
    
    for lemma, pos, root, data_json in entries_with_roots:
        try:
            data = json.loads(data_json)
            print(f"\n📝 {lemma} ({pos})")
            print(f"   Root: {root}")
            
            # Collect all morphological features we find
            for key, value in data.items():
                if key not in ['_source', 'lemma', 'pos', 'definition', 'meaning']:
                    morphological_features.add(key)
                    if value and str(value).strip() and value != "N/A":
                        print(f"   {key}: {value}")
                        
        except Exception as e:
            print(f"   {lemma} - Data parsing error: {e}")
    
    print(f"\n=== MORPHOLOGICAL FEATURES FOUND ===")
    print(f"Unique morphological attributes: {sorted(morphological_features)}")
    
    # Statistical analysis
    print(f"\n=== MORPHOLOGICAL DATA STATISTICS ===")
    
    # Count entries with specific features
    features_to_check = [
        'root', 'wazn', 'gender', 'number', 'transitive', 
        'conjugation', 'plurals', 'verb_form', 'pattern'
    ]
    
    total_entries = 101331
    
    for feature in features_to_check:
        cursor.execute(f'''
            SELECT COUNT(*) FROM entries 
            WHERE json_extract(data, "$.{feature}") IS NOT NULL 
            AND json_extract(data, "$.{feature}") != ""
            AND json_extract(data, "$.{feature}") != "N/A"
        ''')
        count = cursor.fetchone()[0]
        percentage = (count / total_entries) * 100
        print(f"{feature}: {count:,} entries ({percentage:.1f}%)")
    
    # Check Qutrub verb data specifically
    cursor.execute('''
        SELECT COUNT(*) FROM entries 
        WHERE json_extract(data, "$._source") = "Qutrub"
    ''')
    qutrub_count = cursor.fetchone()[0]
    
    print(f"\n=== VERB CONJUGATION DATA (Qutrub) ===")
    print(f"Qutrub verb entries: {qutrub_count:,}")
    
    if qutrub_count > 0:
        cursor.execute('''
            SELECT lemma, data 
            FROM entries 
            WHERE json_extract(data, "$._source") = "Qutrub"
            LIMIT 3
        ''')
        
        print("Sample Qutrub verb data:")
        for lemma, data_json in cursor.fetchall():
            try:
                data = json.loads(data_json)
                print(f"\n🔤 {lemma}")
                for key, value in data.items():
                    if 'tense' in key.lower() or 'conjugat' in key.lower() or 'form' in key.lower():
                        print(f"   {key}: {value}")
            except:
                pass
    
    # Check Arramooz morphological data
    cursor.execute('''
        SELECT COUNT(*) FROM entries 
        WHERE json_extract(data, "$._source") = "Arramooz AlWaseet"
    ''')
    arramooz_count = cursor.fetchone()[0]
    
    print(f"\n=== MORPHOLOGICAL DATA (Arramooz) ===")
    print(f"Arramooz entries: {arramooz_count:,}")
    
    if arramooz_count > 0:
        cursor.execute('''
            SELECT lemma, data 
            FROM entries 
            WHERE json_extract(data, "$._source") = "Arramooz AlWaseet"
            AND json_extract(data, "$.wazn") IS NOT NULL
            LIMIT 3
        ''')
        
        print("Sample Arramooz morphological data:")
        for lemma, data_json in cursor.fetchall():
            try:
                data = json.loads(data_json)
                print(f"\n🏛️ {lemma}")
                morpho_keys = ['wazn', 'gender', 'number', 'root', 'pattern', 'category']
                for key in morpho_keys:
                    if key in data and data[key]:
                        print(f"   {key}: {data[key]}")
            except:
                pass
    
    conn.close()

if __name__ == "__main__":
    analyze_morphological_data()
