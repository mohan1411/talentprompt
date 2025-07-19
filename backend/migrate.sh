#!/bin/bash
# Script to run database migrations

echo "🚀 Running database migrations..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the migration
alembic upgrade head

echo "✅ Migration complete!"