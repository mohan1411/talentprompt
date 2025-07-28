@echo off
echo Testing Backend API...
echo ======================

echo.
echo 1. Testing Health Endpoint:
curl -i http://localhost:8001/api/v1/health/

echo.
echo.
echo 2. Testing Docs:
curl -i http://localhost:8001/docs

echo.
echo.
echo 3. Testing with PowerShell:
powershell -Command "Invoke-WebRequest -Uri 'http://localhost:8001/api/v1/health/' -UseBasicParsing"

echo.
pause