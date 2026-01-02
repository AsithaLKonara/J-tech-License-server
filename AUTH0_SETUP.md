# Auth0 Setup Guide

This guide explains how to configure Auth0 for the Upload Bridge license server.

> **Note**: If you've already provided Auth0 credentials to the project, see [VERIFY_AUTH0_SETUP.md](./VERIFY_AUTH0_SETUP.md) to verify everything is working correctly.

## Prerequisites

- Auth0 account (sign up at https://auth0.com)
- Node.js 18+ installed
- Access to Vercel environment variables (for deployment)

## Step 1: Create Auth0 Application

1. Log in to your Auth0 Dashboard
2. Go to **Applications** → **Applications**
3. Click **Create Application**
4. Choose **Regular Web Application**
5. Name it "Upload Bridge License Server"
6. Click **Create**

## Step 2: Configure Application Settings

In your Auth0 application settings:

1. **Allowed Callback URLs**: Add your callback URLs
   - For local development: `http://localhost:3000/callback`
   - For production: `https://your-domain.vercel.app/callback`

2. **Allowed Logout URLs**: Add your logout URLs
   - For local development: `http://localhost:3000`
   - For production: `https://your-domain.vercel.app`

3. **Allowed Web Origins**: Add your application origins
   - For local development: `http://localhost:3000`
   - For production: `https://your-domain.vercel.app`

4. **Application Type**: Keep as "Regular Web Application"

5. Save changes

## Step 3: Create API (Optional but Recommended)

1. Go to **Applications** → **APIs**
2. Click **Create API**
3. Name: "Upload Bridge API"
4. Identifier: `https://upload-bridge-api` (or your custom identifier)
5. Signing Algorithm: **RS256**
6. Click **Create**

## Step 4: Configure Environment Variables

### For Local Development

Create a `.env.local` file in `apps/license-server/`:

```env
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://upload-bridge-api
AUTH0_JWKS_URI=https://your-tenant.auth0.com/.well-known/jwks.json
```

### For Vercel Deployment

1. Go to your Vercel project dashboard
2. Navigate to **Settings** → **Environment Variables**
3. Add the following variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `AUTH0_DOMAIN` | Your Auth0 tenant domain | `your-tenant.auth0.com` |
| `AUTH0_AUDIENCE` | API identifier (if using API) | `https://upload-bridge-api` |
| `AUTH0_JWKS_URI` | JWKS endpoint (optional, auto-derived) | `https://your-tenant.auth0.com/.well-known/jwks.json` |

## Step 5: Install Dependencies

```bash
cd apps/license-server
npm install
```

This will install:
- `jsonwebtoken` - JWT token verification
- `jwks-rsa` - JWKS client for Auth0 public keys
- `@types/jsonwebtoken` - TypeScript types

## Step 6: Test Configuration

### Test Token Validation

You can test the login endpoint with a valid Auth0 token:

```bash
curl -X POST https://your-domain.vercel.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "auth0_token": "YOUR_AUTH0_JWT_TOKEN",
    "device_id": "test-device-123",
    "device_name": "Test Device"
  }'
```

### Expected Response

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

## Troubleshooting

### Error: "Auth0 is not configured"

**Solution**: Make sure `AUTH0_DOMAIN` environment variable is set.

### Error: "Invalid token"

**Possible causes**:
- Token is expired
- Token signature is invalid
- Token audience doesn't match `AUTH0_AUDIENCE`
- Token issuer doesn't match Auth0 domain

**Solution**: 
- Check token expiration
- Verify `AUTH0_AUDIENCE` matches token audience
- Verify `AUTH0_DOMAIN` matches token issuer

### Error: "Token missing email"

**Solution**: Make sure your Auth0 application requests the `email` scope and the user has verified their email.

### JWKS Endpoint Not Found

**Solution**: 
- Verify `AUTH0_DOMAIN` is correct
- Check that `https://{AUTH0_DOMAIN}/.well-known/jwks.json` is accessible
- If using custom JWKS URI, verify it's correct

## Security Best Practices

1. **Never commit `.env` files** - Use environment variables
2. **Use HTTPS** - Always use HTTPS in production
3. **Validate audience** - Always set `AUTH0_AUDIENCE` to validate tokens
4. **Token expiration** - Tokens should have reasonable expiration times
5. **Rate limiting** - Consider adding rate limiting to prevent abuse

## Database Integration

Currently, the license server uses an in-memory database. For production:

1. Set up a real database (PostgreSQL recommended)
2. Update `lib/database.ts` to use the real database
3. Run database migrations to create tables
4. Update connection string in environment variables

See `lib/database.ts` for TODOs and migration points.

## Next Steps

- Configure user licenses in the database
- Set up device registration limits
- Implement license expiration handling
- Add license revocation support

