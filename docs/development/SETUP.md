# Promtitude Development Setup Guide

## 1. Prerequisites

Before setting up Promtitude, ensure you have the following installed:

### Required Software
- **Python** 3.12 or higher (3.12 recommended as of July 2025)
- **Node.js** 18.x or higher
- **PostgreSQL** 16 or higher (significant performance improvements)
- **Redis** 7.0 or higher
- **Docker** & Docker Compose
- **Git**

### 2025 Updates
- Python 3.12 is now stable and recommended
- PostgreSQL 16 offers better vector search performance
- New AI models: OpenAI o3/o4-mini and Claude 4

### Recommended Tools
- **VS Code** or **PyCharm** for development
- **Postman** or **Insomnia** for API testing
- **pgAdmin** or **DBeaver** for database management
- **Redis Commander** for Redis management

## 2. Environment Setup

### 2.1 Clone the Repository

```bash
git clone https://github.com/your-org/promtitude.git
cd promtitude
```

### 2.2 Environment Variables

Copy the example environment files:

```bash
# Backend environment
cp backend/.env.example backend/.env

# Frontend environment
cp frontend/.env.example frontend/.env
```

#### Backend Environment Variables (.env)

```env
# Application
APP_NAME=Promtitude
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/promtitude
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=0

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# Authentication
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# AI Services (Updated for 2025)
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=o4-mini  # Latest as of June 2025
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-4-sonnet  # Latest as of 2025
EMBEDDING_MODEL=text-embedding-ada-002

# Vector Database
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=promtitude-dev

# Search
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX_PREFIX=promtitude_

# Storage
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_S3_BUCKET=promtitude-resumes-dev
AWS_REGION=us-east-1

# Email
SENDGRID_API_KEY=your-sendgrid-key
FROM_EMAIL=noreply@promtitude.com

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
```

#### Frontend Environment Variables (.env.local)

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Authentication
NEXT_PUBLIC_AUTH0_DOMAIN=your-auth0-domain
NEXT_PUBLIC_AUTH0_CLIENT_ID=your-client-id
NEXT_PUBLIC_AUTH0_REDIRECT_URI=http://localhost:3000/callback

# Features
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_SENTRY=false

# Third-party Services
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=
NEXT_PUBLIC_INTERCOM_APP_ID=
```

## 3. Database Setup

### 3.1 Using Docker (Recommended)

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis elasticsearch

# Wait for services to be ready
docker-compose logs -f postgres
```

### 3.2 Manual PostgreSQL Setup

```bash
# Create database
createdb promtitude

# Install extensions
psql promtitude << EOF
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";
EOF
```

### 3.3 Run Migrations

```bash
cd backend
alembic upgrade head
```

### 3.4 Seed Development Data

```bash
python scripts/seed_data.py
```

## 4. Backend Setup

### 4.1 Create Virtual Environment

```bash
cd backend
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4.2 Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 4.3 Start Backend Server

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the make command
make run-backend
```

### 4.4 Verify Backend

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs
```

## 5. Frontend Setup

### 5.1 Install Dependencies

```bash
cd frontend
npm install
# or
yarn install
```

### 5.2 Start Development Server

```bash
npm run dev
# or
yarn dev
```

### 5.3 Verify Frontend

```bash
# Open in browser
open http://localhost:3000
```

## 6. Additional Services Setup

### 6.1 Elasticsearch

```bash
# Using Docker
docker-compose up -d elasticsearch

# Create indices
curl -X PUT "localhost:9200/promtitude_resumes" -H 'Content-Type: application/json' -d @scripts/elasticsearch/resume_mapping.json
```

### 6.2 Vector Database (Pinecone)

```python
# Run setup script
python scripts/setup_pinecone.py
```

### 6.3 Background Workers

```bash
# Start Celery worker
celery -A app.worker worker --loglevel=info

# Start Celery beat (scheduled tasks)
celery -A app.worker beat --loglevel=info
```

## 7. Development Workflow

### 7.1 Running Tests

```bash
# Backend tests
cd backend
pytest
pytest --cov=app tests/

# Frontend tests
cd frontend
npm test
npm run test:coverage
```

### 7.2 Code Quality

```bash
# Backend linting
cd backend
flake8 app/
black app/
mypy app/

# Frontend linting
cd frontend
npm run lint
npm run format
```

### 7.3 Type Checking

```bash
# Backend
mypy app/

# Frontend
npm run type-check
```

## 8. Docker Development

### 8.1 Full Stack with Docker Compose

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up

# Start specific services
docker-compose up backend frontend

# View logs
docker-compose logs -f backend
```

### 8.2 Docker Compose Override

Create `docker-compose.override.yml` for local overrides:

```yaml
version: '3.8'

services:
  backend:
    volumes:
      - ./backend:/app
    environment:
      - DEBUG=true
  
  frontend:
    volumes:
      - ./frontend:/app
      - /app/node_modules
```

## 9. IDE Configuration

### 9.1 VS Code

Recommended extensions:
- Python
- Pylance
- Black Formatter
- ESLint
- Prettier
- Thunder Client

Create `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### 9.2 PyCharm

1. Set Python interpreter to virtual environment
2. Enable Django support (even though we use FastAPI)
3. Configure code style to use Black
4. Set up database connection

## 10. Troubleshooting

### Common Issues

#### PostgreSQL Connection Error
```bash
# Check if PostgreSQL is running
pg_isready

# Check connection
psql -U postgres -h localhost -p 5432
```

#### Vector Extension Not Found
```bash
# Install pgvector
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install
```

#### Port Already in Use
```bash
# Find process using port
lsof -i :8000
# or on Windows
netstat -ano | findstr :8000

# Kill process
kill -9 <PID>
```

#### Node Modules Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

## 11. Development Tips

### 11.1 Hot Reload

- Backend: Automatically enabled with `--reload` flag
- Frontend: Automatically enabled in development

### 11.2 Database GUI

```bash
# pgAdmin
docker run -p 5050:80 \
  -e PGADMIN_DEFAULT_EMAIL=admin@example.com \
  -e PGADMIN_DEFAULT_PASSWORD=admin \
  dpage/pgadmin4
```

### 11.3 API Testing

Use the interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 11.4 Performance Profiling

```python
# Add to backend code
from app.core.profiler import profile

@profile
def slow_function():
    # Your code here
```

## 12. Next Steps

1. Review the [Architecture Documentation](../technical/ARCHITECTURE.md)
2. Read the [API Specification](../technical/API_SPECIFICATION.md)
3. Check [Coding Standards](CODING_STANDARDS.md)
4. Join our Discord/Slack for questions

---

**Document Version**: 1.0
**Last Updated**: [Date]
**Maintained By**: Development Team
**Support**: dev@promtitude.com