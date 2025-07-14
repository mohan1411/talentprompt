#!/bin/bash

# Development script to run backend without Docker

echo "Starting TalentPrompt Backend in development mode..."
echo "Make sure you have PostgreSQL, Redis, and Qdrant running locally"
echo ""

# Set environment variables
export DATABASE_URL="postgresql://talentprompt:talentprompt123@localhost:5432/talentprompt"
export REDIS_URL="redis://localhost:6379/0"
export QDRANT_URL="http://localhost:6333"
export JWT_SECRET_KEY="your-secret-key-change-in-production"
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the server
echo "Starting FastAPI server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000