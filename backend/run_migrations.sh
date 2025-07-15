#!/bin/bash

# Script to run database migrations

echo "Running database migrations..."

# Check if we're in Docker or local environment
if [ -f /.dockerenv ]; then
    # We're in Docker
    echo "Running migrations in Docker environment..."
    alembic upgrade head
else
    # We're in local environment
    echo "Running migrations in local environment..."
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        # Activate virtual environment
        source venv/bin/activate
        alembic upgrade head
    else
        # Try with system Python
        python3 -m alembic upgrade head || alembic upgrade head
    fi
fi

echo "Migrations completed!"