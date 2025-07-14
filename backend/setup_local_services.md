# Running Promtitude Without Docker

If Docker Desktop is not available or not running, you can run the services locally.

## Prerequisites

### 1. PostgreSQL with pgvector
- Download PostgreSQL 16 from https://www.postgresql.org/download/windows/
- Install pgvector extension:
  ```sql
  CREATE EXTENSION vector;
  ```

### 2. Redis
- Download Redis for Windows from https://github.com/microsoftarchive/redis/releases
- Or use WSL2: `sudo apt install redis-server`

### 3. Qdrant
- Download from https://github.com/qdrant/qdrant/releases
- Or run with: `docker run -p 6333:6333 qdrant/qdrant` (if Docker is available)

## Setup Steps

### 1. Create PostgreSQL Database
```sql
CREATE USER promtitude WITH PASSWORD 'promtitude123';
CREATE DATABASE promtitude OWNER promtitude;
\c promtitude
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Start Redis
```bash
# Windows
redis-server

# WSL2/Linux
sudo service redis-server start
```

### 3. Start Qdrant
```bash
# From Qdrant directory
./qdrant
```

### 4. Run Backend
```bash
# Windows
cd backend
run_dev.bat

# Linux/WSL
cd backend
chmod +x run_dev.sh
./run_dev.sh
```

### 5. Run Frontend
```bash
cd frontend
npm install
npm run dev
```

## Alternative: Minimal Docker Setup

If you just want to run the databases with Docker and the apps locally:

```yaml
# docker-compose.minimal.yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: promtitude
      POSTGRES_PASSWORD: promtitude123
      POSTGRES_DB: promtitude
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  qdrant_data:
```

Run with: `docker-compose -f docker-compose.minimal.yml up`