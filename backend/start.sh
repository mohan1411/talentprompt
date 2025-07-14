#!/bin/bash
# Start script for Railway deployment

# Set default port if not provided
PORT=${PORT:-8000}

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"