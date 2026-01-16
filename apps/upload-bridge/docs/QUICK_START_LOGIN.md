# Quick Start: Login & License

**Upload Bridge v3.0.0**

---

## TL;DR - Quick Options

### Option 1: Use Offline License Key (Easiest - No Setup)

1. Open application
2. Cancel login dialog (or skip if possible)
3. Menu → License → Activate License...
4. Enter: `ULBP-9Q2Z-7K3M-4X1A`
5. Click "Activate"
6. Done! ✅

**No Auth0, no backend server, no configuration needed!**

---

### Option 2: Email/Password Login (No Auth0 Required)

1. **Set up backend server** at `http://localhost:3000`
2. **Create user account** via your backend
3. **Login** with email/password in application
4. License automatically validated ✅

**No Auth0 configuration needed!**

---

### Option 3: OAuth/Social Login (Requires Auth0)

1. **Set Auth0 environment variables**:
   ```bash
   export AUTH0_DOMAIN="your-tenant.auth0.com"
   export AUTH0_CLIENT_ID="your-client-id"
   ```
2. **Login** via Social Login tab
3. License automatically validated ✅

---

## Detailed Setup

### For Email/Password Login (Recommended for Testing)

**No Auth0 needed!** Just need a backend server.

**Backend Endpoint**: `POST /api/v2/auth/login`

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
  "session_token": "session-token",
  "entitlement_token": {
    "sub": "user-id",
    "product": "upload_bridge_pro",
    "plan": "pro",
    "features": ["pattern_upload", "wifi_upload"],
    "expires_at": null
  },
  "user": {
    "id": "user-id",
    "email": "test@example.com"
  }
}
```

---

### For OAuth/Social Login

**Requires Auth0 setup**:

1. **Set environment variables**:
   ```powershell
   # Windows PowerShell
   $env:AUTH0_DOMAIN="your-tenant.auth0.com"
   $env:AUTH0_CLIENT_ID="your-client-id"
   ```

   ```bash
   # Linux/macOS
   export AUTH0_DOMAIN="your-tenant.auth0.com"
   export AUTH0_CLIENT_ID="your-client-id"
   ```

2. **Or configure in file** (`config/auth_config.yaml`):
   ```yaml
   auth0:
     domain: "your-tenant.auth0.com"
     client_id: "your-client-id"
   ```

3. **Login** via Social Login tab

---

## What Happens After Login

1. ✅ **AuthManager** stores session and entitlement tokens
2. ✅ **LicenseManager** automatically validates account-based license
3. ✅ **License info** displayed (plan, features)
4. ✅ **Application** continues with validated license

---

## Troubleshooting

### "Auth0 Not Configured" Message

**Solution**: This only affects Magic Link and Social Login tabs. Use:
- **Email/Password** tab (works without Auth0)
- **Offline License Keys** (no login needed)

### Email/Password Login Fails

**Cause**: Backend server not running or wrong URL

**Solution**: 
- Check server is running at `http://localhost:3000`
- Or use offline license keys instead

### License Not Validated After Login

**Solution**: Check server returns `entitlement_token` in response

---

## Summary

| Method | Auth0 Required? | Backend Required? | Setup Complexity |
|--------|----------------|-------------------|------------------|
| **Offline License Keys** | ❌ No | ❌ No | ⭐ Easiest |
| **Email/Password** | ❌ No | ✅ Yes | ⭐⭐ Easy |
| **Magic Link** | ✅ Yes | ✅ Yes | ⭐⭐⭐ Medium |
| **Social Login** | ✅ Yes | ✅ Yes | ⭐⭐⭐ Medium |

**Recommendation**: Start with **Offline License Keys** for testing, then add Email/Password login when backend is ready.

---

**Last Updated**: 2025-01-27

