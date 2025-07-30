# Railway Migration Commands

## Find Your Service Name

First, find your backend service name:

```bash
railway status
```

Or check your Railway dashboard - the service name is shown for each service (e.g., "backend", "web", "api", etc.)

## Run Migration Commands

### Option 1: Using Railway Run (Recommended)

Replace `<service-name>` with your actual backend service name:

```bash
# Run alembic migration
railway run --service <service-name> alembic upgrade heads

# Or run the manual creation script
railway run --service <service-name> python scripts/create_submission_tables.py
```

Example if your service is named "backend":
```bash
railway run --service backend alembic upgrade heads
```

### Option 2: Using Railway Shell

Connect to your service shell:
```bash
railway shell --service <service-name>
```

Then run commands directly:
```bash
alembic upgrade heads
# or
python scripts/create_submission_tables.py
```

### Option 3: Using Railway Dashboard

1. Go to [railway.app](https://railway.app)
2. Open your project
3. Click on your backend service
4. Go to "Settings" → "Deploy"
5. Find "Run a Command" section
6. Enter: `alembic upgrade heads`
7. Click "Run"

### Option 4: Direct Database Connection

If you have your DATABASE_URL:

```bash
# Windows PowerShell
$env:DATABASE_URL="your-database-url-here"
cd backend
python scripts/create_submission_tables.py

# Or use alembic
alembic upgrade heads
```

## Quick Commands for Common Service Names

If your backend service is named "backend":
```bash
railway run --service backend alembic upgrade heads
```

If your backend service is named "web":
```bash
railway run --service web alembic upgrade heads
```

If your backend service is named "api":
```bash
railway run --service api alembic upgrade heads
```

## Troubleshooting

### "Service not found" Error
- Make sure you're in the right Railway project: `railway status`
- List all services: `railway service list`
- Link to project if needed: `railway link`

### Database Connection Issues
- Check your service has DATABASE_URL variable set
- Verify your service is running
- Check Railway logs: `railway logs --service <service-name>`

### Migration Errors
If alembic fails, try the manual script:
```bash
railway run --service <service-name> python scripts/create_submission_tables.py
```

## Verify Success

After running the migration, verify tables were created:

1. Check your Railway logs
2. Try creating a submission in the app
3. Or run: `railway run --service <service-name> python -c "print('Tables created!')"`

The candidate submission feature should work immediately after successful migration!