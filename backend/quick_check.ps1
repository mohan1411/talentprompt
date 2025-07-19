Write-Host "Checking database state..." -ForegroundColor Green

# Check migration status
Write-Host "`n1. Current migration status:" -ForegroundColor Yellow
alembic current

# Check if outreach tables exist
Write-Host "`n2. Checking outreach tables:" -ForegroundColor Yellow
python check_existing_tables.py

# Show all tables
Write-Host "`n3. All tables in database:" -ForegroundColor Yellow
python check_migrations.py