#!/bin/bash

# Run database fix
echo "Running database fix..."
cd backend
python fix_email_verification.py

# Start the application
echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT