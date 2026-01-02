# Auth0 and License Server E2E Testing Guide

This guide explains how to test the complete Auth0 authentication and license-server integration.

## Overview

The test suite verifies:
1. ✅ License server health endpoint
2. ✅ CORS configuration
3. ✅ Auth0 configuration (JWKS endpoint)
4. ✅ Login endpoint structure and validation
5. ✅ Token validation flow
6. ✅ End-to-end authentication with real tokens (optional)

## Prerequisites

1. **Node.js 18+** installed
2. **License server deployed** to Vercel (or running locally)
3. **Auth0 configured** (optional, some tests will be skipped if not configured)

## Quick Start

### Option 1: Run with PowerShell Script (Windows)

```powershell
cd apps/license-server
.\test-auth0-e2e.ps1
```

### Option 2: Run with npm script

```bash
cd apps/license-server
npm run test:auth0
```

### Option 3: Run directly with ts-node

```bash
cd apps/license-server
npx ts-node test-auth0-e2e.ts
```

## Environment Variables

Set these environment variables before running tests:

### Required (for full test coverage)

```powershell
# Windows PowerShell
$env:LICENSE_SERVER_URL = "https://j-tech-licensing.vercel.app"
$env:AUTH0_DOMAIN = "your-tenant.auth0.com"
$env:AUTH0_AUDIENCE = "https://your-api-audience"  # Optional
```

### Optional (for real token testing)

```powershell
$env:TEST_AUTH0_TOKEN = "your-auth0-jwt-token-here"
```

### Linux/Mac

```bash
export LICENSE_SERVER_URL="https://j-tech-licensing.vercel.app"
export AUTH0_DOMAIN="your-tenant.auth0.com"
export AUTH0_AUDIENCE="https://your-api-audience"  # Optional
export TEST_AUTH0_TOKEN="your-auth0-jwt-token-here"  # Optional
```

## Test Coverage

### 1. Health Endpoint Test

- ✅ Tests `/api/health` endpoint
- ✅ Verifies server is responding
- ✅ Checks response structure

### 2. CORS Headers Test

- ✅ Tests OPTIONS request
- ✅ Verifies CORS headers are present
- ✅ Ensures cross-origin requests will work

### 3. Auth0 Configuration Test

- ✅ Checks `AUTH0_DOMAIN` is set
- ✅ Tests JWKS endpoint accessibility
- ✅ Verifies Auth0 integration is ready

### 4. Login Endpoint Structure Test

- ✅ Tests endpoint with missing token
- ✅ Verifies proper error handling (400 status)
- ✅ Checks response structure

### 5. Login Endpoint Invalid Token Test

- ✅ Tests endpoint with invalid token
- ✅ Verifies proper rejection (401 status)
- ✅ Ensures security is working

### 6. Login Endpoint CORS Test

- ✅ Tests OPTIONS request on login endpoint
- ✅ Verifies CORS headers for authentication

### 7. Token Validation Function Test

- ✅ Tests JWT validation logic
- ✅ Verifies invalid tokens are rejected
- ✅ Ensures token validation is working

### 8. Login Endpoint Real Token Test (Optional)

- ✅ Tests with real Auth0 JWT token
- ✅ Verifies complete authentication flow
- ✅ Checks session and entitlement tokens are returned
- ⚠️ Requires `TEST_AUTH0_TOKEN` environment variable

## Expected Output

### Successful Test Run

```
🧪 Running Auth0 and License Server E2E Tests

License Server URL: https://j-tech-licensing.vercel.app
Auth0 Domain: your-tenant.auth0.com

────────────────────────────────────────────────────────────

✅ Health Endpoint: Server is healthy and responding
✅ CORS Headers: CORS headers are present
✅ Auth0 Configuration: AUTH0_DOMAIN is configured
✅ Auth0 JWKS Endpoint: JWKS endpoint is accessible (2 keys found)
✅ Login Endpoint Structure: Endpoint correctly validates missing token
✅ Login Endpoint Invalid Token: Endpoint correctly rejects invalid token
✅ Login Endpoint CORS: CORS headers are present
✅ Token Validation Function: Correctly rejects invalid tokens
⏭️  Login Endpoint Real Token: TEST_AUTH0_TOKEN not provided (skipping)

────────────────────────────────────────────────────────────
📊 Test Summary

✅ Passed: 7
⏭️  Skipped: 1
📝 Total: 8

🎉 All tests passed!
```

## Getting an Auth0 Token for Testing

To test with a real Auth0 token, you need to obtain a JWT token from Auth0:

### Method 1: Using Auth0 Dashboard

1. Go to Auth0 Dashboard → Applications → Your App
2. Go to the **Test** tab
3. Copy the token from the test interface

### Method 2: Using Auth0 API

```bash
curl -X POST "https://YOUR_AUTH0_DOMAIN/oauth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "audience": "YOUR_API_AUDIENCE",
    "grant_type": "client_credentials"
  }'
```

### Method 3: Using OAuth Flow

1. Configure OAuth in your Auth0 application
2. Complete the authorization flow
3. Extract the `id_token` from the callback

## Troubleshooting

### "Health Endpoint: Request failed"

**Solution**: 
- Verify the license server is deployed and accessible
- Check the `LICENSE_SERVER_URL` environment variable
- Test the URL manually: `curl https://j-tech-licensing.vercel.app/api/health`

### "Auth0 JWKS Endpoint: Failed to access"

**Solution**:
- Verify `AUTH0_DOMAIN` is correct
- Check that `https://{AUTH0_DOMAIN}/.well-known/jwks.json` is accessible
- Ensure Auth0 tenant is active

### "Login Endpoint Invalid Token: Unexpected response"

**Solution**:
- Verify the login endpoint is deployed correctly
- Check Vercel function logs for errors
- Ensure Auth0 environment variables are set in Vercel

### "Token Validation Function: Cannot test without AUTH0_DOMAIN"

**Solution**:
- Set `AUTH0_DOMAIN` environment variable
- This test will be skipped if not configured (this is expected)

## Integration with Upload Bridge

After verifying the license server tests pass:

1. **Configure Upload Bridge**:
   ```yaml
   # apps/upload-bridge/config/auth_config.yaml
   auth_server_url: https://j-tech-licensing.vercel.app
   ```

2. **Test OAuth Flow**:
   - Launch Upload Bridge application
   - Click "Social Login" or "OAuth Login"
   - Complete the Auth0 authentication flow
   - Verify session is established

3. **Verify License**:
   - Check that entitlement token is received
   - Verify license features are accessible

## Next Steps

1. ✅ Run the test suite to verify everything is working
2. ✅ Configure Auth0 callback URLs in Auth0 Dashboard (if not done)
3. ✅ Test the full OAuth flow in Upload Bridge application
4. ✅ Monitor Vercel logs for any errors
5. ✅ Set up production database (replace in-memory storage)

## Related Documentation

- [AUTH0_SETUP.md](./AUTH0_SETUP.md) - Auth0 configuration guide
- [VERIFY_AUTH0_SETUP.md](./VERIFY_AUTH0_SETUP.md) - Verification steps
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Deployment instructions

