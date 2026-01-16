# Pre-Test Systematic Checklist

**Upload Bridge v3.0.0**

**Complete systematic checks before manual E2E testing**

---

## Overview

Before starting manual E2E testing, run systematic automated checks to ensure everything is configured correctly. This prevents wasted time during manual testing due to configuration issues.

---

## Quick Start

### Option 1: Automated Checks (Recommended)

**Run comprehensive pre-test checks**:
```powershell
cd apps\upload-bridge
.\scripts\pre-test-checks.ps1
```

This script checks:
- ✅ License server setup (XAMPP MySQL, database, configuration)
- ✅ Upload Bridge application (Python, dependencies, configuration)
- ✅ API connectivity
- ✅ Test data (users, subscriptions)
- ✅ Code quality tools availability

---

### Option 2: License Server Only

**Check license server setup**:
```powershell
cd apps\web-dashboard
.\pre-test-verify.ps1
```

This script checks:
- ✅ .env file exists and configured
- ✅ APP_KEY generated
- ✅ Database connection works
- ✅ Migrations run
- ✅ Test user exists
- ✅ Dependencies installed

---

## Manual Checklist

If you prefer manual checks, follow this checklist:

### Section 1: License Server Prerequisites

- [ ] **1.1 XAMPP MySQL Running**
  - [ ] MySQL service started in XAMPP Control Panel (green)
  - [ ] Can access phpMyAdmin at http://localhost/phpmyadmin
  - [ ] Verify: `mysql -h 127.0.0.1 -P 3306 -u root -e "SELECT 1;"`

- [ ] **1.2 License Server Directory**
  - [ ] Directory exists: `apps\web-dashboard`
  - [ ] `.env` file exists
  - [ ] `composer.json` exists
  - [ ] `vendor` directory exists (dependencies installed)

- [ ] **1.3 PHP and Composer**
  - [ ] PHP 8.1+ installed: `php -v`
  - [ ] Composer installed: `composer --version`
  - [ ] Both accessible in PATH

- [ ] **1.4 Database Configuration**
  - [ ] Database exists: `upload_bridge_license`
  - [ ] `.env` has correct credentials:
    ```env
    DB_CONNECTION=mysql
    DB_HOST=127.0.0.1
    DB_PORT=3306
    DB_DATABASE=upload_bridge_license
    DB_USERNAME=root
    DB_PASSWORD=
    ```

- [ ] **1.5 Application Key**
  - [ ] `APP_KEY` generated in `.env`
  - [ ] Verify: `APP_KEY=base64:...` (not empty)

- [ ] **1.6 Database Migrations**
  - [ ] Migrations run: `php artisan migrate:status`
  - [ ] All migrations applied (no "Pending")
  - [ ] Tables exist: `users`, `subscriptions`, `licenses`, `devices`

- [ ] **1.7 Test User Created**
  - [ ] Test user exists: `test@example.com`
  - [ ] Password: `password123`
  - [ ] Email verified
  - [ ] Has active subscription (optional)

- [ ] **1.8 License Server Running**
  - [ ] Server started: `php artisan serve`
  - [ ] Health check works: `curl http://localhost:8000/api/v2/health`
  - [ ] Returns: `{"status": "ok", ...}`

---

### Section 2: Upload Bridge Application Prerequisites

- [ ] **2.1 Python Environment**
  - [ ] Python 3.10+ installed: `python --version`
  - [ ] Python accessible in PATH

- [ ] **2.2 Application Directory**
  - [ ] Directory exists: `apps\upload-bridge`
  - [ ] `main.py` exists
  - [ ] `requirements.txt` exists

- [ ] **2.3 Python Dependencies**
  - [ ] PySide6 installed: `python -c "import PySide6"`
  - [ ] requests installed: `python -c "import requests"`
  - [ ] cryptography installed: `python -c "import cryptography"`
  - [ ] numpy installed: `python -c "import numpy"`
  - [ ] All packages from `requirements.txt` installed

