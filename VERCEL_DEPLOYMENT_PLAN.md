# Vercel Serverless Functions Deployment Plan

## Current Issue

The current implementation uses:
- Express.js server (`server.ts`)
- SQLite database (`better-sqlite3`)

**Problem**: Vercel serverless functions don't support:
- Persistent file system (SQLite won't work)
- Long-running Express servers

## Solution: Convert to Vercel Serverless Functions

### Option 1: Vercel KV (Recommended - Free Tier Available)
- Use Vercel KV (Redis) for database
- Free tier: 256 MB storage, 30K requests/day
- Perfect for testing and small production

### Option 2: Vercel Postgres (Alternative)
- Use Vercel Postgres for database
- Free tier: 256 MB storage
- More SQL-like, but requires schema migration

## Implementation Steps

### Step 1: Add Vercel KV Dependency
```json
"@vercel/kv": "^0.2.0"
```

### Step 2: Convert Express Routes to Serverless Functions

Create individual function files in `api/` directory:
- `api/health.ts` - Already exists
- `api/v2/auth/register.ts` - New
- `api/v2/auth/login.ts` - Update existing
- `api/v2/auth/magic-link.ts` - New
- `api/v2/auth/verify-magic-link.ts` - New
- `api/v2/auth/refresh.ts` - Update existing
- `api/v2/subscriptions/create.ts` - New
- `api/v2/subscriptions/index.ts` - New

### Step 3: Create KV Database Adapter

Replace `lib/database.ts` with KV-based implementation:
- Use KV for all data storage
- Same function signatures
- KV operations instead of SQLite

### Step 4: Update vercel.json

Configure KV and function settings.

## Quick Implementation

I'll convert the Express routes to Vercel serverless functions and use Vercel KV for the database.

