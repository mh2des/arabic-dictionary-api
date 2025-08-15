#!/usr/bin/env python3
"""
Download the REAL comprehensive Arabic dictionary database.
This downloads our actual 101,331 entry database that we built.
"""

import os
import sqlite3
import urllib.request
import gzip
import shutil

def download_real_database():
    """Download our actual comprehensive database with 101,331 entries."""
    
    db_path = "/app/app/arabic_dict.db"
    
    print("📥 Downloading REAL comprehensive Arabic dictionary database...")
    
    # Try multiple sources for our real database
    sources = [
        "https://github.com/mh2des/arabic-dictionary-api/releases/download/v1.0/arabic_dict.db.gz",
        "https://raw.githubusercontent.com/mh2des/arabic-dictionary-api/main/database/arabic_dict.db.gz",
        # We'll upload the compressed database to one of these
    ]
    
    for url in sources:
        try:
            print(f"📡 Trying to download from: {url}")
            
            # Download compressed database
            compressed_path = "/tmp/arabic_dict.db.gz"
            urllib.request.urlretrieve(url, compressed_path)
            
            # Decompress
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Verify it's our real database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM entries")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count > 50000:  # Our real database
                file_size = os.path.getsize(db_path) / (1024 * 1024)
                print(f"✅ Successfully downloaded REAL database: {count} entries ({file_size:.1f} MB)")
                return db_path
                
        except Exception as e:
            print(f"❌ Failed to download from {url}: {e}")
            continue
    
    print("❌ Could not download real database from any source")
    return None

if __name__ == "__main__":
    download_real_database()