- [ ] **2.4 Configuration Files**
  - [ ] `config/app_config.yaml` exists
  - [ ] License server URL configured:
    ```yaml
    auth_server_url: "http://localhost:8000"
    license_server_url: "http://localhost:8000"
    ```

- [ ] **2.5 Environment Variables**
  - [ ] `LICENSE_SERVER_URL` set (optional if config file exists)
  - [ ] Points to localhost:8000 for local testing
  - [ ] Verify: `echo $env:LICENSE_SERVER_URL`

- [ ] **2.6 API Connectivity**
  - [ ] Can connect to license server API
  - [ ] Health check endpoint accessible
  - [ ] CORS configured (if needed)

---

### Section 3: Code Quality Checks (Optional)

- [ ] **3.1 Linting**
  - [ ] flake8 installed: `flake8 --version`
  - [ ] Run: `flake8 apps\upload-bridge --max-line-length=120`
  - [ ] No critical errors (warnings acceptable)

- [ ] **3.2 Type Checking**
  - [ ] mypy installed: `mypy --version`
  - [ ] Run: `mypy apps\upload-bridge`
  - [ ] No critical errors

- [ ] **3.3 Unit Tests** (if available)
  - [ ] pytest installed: `pytest --version`
  - [ ] Run: `pytest apps\upload-bridge/tests`
  - [ ] All tests pass (or acceptable failures)

---

### Section 4: Integration Verification

- [ ] **4.1 License Server API**
  - [ ] Health endpoint: `GET /api/v2/health` → 200 OK
  - [ ] Login endpoint: `POST /api/v2/auth/login` → accessible
  - [ ] License validation: `GET /api/v2/license/validate` → accessible (requires auth)

- [ ] **4.2 Test Login Flow**
  - [ ] Can make login request:
    ```powershell
    curl -X POST http://localhost:8000/api/v2/auth/login `
      -H "Content-Type: application/json" `
      -d '{"email": "test@example.com", "password": "password123", "device_id": "TEST", "device_name": "Test"}'
    ```
  - [ ] Returns valid response with `session_token`
  - [ ] No errors in server logs

- [ ] **4.3 Upload Bridge Can Connect**
  - [ ] Run connection test: `.\scripts\test-local-connection.ps1`
  - [ ] All tests pass
  - [ ] No connection errors

---

## Pre-Test Scripts

### 1. Comprehensive Pre-Test Checks

**Script**: `apps/upload-bridge/scripts/pre-test-checks.ps1`

**Runs**:
- ✅ All license server checks
- ✅ All application checks
- ✅ API connectivity tests
- ✅ Test data verification
- ✅ Environment validation

**Usage**:
```powershell
cd apps\upload-bridge
.\scripts\pre-test-checks.ps1
```

**Output**: 
- ✅ All checks pass → Ready for testing
- ❌ Some checks fail → Fix errors first

---

### 2. License Server Verification

**Script**: `apps/web-dashboard/pre-test-verify.ps1`

**Runs**:
- ✅ .env file check
- ✅ APP_KEY verification
- ✅ Database connection test
- ✅ Migration status
- ✅ Test user check
- ✅ Dependencies check

**Usage**:
```powershell
cd apps\web-dashboard
.\pre-test-verify.ps1
```

**Output**:
- ✅ Ready → Start server: `php artisan serve`
- ❌ Fix issues → Run: `.\setup-xampp.ps1`

---

### 3. Connection Test

**Script**: `apps/upload-bridge/scripts/test-local-connection.ps1`

**Runs**:
- ✅ Health check endpoint
- ✅ Login endpoint availability
- ✅ CORS configuration

**Usage**:
```powershell
cd apps\upload-bridge
.\scripts\test-local-connection.ps1
```

---

## Troubleshooting Pre-Test Failures

### Issue: MySQL Not Running

**Solution**:
1. Open XAMPP Control Panel
2. Start MySQL service (click "Start")
3. Verify: green indicator shows "Running"
4. Test: `mysql -h 127.0.0.1 -P 3306 -u root -e "SELECT 1;"`

---

