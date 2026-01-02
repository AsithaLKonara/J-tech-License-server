# Verify Auth0 Setup

This guide helps you verify that your Auth0 credentials are correctly configured and working.

## Environment Variables Check

The following environment variables should be set in your Vercel project:

### Required
- `AUTH0_DOMAIN` - Your Auth0 tenant domain (e.g., `your-tenant.auth0.com`)

### Optional (but recommended)
- `AUTH0_AUDIENCE` - Your API identifier (if using Auth0 API)
- `AUTH0_JWKS_URI` - JWKS endpoint (auto-derived if not set)

## How to Verify in Vercel

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard
2. **Select your project**: `upload-bridge-license-server` (or your project name)
3. **Go to Settings** → **Environment Variables**
4. **Verify these variables exist**:
   - `AUTH0_DOMAIN` ✅
   - `AUTH0_AUDIENCE` (if using API) ✅
   - `AUTH0_JWKS_URI` (optional) ✅

## Test Auth0 Configuration

### Option 1: Test via Login Endpoint

You can test if Auth0 is working by calling the login endpoint with a valid Auth0 JWT token:

```bash
curl -X POST https://your-domain.vercel.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "auth0_token": "YOUR_AUTH0_JWT_TOKEN_HERE",
    "device_id": "test-device-123",
    "device_name": "Test Device"
  }'
```

**Expected Success Response** (200 OK):
```json
{
  "session_token": "session_...",
  "entitlement_token": {
    "sub": "auth0|user-id",
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

**Expected Error if Auth0 Not Configured** (500):
```json
{
  "error": "Internal server error"
}
```

Check server logs for: `"Auth0 is not configured. Set AUTH0_DOMAIN environment variable."`

**Expected Error if Token Invalid** (401):
```json
{
  "error": "Invalid token: [error message]"
}
```

### Option 2: Check Server Logs

1. Go to Vercel Dashboard → Your Project → **Functions**
2. Click on a function (e.g., `/api/v2/auth/login`)
3. View **Logs** tab
4. Look for any Auth0-related errors

### Option 3: Test Health Endpoint

The health endpoint doesn't require Auth0, but you can verify the server is running:

```bash
curl https://your-domain.vercel.app/api/health
```

**Expected Response**:
```json
{
  "status": "ok",
  "service": "upload-bridge-license-server",
  "version": "1.0.0",
  "timestamp": "2025-01-27T..."
}
```

## Common Issues

### Issue: "Auth0 is not configured"

**Symptoms**: Error message in logs or 500 error

**Solution**:
1. Verify `AUTH0_DOMAIN` is set in Vercel environment variables
2. Make sure you're using the correct environment (Production, Preview, or Development)
3. Redeploy after adding environment variables

### Issue: "Invalid token: Token expired"

**Symptoms**: 401 error with "Token expired" message

**Solution**:
- Get a fresh Auth0 token
- Tokens typically expire after 24 hours
- Request a new token from Auth0

### Issue: "Invalid token: audience mismatch"

**Symptoms**: 401 error with audience-related message

**Solution**:
1. Verify `AUTH0_AUDIENCE` matches the audience in your Auth0 token
2. If not using an API, remove `AUTH0_AUDIENCE` or set it to match token audience
3. Check Auth0 application settings

### Issue: "Token missing email"

**Symptoms**: 400 error with "Token missing email"

**Solution**:
1. Make sure your Auth0 application requests the `email` scope
2. Verify the user has a verified email address
3. Check Auth0 Rules/Actions if email is added via custom claims

## Next Steps After Verification

Once Auth0 is verified and working:

1. **Test User Login**: Use the Upload Bridge application to login
2. **Check License Assignment**: Verify users get proper licenses from database
3. **Monitor Logs**: Watch for any authentication errors
4. **Set Up Database**: Replace in-memory database with real database (see `lib/database.ts`)

## Getting an Auth0 Token for Testing

To get a test token:

1. **Using Auth0 Dashboard**:
   - Go to Auth0 Dashboard → Applications → Your App
   - Use the "Test" tab to get a token

2. **Using Auth0 CLI**:
   ```bash
   auth0 login
   auth0 test token
   ```

3. **Using Postman/Insomnia**:
   - Create a request to `https://{AUTH0_DOMAIN}/oauth/token`
   - Use Client Credentials or Authorization Code flow

## Production Checklist

- [ ] `AUTH0_DOMAIN` is set in Vercel
- [ ] `AUTH0_AUDIENCE` is set (if using API)
- [ ] Test login endpoint with real token
- [ ] Verify user creation in database
- [ ] Test license assignment
- [ ] Monitor error logs
- [ ] Set up real database (replace in-memory)

