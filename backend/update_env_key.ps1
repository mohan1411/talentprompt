Write-Host "Updating .env file to use SECRET_KEY..." -ForegroundColor Green

if (Test-Path ".env") {
    $content = Get-Content ".env" -Raw
    if ($content -match "JWT_SECRET_KEY") {
        Write-Host "Found JWT_SECRET_KEY, updating to SECRET_KEY..." -ForegroundColor Yellow
        $content = $content -replace "JWT_SECRET_KEY=", "SECRET_KEY="
        $content | Set-Content ".env" -NoNewline
        Write-Host "✅ Updated .env file!" -ForegroundColor Green
    } else {
        Write-Host "No JWT_SECRET_KEY found, checking for SECRET_KEY..." -ForegroundColor Yellow
        if ($content -match "SECRET_KEY") {
            Write-Host "✅ SECRET_KEY already exists!" -ForegroundColor Green
        } else {
            Write-Host "⚠️  No SECRET_KEY found! Adding default..." -ForegroundColor Red
            Add-Content ".env" "`nSECRET_KEY=local-dev-secret-key-change-in-production"
        }
    }
} else {
    Write-Host "❌ No .env file found! Please create one first." -ForegroundColor Red
}