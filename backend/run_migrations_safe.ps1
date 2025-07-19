Write-Host "Running migrations safely..." -ForegroundColor Green

# First check current status
Write-Host "`nChecking current migration status..." -ForegroundColor Yellow
python check_migrations.py

# Clean up any conflicting enums
Write-Host "`nCleaning up enum types..." -ForegroundColor Yellow
python clean_enums.py

# Run migrations
Write-Host "`nRunning Alembic migrations..." -ForegroundColor Yellow
alembic upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Migrations completed successfully!" -ForegroundColor Green
    
    # Check final status
    Write-Host "`nFinal migration status:" -ForegroundColor Cyan
    python check_migrations.py
} else {
    Write-Host "`n❌ Migration failed!" -ForegroundColor Red
    Write-Host "Check the error messages above for details." -ForegroundColor Yellow
}