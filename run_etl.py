#!/usr/bin/env python3
"""
ETL Runner Script
~~~~~~~~~~~~~~~~~

Script to run the complete ETL pipeline and populate the database
with data from all available sources.
"""

import os
import sys
import time
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.etl.merge import run_etl_pipeline


def main():
    """Run the ETL pipeline."""
    print("=== Arabic Dictionary ETL Pipeline ===")
    print(f"Starting at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Configuration
    db_path = "app/arabic_dict.db"
    sources_dir = "data/sources"
    
    # Check if sources directory exists
    if not os.path.exists(sources_dir):
        print(f"ERROR: Sources directory not found: {sources_dir}")
        print("Please ensure data sources are in the correct location.")
        return 1
    
    # Run ETL pipeline
    try:
        start_time = time.time()
        stats = run_etl_pipeline(db_path, sources_dir)
        end_time = time.time()
        
        print("\n=== ETL Pipeline Results ===")
        print(f"Total entries processed: {stats.get('total', 0)}")
        print(f"Successfully inserted: {stats.get('success', 0)}")
        print(f"Errors encountered: {stats.get('errors', 0)}")
        print(f"Processing time: {end_time - start_time:.2f} seconds")
        
        if stats.get('errors', 0) > 0:
            print(f"\nWarning: {stats['errors']} errors occurred during processing")
        
        print(f"\nDatabase created at: {os.path.abspath(db_path)}")
        print("ETL pipeline completed successfully!")
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: ETL pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
