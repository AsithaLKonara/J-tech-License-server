# Vercel Deployment Guide

## Overview

The license server has been converted to Vercel serverless functions with Vercel KV (Redis) as the database.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI**: Install globally
   ```bash
   npm install -g vercel
   ```
3. **Vercel KV**: Free tier available (256 MB, 30K requests/day)

## Setup Steps

### Step 1: Install Dependencies

```bash
cd apps/license-server
npm install
```

### Step 2: Create Vercel KV Database

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Create a new project or select existing project
3. Go to **Storage** → **Create Database**
4. Select **KV** (Redis)
5. Create database (free tier is fine for testing)
6. Note the connection details

### Step 3: Set Environment Variables

In Vercel Dashboard → Project → Settings → Environment Variables:

```
# Vercel KV (automatically available, but you can set explicitly)
KV_REST_API_URL=your-kv-url
KV_REST_API_TOKEN=your-kv-token
KV_REST_API_READ_ONLY_TOKEN=your-readonly-token

# SMTP Email
SMTP_HOST=smtp.yourhost.com
SMTP_PORT=587
SMTP_USER=your-email@domain.com
SMTP_PASS=your-password
SMTP_FROM=noreply@yourdomain.com

# App
APP_URL=https://your-project.vercel.app
JWT_SECRET=your-secret-key-change-this

# Server
NODE_ENV=production
```

**Note**: Vercel KV credentials are automatically available in serverless functions via `@vercel/kv`, but you can set them explicitly if needed.

### Step 4: Deploy to Vercel

```bash
cd apps/license-server
vercel --prod
```

Or connect your GitHub repository to Vercel for automatic deployments.

## API Endpoints

All endpoints are available as serverless functions:

- `GET /api/health` - Health check
- `POST /api/v2/auth/register` - User registration
- `POST /api/v2/auth/login` - User login
- `POST /api/v2/auth/magic-link` - Request magic link
- `GET /api/v2/auth/verify-magic-link` - Verify magic link
- `POST /api/v2/auth/refresh` - Refresh token
- `POST /api/v2/subscriptions/create` - Create subscription
- `GET /api/v2/subscriptions` - Get subscription

## Testing

After deployment, test endpoints:

```bash
# Health check
curl https://your-project.vercel.app/api/health

# Register
curl -X POST https://your-project.vercel.app/api/v2/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Login
curl -X POST https://your-project.vercel.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

## File Structure

```
apps/license-server/
├── api/
│   ├── health.ts
│   └── v2/
│       ├── auth/
│       │   ├── register.ts
│       │   ├── login.ts
│       │   ├── magic-link.ts
│       │   ├── verify-magic-link.ts
│       │   └── refresh.ts
│       └── subscriptions/
│           ├── create.ts
│           └── index.ts
├── lib/
│   ├── database-kv.ts    (Vercel KV implementation)
│   ├── email.ts
│   ├── jwt-validator.ts
│   ├── models.ts
│   └── subscriptions.ts
├── package.json
└── vercel.json
```

## Differences from Express Server

1. **Database**: Uses Vercel KV (Redis) instead of SQLite
2. **Structure**: Individual serverless functions instead of Express routes
3. **File System**: No persistent file system (KV is used for storage)
4. **Cold Starts**: Functions may have cold start delays (usually < 1 second)

## Vercel KV Free Tier Limits

- **Storage**: 256 MB
- **Requests**: 30,000/day
- **Perfect for testing and small production**

## Troubleshooting

### Issue: "KV connection failed"
- Check that Vercel KV database is created
- Verify environment variables are set
- Check Vercel dashboard for KV status

### Issue: "Function timeout"
- Increase `maxDuration` in `vercel.json` (max 10s on free tier)
- Optimize database queries
- Check function logs in Vercel dashboard

### Issue: "Module not found"
- Ensure all dependencies are in `package.json`
- Run `npm install` before deploying
- Check build logs in Vercel dashboard

## Next Steps

1. Deploy to Vercel
2. Set up Vercel KV database
3. Configure environment variables
4. Test all endpoints
5. Update Upload Bridge config with Vercel URL

---

**Last Updated**: 2025-01-02

