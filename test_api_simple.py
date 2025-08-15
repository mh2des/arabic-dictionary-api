#!/usr/bin/env python3
"""
Simple API test for CAMeL Tools integration.
"""

from app.main import app
from fastapi.testclient import TestClient

def test_api():
    """Test the CAMeL Tools API endpoints."""
    
    # Install httpx if needed
    try:
        import httpx
    except ImportError:
        import subprocess
        subprocess.check_call(['C:/backend/.venv/Scripts/pip.exe', 'install', 'httpx'])
    
    client = TestClient(app)
    
    print("Testing CAMeL Tools API with TestClient...")
    
    # Test the analyze endpoint
    print("\nTesting word analysis:")
    test_word = "\u0643\u062a\u0627\u0628"  # كتاب in Unicode escape
    response = client.get(f'/camel/analyze/{test_word}')
    if response.status_code == 200:
        data = response.json()
        print(f"   Word: {test_word}")
        print(f"   Lemmas: {data.get('lemmas', [])}")
        print(f"   Roots: {data.get('roots', [])}")
        print(f"   POS: {data.get('pos', [])}")
    else:
        print(f"   Failed with status {response.status_code}")
    
    # Test the stats endpoint
    print("\nTesting stats:")
    response = client.get('/camel/stats')
    if response.status_code == 200:
        data = response.json()
        print(f"   Enhanced entries: {data.get('enhanced_entries', 0)}")
        print(f"   Total entries: {data.get('total_entries', 0)}")
    else:
        print(f"   Failed with status {response.status_code}")
    
    print("\nAPI testing complete!")

if __name__ == "__main__":
    test_api()
