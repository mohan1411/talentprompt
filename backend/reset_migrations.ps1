Write-Host "Resetting Alembic migrations..." -ForegroundColor Yellow

$confirm = Read-Host "This will reset the alembic_version table. Continue? (y/N)"
if ($confirm -ne 'y') {
    Write-Host "Cancelled." -ForegroundColor Red
    exit
}

Write-Host "`nDowngrading all migrations..." -ForegroundColor Yellow
alembic downgrade base

Write-Host "`nRunning all migrations fresh..." -ForegroundColor Yellow
alembic upgrade head

Write-Host "`n✅ Migrations reset complete!" -ForegroundColor Green