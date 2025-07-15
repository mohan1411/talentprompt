#!/bin/bash

echo "Resetting PostgreSQL database..."

# Stop all services
docker-compose down

# Remove the postgres volume to start fresh
docker volume rm talentprompt_postgres_data 2>/dev/null || true

# Start only postgres first
echo "Starting PostgreSQL..."
docker-compose up -d postgres

# Wait for PostgreSQL to initialize
echo "Waiting for PostgreSQL to initialize (30 seconds)..."
sleep 30

# Check if it's ready
docker-compose exec postgres pg_isready -U promtitude

# Now start the backend
echo "Starting backend..."
docker-compose up -d backend

# Wait a bit more
sleep 10

# Run migrations
echo "Running migrations..."
docker-compose exec backend alembic upgrade head

echo "Database reset complete!"