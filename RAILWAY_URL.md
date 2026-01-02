# 🚂 Railway Deployment URL

## Production URL

```
https://j-tech-license-server-production.up.railway.app
```

## ✅ Deployment Status

**Status**: ✅ **LIVE AND WORKING**

All tests passing:
- ✅ Health endpoint: Working
- ✅ CORS headers: Configured
- ✅ Auth0 configuration: Working
- ✅ Login endpoint: Working
- ✅ Token validation: Working

## 📋 API Endpoints

### Health Check
```
GET https://j-tech-license-server-production.up.railway.app/api/health
```

### Login
```
POST https://j-tech-license-server-production.up.railway.app/api/v2/auth/login
Content-Type: application/json

{
  "auth0_token": "your-auth0-token",
  "device_id": "DEVICE_123",
  "device_name": "Test Device"
}
```

### Refresh Token
```
POST https://j-tech-license-server-production.up.railway.app/api/v2/auth/refresh
Content-Type: application/json

{
  "session_token": "session_...",
  "device_id": "DEVICE_123"
}
```

## 🔧 Environment Variables

Set in Railway Dashboard:
- `AUTH0_DOMAIN` = `dev-oczlciw58f2a4oei.us.auth0.com`
- `AUTH0_CLIENT_ID` = (your client ID)
- `AUTH0_AUDIENCE` = (optional)

## 📝 Update Upload Bridge Config

```yaml
# apps/upload-bridge/config/auth_config.yaml
auth_server_url: https://j-tech-license-server-production.up.railway.app
```

---

**Deployed**: 2025-01-27  
**Platform**: Railway  
**Status**: ✅ Production

