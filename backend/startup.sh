#!/bin/sh

# Try to run database fix, but don't fail if it errors
echo "Running database fix..."
python fix_email_verification.py || echo "Database fix failed, continuing anyway..."

# Start the application
echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}