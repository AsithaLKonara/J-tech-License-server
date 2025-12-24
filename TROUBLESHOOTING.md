# 🔧 Vercel Deployment Troubleshooting

## Issue: 404 Errors

If you're getting 404 errors, follow these steps:

### Step 1: Verify File Structure

Make sure your files are in this structure:
```
license-server/
├── api/
│   ├── health.ts
│   └── v2/
│       └── auth/
│           ├── login.ts
│           └── refresh.ts
├── package.json
└── vercel.json
```

### Step 2: Check Vercel Dashboard

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click on your project: `j-tech-licensing`
3. Go to **Settings** → **Functions**
4. Check if the functions are listed:
   - `api/health.ts`
   - `api/v2/auth/login.ts`
   - `api/v2/auth/refresh.ts`

### Step 3: Check Deployment Logs

1. In Vercel dashboard, go to **Deployments**
2. Click on the latest deployment
3. Check **Build Logs** for errors
4. Check **Function Logs** for runtime errors

### Step 4: Verify package.json

Make sure `package.json` includes:
```json
{
  "dependencies": {
    "@vercel/node": "^3.0.0"
  }
}
```

### Step 5: Redeploy

If files are correct but still 404:

```bash
cd license-server
vercel --prod --force
```

### Step 6: Test with curl

```bash
# Health endpoint
curl https://j-tech-licensing.vercel.app/api/health

# Login endpoint
curl -X POST https://j-tech-licensing.vercel.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpassword123","device_id":"DEVICE_123","device_name":"Test"}'
```

## Common Issues

### Issue: "Module not found"

**Solution**: Make sure `package.json` has all dependencies and run `npm install` before deploying.

### Issue: "TypeScript errors"

**Solution**: Check that TypeScript files have proper exports and types.

### Issue: "Function timeout"

**Solution**: Increase timeout in `vercel.json`:
```json
{
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 10
    }
  }
}
```

### Issue: Files not detected

**Solution**: 
1. Make sure files are in `api/` folder (not `src/api/` or elsewhere)
2. Check `.vercelignore` doesn't exclude `api/` folder
3. Redeploy with `vercel --prod --force`

## Quick Fix: Minimal vercel.json

If nothing works, try this minimal config:

```json
{
  "version": 2
}
```

Vercel should auto-detect the `api/` folder and create routes automatically.

## Still Not Working?

1. Check Vercel documentation: https://vercel.com/docs/functions
2. Check deployment logs in Vercel dashboard
3. Try deploying a simple test function first:
   ```typescript
   // api/test.ts
   export default function handler(req, res) {
     res.json({ message: 'Hello from Vercel!' });
   }
   ```

