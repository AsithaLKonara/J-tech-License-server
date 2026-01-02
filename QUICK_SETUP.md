# Quick Setup Guide - Auth0 Configuration

Your Auth0 credentials are already configured! This guide helps you complete the setup.

## Your Configuration

- **Auth0 Domain**: `dev-oczlciw58f2a4oei.us.auth0.com`
- **Client ID**: `7kciWD98RzUsktuzXtJkfSmLcr80Ix2X`
- **Vercel URL**: `https://j-tech-licensing.vercel.app`

## Automated Setup (Recommended)

### Option 1: PowerShell (Windows)

```powershell
cd apps/license-server
.\setup-auth0.ps1
```

### Option 2: Bash (Linux/Mac)

```bash
cd apps/license-server
chmod +x setup-auth0.sh
./setup-auth0.sh
```

### Option 3: Manual Vercel CLI

If you prefer to set variables manually:

```bash
# Login to Vercel (if not already)
vercel login

# Set environment variables
echo "dev-oczlciw58f2a4oei.us.auth0.com" | vercel env add AUTH0_DOMAIN production
echo "7kciWD98RzUsktuzXtJkfSmLcr80Ix2X" | vercel env add AUTH0_CLIENT_ID production

# Repeat for preview and development environments
echo "dev-oczlciw58f2a4oei.us.auth0.com" | vercel env add AUTH0_DOMAIN preview
echo "7kciWD98RzUsktuzXtJkfSmLcr80Ix2X" | vercel env add AUTH0_CLIENT_ID preview
```

## Verify Setup

### 1. Check Environment Variables in Vercel

```bash
vercel env ls
```

You should see:
- `AUTH0_DOMAIN` = `dev-oczlciw58f2a4oei.us.auth0.com`
- `AUTH0_CLIENT_ID` = `7kciWD98RzUsktuzXtJkfSmLcr80Ix2X`

### 2. Test Health Endpoint

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

### 3. Test Auth0 Integration

Once deployed, test with a real Auth0 token:

```bash
curl -X POST https://j-tech-licensing.vercel.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "auth0_token": "YOUR_AUTH0_JWT_TOKEN",
    "device_id": "test-device",
    "device_name": "Test Device"
  }'
```

## Configure Auth0 Application

### 1. Update Allowed Callback URLs

In Auth0 Dashboard → Applications → J-Tech Licensing API (Test Application):

Add these callback URLs:
- `https://j-tech-licensing.vercel.app/callback`
- `http://localhost:3000/callback` (for local development)

### 2. Update Allowed Logout URLs

Add:
- `https://j-tech-licensing.vercel.app`
- `http://localhost:3000`

### 3. Update Allowed Web Origins

Add:
- `https://j-tech-licensing.vercel.app`
- `http://localhost:3000`

## Deploy

After setting environment variables:

```bash
cd apps/license-server
npm install
vercel --prod
```

## Update Upload Bridge Configuration

Update the Upload Bridge app to use your Vercel URL:

**File**: `apps/upload-bridge/config/auth_config.yaml`

```yaml
auth_server_url: https://j-tech-licensing.vercel.app
auth_domain: dev-oczlciw58f2a4oei.us.auth0.com
auth_client_id: 7kciWD98RzUsktuzXtJkfSmLcr80Ix2X
```

Or set environment variable:
```bash
export AUTH_SERVER_URL=https://j-tech-licensing.vercel.app
```

## Troubleshooting

### "Auth0 is not configured" Error

- Check environment variables: `vercel env ls`
- Make sure variables are set for the correct environment (production/preview/development)
- Redeploy after setting variables: `vercel --prod`

### "Invalid token" Error

- Verify token is from the correct Auth0 domain
- Check token hasn't expired
- Ensure email scope is requested in Auth0

### JWKS Endpoint Not Accessible

- Verify domain is correct: `dev-oczlciw58f2a4oei.us.auth0.com`
- Test JWKS URL: `https://dev-oczlciw58f2a4oei.us.auth0.com/.well-known/jwks.json`

## Next Steps

1. ✅ Run setup script to configure Vercel
2. ✅ Update Auth0 application settings (callback URLs)
3. ✅ Deploy to Vercel
4. ✅ Test health endpoint
5. ✅ Test login endpoint with Auth0 token
6. ✅ Update Upload Bridge configuration
7. ✅ Test end-to-end login flow

## Support

- See [VERIFY_AUTH0_SETUP.md](./VERIFY_AUTH0_SETUP.md) for detailed verification
- See [AUTH0_SETUP.md](./AUTH0_SETUP.md) for complete setup guide
- Check Vercel logs: `vercel logs`

