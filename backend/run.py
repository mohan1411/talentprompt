#!/usr/bin/env python3
"""Alternative start script using module run."""
import os
import sys

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run uvicorn as a module
if __name__ == "__main__":
    port = os.environ.get("PORT", "8000")
    sys.argv = [
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", port,
        "--log-level", "info"
    ]
    
    # Import and run uvicorn
    from uvicorn import main
    sys.exit(main())