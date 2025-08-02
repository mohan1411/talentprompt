# Qdrant Connection Guide for Railway Production

## Quick Status Check

### 1. Via API Endpoints (External)

Check these endpoints from your browser or curl:

```bash
# General health check
curl https://talentprompt-production.up.railway.app/api/v1/health

# Specific Qdrant health check
curl https://talentprompt-production.up.railway.app/api/v1/health/qdrant
```

### 2. Via Railway Logs

In your Railway dashboard:
1. Go to your backend service
2. Click on "View Logs"
3. Look for Qdrant-related messages:
   - `"Vector search initialized successfully"` - Good!
   - `"Failed to connect to Qdrant"` - Connection issue
   - `"Qdrant collection 'promtitude_resumes' created"` - First time setup

### 3. Via Railway Shell (Direct Container Access)

In Railway dashboard:
1. Click on your backend service
2. Go to "Settings" → "Railway CLI" or use the shell feature
3. Run these commands:

```bash
# Check environment variables
echo $QDRANT_URL
echo $QDRANT_API_KEY

# Run the monitoring script
python monitor_qdrant.py

# Quick Python check
python -c "
import os
print(f'QDRANT_URL: {os.getenv(\"QDRANT_URL\", \"Not Set\")}')
print(f'QDRANT_API_KEY: {\"Set\" if os.getenv(\"QDRANT_API_KEY\") else \"Not Set\"}')
"
```

## Common Qdrant Configurations

### Option 1: Qdrant Cloud (Recommended for Production)
```bash
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your-api-key-here
QDRANT_COLLECTION_NAME=promtitude_resumes
```

### Option 2: Self-Hosted Qdrant on Railway
```bash
QDRANT_URL=http://qdrant.railway.internal:6333
QDRANT_COLLECTION_NAME=promtitude_resumes
```

### Option 3: External Self-Hosted Qdrant
```bash
QDRANT_URL=http://your-qdrant-server.com:6333
QDRANT_API_KEY=your-api-key-if-secured
QDRANT_COLLECTION_NAME=promtitude_resumes
```

## Troubleshooting

### Issue: "Qdrant configured for localhost"
**Cause**: QDRANT_URL is still set to localhost
**Fix**: Update QDRANT_URL in Railway environment variables

### Issue: "Failed to connect to Qdrant"
**Possible Causes**:
1. Wrong QDRANT_URL
2. Missing QDRANT_API_KEY for cloud instances
3. Network connectivity issues
4. Qdrant service is down

**Debugging Steps**:
1. Verify environment variables are set correctly
2. Test connection from Railway shell
3. Check if Qdrant service is running (for self-hosted)
4. Verify firewall/security group rules

### Issue: "Collection not found"
**Cause**: First time running or collection was deleted
**Fix**: The app will automatically create it on first resume upload

## Monitoring Best Practices

1. **Set up alerts** for the `/api/v1/health/qdrant` endpoint
2. **Monitor logs** for Qdrant connection errors
3. **Track metrics**:
   - Vector count growth
   - Search query performance
   - Connection failures

## Fallback Behavior

If Qdrant is unavailable, Promtitude will:
1. Log the error but continue running
2. Fall back to PostgreSQL keyword search
3. Queue resumes for indexing when Qdrant returns
4. Show a warning in search results

## Performance Tips

1. **Use Qdrant Cloud** for production - it's optimized and managed
2. **Set appropriate timeouts** - currently 30 seconds
3. **Monitor vector count** - performance may degrade over 1M vectors without proper indexing
4. **Use approximate counts** for performance in health checks

## Quick Diagnosis Script

Run this from your local machine:

```bash
python check_qdrant_production.py
```

Or with a custom URL:

```bash
python check_qdrant_production.py https://your-custom-domain.com
```