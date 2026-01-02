# 🚂 Migration from Vercel to Railway

## Why Migrate?

Vercel serverless functions have known issues with:
- ❌ TypeScript module resolution (`Cannot find module '../../lib/jwt-validator'`)
- ❌ Complex file structure requirements
- ❌ Runtime compatibility issues with Node.js versions
- ❌ FUNCTION_INVOCATION_FAILED errors

Railway provides:
- ✅ Traditional Express server (no serverless limitations)
- ✅ Better TypeScript support
- ✅ Simpler deployment process
- ✅ More reliable runtime environment

## What Changed

### 1. Server Architecture

**Before (Vercel)**:
- Serverless functions in `api/` directory
- Each endpoint is a separate file
- Vercel-specific request/response types

**After (Railway)**:
- Single Express server (`server.ts`)
- All routes in one file
- Standard Express Request/Response types

### 2. Dependencies

**Removed**:
- `@vercel/node` - Vercel-specific runtime

**Added**:
- `express` - Web framework
- `@types/express` - TypeScript types

### 3. Build Process

**Before**:
- Vercel auto-detects and builds serverless functions
- No explicit build step

**After**:
- `npm run build` - Compiles TypeScript to JavaScript
- `npm start` - Runs the compiled server

### 4. Configuration Files

**New Files**:
- `server.ts` - Express server
- `railway.json` - Railway configuration
- `Procfile` - Process file for Railway
- `RAILWAY_DEPLOYMENT.md` - Deployment guide

**Updated Files**:
- `package.json` - Express dependencies, new scripts
- `tsconfig.json` - Includes `server.ts`

## Migration Steps

### 1. Install Dependencies

```bash
cd apps/license-server
npm install
```

### 2. Test Locally

```bash
npm run build
npm start
```

Server should start on `http://localhost:3000`

### 3. Deploy to Railway

See `RAILWAY_DEPLOYMENT.md` for complete instructions.

Quick start:
```bash
railway login
railway init
railway variables set AUTH0_DOMAIN=dev-oczlciw58f2a4oei.us.auth0.com
railway up
```

## API Endpoints (Unchanged)

All endpoints remain the same:

- `GET /api/health` - Health check
- `POST /api/v2/auth/login` - Login with Auth0 token
- `POST /api/v2/auth/refresh` - Refresh session token

## Environment Variables

Same environment variables needed:
- `AUTH0_DOMAIN` - Required
- `AUTH0_CLIENT_ID` - Required
- `AUTH0_AUDIENCE` - Optional
- `PORT` - Auto-set by Railway

## Testing

Run the same tests:
```bash
npm run test:auth0
```

Update `LICENSE_SERVER_URL` to your Railway URL:
```bash
$env:LICENSE_SERVER_URL = "https://your-project.up.railway.app"
npm run test:auth0
```

## Rollback Plan

If you need to rollback to Vercel:
1. The original Vercel files are still in `api/` directory
2. Revert `package.json` changes
3. Redeploy to Vercel

## Status

✅ **Migration Complete**
- Express server created
- Railway configuration added
- Dependencies updated
- Documentation created

**Next Step**: Deploy to Railway using `RAILWAY_DEPLOYMENT.md`

---

**Date**: 2025-01-27  
**Status**: Ready for Railway deployment

