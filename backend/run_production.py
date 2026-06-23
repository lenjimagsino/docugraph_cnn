#!/usr/bin/env python3
"""
DOCUGRAPH Backend Production Server
Runs with Gunicorn for optimal performance and reliability
Automatically restarts on crashes
"""

import os
import sys
import time
import subprocess
import signal

class BackendServer:
    def __init__(self):
        self.backend_dir = os.path.dirname(os.path.abspath(__file__))
        self.port = os.getenv('PORT', '5000')
        self.workers = os.getenv('WORKERS', '4')
        self.timeout = os.getenv('TIMEOUT', '120')
        self.process = None
        self.running = True
        
    def check_dependencies(self):
        """Verify all required packages are installed"""
        print("\n🔍 Checking dependencies...")
        
        required = ['flask', 'cv2', 'numpy', 'gunicorn']
        optional = ['easyocr', 'layoutparser', 'torch']
        
        for pkg in required:
            try:
                __import__(pkg)
                print(f"  ✓ {pkg}")
            except ImportError:
                print(f"  ❌ {pkg} (REQUIRED)")
                print(f"\n     Install with: pip install {pkg}")
                return False
        
        for pkg in optional:
            try:
                __import__(pkg)
                print(f"  ✓ {pkg} (optional)")
            except ImportError:
                print(f"  ℹ {pkg} not installed (optional)")
        
        return True
    
    def get_gunicorn_cmd(self):
        """Build Gunicorn command with optimal settings"""
        return [
            'gunicorn',
            'app:app',
            f'--workers={self.workers}',
            f'--bind=0.0.0.0:{self.port}',
            f'--timeout={self.timeout}',
            '--access-logfile=-',
            '--error-logfile=-',
            '--log-level=info',
            '--capture-output',
        ]
    
    def start(self):
        """Start the backend server"""
        print("\n" + "="*70)
        print("🚀 DOCUGRAPH Backend Server - PRODUCTION MODE")
        print("="*70)
        
        if not self.check_dependencies():
            return False
        
        cmd = self.get_gunicorn_cmd()
        
        print(f"\n📡 Server Configuration:")
        print(f"   Host: 0.0.0.0")
        print(f"   Port: {self.port}")
        print(f"   Workers: {self.workers}")
        print(f"   Timeout: {self.timeout}s")
        print(f"\n🌐 Access URLs:")
        print(f"   Local: http://localhost:{self.port}")
        print(f"   Production: https://docugraph.site:{self.port}")
        print(f"\n📋 Important Endpoints:")
        print(f"   Health: http://localhost:{self.port}/health")
        print(f"   Diagnostics: http://localhost:{self.port}/diagnostics")
        print(f"   OCR Extract: http://localhost:{self.port}/api/v1/ocr/extract")
        print(f"   Layout Analyze: http://localhost:{self.port}/api/v1/layout/analyze")
        print(f"\n🔄 Auto-Restart: ENABLED")
        print(f"   Server will automatically restart if it crashes")
        print(f"\n⌨️  Press CTRL+C to stop the server")
        print("="*70 + "\n")
        
        restart_count = 0
        while self.running:
            try:
                print(f"🔄 Starting Gunicorn server...")
                self.process = subprocess.Popen(
                    cmd,
                    cwd=self.backend_dir,
                    env={**os.environ, 'FLASK_ENV': 'production'}
                )
                
                # Wait for process
                exit_code = self.process.wait()
                
                if self.running:
                    restart_count += 1
                    print(f"\n⚠️  Server crashed (exit code: {exit_code})")
                    print(f"📊 Restart attempt: {restart_count}")
                    print(f"⏳ Waiting 5 seconds before restart...\n")
                    time.sleep(5)
                
            except Exception as e:
                print(f"❌ Error starting server: {e}")
                if self.running:
                    print("⏳ Waiting 5 seconds before retry...")
                    time.sleep(5)
        
        return True
    
    def handle_signal(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print("\n\n🛑 Received shutdown signal")
        self.running = False
        if self.process:
            print("Terminating server process...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("Force killing server process...")
                self.process.kill()
        sys.exit(0)

def main():
    server = BackendServer()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, server.handle_signal)
    signal.signal(signal.SIGTERM, server.handle_signal)
    
    success = server.start()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
