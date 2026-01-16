# Login & License System - Complete Integration Summary

**Upload Bridge v3.0.0**

---

## ✅ Integration Complete

The license system is now fully integrated with the account-based login system.

---

## How It Works

### Login Flow

1. **User opens application**
2. **Login dialog appears** (if not authenticated)
3. **User chooses login method**:
   - Email/Password (no Auth0 needed)
   - Magic Link (requires Auth0)
   - Social Login (requires Auth0)
4. **After successful login**:
   - AuthManager stores session & entitlement tokens
   - LicenseManager automatically validates license
   - License info displayed to user
   - Application continues normally

### License Validation Priority

1. **Account-Based License** (from AuthManager) - Checked first
2. **File-Based License** (offline keys) - Fallback if no account license

---

## Login Methods

### ✅ Email/Password Login

**Status**: ✅ Works without Auth0

**Requirements**:
- Web dashboard server at configured URL (default: `http://localhost:8000`)
- API endpoint: `POST /api/v2/auth/login`
- User account created via web dashboard registration

**How to Use**:
1. Go to "Email/Password" tab
2. Enter email and password (registered via web dashboard)
3. Click "Login"
4. License automatically validated
5. Device automatically registered

**No Auth0 configuration needed!**

---

### ✅ Magic Link Login

**Status**: ✅ Works with integrated web dashboard

**Requirements**:
- Web dashboard server at configured URL
- SMTP configured in web dashboard for sending emails
- Magic link endpoint: `POST /magic-link` (web) or `POST /api/v2/auth/magic-link/verify` (API)

**How to Use**:
1. Go to "Magic Link" tab
2. Enter email address
3. Click "Send Magic Link"
4. Check email and click link (opens web dashboard)
5. Return to application
6. Application automatically authenticates with magic link token

**Note**: Magic link is now fully integrated - no Auth0 required!

---

### ⚠️ Social Login (OAuth)

**Status**: ⚠️ Requires Auth0

**Requirements**:
- Auth0 domain and client ID configured
- OAuth providers configured in Auth0

**Configuration**:
```bash
export AUTH0_DOMAIN="your-tenant.auth0.com"
export AUTH0_CLIENT_ID="your-client-id"
```

**How to Use**:
1. Go to "Social Login" tab
2. Click "Login with Google" or "Login with GitHub"
3. Complete OAuth flow in browser
4. Return to application

**Note**: Tab is disabled if Auth0 not configured (shows helpful message)

---

## Configuration Options

### Server URL Configuration

**Option 1: Environment Variable (Recommended)**

**Windows PowerShell**:
```powershell
$env:LICENSE_SERVER_URL="https://yourdomain.com"
```

**Windows CMD**:
```cmd
set LICENSE_SERVER_URL=https://yourdomain.com
```

**Linux/macOS**:
```bash
export LICENSE_SERVER_URL="https://yourdomain.com"
```

**Option 2: Config File**

Edit `config/auth_config.yaml`:

```yaml
# License Server URL (web dashboard URL)
auth_server_url: "https://yourdomain.com"
license_server_url: "https://yourdomain.com"
```

**Default**: `http://localhost:8000` (for local development)

### Auth0 Configuration (Optional - for OAuth/Social Login)

Auth0 is now **optional**. Only needed if you want OAuth/Social Login features.

**Environment Variables**:
```powershell
$env:AUTH0_DOMAIN="your-tenant.auth0.com"
$env:AUTH0_CLIENT_ID="your-client-id"
```

**Config File** (`config/auth_config.yaml`):
```yaml
auth0:
  domain: "your-tenant.auth0.com"
  client_id: "your-client-id"
  audience: "your-api-audience"  # Optional
```

---

## What Happens When Auth0 Not Configured

### Email/Password Tab
- ✅ **Always enabled** - Works without Auth0
- ✅ **Direct API call** to backend server
- ✅ **No Auth0 required**

### Magic Link Tab
- ⚠️ **Disabled** if Auth0 not configured
- ℹ️ **Shows message**: "Magic Link login requires Auth0 configuration..."
- 💡 **Suggests**: "Alternatively, use Email/Password login"

### Social Login Tab
- ⚠️ **Disabled** if Auth0 not configured
- ℹ️ **Shows message**: "Social Login requires Auth0 configuration..."
- 💡 **Suggests**: "Alternatively, use Email/Password login"

