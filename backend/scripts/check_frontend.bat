@echo off
echo Checking Frontend Status...
echo ==========================

echo.
echo Checking port 3000:
netstat -an | findstr :3000

echo.
echo Trying to access frontend:
curl -I http://localhost:3000 2>nul || echo Frontend not accessible

echo.
echo If frontend is not running, start it with:
echo   cd frontend
echo   npm run dev

echo.
pause