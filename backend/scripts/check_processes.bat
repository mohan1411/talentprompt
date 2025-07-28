@echo off
echo Checking for running Python/Uvicorn processes...
echo ================================================

echo.
echo Python processes:
tasklist | findstr python

echo.
echo Checking port 8001:
netstat -an | findstr :8001

echo.
echo Checking port 8000:
netstat -an | findstr :8000

echo.
pause