#!/bin/bash

# Run database migration in Docker container

echo "Running database migration for LinkedIn fields..."

# Run the migration using docker-compose exec
docker-compose exec talentprompt-backend alembic upgrade head

echo "Migration completed!"
echo ""
echo "To verify the migration, you can run:"
echo "docker-compose exec talentprompt-backend alembic current"