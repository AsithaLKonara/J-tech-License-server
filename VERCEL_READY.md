# Vercel Deployment - Ready for Testing

## Status: ✅ Converted to Vercel Serverless Functions

The license server has been successfully converted from Express.js to Vercel serverless functions.

## Changes Made

### 1. Database: SQLite → Vercel KV
- **Before**: SQLite (`better-sqlite3`) - requires file system
- **After**: Vercel KV (Redis) - serverless-compatible
- **File**: `lib/database-kv.ts` (new implementation)

### 2. Server Structure: Express → Serverless Functions
- **Before**: Single `server.ts` Express app
- **After**: Individual serverless functions in `api/` directory
- **Functions Created**:
  - `api/health.ts` ✅ (already existed)
  - `api/v2/auth/register.ts` ✅ (new)
  - `api/v2/auth/login.ts` ✅ (updated)
  - `api/v2/auth/magic-link.ts` ✅ (new)
  - `api/v2/auth/verify-magic-link.ts` ✅ (new)
  - `api/v2/auth/refresh.ts` ✅ (updated)
  - `api/v2/subscriptions/create.ts` ✅ (new)
  - `api/v2/subscriptions/index.ts` ✅ (new)

### 3. Dependencies Updated
- **Removed**: `better-sqlite3`, `express`
- **Added**: `@vercel/node`, `@vercel/kv`
- **Kept**: `bcrypt`, `jsonwebtoken`, `nodemailer`

## Deployment Steps

### Step 1: Create Vercel KV Database

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Create a new project or select existing
3. Go to **Storage** tab
4. Click **Create Database**
5. Select **KV** (Redis)
6. Create database (free tier is fine)
7. Vercel will automatically provide credentials

### Step 2: Set Environment Variables

In Vercel Dashboard → Project → Settings → Environment Variables:

**Required:**
```
SMTP_HOST=smtp.yourhost.com
SMTP_PORT=587
SMTP_USER=your-email@domain.com
SMTP_PASS=your-password
SMTP_FROM=noreply@yourdomain.com
APP_URL=https://your-project.vercel.app
JWT_SECRET=your-secret-key-change-this
```

**Note**: Vercel KV credentials are automatically available - no need to set manually.

### Step 3: Deploy

```bash
cd apps/license-server
vercel --prod
```

Or connect GitHub repository for automatic deployments.

## Testing After Deployment

```bash
# Health check
curl https://your-project.vercel.app/api/health

# Register user
curl -X POST https://your-project.vercel.app/api/v2/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Login
curl -X POST https://your-project.vercel.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Request magic link
curl -X POST https://your-project.vercel.app/api/v2/auth/magic-link \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Create subscription (use session_token from login)
curl -X POST https://your-project.vercel.app/api/v2/subscriptions/create \
  -H "Content-Type: application/json" \
  -d '{"session_token":"YOUR_TOKEN","plan_type":"monthly"}'
```

## File Structure

```
apps/license-server/
├── api/                          (Serverless functions)
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
│   ├── database-kv.ts            (Vercel KV implementation)
│   ├── database.ts               (SQLite - for local dev)
│   ├── email.ts
│   ├── jwt-validator.ts
│   ├── models.ts
│   └── subscriptions.ts
├── package.json
└── vercel.json
```

## Important Notes

1. **Vercel KV Free Tier**:
   - 256 MB storage
   - 30,000 requests/day
   - Perfect for testing

2. **Cold Starts**:
   - First request may take 1-2 seconds
   - Subsequent requests are fast (< 100ms)

3. **Function Timeout**:
   - Free tier: 10 seconds max
   - Configured in `vercel.json`

4. **Environment Variables**:
   - Set in Vercel Dashboard
   - Available automatically in functions
   - KV credentials auto-injected

## Next Steps

1. ✅ Code converted to serverless functions
2. ⏳ Create Vercel KV database
3. ⏳ Set environment variables
4. ⏳ Deploy to Vercel
5. ⏳ Test all endpoints

---

**Status**: Ready for Vercel deployment  
**Build**: ✅ Successful  
**TypeScript**: ✅ No errors

