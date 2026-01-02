# 🧪 Test Your Railway Deployment

## Quick Test Commands

### 1. Health Check

Replace `YOUR_RAILWAY_URL` with your actual Railway URL:

```bash
curl https://YOUR_RAILWAY_URL.up.railway.app/api/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "service": "upload-bridge-license-server",
  "version": "1.0.0",
  "timestamp": "2025-01-27T..."
}
```

### 2. Test with PowerShell

```powershell
# Health check
Invoke-RestMethod -Uri "https://YOUR_RAILWAY_URL.up.railway.app/api/health" -Method Get

# Login endpoint (with Auth0 token)
$body = @{
    auth0_token = "your-auth0-token-here"
    device_id = "DEVICE_123"
    device_name = "Test Device"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://YOUR_RAILWAY_URL.up.railway.app/api/v2/auth/login" -Method Post -Body $body -ContentType "application/json"
```

### 3. Test with Browser

Open in browser:
```
https://YOUR_RAILWAY_URL.up.railway.app/api/health
```

You should see the JSON response.

## ✅ Verification Checklist

- [ ] Health endpoint returns `{"status": "ok"}`
- [ ] CORS headers are present (check browser console)
- [ ] Login endpoint accepts POST requests
- [ ] Environment variables are set in Railway dashboard
- [ ] Server logs show no errors

## 🔍 Troubleshooting

### If health check fails:
1. Check Railway Dashboard → Deployments → Logs
2. Verify the service is running (not crashed)
3. Check environment variables are set

### If login endpoint fails:
1. Verify `AUTH0_DOMAIN` is set correctly
2. Check Railway logs for error messages
3. Test with a valid Auth0 token

### If CORS errors:
- CORS is already configured in the server
- Check browser console for specific error
- Verify the request is going to the correct URL

## 📝 Update Your Config

Once verified, update Upload Bridge:

```yaml
# apps/upload-bridge/config/auth_config.yaml
auth_server_url: https://YOUR_RAILWAY_URL.up.railway.app
```

---

**Status**: ✅ Deployment Successful!  
**Next**: Test endpoints and update Upload Bridge config

