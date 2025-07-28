@echo off
echo Starting Promtitude Backend...
echo ================================

cd ..
echo Current directory: %CD%

echo.
echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Starting backend server...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

pause