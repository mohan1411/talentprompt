Write-Host "Setting up local database configuration..." -ForegroundColor Green

# Copy local env file
if (Test-Path ".env") {
    Write-Host "Backing up existing .env to .env.backup" -ForegroundColor Yellow
    Copy-Item ".env" ".env.backup"
}

Write-Host "Using local database configuration..." -ForegroundColor Yellow
Copy-Item ".env.local" ".env"

Write-Host "`n✅ Local database configuration set!" -ForegroundColor Green
Write-Host "`nDatabase URL: postgresql://postgres:postgres@localhost:5432/talentprompt" -ForegroundColor Cyan

Write-Host "`nMake sure:" -ForegroundColor Yellow
Write-Host "1. PostgreSQL is running locally" -ForegroundColor White
Write-Host "2. Database 'talentprompt' exists" -ForegroundColor White
Write-Host "3. Update OPENAI_API_KEY in .env file" -ForegroundColor White

Write-Host "`nTo create the database (if needed):" -ForegroundColor Cyan
Write-Host 'psql -U postgres -c "CREATE DATABASE talentprompt;"' -ForegroundColor White

Write-Host "`nTo run migrations:" -ForegroundColor Cyan
Write-Host "alembic upgrade head" -ForegroundColor White