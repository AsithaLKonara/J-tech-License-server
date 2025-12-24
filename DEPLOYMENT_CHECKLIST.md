# ✅ Vercel Deployment Checklist

Use this checklist to verify your deployment is working correctly.

## Pre-Deployment

- [ ] All files are in `api/` folder
- [ ] `package.json` includes `@vercel/node`
- [ ] `vercel.json` exists (can be minimal: `{"version": 2}`)
- [ ] TypeScript files have proper exports
- [ ] No syntax errors in code

## Deployment Steps

- [ ] Run `npm install` locally
- [ ] Run `vercel login` (if not already logged in)
- [ ] Run `vercel --prod`
- [ ] Note the deployment URL

## Post-Deployment Verification

### 1. Check Vercel Dashboard

- [ ] Deployment shows as "Ready"
- [ ] No build errors in logs
- [ ] Functions are listed in Settings → Functions

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
  "timestamp": "2025-01-27T..."
}
```

- [ ] Returns 200 status
- [ ] JSON response is valid
- [ ] Contains expected fields

### 3. Test Login Endpoint

```bash
curl -X POST https://j-tech-licensing.vercel.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "device_id": "DEVICE_123",
    "device_name": "Test Device"
  }'
```

Expected response:
```json
{
  "session_token": "session_...",
  "entitlement_token": {
    "sub": "user_test_example_com",
    "product": "upload_bridge_pro",
    "plan": "pro",
    "features": ["pattern_upload", "wifi_upload", "advanced_controls"],
    "expires_at": null
  },
  "user": {
    "id": "user_test_example_com",
    "email": "test@example.com"
  }
}
```

- [ ] Returns 200 status
- [ ] Contains session_token
- [ ] Contains entitlement_token
- [ ] Contains user info

### 4. Test Invalid Credentials

```bash
curl -X POST https://j-tech-licensing.vercel.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "wrong@example.com",
    "password": "wrongpassword",
    "device_id": "DEVICE_123",
    "device_name": "Test Device"
  }'
```

Expected response:
```json
{
  "error": "Invalid credentials"
}
```

- [ ] Returns 401 status
- [ ] Error message is clear

### 5. Test from Upload Bridge App

- [ ] Update `apps/upload-bridge/config/auth_config.yaml`:
  ```yaml
  auth_server_url: https://j-tech-licensing.vercel.app
  ```
- [ ] Launch Upload Bridge
- [ ] Open login dialog
- [ ] Enter: `test@example.com` / `testpassword123`
- [ ] Click Login
- [ ] Should successfully authenticate

## Troubleshooting

If any step fails:

1. Check Vercel dashboard logs
2. Verify file structure matches expected layout
3. Check `vercel.json` configuration
4. Try redeploying: `vercel --prod --force`
5. See `TROUBLESHOOTING.md` for detailed help

## Success Criteria

✅ All endpoints return expected responses  
✅ No 404 errors  
✅ Login works from Upload Bridge app  
✅ Health check returns valid JSON  

---

**Once all checks pass, your deployment is ready!** 🎉

