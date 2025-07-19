Write-Host "Running database migrations..." -ForegroundColor Green

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    if (Test-Path "venv\Scripts\Activate.ps1") {
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        & .\venv\Scripts\Activate.ps1
    } else {
        Write-Host "Warning: No virtual environment found. Using global Python." -ForegroundColor Yellow
    }
}

Write-Host "Executing migrations..." -ForegroundColor Yellow
alembic upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Migrations completed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Migration failed!" -ForegroundColor Red
    exit 1
}