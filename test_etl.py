#!/usr/bin/env python3
"""Simple test to check import functionality."""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

try:
    print("Testing imports...")
    from app.etl.merge import ETLPipeline
    print("✓ ETLPipeline imported successfully")
    
    from app.etl.merge import run_etl_pipeline
    print("✓ run_etl_pipeline imported successfully")
    
    print("All imports successful!")
    
    # Test the actual function call
    print("Testing ETL pipeline...")
    db_path = "dictionary.db"
    sources_dir = "data/sources"
    
    if os.path.exists(sources_dir):
        print(f"✓ Sources directory exists: {sources_dir}")
        result = run_etl_pipeline(db_path, sources_dir)
        print(f"✓ ETL pipeline completed: {result}")
    else:
        print(f"✗ Sources directory not found: {sources_dir}")
        print("Available directories:", os.listdir("data") if os.path.exists("data") else "data/ not found")

except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Runtime error: {e}")
    import traceback
    traceback.print_exc()
