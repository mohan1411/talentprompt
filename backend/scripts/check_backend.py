#!/usr/bin/env python3
"""Check if backend can start and diagnose issues."""

import subprocess
import sys
import os
import time

print("="*60)
print("BACKEND DIAGNOSTIC TOOL")
print("="*60)

# Check Python version
print(f"\n1. Python version: {sys.version}")

# Check if we're in the right directory
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"\n2. Backend directory: {backend_dir}")
os.chdir(backend_dir)

# Check if virtual environment exists
venv_path = os.path.join(backend_dir, "venv")
venv_python = os.path.join(venv_path, "Scripts", "python.exe") if sys.platform == "win32" else os.path.join(venv_path, "bin", "python")

if os.path.exists(venv_python):
    print(f"\n3. ✓ Virtual environment found at: {venv_path}")
else:
    print(f"\n3. ❌ Virtual environment NOT found at: {venv_path}")
    print("   Create it with: python -m venv venv")

# Check if main app file exists
main_file = os.path.join(backend_dir, "app", "main.py")
if os.path.exists(main_file):
    print(f"\n4. ✓ Main app file found: {main_file}")
else:
    print(f"\n4. ❌ Main app file NOT found: {main_file}")

# Try to import required modules
print("\n5. Checking required modules:")
try:
    import uvicorn
    print("   ✓ uvicorn installed")
except ImportError:
    print("   ❌ uvicorn NOT installed")
    print("   Install with: pip install uvicorn")

try:
    import fastapi
    print("   ✓ fastapi installed")
except ImportError:
    print("   ❌ fastapi NOT installed")
    print("   Install with: pip install fastapi")

# Check if port 8001 is already in use
print("\n6. Checking if port 8001 is available:")
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('localhost', 8001))
sock.close()

if result == 0:
    print("   ⚠️  Port 8001 is already in use!")
    print("   Maybe the backend is already running?")
    
    # Try to access the health endpoint
    try:
        import requests
        response = requests.get("http://localhost:8001/api/v1/health/")
        if response.status_code == 200:
            print("   ✓ Backend is already running and responsive!")
        else:
            print("   ❌ Something is using port 8001 but it's not our backend")
    except:
        print("   ❌ Port is in use but can't connect to it")
else:
    print("   ✓ Port 8001 is available")

# Try to start the backend
print("\n7. Attempting to start backend...")
print("   Command: uvicorn app.main:app --host 0.0.0.0 --port 8001")

# Create a simple test script
test_start = """
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import app
    print("✓ Successfully imported app")
except Exception as e:
    print(f"❌ Failed to import app: {e}")
    import traceback
    traceback.print_exc()
"""

with open("test_import.py", "w") as f:
    f.write(test_start)

print("\n8. Testing app import:")
result = subprocess.run([sys.executable, "test_import.py"], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("Errors:")
    print(result.stderr)

# Clean up
os.remove("test_import.py")

print("\n" + "="*60)
print("RECOMMENDED ACTIONS")
print("="*60)

if result == 0:
    print("\n✓ Backend appears to be already running!")
    print("  Open http://localhost:8001/docs to check")
else:
    print("\n1. Make sure you're in the virtual environment:")
    print("   cd", backend_dir)
    print("   .\\venv\\Scripts\\activate  (Windows)")
    print("\n2. Install dependencies:")
    print("   pip install -r requirements.txt")
    print("\n3. Start the backend:")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8001")