# Auth0 Setup Guide

**Upload Bridge v3.0.0**

---

## Overview

Auth0 is **optional** for Upload Bridge. You can use the application with:

1. **Email/Password Login** - Works without Auth0 (direct API call to your backend)
2. **Offline License Keys** - Works completely offline (no login required)

Auth0 is only required for:
- **Magic Link** login (passwordless)
- **Social Login** (Google, GitHub, etc.)

---

## Quick Start: Using Without Auth0

### Option 1: Email/Password Login (No Auth0 Required)

1. **Set up your backend server** at `http://localhost:3000` (or configure different URL)
2. **Create user accounts** via your backend API
3. **Login** using email/password in the application

**No Auth0 configuration needed!**

### Option 2: Offline License Keys (No Login Required)

1. **Skip login** or cancel login dialog
2. **Activate license key**:
   - Menu → License → Activate License...
   - Enter: `ULBP-9Q2Z-7K3M-4X1A`
   - Click "Activate"

**No Auth0 or backend server needed!**

---

## Setting Up Auth0 (Optional)

Auth0 is only needed if you want Magic Link or Social Login features.

### Step 1: Create Auth0 Account

1. Go to https://auth0.com
2. Sign up for free account
3. Create a new Application (Single Page Application or Native)

### Step 2: Configure Auth0 Application

1. **Application Settings**:
   - Application Type: Native (for desktop app)
   - Allowed Callback URLs: `http://localhost:3000/callback`
   - Allowed Logout URLs: `http://localhost:3000`
   - Allowed Web Origins: `http://localhost:3000`

2. **Note your credentials**:
   - Domain: `your-tenant.auth0.com`
   - Client ID: `your-client-id`

### Step 3: Configure in Upload Bridge

#### Method 1: Environment Variables (Recommended)

**Windows (PowerShell)**:
```powershell
$env:AUTH0_DOMAIN="your-tenant.auth0.com"
$env:AUTH0_CLIENT_ID="your-client-id"
$env:AUTH0_AUDIENCE="your-api-audience"  # Optional
```

**Windows (Command Prompt)**:
```cmd
set AUTH0_DOMAIN=your-tenant.auth0.com
set AUTH0_CLIENT_ID=your-client-id
set AUTH0_AUDIENCE=your-api-audience
```

**Linux/macOS**:
```bash
export AUTH0_DOMAIN="your-tenant.auth0.com"
export AUTH0_CLIENT_ID="your-client-id"
export AUTH0_AUDIENCE="your-api-audience"
```

#### Method 2: Configuration File

Edit `config/auth_config.yaml`:

```yaml
# Auth0 Configuration
# Set these values or use environment variables

auth0:
  domain: "your-tenant.auth0.com"  # Or "${AUTH0_DOMAIN}" to use env var
  client_id: "your-client-id"      # Or "${AUTH0_CLIENT_ID}" to use env var
  audience: "your-api-audience"    # Optional, or "${AUTH0_AUDIENCE}"
  client_secret: "${AUTH0_CLIENT_SECRET}"  # Not needed for public apps
```

**Note**: The application will try to load from config file if environment variables are not set.

---

## Testing Auth0 Setup

### Check Configuration

The login dialog will:
- ✅ Enable "Magic Link" and "Social Login" tabs if Auth0 is configured
- ❌ Disable these tabs and show message if Auth0 is not configured
- ✅ Always enable "Email/Password" tab (doesn't require Auth0)

### Test OAuth Login

1. Open application
2. Go to "Social Login" tab
3. Click "Login with Google" or "Login with GitHub"
4. Complete OAuth flow in browser
5. Should return to application with license validated

---

## Troubleshooting

### "Auth0 Not Configured" Message

**Cause**: AUTH0_DOMAIN and AUTH0_CLIENT_ID not set

**Solutions**:
1. Set environment variables (see above)
2. Or configure in `config/auth_config.yaml`
3. Or use Email/Password login (doesn't require Auth0)

### OAuth Login Fails

**Cause**: Auth0 configuration incorrect

**Solutions**:
1. Verify domain and client ID are correct
2. Check callback URLs in Auth0 dashboard
3. Verify application type is correct (Native)
4. Check Auth0 logs for errors

### Magic Link Not Working

**Cause**: Auth0 Passwordless API not enabled

**Solutions**:
1. Enable Passwordless in Auth0 dashboard
2. Configure email provider in Auth0
3. See: https://auth0.com/docs/authenticate/passwordless

---

## Configuration Priority

The application checks Auth0 configuration in this order:

1. **Environment Variables** (highest priority)
   - `AUTH0_DOMAIN`
   - `AUTH0_CLIENT_ID`
   - `AUTH0_AUDIENCE`

2. **Config File** (`config/auth_config.yaml`)
   - Loaded if environment variables not set
   - Supports `${VAR_NAME}` syntax for env var substitution

3. **Default** (if neither set)
   - Auth0 features disabled
   - Email/Password login still works
   - Offline license keys still work

---

## Sample Configuration

### Minimal Setup (Email/Password Only)

**No configuration needed!**

Just set up your backend server and use email/password login.

### Full Setup (With Auth0)

**Environment Variables**:
```bash
export AUTH0_DOMAIN="dev-abc123.us.auth0.com"
export AUTH0_CLIENT_ID="xyz789ABC123"
export AUTH0_AUDIENCE="https://api.yourapp.com"
```

**Or Config File** (`config/auth_config.yaml`):
```yaml
auth0:
  domain: "dev-abc123.us.auth0.com"
  client_id: "xyz789ABC123"
  audience: "https://api.yourapp.com"
```

---

## Backend Server Requirements

For email/password login, your backend needs:

**Endpoint**: `POST /api/v2/auth/login`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "device_id": "DEVICE_XXXX",
  "device_name": "Windows Device"
}
```

**Response**:
```json
{
  "session_token": "session-token-here",
  "entitlement_token": {
    "sub": "user-id",
    "product": "upload_bridge_pro",
    "plan": "pro",
    "features": ["pattern_upload", "wifi_upload"],
    "expires_at": null
  },
  "user": {
    "id": "user-id",
    "email": "user@example.com"
  }
}
```

---

## Summary

- ✅ **Email/Password Login**: Works without Auth0
- ✅ **Offline License Keys**: Works without Auth0 or backend
- ⚠️ **Magic Link**: Requires Auth0
- ⚠️ **Social Login**: Requires Auth0

**Recommendation**: Start with Email/Password login or offline license keys. Add Auth0 later if you need Magic Link or Social Login.

---

**Last Updated**: 2025-01-27  
**Version**: 3.0.0

