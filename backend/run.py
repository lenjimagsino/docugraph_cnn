#!/usr/bin/env python3
"""
DOCUGRAPH Backend Startup Script
Runs the Flask backend server with proper configuration
"""

import os
import sys
import subprocess

def main():
    # Add backend directory to path
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, backend_dir)
    
    print("=" * 60)
    print("DOCUGRAPH Backend Server")
    print("=" * 60)
    
    # Check environment
    print("\n🔍 Checking environment...")
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required")
        return False
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check key packages
    packages = ['flask', 'cv2', 'numpy']
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"✓ {pkg} installed")
        except ImportError:
            print(f"❌ {pkg} not installed - run: pip install -r requirements.txt")
            return False
    
    # Check OCR
    try:
        import easyocr
        print("✓ easyocr installed")
    except ImportError:
        print("⚠ easyocr not installed - OCR features will not work")
        print("  Run: pip install easyocr")
    
    # Set environment variables
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = os.getenv('FLASK_ENV', 'development')
    port = os.getenv('PORT', '5000')
    
    print(f"\n🚀 Starting server on http://localhost:{port}")
    print("📋 API Docs:")
    print(f"   - Health: http://localhost:{port}/health")
    print(f"   - Diagnostics: http://localhost:{port}/diagnostics")
    print("\n⌨️  Press CTRL+C to stop\n")
    print("=" * 60 + "\n")
    
    # Start Flask app
    try:
        from app import app
        app.run(
            host='0.0.0.0',
            port=int(port),
            debug=os.getenv('FLASK_ENV') == 'development'
        )
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
        return True
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
