#!/usr/bin/env python3
"""Run backend with no caching whatsoever."""

import os
import sys
import subprocess
import shutil

# Step 1: Clean all caches
print("Cleaning Python cache...")
for root, dirs, files in os.walk('.'):
    for dir in dirs:
        if dir == '__pycache__':
            full_path = os.path.join(root, dir)
            print(f"  Removing {full_path}")
            shutil.rmtree(full_path)

# Step 2: Clear Python's import cache
for module in list(sys.modules.keys()):
    if module.startswith('app'):
        del sys.modules[module]

# Step 3: Set environment to disable Python bytecode
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Step 4: Run uvicorn as a subprocess with no reload
print("\nStarting backend server with no caching...")
print("="*60)

cmd = [
    sys.executable,
    '-B',  # Don't write bytecode
    '-m',
    'uvicorn',
    'app.main:app',
    '--host', '0.0.0.0',
    '--port', '8001',
    '--no-reload',  # Disable reload
    '--log-level', 'info'
]

subprocess.run(cmd)