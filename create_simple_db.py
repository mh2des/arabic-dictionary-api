#!/usr/bin/env python3
"""
Create a simple Arabic dictionary database for Railway deployment.
"""

import os
import sqlite3
from typing import Optional

def create_simple_database() -> Optional[str]:
    """Create the Arabic dictionary database with simplified schema."""
    
    db_path = "/app/app/arabic_dict.db"
    
    # Remove any existing database
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️ Removed existing database")
    
    print("🔧 Creating simplified Arabic database...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the simplified schema that matches our API
    cursor.execute('''
        CREATE TABLE entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lemma TEXT NOT NULL,
            lemma_norm TEXT,
            root TEXT,
            pos TEXT,
            subpos TEXT,
            register TEXT,
            domain TEXT,
            freq_rank INTEGER
        )
    ''')
    
    # Add comprehensive Arabic vocabulary - only the basic fields
    sample_entries = [
        # ك ت ب root family
        ("كَتَبَ", "كتب", "ك ت ب", "verb", "perfect", "فصحى", "education", 100),
        ("كِتَابٌ", "كتاب", "ك ت ب", "noun", "common", "فصحى", "education", 50),
        ("مَكْتَبٌ", "مكتب", "ك ت ب", "noun", "common", "فصحى", "workplace", 200),
        ("مَكْتَبَةٌ", "مكتبة", "ك ت ب", "noun", "common", "فصحى", "education", 150),
        ("كَاتِبٌ", "كاتب", "ك ت ب", "noun", "agent", "فصحى", "profession", 300),
        
        # ق ر أ root family
        ("قَرَأَ", "قرا", "ق ر أ", "verb", "perfect", "فصحى", "education", 80),
        ("قُرْآنٌ", "قران", "ق ر أ", "noun", "proper", "فصحى", "religion", 25),
        ("قَارِئٌ", "قارئ", "ق ر أ", "noun", "agent", "فصحى", "education", 400),
        ("مَقْرُوءٌ", "مقروء", "ق ر أ", "adjective", "passive", "فصحى", "education", 800),
        ("قِرَاءَةٌ", "قراءة", "ق ر أ", "noun", "verbal", "فصحى", "education", 250),
        
        # د ر س root family
        ("دَرَسَ", "درس", "د ر س", "verb", "perfect", "فصحى", "education", 120),
        ("دَرْسٌ", "درس", "د ر س", "noun", "common", "فصحى", "education", 90),
        ("مَدْرَسَةٌ", "مدرسة", "د ر س", "noun", "common", "فصحى", "education", 60),
        ("مُدَرِّسٌ", "مدرس", "د ر س", "noun", "agent", "فصحى", "profession", 180),
        ("دَارِسٌ", "دارس", "د ر س", "noun", "agent", "فصحى", "education", 350),
        
        # ع ل م root family
        ("عَلِمَ", "علم", "ع ل م", "verb", "perfect", "فصحى", "knowledge", 70),
        ("عِلْمٌ", "علم", "ع ل م", "noun", "common", "فصحى", "knowledge", 45),
        ("عَالِمٌ", "عالم", "ع ل م", "noun", "agent", "فصحى", "profession", 220),
        ("مُعَلِّمٌ", "معلم", "ع ل م", "noun", "agent", "فصحى", "profession", 130),
        ("تَعْلِيمٌ", "تعليم", "ع ل م", "noun", "verbal", "فصحى", "education", 160),
        
        # Common words
        ("بَيْتٌ", "بيت", "ب ي ت", "noun", "common", "فصحى", "home", 30),
    ]
    
    # Insert entries
    for entry in sample_entries:
        cursor.execute('''
            INSERT INTO entries 
            (lemma, lemma_norm, root, pos, subpos, register, domain, freq_rank)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', entry)
    
    conn.commit()
    
    # Verify count
    cursor.execute("SELECT COUNT(*) FROM entries")
    count = cursor.fetchone()[0]
    
    # Test queries
    cursor.execute("SELECT lemma, root, pos FROM entries LIMIT 5")
    sample_data = cursor.fetchall()
    
    conn.close()
    
    print(f"✅ Created simplified database with {count} entries")
    print("📋 Sample entries:")
    for row in sample_data:
        print(f"  - {row[0]} ({row[1]}) - {row[2]}")
    
    return db_path

if __name__ == "__main__":
    create_simple_database()
