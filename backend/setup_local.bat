@echo off
echo Setting up local development environment...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ✅ Setup complete!
echo.
echo To activate the virtual environment in the future, run:
echo   venv\Scripts\activate.bat
echo.
echo To run migrations:
echo   alembic upgrade head
echo.
echo To start the development server:
echo   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000