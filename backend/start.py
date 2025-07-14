#!/usr/bin/env python3
"""Start script for Railway deployment."""
import os
import sys

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Also add parent directory in case of import issues
parent_dir = os.path.dirname(backend_dir)
sys.path.insert(0, parent_dir)

# Print debug info
print(f"Python path: {sys.path}")
print(f"Working directory: {os.getcwd()}")
print(f"Backend directory: {backend_dir}")

# Check if app module exists
app_path = os.path.join(backend_dir, "app")
if os.path.exists(app_path):
    print(f"App module found at: {app_path}")
    models_path = os.path.join(app_path, "models")
    if os.path.exists(models_path):
        print(f"Models module found at: {models_path}")
    else:
        print("WARNING: Models module not found!")
else:
    print("ERROR: App module not found!")

import uvicorn

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    print(f"Starting server on port {port}...")
    
    # Start the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )