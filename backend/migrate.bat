@echo off
echo Running database migrations...

REM Check if virtual environment is activated
if "%VIRTUAL_ENV%"=="" (
    if exist "venv\Scripts\activate.bat" (
        echo Activating virtual environment...
        call venv\Scripts\activate.bat
    ) else (
        echo Warning: No virtual environment found. Using global Python.
    )
)

echo Executing migrations...
alembic upgrade head

if %ERRORLEVEL% EQU 0 (
    echo ✅ Migrations completed successfully!
) else (
    echo ❌ Migration failed!
    exit /b 1
)