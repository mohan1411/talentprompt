Write-Host "Setting up environment configuration..." -ForegroundColor Green

# Check if .env file exists
if (Test-Path ".env") {
    Write-Host ".env file already exists. Skipping creation." -ForegroundColor Yellow
    Write-Host "Please update it with your Railway DATABASE_URL" -ForegroundColor Cyan
} else {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    
    Write-Host "`n⚠️  IMPORTANT: Update your .env file with:" -ForegroundColor Red
    Write-Host "1. Railway DATABASE_URL (get from Railway dashboard)" -ForegroundColor Yellow
    Write-Host "2. Your OpenAI API key" -ForegroundColor Yellow
    Write-Host "3. JWT_SECRET_KEY (generate a secure random string)" -ForegroundColor Yellow
    
    Write-Host "`nExample DATABASE_URL format:" -ForegroundColor Cyan
    Write-Host "DATABASE_URL=postgresql://postgres:password@host.railway.app:5432/railway" -ForegroundColor White
}

Write-Host "`nTo edit the .env file:" -ForegroundColor Cyan
Write-Host "notepad .env" -ForegroundColor White