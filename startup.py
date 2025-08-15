#!/usr/bin/env python3
"""
Simple startup script for Railway deployment
"""

import os
import sys
import subprocess
import time

def main():
    print("=== Arabic Dictionary API Startup ===")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Files in current directory: {os.listdir('.')}")
    
    # Check if app directory exists
    if os.path.exists('app'):
        print(f"Files in app directory: {os.listdir('app')}")
        
        # Check for database
        db_path = 'app/arabic_dict.db'
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path) / (1024 * 1024)
            print(f"Database found: {db_path} ({db_size:.1f} MB)")
        else:
            print("Database not found, will use fallback")
    
    # Set PORT from environment or default
    port = os.environ.get('PORT', '8000')
    print(f"Starting on port: {port}")
    
    # Start uvicorn
    cmd = [
        'uvicorn', 
        'app.main:app', 
        '--host', '0.0.0.0', 
        '--port', port,
        '--log-level', 'info'
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    
    try:
        # Start the server
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
