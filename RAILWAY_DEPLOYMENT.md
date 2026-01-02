# 🚂 Railway Deployment Guide

Complete guide to deploy the Upload Bridge License Server to Railway.

## 📋 Why Railway?

Railway is a modern platform that provides:
- ✅ Traditional Node.js server deployment (no serverless function issues)
- ✅ Automatic HTTPS and custom domains
- ✅ Environment variable management
- ✅ Simple deployment process
- ✅ Free tier available
- ✅ Better TypeScript support

## 🎯 Quick Start

### Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app) (free tier available)
2. **Node.js**: Version 18+ installed locally
3. **Git**: For deployment (optional, Railway CLI also available)

### Step 1: Install Railway CLI (Optional)

```bash
npm install -g @railway/cli
```

### Step 2: Login to Railway

```bash
railway login
```

### Step 3: Initialize Project

```bash
cd apps/license-server
railway init
```

When prompted:
- **Project name**: `upload-bridge-license-server` (or your choice)
- **Environment**: `production`

### Step 4: Set Environment Variables

```bash
railway variables set AUTH0_DOMAIN=dev-oczlciw58f2a4oei.us.auth0.com
railway variables set AUTH0_CLIENT_ID=your-client-id
railway variables set AUTH0_AUDIENCE=your-audience
```

Or use the Railway dashboard:
1. Go to your project → Variables
2. Add each environment variable

### Step 5: Deploy

```bash
railway up
```

Or deploy via Git:
1. Connect your GitHub repository to Railway
2. Railway will auto-deploy on push

### Step 6: Get Your URL

After deployment, Railway will provide a URL like:
```
https://your-project-name.up.railway.app
```

Or set a custom domain in Railway dashboard.

## 📚 Detailed Steps

### Option A: Deploy via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Navigate to project
cd apps/license-server

# Initialize (first time only)
railway init

# Set environment variables
railway variables set AUTH0_DOMAIN=dev-oczlciw58f2a4oei.us.auth0.com
railway variables set AUTH0_CLIENT_ID=your-client-id

# Deploy
railway up
```

### Option B: Deploy via GitHub

1. **Push code to GitHub** (if not already)
2. **Go to Railway Dashboard**: [railway.app](https://railway.app)
3. **New Project** → **Deploy from GitHub repo**
4. **Select repository** and **branch**
5. **Set Root Directory**: `apps/license-server`
6. **Add Environment Variables**:
   - `AUTH0_DOMAIN` = `dev-oczlciw58f2a4oei.us.auth0.com`
   - `AUTH0_CLIENT_ID` = (your client ID)
   - `AUTH0_AUDIENCE` = (your audience, optional)
7. **Deploy** - Railway will automatically build and deploy

## 🔧 Configuration

### Environment Variables

Required:
- `AUTH0_DOMAIN` - Your Auth0 domain (e.g., `dev-xxx.us.auth0.com`)
- `AUTH0_CLIENT_ID` - Your Auth0 client ID

Optional:
- `AUTH0_AUDIENCE` - Auth0 API audience
- `PORT` - Server port (default: 3000, Railway sets this automatically)

### Build Configuration

Railway will automatically:
1. Detect Node.js project
2. Run `npm install`
3. Run `npm run build` (compiles TypeScript)
4. Run `npm start` (starts the server)

## 🧪 Testing Deployment

### Health Check

```bash
curl https://your-project.up.railway.app/api/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "upload-bridge-license-server",
  "version": "1.0.0",
  "timestamp": "2025-01-27T12:00:00.000Z"
}
```

### Test Login Endpoint

```bash
curl -X POST https://your-project.up.railway.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "auth0_token": "your-auth0-token",
    "device_id": "DEVICE_123",
    "device_name": "Test Device"
  }'
```

## 🔄 Update Deployment

### Via CLI

```bash
cd apps/license-server
railway up
```

### Via Git

Just push to your connected branch:
```bash
git add .
git commit -m "Update license server"
git push
```

Railway will automatically redeploy.

## 📊 Monitor Deployment

1. **Railway Dashboard**: [railway.app/dashboard](https://railway.app/dashboard)
2. **View Logs**: Project → Deployments → View Logs
3. **Metrics**: View request metrics and performance

## 🐛 Troubleshooting

### Build Fails

**Error**: `Module not found`
- **Fix**: Ensure all dependencies are in `package.json` and run `npm install` locally first

**Error**: `TypeScript errors`
- **Fix**: Check `tsconfig.json` and fix type errors
- **Fix**: Ensure `lib/` directory is included in `tsconfig.json`

### Server Not Starting

**Error**: `Port already in use`
- **Fix**: Railway sets `PORT` automatically, don't hardcode it

**Error**: `Cannot find module`
- **Fix**: Ensure `npm run build` completes successfully
- **Fix**: Check that `dist/` directory contains compiled files

### Environment Variables Not Working

**Issue**: Environment variables not accessible
- **Fix**: Set variables in Railway dashboard → Variables
- **Fix**: Redeploy after adding variables
- **Fix**: Check variable names match exactly (case-sensitive)

## 🔒 Production Considerations

### Current Implementation

- ✅ Express server (traditional Node.js)
- ✅ TypeScript compilation
- ✅ Auth0 JWT validation
- ✅ In-memory database (for demo)

### Production Checklist

- [ ] Replace in-memory database with PostgreSQL/MongoDB
- [ ] Add rate limiting
- [ ] Add request logging
- [ ] Set up monitoring/alerting
- [ ] Configure custom domain
- [ ] Set up SSL (automatic with Railway)

## 📝 Update Upload Bridge Config

After deployment, update your Upload Bridge configuration:

```yaml
# apps/upload-bridge/config/auth_config.yaml
auth_server_url: https://your-project.up.railway.app
```

Or use environment variable:
```bash
export AUTH_SERVER_URL=https://your-project.up.railway.app
```

## 🎉 Success!

Your license server is now running on Railway! The server will:
- ✅ Handle all API requests
- ✅ Validate Auth0 tokens
- ✅ Manage user licenses
- ✅ Support CORS for frontend requests

## 🔗 Useful Links

- [Railway Documentation](https://docs.railway.app)
- [Railway Dashboard](https://railway.app/dashboard)
- [Railway CLI Reference](https://docs.railway.app/develop/cli)

---

**Status**: ✅ Ready for Railway deployment  
**Last Updated**: 2025-01-27

