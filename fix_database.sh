#!/bin/bash

echo "Fixing PostgreSQL database setup..."

# Connect to PostgreSQL as the default postgres user and create our database and user
docker-compose exec postgres psql -U postgres -c "CREATE USER promtitude WITH PASSWORD 'promtitude123';"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE promtitude OWNER promtitude;"
docker-compose exec postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE promtitude TO promtitude;"

# Create pgvector extension (even though we're using Qdrant, some tables might still reference it)
docker-compose exec postgres psql -U postgres -d promtitude -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
docker-compose exec postgres psql -U postgres -d promtitude -c "CREATE EXTENSION IF NOT EXISTS pgvector;"

echo "Database setup completed!"

# Restart backend to reconnect
echo "Restarting backend..."
docker-compose restart backend

sleep 5

# Run migrations
echo "Running migrations..."
docker-compose exec backend alembic upgrade head

echo "All done!"