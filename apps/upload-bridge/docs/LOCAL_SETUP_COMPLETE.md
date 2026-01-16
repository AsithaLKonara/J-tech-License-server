# Local Setup Complete - Ready for Manual E2E Testing

**Date:** January 9, 2026  
**Status:** ✅ **READY FOR TESTING**

---

## ✅ Setup Summary

### License Server (Laravel)
- **Status:** ✅ Configured and Running
- **Location:** `apps/web-dashboard/`
- **URL:** `http://localhost:8000`
- **Database:** SQLite (`database/database.sqlite`)
- **Migrations:** ✅ All migrations completed
- **Test Users Created:**
  - `test@example.com` / `testpassword123`
  - `admin@example.com` / `admin123`

### Upload Bridge Application
- **Status:** ✅ Configured
- **Location:** `apps/upload-bridge/`
- **Python Version:** 3.12.10 ✅
- **Dependencies:** ✅ All installed (PySide6, requests, cryptography, numpy)
- **Environment Variables:**
  - `LICENSE_SERVER_URL=http://localhost:8000`
  - `AUTH_SERVER_URL=http://localhost:8000`

### Pre-Test Checks
- ✅ License server directory exists
- ✅ Dependencies installed (vendor, Python packages)
- ✅ Database configured (SQLite)
- ✅ Migrations completed
- ✅ Test users seeded
- ✅ Environment variables set
- ⚠️  License server connection (may need manual verification)

---

## 🚀 Quick Start for Manual Testing

### 1. Start License Server (if not running)

```powershell
cd apps\web-dashboard
php artisan serve --host=127.0.0.1 --port=8000
```

**Verify server is running:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/v2/health" -UseBasicParsing
```

Expected response: `{"status":"ok","timestamp":"...","version":"2.0"}`

### 2. Start Upload Bridge Application

```powershell
cd apps\upload-bridge
python main.py
```

---

## 📋 Manual E2E Test Checklist

### Authentication Tests

#### Email/Password Login
- [ ] **Valid credentials:** `test@example.com` / `testpassword123`
  - [ ] Login succeeds
  - [ ] Token stored correctly
  - [ ] App proceeds to main window
- [ ] **Invalid credentials:** Wrong email/password
  - [ ] Error message displayed
  - [ ] App remains on login screen
- [ ] **Empty fields:** Submit with blank email/password
  - [ ] Validation errors shown
- [ ] **Network error:** Disconnect internet, try login
  - [ ] Appropriate error message

#### Magic Link Login
- [ ] **Request magic link:** Enter email, click "Send Magic Link"
  - [ ] Success message shown
  - [ ] Link sent (check logs/email if configured)
- [ ] **Verify magic link:** Use token from server logs
  - [ ] Login succeeds
  - [ ] App proceeds to main window

### License Validation Tests

- [ ] **Active license:** User with valid subscription
  - [ ] License validated successfully
  - [ ] App launches normally
- [ ] **No license:** User without subscription
  - [ ] Appropriate message shown
  - [ ] Upgrade prompt displayed
- [ ] **Offline grace period:** 
  - [ ] Login while online
  - [ ] Disconnect internet
  - [ ] App should work for 7 days
  - [ ] After grace period, app requires re-authentication

### Application Features with License

- [ ] **Pattern Upload:** Create/upload pattern
  - [ ] Works with valid license
  - [ ] Blocked/limited without license
- [ ] **WiFi Upload:** Upload to device via WiFi
  - [ ] Works with valid license
- [ ] **Media Upload:** Upload media files
  - [ ] Works with valid license
- [ ] **Device Management:** Add/remove devices
  - [ ] Works with valid license

### Error Handling Tests

- [ ] **Server unavailable:** Stop license server, try operations
  - [ ] Graceful error messages
  - [ ] Grace period respected
- [ ] **Invalid responses:** Mock server errors
  - [ ] App handles gracefully
- [ ] **Token expiration:** Wait for token to expire
  - [ ] Re-authentication prompt
  - [ ] Can re-login successfully

### Performance Tests

- [ ] **Startup time:** Measure app launch time
- [ ] **Memory usage:** Monitor during extended use
- [ ] **CPU usage:** Check during rendering/upload
- [ ] **Long session:** Run app for 1+ hours
  - [ ] No memory leaks
  - [ ] Token refresh works

---

## 🔧 Test User Accounts

### Regular User
- **Email:** `test@example.com`
- **Password:** `testpassword123`
- **Status:** Active, verified
- **License:** Check via license server

### Admin User
- **Email:** `admin@example.com`
- **Password:** `admin123`
- **Status:** Super-admin
- **License:** Full access

---

## 📝 API Endpoints Reference

### Authentication
- `POST /api/v2/auth/login` - Email/password login
- `POST /api/v2/auth/logout` - Logout
- `POST /api/v2/auth/magic-link/request` - Request magic link
- `POST /api/v2/auth/magic-link/verify` - Verify magic link
- `POST /api/v2/auth/refresh` - Refresh token

### License
- `GET /api/v2/license/info` - Get license information
- `GET /api/v2/license/validate` - Validate license
- `POST /api/v2/license/verify` - Verify license

### Health
- `GET /api/v2/health` - Server health check

---

## 🐛 Troubleshooting

### License Server Not Responding
1. Check if server is running: `Get-Process -Name php`
2. Check port 8000: `netstat -an | findstr :8000`
3. Restart server: `cd apps\web-dashboard && php artisan serve`

### Database Issues
1. Check SQLite file exists: `Test-Path apps\web-dashboard\database\database.sqlite`
2. Re-run migrations: `cd apps\web-dashboard && php artisan migrate:fresh --seed`

### Upload Bridge Connection Issues
1. Verify environment variables: `$env:LICENSE_SERVER_URL`
2. Test connection: `Invoke-WebRequest -Uri "http://localhost:8000/api/v2/health"`
3. Check firewall/antivirus blocking localhost

### Authentication Failures
1. Verify test users exist in database
2. Check server logs: `apps\web-dashboard\storage\logs\laravel.log`
3. Verify CORS settings in `.env`

---

## 📚 Documentation References

- **E2E Manual Testing Guide:** `docs/E2E_MANUAL_TESTING_GUIDE.md`
- **Quick Start E2E:** `docs/QUICK_START_E2E_TESTING.md`
- **Pre-Test Checklist:** `docs/PRE_TEST_CHECKLIST.md`
- **License Activation Guide:** `docs/LICENSE_ACTIVATION_GUIDE.md`

---

## ✅ Next Steps

1. **Start license server** (if not already running)
2. **Launch Upload Bridge** application
3. **Begin manual testing** using the checklist above
4. **Document any issues** found during testing
5. **Verify all features** work with the license system

---

**Ready to proceed with manual E2E testing!** 🎉