### Issue: Database Not Found

**Solution**:
```powershell
cd apps\web-dashboard
.\setup-xampp.ps1
```

Or manually:
1. Open http://localhost/phpmyadmin
2. Click "New" → Database name: `upload_bridge_license`
3. Collation: `utf8mb4_unicode_ci`
4. Click "Create"

---

### Issue: Dependencies Not Installed

**License Server**:
```powershell
cd apps\web-dashboard
composer install
```

**Upload Bridge**:
```powershell
cd apps\upload-bridge
pip install -r requirements.txt
```

---

### Issue: APP_KEY Not Set

**Solution**:
```powershell
cd apps\web-dashboard
php artisan key:generate
```

---

### Issue: Migrations Not Run

**Solution**:
```powershell
cd apps\web-dashboard
php artisan migrate --force
```

---

### Issue: Test User Not Found

**Solution**:
```powershell
cd apps\web-dashboard
php artisan tinker
```

Then:
```php
App\Models\User::create([
    'name' => 'Test User',
    'email' => 'test@example.com',
    'password' => bcrypt('password123'),
    'email_verified_at' => now(),
]);
```

---

### Issue: API Connection Failed

**Solution**:
1. Verify server is running: `php artisan serve`
2. Check port 8000 is available: `netstat -ano | findstr :8000`
3. Test health check: `curl http://localhost:8000/api/v2/health`
4. Check firewall allows localhost connections
5. Verify `LICENSE_SERVER_URL` points to `http://localhost:8000`

---

## Pre-Test Checklist Summary

### Critical (Must Pass):
- [ ] XAMPP MySQL running
- [ ] License server configured and running
- [ ] Database exists and migrations run
- [ ] Test user created
- [ ] Upload Bridge configured
- [ ] API connectivity verified

### Important (Should Pass):
- [ ] All dependencies installed
- [ ] Configuration files correct
- [ ] Environment variables set (if needed)
- [ ] Code quality checks pass

### Optional (Nice to Have):
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Unit tests pass

---

## Next Steps After Pre-Test

### If All Checks Pass:

1. **Start License Server**:
   ```powershell
   cd apps\web-dashboard
   php artisan serve
   ```

2. **Start Upload Bridge**:
   ```powershell
   cd apps\upload-bridge
   python main.py
   ```

3. **Begin Manual Testing**:
   - Follow: `docs\E2E_MANUAL_TESTING_GUIDE.md`
   - Use: `docs\QUICK_START_E2E_TESTING.md` for quick reference

### If Checks Fail:

1. **Review Errors**: Read error messages from pre-test script
2. **Fix Issues**: Follow troubleshooting guide above
3. **Re-run Checks**: Run pre-test script again
4. **Verify**: Ensure all critical checks pass before testing

---

## Quick Reference Commands

### Pre-Test Checks

```powershell
# Comprehensive checks (recommended)
cd apps\upload-bridge
.\scripts\pre-test-checks.ps1

# License server only
cd apps\web-dashboard
.\pre-test-verify.ps1

# Connection test
cd apps\upload-bridge
.\scripts\test-local-connection.ps1
```

### Fix Common Issues

```powershell
# Setup license server
cd apps\web-dashboard
.\setup-xampp.ps1

# Start server
php artisan serve

# Create test user
php artisan tinker
>>> App\Models\User::create(['name' => 'Test', 'email' => 'test@example.com', 'password' => bcrypt('password123'), 'email_verified_at' => now()]);
```

---

## Summary

**Before manual testing, ensure**:
1. ✅ Run `pre-test-checks.ps1` - All critical checks pass
2. ✅ License server running - Health check returns OK
3. ✅ Test user exists - Can login with `test@example.com` / `password123`
4. ✅ Upload Bridge configured - Can connect to license server
5. ✅ API connectivity verified - All endpoints accessible

**Estimated Pre-Test Time**: 5-10 minutes

**Benefit**: Prevents wasted time during manual testing due to configuration issues

---

**Last Updated**: 2025-01-27  
**Version**: 3.0.0
