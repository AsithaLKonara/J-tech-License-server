# Complete Setup Guide - Automated Configuration

This guide will help you set up everything automatically using the provided credentials.

## Your Credentials

- **Auth0 Domain**: `dev-oczlciw58f2a4oei.us.auth0.com`
- **Client ID**: `7kciWD98RzUsktuzXtJkfSmLcr80Ix2X`
- **Vercel URL**: `https://j-tech-licensing.vercel.app`

## Step 1: Install Dependencies

```bash
cd apps/license-server
npm install
```

## Step 2: Configure Vercel Environment Variables

### Option A: Automated Script (Recommended)

**Windows (PowerShell):**
```powershell
cd apps/license-server
.\setup-auth0.ps1
```

**Linux/Mac (Bash):**
```bash
cd apps/license-server
chmod +x setup-auth0.sh
./setup-auth0.sh
```

### Option B: Manual Vercel CLI

```bash
# Make sure you're logged in
vercel login

# Set for production
echo "dev-oczlciw58f2a4oei.us.auth0.com" | vercel env add AUTH0_DOMAIN production
echo "7kciWD98RzUsktuzXtJkfSmLcr80Ix2X" | vercel env add AUTH0_CLIENT_ID production

# Set for preview
echo "dev-oczlciw58f2a4oei.us.auth0.com" | vercel env add AUTH0_DOMAIN preview
echo "7kciWD98RzUsktuzXtJkfSmLcr80Ix2X" | vercel env add AUTH0_CLIENT_ID preview

# Set for development
echo "dev-oczlciw58f2a4oei.us.auth0.com" | vercel env add AUTH0_DOMAIN development
echo "7kciWD98RzUsktuzXtJkfSmLcr80Ix2X" | vercel env add AUTH0_CLIENT_ID development
```

## Step 3: Configure Auth0 Application

### Update Callback URLs

1. Go to [Auth0 Dashboard](https://manage.auth0.com)
2. Navigate to **Applications** → **J-Tech Licensing API (Test Application)**
3. Go to **Settings** tab
4. Scroll to **Application URIs**

**Allowed Callback URLs:**
```
https://j-tech-licensing.vercel.app/callback,http://localhost:3000/callback
```

**Allowed Logout URLs:**
```
https://j-tech-licensing.vercel.app,http://localhost:3000
```

**Allowed Web Origins:**
```
https://j-tech-licensing.vercel.app,http://localhost:3000
```

5. Click **Save Changes**

## Step 4: Deploy to Vercel

```bash
cd apps/license-server
vercel --prod
```

## Step 5: Verify Deployment

### Test Health Endpoint

```bash
curl https://j-tech-licensing.vercel.app/api/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "upload-bridge-license-server",
  "version": "1.0.0",
  "timestamp": "..."
}
```

### Verify Environment Variables

```bash
vercel env ls
```

You should see:
- `AUTH0_DOMAIN` = `dev-oczlciw58f2a4oei.us.auth0.com`
- `AUTH0_CLIENT_ID` = `7kciWD98RzUsktuzXtJkfSmLcr80Ix2X`

## Step 6: Test Auth0 Integration

### Get a Test Token

You can get a test token from Auth0 Dashboard:

1. Go to Auth0 Dashboard → **Applications** → **J-Tech Licensing API (Test Application)**
2. Go to **Test** tab
3. Copy the token

### Test Login Endpoint

```bash
curl -X POST https://j-tech-licensing.vercel.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "auth0_token": "YOUR_AUTH0_JWT_TOKEN_HERE",
    "device_id": "test-device-123",
    "device_name": "Test Device"
  }'
```

**Expected Success Response:**
```json
{
  "session_token": "session_...",
  "entitlement_token": {
    "sub": "auth0|...",
    "product": "upload_bridge_pro",
    "plan": "pro",
    "features": ["pattern_upload", "wifi_upload", "advanced_controls"],
    "expires_at": null
  },
  "user": {
    "id": "user_...",
    "email": "user@example.com"
  }
}
```

## Step 7: Update Upload Bridge Configuration

The Upload Bridge app configuration has been updated with your credentials:

**File**: `apps/upload-bridge/config/auth_config.yaml`

```yaml
auth0:
  domain: "dev-oczlciw58f2a4oei.us.auth0.com"
  client_id: "7kciWD98RzUsktuzXtJkfSmLcr80Ix2X"

auth_server_url: "https://j-tech-licensing.vercel.app"
```

## Troubleshooting

### Issue: "Auth0 is not configured"

**Solution:**
1. Verify environment variables: `vercel env ls`
2. Make sure you set them for the correct environment
3. Redeploy: `vercel --prod`

### Issue: "Invalid token"

**Possible causes:**
- Token expired (get a new one)
- Token from wrong Auth0 tenant
- Audience mismatch

**Solution:**
- Get a fresh token from Auth0
- Verify token is from `dev-oczlciw58f2a4oei.us.auth0.com`

### Issue: CORS Errors

**Solution:**
- Make sure callback URLs are configured in Auth0
- Check Allowed Web Origins includes your Vercel URL

## Verification Checklist

- [ ] Dependencies installed (`npm install`)
- [ ] Vercel environment variables set
- [ ] Auth0 callback URLs configured
- [ ] Deployed to Vercel (`vercel --prod`)
- [ ] Health endpoint works
- [ ] Login endpoint accepts Auth0 tokens
- [ ] Upload Bridge config updated

## Next Steps

1. **Test End-to-End**: Use Upload Bridge app to login
2. **Monitor Logs**: Check Vercel function logs for errors
3. **Set Up Database**: Replace in-memory database (see `lib/database.ts`)
4. **Configure Licenses**: Set up user licenses in database

## Support

- **Quick Setup**: See [QUICK_SETUP.md](./QUICK_SETUP.md)
- **Verification**: See [VERIFY_AUTH0_SETUP.md](./VERIFY_AUTH0_SETUP.md)
- **Full Guide**: See [AUTH0_SETUP.md](./AUTH0_SETUP.md)

