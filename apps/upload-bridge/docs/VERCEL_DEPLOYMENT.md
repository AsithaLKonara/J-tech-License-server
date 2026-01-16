# 🚀 Vercel License Server Deployment

Complete guide to deploy and configure the license server on Vercel.

## 📋 Overview

The Upload Bridge application requires a license server for account-based authentication. This guide shows you how to deploy it to Vercel (free tier available).

## 🎯 Quick Start

### 1. Deploy to Vercel

```bash
cd license-server
npm install
vercel login
vercel --prod
```

### 2. Get Your URL

After deployment, Vercel will show:
```
✅ Production: https://your-project-name.vercel.app
```

### 3. Update Application Config

```bash
python scripts/update_vercel_url.py https://your-project-name.vercel.app
```

Or manually edit `config/auth_config.yaml`:
```yaml
auth_server_url: https://your-project-name.vercel.app
```

## 📚 Detailed Steps

### Prerequisites

1. **Vercel Account**: [Sign up](https://vercel.com) (free)
2. **Node.js**: Version 18+ installed
3. **Vercel CLI**: `npm install -g vercel`

### Step 1: Navigate to License Server

```bash
cd license-server
```

### Step 2: Install Dependencies

```bash
npm install
```

### Step 3: Login to Vercel

```bash
vercel login
```

Follow the browser prompts to authenticate.

### Step 4: Deploy

```bash
vercel --prod
```

**Prompts:**
- Set up and deploy? → **Y**
- Link to existing project? → **N** (first time)
- Project name? → **upload-bridge-license** (or your choice)
- Directory? → **.** (current directory)

### Step 5: Test Deployment

```bash
# Health check
curl https://your-project-name.vercel.app/api/health

# Test login
curl -X POST https://your-project-name.vercel.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "device_id": "DEVICE_123",
    "device_name": "Test Device"
  }'
```

### Step 6: Configure Upload Bridge

**Option A: Use Script**
```bash
python scripts/update_vercel_url.py https://your-project-name.vercel.app
```

**Option B: Manual Edit**
Edit `config/auth_config.yaml`:
```yaml
auth_server_url: https://your-project-name.vercel.app
```

**Option C: Environment Variable**
```powershell
# Windows PowerShell
$env:AUTH_SERVER_URL = "https://your-project-name.vercel.app"

# Permanent
[System.Environment]::SetEnvironmentVariable('AUTH_SERVER_URL', 'https://your-project-name.vercel.app', 'User')
```

## 🧪 Test Accounts

Default test accounts (configured in server):

| Email | Password | Plan | Features |
|-------|----------|------|----------|
| `test@example.com` | `testpassword123` | pro | pattern_upload, wifi_upload, advanced_controls |
| `demo@example.com` | `demo123` | basic | pattern_upload |

## 🔄 Update Deployment

To update after making changes:

```bash
cd license-server
vercel --prod
```

## 📊 Monitor Deployment

1. **Vercel Dashboard**: [vercel.com/dashboard](https://vercel.com/dashboard)
2. **View Logs**: Project → Functions → Logs
3. **Analytics**: View request metrics

## 🐛 Troubleshooting

### Deployment Fails

**Error**: `Module not found`
- **Fix**: Run `npm install` before deploying

**Error**: `TypeScript errors`
- **Fix**: Check `tsconfig.json` and fix type errors

### API Returns 404

**Cause**: Incorrect route
- **Fix**: Check `vercel.json` configuration

### Connection Timeout

**Cause**: Cold start (first request)
- **Fix**: Normal for serverless. Subsequent requests are faster.

### CORS Errors

**Cause**: Browser blocking requests
- **Fix**: CORS headers are already included in the API functions

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
- [ ] Add proper error handling
- [ ] Add logging and monitoring
- [ ] Set up environment variables in Vercel
- [ ] Configure custom domain (optional)

## 📝 API Endpoints

### POST `/api/v2/auth/login`

Authenticate user and return tokens.

**Request**:
```json
{
  "email": "test@example.com",
  "password": "testpassword123",
  "device_id": "DEVICE_XXXX",
  "device_name": "Windows Device"
}
```

**Response**:
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

### POST `/api/v2/auth/refresh`

Refresh session token.

### GET `/api/health`

Health check endpoint.

## ✅ Verification Checklist

- [ ] Vercel account created
- [ ] Vercel CLI installed
- [ ] Dependencies installed
- [ ] Deployed to Vercel
- [ ] Got deployment URL
- [ ] Tested health endpoint
- [ ] Tested login endpoint
- [ ] Updated Upload Bridge config
- [ ] Tested login from Upload Bridge app

## 📚 Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Serverless Functions](https://vercel.com/docs/functions)
- [License Server README](../license-server/README.md)

---

**Need Help?** Check the [QUICK_DEPLOY.md](../license-server/QUICK_DEPLOY.md) for a faster setup.

