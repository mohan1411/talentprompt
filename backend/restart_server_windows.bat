@echo off
echo Stopping existing backend server...

REM Kill any existing uvicorn processes
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *uvicorn*" 2>nul

REM Alternative method using netstat to find process on port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing process on port 8000 (PID: %%a)
    taskkill /F /PID %%a 2>nul
)

echo Starting backend server...

REM Activate virtual environment and start server
call venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000