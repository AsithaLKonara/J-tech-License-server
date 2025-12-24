# 🚀 Vercel Deployment Guide

Complete guide to deploy the Upload Bridge License Server to Vercel.

## 📋 Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com) (free tier works)
2. **Node.js**: Version 18+ installed locally
3. **Vercel CLI**: Install globally
   ```bash
   npm install -g vercel
   ```

## 🔧 Step-by-Step Deployment

### Step 1: Install Dependencies

```bash
cd license-server
npm install
```

### Step 2: Login to Vercel

```bash
vercel login
```

Follow the prompts to authenticate.

### Step 3: Deploy to Vercel

```bash
vercel --prod
```

When prompted:
- **Set up and deploy?** → Yes
- **Which scope?** → Your account
- **Link to existing project?** → No (first time)
- **Project name?** → `upload-bridge-license-server` (or your choice)
- **Directory?** → `./` (current directory)
- **Override settings?** → No

### Step 4: Get Your Deployment URL

After deployment, Vercel will output:
```
✅ Production: https://your-project-name.vercel.app [copied to clipboard]
```

**Save this URL!** You'll need it to configure the Upload Bridge application.

### Step 5: Test the Deployment

Test the health endpoint:
```bash
curl https://your-project-name.vercel.app/api/health
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

Test login endpoint:
```bash
curl -X POST https://your-project-name.vercel.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "device_id": "DEVICE_123",
    "device_name": "Test Device"
  }'
```

Expected response:
```json
{
  "session_token": "session_...",
  "entitlement_token": {
    "sub": "user_test_example_com",
    "product": "upload_bridge_pro",
    "plan": "pro",
    "features": ["pattern_upload", "wifi_upload", "advanced_controls"],
    "expires_at": null
  },
  "user": {
    "id": "user_test_example_com",
    "email": "test@example.com"
  }
}
```

## ⚙️ Configure Upload Bridge Application

### Option 1: Update Config File

Edit `apps/upload-bridge/config/auth_config.yaml`:

```yaml
auth_server_url: https://your-project-name.vercel.app
```

### Option 2: Set Environment Variable

**Windows (PowerShell)**:
```powershell
$env:AUTH_SERVER_URL = "https://your-project-name.vercel.app"
```

**Windows (Permanent)**:
```powershell
[System.Environment]::SetEnvironmentVariable('AUTH_SERVER_URL', 'https://your-project-name.vercel.app', 'User')
```

**Linux/Mac**:
```bash
export AUTH_SERVER_URL="https://your-project-name.vercel.app"
```

### Option 3: Use Script

Run the provided script:
```bash
python apps/upload-bridge/scripts/setup_test_env.ps1
# Then update the URL in the script
```

## 🔄 Update Existing Deployment

To update the server after making changes:

```bash
cd license-server
vercel --prod
```

## 📊 Monitor Deployment

1. **Vercel Dashboard**: Visit [vercel.com/dashboard](https://vercel.com/dashboard)
2. **View Logs**: Click on your project → Functions → View logs
3. **Check Analytics**: View request metrics and performance

## 🧪 Test Accounts

Default test accounts configured:

| Email | Password | Plan | Features |
|-------|----------|------|----------|
| `test@example.com` | `testpassword123` | pro | pattern_upload, wifi_upload, advanced_controls |
| `demo@example.com` | `demo123` | basic | pattern_upload |

## 🔒 Production Considerations

### Current Implementation (Demo)

- ✅ Basic authentication
- ✅ In-memory user database
- ✅ Simple session tokens
- ✅ Test accounts included

### Production Checklist

- [ ] Replace in-memory database with PostgreSQL/MongoDB
- [ ] Implement password hashing (bcrypt/argon2)
- [ ] Use JWT tokens with proper signing
- [ ] Add rate limiting
- [ ] Add CORS configuration
- [ ] Implement proper error handling
- [ ] Add logging and monitoring
- [ ] Set up environment variables in Vercel
- [ ] Configure custom domain (optional)
- [ ] Set up SSL/TLS (automatic with Vercel)

## 🐛 Troubleshooting

### Deployment Fails

**Error**: `Module not found`
- **Solution**: Run `npm install` before deploying

**Error**: `TypeScript errors`
- **Solution**: Check `tsconfig.json` and fix type errors

### API Returns 404

**Cause**: Incorrect route configuration
- **Solution**: Check `vercel.json` routes match your API structure

### CORS Errors

**Cause**: Browser blocking cross-origin requests
- **Solution**: Add CORS headers in API functions (see example below)

### Connection Timeout

**Cause**: Cold start delay (first request)
- **Solution**: Normal for serverless. Subsequent requests are faster.

## 📝 Example: Adding CORS

Update your API functions to include CORS headers:

```typescript
export default async function handler(
  req: VercelRequest,
  res: VercelResponse
): Promise<VercelResponse> {
  // Add CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // ... rest of your handler
}
```

## 📚 Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Serverless Functions](https://vercel.com/docs/functions)
- [TypeScript on Vercel](https://vercel.com/docs/functions/serverless-functions/runtimes/node-js#typescript)

## ✅ Deployment Checklist

- [ ] Vercel account created
- [ ] Vercel CLI installed
- [ ] Dependencies installed (`npm install`)
- [ ] Deployed to Vercel (`vercel --prod`)
- [ ] Got deployment URL
- [ ] Tested health endpoint
- [ ] Tested login endpoint
- [ ] Updated Upload Bridge config
- [ ] Tested login from Upload Bridge app

---

**Need Help?** Check the [README.md](./README.md) for more details.

