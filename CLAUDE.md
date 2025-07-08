# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TalentPrompt is an AI-powered recruitment platform that enables natural language searches to find candidates. The project is currently in the documentation/planning phase with comprehensive technical specifications but no implemented source code yet.

## Development Commands

### Backend Development (Once implemented)
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest
pytest --cov=app tests/

# Code quality checks
flake8 app/
black app/
mypy app/
```

### Frontend Development (Once implemented)
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm test
npm run test:coverage

# Code quality checks
npm run lint
npm run format
npm run type-check
```

### Full Stack with Docker
```bash
# Start all services
docker-compose up

# Run migrations
cd backend && alembic upgrade head

# Seed development data
python scripts/seed_data.py
```

## Architecture Overview

The platform follows a microservices architecture with these key components:

1. **API Gateway**: Routes requests and handles authentication
2. **Core API Service**: FastAPI-based service handling business logic
3. **Search API Service**: Dedicated service for natural language search using vector databases
4. **AI Service**: Manages LLM interactions (OpenAI o4-mini, Claude 4 Sonnet)
5. **AI Compliance Layer**: Ensures EU AI Act compliance with transparency and oversight

### Technology Stack
- **Backend**: Python 3.12 with FastAPI
- **Frontend**: Next.js 15 with React 19 and TypeScript
- **Database**: PostgreSQL 16 with pgvector extension
- **Vector Store**: Qdrant for semantic search
- **LLMs**: OpenAI o4-mini and Claude 4 Sonnet
- **Cache**: Redis 7.0
- **Queue**: Celery with RabbitMQ

### Key Design Patterns
- RESTful APIs with OpenAPI documentation
- Event-driven architecture for asynchronous processing
- Repository pattern for data access
- Dependency injection for testability
- Circuit breaker pattern for external service calls

## EU AI Act Compliance

This project has built-in compliance features for the EU AI Act (required by August 2025):
- All AI decisions must have transparency mechanisms
- Human oversight is required for critical decisions
- Bias detection and mitigation must be implemented
- Comprehensive audit trails for all AI interactions
- Users have the right to contest AI decisions

## Important Notes

1. **Current Status**: Documentation phase - no source code exists yet
2. **AI Models**: Uses latest models (o4-mini, Claude 4) as of 2025
3. **Performance Targets**: < 300ms search for 1M resumes, 95% relevance accuracy
4. **Security**: GDPR compliant, SOC 2 Type II certified, end-to-end encryption

## File Organization

```
TalentPrompt/
├── backend/           # FastAPI backend (to be implemented)
├── frontend/          # Next.js frontend (to be implemented)
├── docs/              # Comprehensive documentation
│   ├── technical/     # Architecture, API specs, database schema
│   ├── development/   # Setup guides
│   ├── business/      # Business model
│   └── project/       # Roadmap
└── docker-compose.yml # Container orchestration (to be created)
```

## Key Environment Variables

Backend requires:
- `OPENAI_API_KEY`: For OpenAI o4-mini access
- `ANTHROPIC_API_KEY`: For Claude 4 Sonnet access
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for caching
- `JWT_SECRET_KEY`: For authentication

Frontend requires:
- `NEXT_PUBLIC_API_URL`: Backend API endpoint
- `NEXT_PUBLIC_WS_URL`: WebSocket endpoint for real-time features