# License Flow Testing Guide

**Complete guide for testing the license activation and validation flow with local Laravel server.**

---

## Prerequisites

1. **License Server Running:**
   ```powershell
   cd apps\web-dashboard
   php artisan serve --host=127.0.0.1 --port=8000
   ```

2. **Test User Created:**
   - Email: `test@example.com`
   - Password: `testpassword123`
   - Created via: `php artisan migrate:fresh --seed`

3. **Environment Variables (Optional):**
   ```powershell
   $env:LICENSE_SERVER_URL = "http://localhost:8000"
   $env:AUTH_SERVER_URL = "http://localhost:8000"
   ```

---

## Automated Testing

### Run Complete License Flow Test

```powershell
cd apps\upload-bridge
python scripts\test_license_flow.py
```

### What It Tests

1. **Server Health Check**
   - Verifies license server is accessible
   - Checks `/api/v2/health` endpoint

2. **Email/Password Login**
   - Tests successful login with valid credentials
   - Verifies session token and entitlement token received

3. **Invalid Credentials**
   - Tests rejection of invalid credentials
   - Verifies proper error handling

4. **License Validation**
   - Tests license validation with authenticated user
   - Verifies license status, plan, and expiry

5. **Session Persistence**
   - Tests session save/load (simulates app restart)
   - Verifies tokens persist correctly

6. **Token Refresh**
   - Tests token refresh functionality
   - Verifies new tokens received

7. **License Info Endpoint**
   - Tests `/api/v2/license/info` endpoint
   - Verifies license information retrieval

8. **Logout**
   - Tests logout functionality
   - Verifies tokens cleared and session file deleted

9. **Offline Grace Period**
   - Tests grace period logic
   - Verifies offline operation support

10. **Magic Link Request**
    - Tests magic link request endpoint
    - Verifies email-based passwordless login support

---

## Manual Testing Checklist

### 1. Application Launch

- [ ] Start license server: `php artisan serve`
- [ ] Launch Upload Bridge: `python main.py`
- [ ] Verify application starts without errors
- [ ] Check if login dialog appears (if not authenticated)

### 2. Email/Password Login

- [ ] Enter valid credentials: `test@example.com` / `testpassword123`
- [ ] Click "Login"
- [ ] Verify login succeeds
- [ ] Verify main application window opens
- [ ] Check status bar shows "License activated"

### 3. Invalid Credentials

- [ ] Enter invalid email: `wrong@example.com`
- [ ] Enter invalid password: `wrongpassword`
- [ ] Click "Login"
- [ ] Verify error message displayed
- [ ] Verify login dialog remains open

### 4. License Status Dialog

- [ ] Go to: Help → License Status
- [ ] Verify license information displayed:
  - [ ] User email
  - [ ] License status (ACTIVE)
  - [ ] Plan type
  - [ ] Expiry date (if applicable)
- [ ] Test "Reactivate" button
- [ ] Test "Logout" button

### 5. License Activation Dialog

- [ ] Go to: Help → Activate License
- [ ] Test Email/Password tab:
  - [ ] Enter credentials
  - [ ] Click "Login"
  - [ ] Verify activation succeeds
- [ ] Test Magic Link tab:
  - [ ] Enter email
  - [ ] Click "Send Magic Link"
  - [ ] Verify success message

### 6. Session Persistence

- [ ] Login successfully
- [ ] Close application
- [ ] Restart application
- [ ] Verify user remains logged in
- [ ] Verify license still valid

### 7. Logout

- [ ] Go to: Help → License Status
- [ ] Click "Logout"
- [ ] Confirm logout
- [ ] Verify application returns to login screen
- [ ] Verify session cleared

### 8. Offline Grace Period

- [ ] Login while online
- [ ] Verify license validated
- [ ] Disconnect internet (or stop license server)
- [ ] Restart application
- [ ] Verify application works (within 7-day grace period)
- [ ] Check grace period status in license dialog

### 9. Token Refresh

- [ ] Login successfully
- [ ] Wait for token to expire (or manually trigger refresh)
- [ ] Verify token refresh happens automatically
- [ ] Verify application continues working

### 10. Error Handling

- [ ] Stop license server
- [ ] Try to login
- [ ] Verify appropriate error message
- [ ] Start license server
- [ ] Try to login again
- [ ] Verify login succeeds

---

## API Endpoint Testing

### Health Check

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/v2/health" -UseBasicParsing
```

Expected: `{"status":"ok","timestamp":"...","version":"2.0"}`

### Login

```powershell
$body = @{
    email = "test@example.com"
    password = "testpassword123"
    device_id = "TEST_DEVICE"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/v2/auth/login" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
```

Expected: `{"session_token":"...","entitlement_token":"...","user":{...}}`

### License Validation

```powershell
$headers = @{
    Authorization = "Bearer YOUR_SESSION_TOKEN"
}

Invoke-WebRequest -Uri "http://localhost:8000/api/v2/license/validate" -Method GET -Headers $headers -UseBasicParsing
```

Expected: `{"status":"ACTIVE","plan":"...","expires_at":"..."}`

---

## Troubleshooting

### Server Not Responding

**Problem:** Tests fail with connection errors

**Solutions:**
1. Check server is running: `Get-Process -Name php`
2. Check port 8000: `netstat -an | findstr :8000`
3. Restart server: `cd apps\web-dashboard && php artisan serve`

### Login Fails

**Problem:** Login returns 401 or 422

**Solutions:**
1. Verify test user exists: Check database
2. Verify password: `testpassword123`
3. Check server logs: `apps\web-dashboard\storage\logs\laravel.log`

### License Validation Fails

**Problem:** License validation returns inactive or error

**Solutions:**
1. Verify user has active subscription in database
2. Check license server logs
3. Verify session token is valid
4. Check device registration

### Session Not Persisting

**Problem:** User logged out after app restart

**Solutions:**
1. Check session file exists: `~/.upload_bridge/auth/token.enc`
2. Verify file permissions
3. Check encryption key generation
4. Verify device ID consistency

---

## Test Results Interpretation

### All Tests Pass ✅

- License flow is working correctly
- Ready for manual testing
- All endpoints accessible
- Authentication working

### Some Tests Fail ❌

- Check server status
- Verify test user exists
- Check network connectivity
- Review error messages

### Warnings ⚠️

- Non-critical issues
- May indicate configuration issues
- Review warnings for details

---

## Next Steps

After successful automated testing:

1. **Run Manual Tests:** Follow the manual testing checklist
2. **Test Application Features:** Verify app features work with license system
3. **Test Error Scenarios:** Test various error conditions
4. **Performance Testing:** Test with long-running sessions
5. **Production Readiness:** Review production readiness checklist

---

## Related Documentation

- `RAILWAY_TO_LOCAL_MIGRATION.md` - Migration details
- `LOCAL_SETUP_COMPLETE.md` - Setup summary
- `E2E_MANUAL_TESTING_GUIDE.md` - Complete E2E testing guide
- `QUICK_START_E2E_TESTING.md` - Quick start guide

---

**Ready to test!** 🚀
