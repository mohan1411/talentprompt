# TalentPrompt Backend

FastAPI-based backend for the TalentPrompt AI recruitment platform.

## Quick Start

### Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000
- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Docker Development

Use Docker Compose from the project root:
```bash
docker-compose up backend
```

## Project Structure

```
backend/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Core configuration
│   ├── db/            # Database configuration
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   └── main.py        # FastAPI application
├── tests/             # Test files
├── alembic/           # Database migrations
└── scripts/           # Utility scripts
```

## Key Features

- FastAPI with async/await support
- PostgreSQL with pgvector for embeddings
- Redis for caching
- Qdrant for vector search
- OpenAI/Anthropic integration
- JWT authentication
- Comprehensive API documentation

## Testing

Run tests with pytest:
```bash
pytest
pytest --cov=app  # With coverage
```

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```