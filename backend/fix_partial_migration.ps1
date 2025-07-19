Write-Host "Fixing partial migration state..." -ForegroundColor Green

# Check what exists
Write-Host "`nChecking existing outreach tables and types..." -ForegroundColor Yellow
python check_existing_tables.py

# Ask user what to do
Write-Host "`nOptions:" -ForegroundColor Cyan
Write-Host "1. Drop existing types and tables, then re-run migration" -ForegroundColor White
Write-Host "2. Mark migration as complete (if tables already exist)" -ForegroundColor White
Write-Host "3. Cancel" -ForegroundColor White

$choice = Read-Host "`nEnter choice (1-3)"

switch ($choice) {
    "1" {
        Write-Host "`nDropping existing outreach objects..." -ForegroundColor Yellow
        
        # Create cleanup script
        @"
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os

async def cleanup():
    load_dotenv()
    database_url = os.getenv('DATABASE_URL')
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    engine = create_async_engine(database_url)
    async with engine.connect() as conn:
        # Drop tables if they exist
        await conn.execute(text('DROP TABLE IF EXISTS outreach_templates CASCADE'))
        await conn.execute(text('DROP TABLE IF EXISTS outreach_messages CASCADE'))
        await conn.commit()
        
        # Drop types if they exist
        await conn.execute(text('DROP TYPE IF EXISTS messagestatus CASCADE'))
        await conn.execute(text('DROP TYPE IF EXISTS messagestyle CASCADE'))
        await conn.commit()
        
        print('✅ Cleanup complete!')
    await engine.dispose()

asyncio.run(cleanup())
"@ | python
        
        Write-Host "`nRunning migration again..." -ForegroundColor Yellow
        alembic upgrade head
    }
    "2" {
        Write-Host "`nMarking migration as complete..." -ForegroundColor Yellow
        
        # Create stamp script
        @"
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os

async def stamp():
    load_dotenv()
    database_url = os.getenv('DATABASE_URL')
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    engine = create_async_engine(database_url)
    async with engine.connect() as conn:
        # Update alembic version
        await conn.execute(text("DELETE FROM alembic_version"))
        await conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('add_outreach_tables')"))
        await conn.commit()
        print('✅ Migration marked as complete!')
    await engine.dispose()

asyncio.run(stamp())
"@ | python
    }
    "3" {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit
    }
    default {
        Write-Host "Invalid choice." -ForegroundColor Red
        exit
    }
}

Write-Host "`n✅ Done!" -ForegroundColor Green