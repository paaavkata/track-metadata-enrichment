#!/usr/bin/env python3
"""
Setup script for Track Metadata Enrichment
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 6):
        print("✗ Python 3.6 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✓ Python version {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\nInstalling dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def setup_api_keys():
    """Set up API keys configuration"""
    print("\nSetting up API keys...")
    
    api_keys_file = Path("api_keys.json")
    example_file = Path("api_keys.json.example")
    
    if api_keys_file.exists():
        print("✓ API keys file already exists")
        return True
    
    if example_file.exists():
        try:
            shutil.copy(example_file, api_keys_file)
            print("✓ Created api_keys.json from template")
            print("⚠️  Please edit api_keys.json and add your API keys")
            return True
        except Exception as e:
            print(f"✗ Failed to create API keys file: {e}")
            return False
    else:
        print("✗ api_keys.json.example not found")
        return False

def run_tests():
    """Run installation tests"""
    print("\nRunning installation tests...")
    
    try:
        subprocess.check_call([sys.executable, "test_installation.py"])
        return True
    except subprocess.CalledProcessError:
        print("✗ Some tests failed")
        return False

def main():
    """Main setup function"""
    print("Track Metadata Enrichment - Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\nTroubleshooting:")
        print("1. Try: pip install --upgrade pip")
        print("2. Try: pip install -r requirements.txt --user")
        sys.exit(1)
    
    # Setup API keys
    setup_api_keys()
    
    # Run tests
    if run_tests():
        print("\n" + "=" * 40)
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit api_keys.json and add your API keys")
        print("2. Run: python track_metadata_enrichment.py /path/to/your/music")
        print("\nFor help, see README.md")
    else:
        print("\n⚠️  Setup completed with warnings")
        print("Some tests failed, but the script may still work")
        print("Check the test output above for details")

if __name__ == "__main__":
    main() 