#!/bin/bash

# Run the backend in a Docker container connecting to the already running databases

docker run --rm -it \
  --name talentprompt-backend-dev \
  --network talentprompt_default \
  -p 8001:8000 \
  -v $(pwd):/app \
  -e DATABASE_URL="postgresql://talentprompt:talentprompt123@talentprompt-postgres:5432/talentprompt" \
  -e REDIS_URL="redis://talentprompt-redis:6379/0" \
  -e QDRANT_URL="http://talentprompt-qdrant:6333" \
  -e SECRET_KEY="your-secret-key-at-least-32-characters-long-change-this" \
  -e FIRST_SUPERUSER="admin@talentprompt.ai" \
  -e FIRST_SUPERUSER_PASSWORD="admin123" \
  -e OPENAI_API_KEY="${OPENAI_API_KEY:-your-openai-key}" \
  -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-your-anthropic-key}" \
  python:3.12-slim \
  bash -c "
    cd /app && \
    apt-get update && apt-get install -y gcc libpq-dev && \
    pip install -r requirements.txt && \
    alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  "