---

## Sample Test Credentials

### For Email/Password Login

**Test Account**:
- Email: `test@example.com`
- Password: `testpassword123`

**Note**: Requires backend server with this account created.

### For Offline License Keys (No Login)

**Sample Keys**:
- `ULBP-9Q2Z-7K3M-4X1A` - Pattern + WiFi
- `ULBP-1P4E-8C2J-7R6B` - Pattern + WiFi + Advanced Controls
- `ULBP-5X9K-3M7V-1Q4Z` - Pattern only

**How to Use**:
1. Cancel login dialog
2. Menu → License → Activate License...
3. Enter key and activate

---

## Backend Server Requirements

The license server is now integrated into the web dashboard. The web dashboard URL serves as both the web interface and the API server.

**Default Server URL**: `http://localhost:8000` (for local development)  
**Production Server URL**: Your web dashboard domain (e.g., `https://yourdomain.com`)

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

**OR with Magic Link**:
```json
{
  "magic_link_token": "token_from_email",
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
    "email": "user@example.com",
    "plan": "monthly",
    "features": ["pattern_upload", "wifi_upload"],
    "max_devices": 2,
    "expires_at": 1234567890,
    "iat": 1234567890,
    "exp": 1234567890
  },
  "user": {
    "id": "user-id",
    "email": "user@example.com",
    "name": "User Name"
  }
}
```

**Configuration**:
- Update `config/auth_config.yaml` with your web dashboard URL
- Or set `LICENSE_SERVER_URL` environment variable
- Default: `http://localhost:8000` (for local development)

---

## Troubleshooting

### "Auth0 Not Configured" Error

**For Email/Password**: This error should NOT appear. Email/Password works without Auth0.

**For Magic Link/Social Login**: This is expected if Auth0 not configured. Use Email/Password instead.

**Solution**: 
- Use Email/Password login (no Auth0 needed)
- Or configure Auth0 (see AUTH0_SETUP_GUIDE.md)
- Or use offline license keys (no login needed)

### Email/Password Login Fails

**Cause**: Web dashboard server not available or misconfigured

**Solutions**:
1. Check web dashboard is running at configured URL
2. Verify endpoint exists: `/api/v2/auth/login`
3. Check web dashboard logs (`storage/logs/laravel.log`)
4. Verify database is set up and migrations are run
5. Check `.env` file configuration in web dashboard
6. Use offline license keys as fallback

### License Not Validated After Login

**Cause**: Server didn't return entitlement_token

**Solutions**:
1. Verify server response includes `entitlement_token`
2. Check entitlement_token structure matches expected format
3. Verify token includes: `sub`, `product`, `plan`, `features`
4. Check application logs for errors

---

## Code Changes Made

### LicenseManager.validate_license()
- ✅ Checks account-based license first (from AuthManager)
- ✅ Falls back to file-based license if account license not available
- ✅ Validates entitlement token expiry
- ✅ Refreshes token if needed

### LoginDialog
- ✅ Loads Auth0 config from environment or config file
- ✅ Email/Password login works without Auth0
- ✅ OAuth/Social login requires Auth0 (tabs disabled if not configured)
- ✅ Shows helpful messages when Auth0 not configured
- ✅ Validates license after successful login
- ✅ Displays license info (plan, features) to user

---

## Quick Reference

| Feature | Auth0 Required? | Web Dashboard Required? | Status |
|---------|----------------|-------------------------|--------|
| Email/Password Login | ❌ No | ✅ Yes | ✅ Working |
| Magic Link Login | ❌ No | ✅ Yes | ✅ Working |
| Social Login | ✅ Yes (optional) | ✅ Yes | ⚠️ Requires Auth0 |
| Offline License Keys | ❌ No | ❌ No | ✅ Working |
| License Validation | ❌ No | ❌ No* | ✅ Working |

*License validation works offline with cached tokens, but may need backend for initial validation.

---

## Next Steps

1. **For Testing**: Use offline license keys (easiest)
2. **For Development**: Set up backend server for email/password login
3. **For Production**: Configure Auth0 for OAuth/Social login (optional)

---

**Last Updated**: 2025-01-27  
**Version**: 3.0.0

