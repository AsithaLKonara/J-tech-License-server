# 🚂 Upload Bridge License Server - Railway Deployment

## Quick Start

### 1. Install Railway CLI

```bash
npm install -g @railway/cli
```

### 2. Login and Deploy

```bash
cd apps/license-server
railway login
railway init
railway variables set AUTH0_DOMAIN=dev-oczlciw58f2a4oei.us.auth0.com
railway up
```

### 3. Get Your URL

Railway will provide a URL like:
```
https://your-project.up.railway.app
```

## Environment Variables

Set these in Railway dashboard or via CLI:

- `AUTH0_DOMAIN` - Required (e.g., `dev-oczlciw58f2a4oei.us.auth0.com`)
- `AUTH0_CLIENT_ID` - Required
- `AUTH0_AUDIENCE` - Optional
- `PORT` - Auto-set by Railway

## Testing

```bash
# Health check
curl https://your-project.up.railway.app/api/health

# Login
curl -X POST https://your-project.up.railway.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "auth0_token": "your-token",
    "device_id": "DEVICE_123",
    "device_name": "Test"
  }'
```

## Documentation

- **Full Guide**: See `RAILWAY_DEPLOYMENT.md`
- **Migration Details**: See `MIGRATION_TO_RAILWAY.md`

## Why Railway?

✅ Traditional Express server (no serverless limitations)  
✅ Better TypeScript support  
✅ Simpler deployment  
✅ More reliable runtime  

---

**Status**: ✅ Ready for Railway deployment

