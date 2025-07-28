#!/usr/bin/env python3
"""Run the backend server with a fresh import."""

import os
import sys

# Clear Python cache
import shutil
for root, dirs, files in os.walk('.'):
    for dir in dirs:
        if dir == '__pycache__':
            shutil.rmtree(os.path.join(root, dir))
            print(f"Removed {os.path.join(root, dir)}")

# Force reimport of modules
for module in list(sys.modules.keys()):
    if module.startswith('app.'):
        del sys.modules[module]

# Now start the server
import uvicorn
from app.main import app

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Starting fresh backend server...")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False,  # Disable reload to avoid caching issues
        log_level="info"
    )