#!/usr/bin/env python3
"""
Setup script to ensure comprehensive database is available for Railway deployment.
This runs during Docker build/startup to prepare the 101,331-entry database.
"""

import os
import sys
import sqlite3
import gzip
import shutil

def setup_comprehensive_database():
    """Prepare the comprehensive database for deployment."""
    
    print("🔧 SETTING UP COMPREHENSIVE DATABASE FOR DEPLOYMENT")
    print("=" * 60)
    
    # Ensure the compressed database exists
    compressed_file = "arabic_dict.db.gz"
    if not os.path.exists(compressed_file):
        print(f"❌ Compressed database not found: {compressed_file}")
        return False
    
    # Check size
    compressed_size = os.path.getsize(compressed_file) / (1024 * 1024)
    print(f"📦 Compressed database size: {compressed_size:.1f}MB")
    
    if compressed_size < 15:
        print(f"❌ Compressed file too small: {compressed_size:.1f}MB")
        return False
    
    # Test decompression
    try:
        print("🧪 Testing decompression...")
        test_path = "test_decompress.db"
        
        with gzip.open(compressed_file, 'rb') as f_in:
            with open(test_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Verify the test database
        file_size = os.path.getsize(test_path) / (1024 * 1024)
        print(f"📊 Decompressed test size: {file_size:.1f}MB")
        
        if file_size > 100:  # Should be ~172MB
            conn = sqlite3.connect(test_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM entries")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count > 100000:  # Should be 101,331
                print(f"✅ Decompression test successful: {count} entries")
                os.remove(test_path)  # Clean up test file
                return True
            else:
                print(f"❌ Test database too small: {count} entries")
        else:
            print(f"❌ Decompressed test file too small: {file_size:.1f}MB")
        
        # Clean up test file
        if os.path.exists(test_path):
            os.remove(test_path)
            
    except Exception as e:
        print(f"❌ Decompression test failed: {e}")
        return False
    
    return False

if __name__ == "__main__":
    success = setup_comprehensive_database()
    if success:
        print("🎉 Setup complete - comprehensive database ready for deployment")
        sys.exit(0)
    else:
        print("❌ Setup failed - deployment may use fallback database")
        sys.exit(1)
