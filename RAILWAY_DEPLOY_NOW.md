# 🚂 Railway Deployment - Quick Steps

## Current Status

✅ Railway CLI installed and logged in  
✅ Code pushed to GitHub: https://github.com/AsithaLKonara/J-tech-License-server.git  
⚠️ Project needs to be created (workspace upgrade may be required)

## Option 1: Deploy via Railway Dashboard (Recommended)

### Step 1: Create Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose repository: `AsithaLKonara/J-tech-License-server`
5. Set **Root Directory**: `apps/license-server` (if deploying from monorepo) OR deploy the repo directly
6. Railway will automatically detect Node.js and start building

### Step 2: Set Environment Variables

In Railway Dashboard:
1. Go to your project → **Variables** tab
2. Add these variables:
   - `AUTH0_DOMAIN` = `dev-oczlciw58f2a4oei.us.auth0.com`
   - `AUTH0_CLIENT_ID` = (your Auth0 client ID)
   - `AUTH0_AUDIENCE` = (optional, your Auth0 audience)

### Step 3: Deploy

Railway will automatically deploy after:
- Project is created
- Environment variables are set
- Code is pushed to GitHub

### Step 4: Get Your URL

1. Go to project → **Settings** → **Domains**
2. Railway provides: `https://your-project.up.railway.app`
3. Or add a custom domain

## Option 2: Deploy via CLI (After Project Created)

If you create the project via dashboard, you can then use CLI:

```bash
cd apps/license-server

# Link to existing project
railway link

# Set environment variables
railway variables --set "AUTH0_DOMAIN=dev-oczlciw58f2a4oei.us.auth0.com"
railway variables --set "AUTH0_CLIENT_ID=your-client-id"

# Deploy
railway up
```

## Option 3: Direct CLI (If Workspace Upgraded)

```bash
cd apps/license-server

# Create project (requires workspace upgrade)
railway init

# Set variables
railway variables --set "AUTH0_DOMAIN=dev-oczlciw58f2a4oei.us.auth0.com"
railway variables --set "AUTH0_CLIENT_ID=your-client-id"

# Deploy
railway up
```

## Testing After Deployment

```bash
# Health check
curl https://your-project.up.railway.app/api/health

# Should return:
# {
#   "status": "ok",
#   "service": "upload-bridge-license-server",
#   "version": "1.0.0",
#   "timestamp": "..."
# }
```

## Troubleshooting

### Build Fails
- Check Railway logs in dashboard
- Ensure `package.json` has correct scripts
- Verify Node.js version (18+)

### Environment Variables Not Working
- Set in Railway dashboard → Variables
- Redeploy after adding variables
- Check variable names (case-sensitive)

### Port Issues
- Railway sets `PORT` automatically
- Don't hardcode port in code

---

**Recommended**: Use Option 1 (Dashboard) for easiest deployment!

