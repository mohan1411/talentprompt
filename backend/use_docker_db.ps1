Write-Host "Setting up Docker database configuration..." -ForegroundColor Green

# Copy Docker env file
if (Test-Path ".env") {
    Write-Host "Backing up existing .env to .env.backup" -ForegroundColor Yellow
    Copy-Item ".env" ".env.backup"
}

Write-Host "Using Docker database configuration..." -ForegroundColor Yellow
Copy-Item ".env.docker" ".env"

Write-Host "`n✅ Docker database configuration set!" -ForegroundColor Green
Write-Host "`nDatabase URL: postgresql://promtitude:promtitude123@localhost:5433/promtitude" -ForegroundColor Cyan

Write-Host "`nMake sure:" -ForegroundColor Yellow
Write-Host "1. Docker containers are running: docker-compose up -d postgres redis" -ForegroundColor White
Write-Host "2. Update OPENAI_API_KEY in .env file" -ForegroundColor White

Write-Host "`nTo start Docker services:" -ForegroundColor Cyan
Write-Host "docker-compose up -d postgres redis qdrant" -ForegroundColor White

Write-Host "`nTo run migrations:" -ForegroundColor Cyan
Write-Host "alembic upgrade head" -ForegroundColor White