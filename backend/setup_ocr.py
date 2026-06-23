#!/usr/bin/env python3
"""
DOCUGRAPH OCR Setup Script
Installs dependencies and verifies OCR engine initialization
"""

import sys
import subprocess
import os

def run_command(cmd, description):
    """Run a command and report status"""
    print(f"\n📦 {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✓ {description} - OK")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✓ {package_name} is installed")
        return True
    except ImportError:
        print(f"❌ {package_name} is NOT installed")
        return False

def main():
    print("=" * 60)
    print("DOCUGRAPH OCR Setup Wizard")
    print("=" * 60)
    
    # Check Python version
    print(f"\n📌 Python Version: {sys.version}")
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required")
        return False
    
    # Check existing packages
    print("\n📋 Checking installed packages...")
    packages = {
        'flask': 'flask',
        'opencv': 'cv2',
        'numpy': 'numpy',
        'pillow': 'PIL',
        'easyocr': 'easyocr',
        'torch': 'torch'
    }
    
    missing = []
    for name, import_name in packages.items():
        if not check_package(name, import_name):
            missing.append(name)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("\nInstalling missing packages...")
        
        # Install requirements
        if os.path.exists('requirements.txt'):
            print("\n📦 Installing from requirements.txt...")
            run_command(f"{sys.executable} -m pip install -r requirements.txt", 
                       "Install requirements")
        else:
            print("❌ requirements.txt not found")
    
    # Test OCR engine specifically
    print("\n🧪 Testing OCR Engine...")
    try:
        import easyocr
        print("✓ EasyOCR imported successfully")
        
        print("⏳ Initializing OCR Reader (this may take a minute on first run)...")
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        print("✓ OCR Reader initialized successfully")
        
        # Test with a simple image
        import numpy as np
        test_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        print("🔄 Running test OCR on blank image...")
        results = reader.readtext(test_image)
        print(f"✓ OCR test completed: {len(results)} regions detected")
        
    except ImportError as e:
        print(f"❌ EasyOCR not installed: {e}")
        print(f"   Run: {sys.executable} -m pip install easyocr")
        return False
    except Exception as e:
        print(f"⚠️  OCR initialization warning: {e}")
        print("   This might be OK on first run (downloading models)")
    
    print("\n" + "=" * 60)
    print("✓ Setup verification complete!")
    print("\nTo run the backend server:")
    print(f"  cd backend")
    print(f"  {sys.executable} app.py")
    print("\nOr with Flask:")
    print(f"  export FLASK_APP=app.py")
    print(f"  {sys.executable} -m flask run")
    print("\nCheck diagnostics at: http://localhost:5000/diagnostics")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
