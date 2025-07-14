# Deployment Guide for Promtitude

This guide provides step-by-step instructions to deploy Promtitude on Railway.app.

## Prerequisites

1. Railway account (https://railway.app)
2. GitHub repository connected to Railway
3. Domain name (promtitude.com) configured

## Environment Variables

### Backend Service

Copy these environment variables to your Railway backend service:

```env
# Application
PROJECT_NAME=Promtitude
VERSION=0.1.0
API_V1_STR=/api/v1

# Security
SECRET_KEY=<generate-a-secure-32-char-key>
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# CORS (update with your production URLs)
BACKEND_CORS_ORIGINS=["https://promtitude.com","https://www.promtitude.com","https://api.promtitude.com"]

# Database (Railway provides these)
POSTGRES_SERVER=${{Postgres.PGHOST}}
POSTGRES_PORT=${{Postgres.PGPORT}}
POSTGRES_USER=${{Postgres.PGUSER}}
POSTGRES_PASSWORD=${{Postgres.PGPASSWORD}}
POSTGRES_DB=${{Postgres.PGDATABASE}}

# Redis (Railway provides these)
REDIS_URL=${{Redis.REDIS_URL}}

# AI Services (add your keys)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-ada-002

# Vector Database
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION_NAME=promtitude_resumes

# Email
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=noreply@promtitude.com
EMAILS_FROM_NAME=Promtitude

# First User
FIRST_SUPERUSER=admin@promtitude.com
FIRST_SUPERUSER_PASSWORD=changethispassword

# Monitoring
LOG_LEVEL=INFO
```

### Frontend Service

```env
NEXT_PUBLIC_API_URL=https://api.promtitude.com
NEXT_PUBLIC_WS_URL=wss://api.promtitude.com
```

## Deployment Steps

### 1. Create Railway Services

1. Log in to Railway
2. Create a new project
3. Add services:
   - PostgreSQL (from Railway templates)
   - Redis (from Railway templates)
   - Backend (from GitHub - point to `/backend`)
   - Frontend (from GitHub - point to `/frontend`)

### 2. Configure Backend Service

1. Set root directory: `/backend`
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add all backend environment variables
5. Set up custom domain: `api.promtitude.com`

### 3. Configure Frontend Service

1. Set root directory: `/frontend`
2. Set build command: `npm install && npm run build`
3. Set start command: `npm start`
4. Add frontend environment variables
5. Set up custom domain: `promtitude.com` and `www.promtitude.com`

### 4. Database Migration

After backend is deployed, run migrations:

```bash
# SSH into backend service or use Railway CLI
cd backend
alembic upgrade head
```

### 5. Create Initial Admin User

The first superuser will be created automatically using the environment variables:
- Email: admin@promtitude.com
- Password: (set in FIRST_SUPERUSER_PASSWORD)

### 6. DNS Configuration

Configure your domain DNS:

1. A record for `promtitude.com` → Railway frontend IP
2. A record for `www.promtitude.com` → Railway frontend IP
3. A record for `api.promtitude.com` → Railway backend IP

## Post-Deployment Checklist

- [ ] Frontend accessible at https://promtitude.com
- [ ] API accessible at https://api.promtitude.com/docs
- [ ] Can register new users
- [ ] Can upload resumes
- [ ] Search functionality works
- [ ] WebSocket connection for interviews works
- [ ] Email notifications sent correctly

## Monitoring

- Check Railway dashboard for service health
- Monitor logs for errors
- Set up alerts for service downtime

## Backup Strategy

1. Enable automatic PostgreSQL backups in Railway
2. Export data regularly using pg_dump
3. Store backups in secure cloud storage

## Scaling

Railway automatically handles scaling. For manual control:

1. Adjust service resources in Railway dashboard
2. Enable horizontal scaling for backend service
3. Consider CDN for frontend assets

## Troubleshooting

### Frontend can't connect to backend
- Check CORS settings in backend
- Verify API URL in frontend env vars
- Check Railway service logs

### Database connection issues
- Verify PostgreSQL service is running
- Check connection string format
- Ensure migrations have run

### WebSocket connection fails
- Check WebSocket URL includes `wss://`
- Verify CORS allows WebSocket origin
- Check nginx/proxy WebSocket headers

## Support

For deployment issues:
1. Check Railway documentation
2. Review service logs
3. Contact Railway support

For application issues:
1. Check application logs
2. Review error messages
3. Create GitHub issue