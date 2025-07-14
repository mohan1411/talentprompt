#!/bin/sh
# Simple entrypoint script for Railway

# Use PORT environment variable or default to 8000
PORT=${PORT:-8000}

echo "Starting application on port $PORT"

# Start uvicorn with the resolved port
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT