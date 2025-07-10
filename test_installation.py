#!/usr/bin/env python3
"""
Test script to verify installation and basic functionality
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import requests
        print("✓ requests module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import requests: {e}")
        return False
    
    try:
        import mutagen
        print("✓ mutagen module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import mutagen: {e}")
        return False
    
    try:
        from mutagen import File
        print("✓ mutagen.File imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import mutagen.File: {e}")
        return False
    
    try:
        from concurrent.futures import ThreadPoolExecutor
        print("✓ ThreadPoolExecutor imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import ThreadPoolExecutor: {e}")
        return False
    
    return True

def test_api_connectivity():
    """Test basic API connectivity"""
    print("\nTesting API connectivity...")
    
    import requests
    
    # Test MusicBrainz (no API key required)
    try:
        response = requests.get("https://musicbrainz.org/ws/2/recording/", 
                              params={'query': 'artist:"Daft Punk" AND recording:"Get Lucky"', 'fmt': 'json', 'limit': 1},
                              headers={'User-Agent': 'TrackMetadataEnricher/1.0 (Test)'})
        if response.status_code == 200:
            print("✓ MusicBrainz API accessible")
        else:
            print(f"✗ MusicBrainz API returned status {response.status_code}")
    except Exception as e:
        print(f"✗ MusicBrainz API test failed: {e}")
    
    # Test Last.fm (will fail without API key, but should not crash)
    try:
        response = requests.get("http://ws.audioscrobbler.com/2.0/", 
                              params={'method': 'track.getInfo', 'artist': 'Test', 'track': 'Test', 'api_key': 'test', 'format': 'json'})
        print("✓ Last.fm API endpoint accessible (will need valid API key for actual use)")
    except Exception as e:
        print(f"✗ Last.fm API test failed: {e}")

def test_file_operations():
    """Test basic file operations"""
    print("\nTesting file operations...")
    
    # Test if we can create and read files
    test_file = Path("test_metadata.txt")
    try:
        with open(test_file, 'w') as f:
            f.write("test metadata")
        print("✓ File write operation successful")
        
        with open(test_file, 'r') as f:
            content = f.read()
        print("✓ File read operation successful")
        
        # Clean up
        test_file.unlink()
        print("✓ File cleanup successful")
        
    except Exception as e:
        print(f"✗ File operations failed: {e}")
        return False
    
    return True

def test_metadata_enricher_import():
    """Test if the main script can be imported"""
    print("\nTesting main script import...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Try to import the main module
        from track_metadata_enrichment import MetadataEnricher, load_api_keys
        print("✓ Main script imported successfully")
        
        # Test creating an instance
        enricher = MetadataEnricher()
        print("✓ MetadataEnricher instance created successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Main script import failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Track Metadata Enrichment - Installation Test")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test imports
    if not test_imports():
        all_tests_passed = False
    
    # Test API connectivity
    test_api_connectivity()
    
    # Test file operations
    if not test_file_operations():
        all_tests_passed = False
    
    # Test main script import
    if not test_metadata_enricher_import():
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("✓ All tests passed! Installation is successful.")
        print("\nNext steps:")
        print("1. Copy api_keys.json.example to api_keys.json")
        print("2. Add your API keys to api_keys.json")
        print("3. Run: python track_metadata_enrichment.py /path/to/your/music")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Check your Python version (3.6+ required)")
        print("3. Ensure you have write permissions in the current directory")

if __name__ == "__main__":
    main() 