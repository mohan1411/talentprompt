@echo off
REM Development script to run backend without Docker on Windows

echo Starting TalentPrompt Backend in development mode...
echo Make sure you have PostgreSQL, Redis, and Qdrant running locally
echo.

REM Set environment variables
set DATABASE_URL=postgresql://talentprompt:talentprompt123@localhost:5432/talentprompt
set REDIS_URL=redis://localhost:6379/0
set QDRANT_URL=http://localhost:6333
set JWT_SECRET_KEY=your-secret-key-change-in-production

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run database migrations
echo Running database migrations...
alembic upgrade head

REM Start the server
echo Starting FastAPI server...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000