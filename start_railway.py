#!/usr/bin/env python3
"""
Explicit startup script for Railway deployment.
This bypasses any uvicorn command-line issues.
"""

import os
import sys
import uvicorn

# Add current directory to Python path
sys.path.insert(0, '/app')

print("🚀 Starting Railway deployment...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}")

# List files for debugging
print("Files in /app:")
try:
    for item in os.listdir('/app'):
        if not item.startswith('.'):
            print(f"  {item}")
except Exception as e:
    print(f"Error listing files: {e}")

# Import and run the app
try:
    print("Importing minimal_standalone app...")
    from minimal_standalone import app
    print("✅ App imported successfully")
    
    # Get port from environment
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting server on port {port}...")
    
    # Start uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
    
except Exception as e:
    print(f"❌ Error starting app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
