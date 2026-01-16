# End-to-End Manual Testing Guide

**Upload Bridge v3.0.0**

**Complete manual testing of entire application with license system**

---

## Prerequisites

Before starting, ensure you have:

- ✅ XAMPP installed and running
- ✅ MySQL service running in XAMPP
- ✅ Apache service running in XAMPP
- ✅ PHP 8.1+ installed (or use XAMPP PHP)
- ✅ Composer installed
- ✅ Python 3.10+ installed
- ✅ Upload Bridge application ready

---

## Step 1: Setup License Server (Laravel)

### 1.1 Navigate to License Server Directory

```powershell
cd apps\web-dashboard
```

### 1.2 Configure Database for XAMPP/MySQL

**Edit `.env` file** (create from `.env.example` if not exists):

```env
APP_NAME="Upload Bridge License Server"
APP_ENV=local
APP_KEY=
APP_DEBUG=true
APP_URL=http://localhost:8000

# MySQL Configuration (XAMPP)
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=upload_bridge_license
DB_USERNAME=root
DB_PASSWORD=

# License Server Settings
LICENSE_SERVER_URL=http://localhost:8000
AUTH_SERVER_URL=http://localhost:8000

# CORS Settings (for desktop app)
CORS_ALLOWED_ORIGINS=http://localhost,http://127.0.0.1,app://localhost
CORS_ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOWED_HEADERS=Content-Type,Authorization,X-Requested-With,Accept

# Session Settings
SESSION_DRIVER=database
SESSION_LIFETIME=120

# Mail Settings (for magic links - optional for testing)
MAIL_MAILER=smtp
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME="${APP_NAME}"

# Stripe (optional - can skip for basic testing)
STRIPE_KEY=pk_test_...
STRIPE_SECRET=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 1.3 Create MySQL Database

**Option A: Using XAMPP phpMyAdmin**
1. Open http://localhost/phpmyadmin
2. Click "New" to create database
3. Database name: `upload_bridge_license`
4. Collation: `utf8mb4_unicode_ci`
5. Click "Create"

**Option B: Using MySQL Command Line**
```sql
CREATE DATABASE upload_bridge_license CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**Option C: Using Setup Script**
```powershell
.\create-database-and-migrate.ps1
```

### 1.4 Install Dependencies

```powershell
composer install
```

### 1.5 Generate Application Key

```powershell
php artisan key:generate
```

### 1.6 Run Database Migrations

```powershell
php artisan migrate --force
```

**Expected Output**:
```
Migration table created successfully.
Migrating: 2024_01_01_000000_create_users_table
Migrated:  2024_01_01_000000_create_users_table
Migrating: 2024_01_01_000001_create_subscriptions_table
Migrated:  2024_01_01_000001_create_subscriptions_table
...
```

### 1.7 (Optional) Run Seeders for Test Data

```powershell
php artisan db:seed
```

This creates test users and subscriptions for testing.

### 1.8 Create Test User (If Not Using Seeders)

**Using Artisan Tinker**:
```powershell
php artisan tinker
```

Then run:
```php
\App\Models\User::create([
    'name' => 'Test User',
    'email' => 'test@example.com',
    'password' => bcrypt('password123'),
    'email_verified_at' => now(),
]);
```

**Or Create via SQL**:
```sql
USE upload_bridge_license;
INSERT INTO users (name, email, password, email_verified_at, created_at, updated_at) 
VALUES ('Test User', 'test@example.com', '$2y$10$...', NOW(), NOW(), NOW());
```

**Note**: For password, use `bcrypt('password123')` or run:
```php
php artisan tinker
>>> bcrypt('password123')
```

### 1.9 Start License Server

**Option A: Using Laravel Built-in Server**
```powershell
php artisan serve
```

Server starts at: **http://localhost:8000**

**Option B: Using XAMPP Apache**
1. Configure XAMPP virtual host (optional)
2. Point Apache to `apps/web-dashboard/public` directory
3. Access at: **http://localhost** or your configured host

**Verify Server is Running**:
```powershell
curl http://localhost:8000/api/v2/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2025-01-27T12:00:00Z"
}
```

---

## Step 2: Configure Upload Bridge Application

### 2.1 Update Config for Local Server

**Edit `apps/upload-bridge/config/app_config.yaml`**:

```yaml
# Authentication
auth_server_url: "http://localhost:8000"
license_server_url: "http://localhost:8000"

# Or use environment variable
# Set LICENSE_SERVER_URL=http://localhost:8000
```

**Edit `apps/upload-bridge/config/auth_config.yaml`** (if exists):

```yaml
auth_server_url: "http://localhost:8000"
license_server_url: "http://localhost:8000"
```

### 2.2 Set Environment Variable (Alternative)

**Windows PowerShell**:
```powershell
$env:LICENSE_SERVER_URL = "http://localhost:8000"
$env:AUTH_SERVER_URL = "http://localhost:8000"
```

**Windows CMD**:
```cmd
set LICENSE_SERVER_URL=http://localhost:8000
set AUTH_SERVER_URL=http://localhost:8000
```

**Permanent (User-level)**:
```powershell
[System.Environment]::SetEnvironmentVariable('LICENSE_SERVER_URL', 'http://localhost:8000', 'User')
[System.Environment]::SetEnvironmentVariable('AUTH_SERVER_URL', 'http://localhost:8000', 'User')
```

---

## Step 3: Manual Testing Checklist

### Test Category 1: License Server Setup ✅

- [ ] **3.1.1** XAMPP MySQL running
  - [ ] MySQL service started in XAMPP Control Panel
  - [ ] Can access phpMyAdmin at http://localhost/phpmyadmin
  - [ ] Database `upload_bridge_license` exists

- [ ] **3.1.2** XAMPP Apache running
  - [ ] Apache service started in XAMPP Control Panel
  - [ ] Can access http://localhost

- [ ] **3.1.3** License Server Running
  - [ ] Laravel server running: `php artisan serve`
  - [ ] Health check returns OK: `curl http://localhost:8000/api/v2/health`
  - [ ] No errors in `storage/logs/laravel.log`

- [ ] **3.1.4** Database Migrations Complete
  - [ ] All migrations ran successfully
  - [ ] Tables exist: `users`, `subscriptions`, `licenses`, `devices`
  - [ ] Test user created: `test@example.com` / `password123`

---

### Test Category 2: Upload Bridge Application Launch ✅

- [ ] **3.2.1** Application Starts
  - [ ] Run `python main.py` or launch EXE
  - [ ] Application window appears
  - [ ] No crash on startup
  - [ ] No console errors

- [ ] **3.2.2** Login Dialog Appears (First Launch)
  - [ ] Login dialog shown on first launch
  - [ ] Three tabs visible: "Email/Password", "Magic Link", "OAuth"
  - [ ] No errors in application logs

- [ ] **3.2.3** Server Connection Check
  - [ ] Application attempts to connect to `http://localhost:8000`
  - [ ] Connection successful (no error messages)
  - [ ] Health check endpoint accessible from app

---

### Test Category 3: Email/Password Authentication ✅

- [ ] **3.3.1** Email/Password Login - Valid Credentials
  - [ ] Enter email: `test@example.com`
  - [ ] Enter password: `password123`
  - [ ] Click "Login"
  - [ ] Loading indicator appears
  - [ ] Login successful
  - [ ] Main window opens
  - [ ] License validated

- [ ] **3.3.2** Email/Password Login - Invalid Credentials
  - [ ] Enter invalid email or password
  - [ ] Click "Login"
  - [ ] Error message shown: "Invalid email or password"
  - [ ] Login dialog remains open
  - [ ] Can retry login

- [ ] **3.3.3** Email/Password Login - Empty Fields
  - [ ] Leave email or password empty
  - [ ] Click "Login"
  - [ ] Validation error shown
  - [ ] Login blocked

- [ ] **3.3.4** Email/Password Login - Network Error
  - [ ] Stop license server
  - [ ] Attempt login
  - [ ] Network error shown: "Connection failed" or similar
  - [ ] Appropriate error message displayed

---

### Test Category 4: Magic Link Authentication ✅

- [ ] **4.1** Magic Link Request
  - [ ] Go to "Magic Link" tab
  - [ ] Enter email: `test@example.com`
  - [ ] Click "Send Magic Link"
  - [ ] Message shown: "Magic link sent to your email"
  - [ ] Email received (if SMTP configured)
  - [ ] Link in email opens application
  - [ ] Login successful

- [ ] **4.2** Magic Link - Invalid Email
  - [ ] Enter invalid email format
  - [ ] Click "Send Magic Link"
  - [ ] Validation error shown

- [ ] **4.3** Magic Link - Email Not Found
  - [ ] Enter non-existent email
  - [ ] Click "Send Magic Link"
  - [ ] Error message shown (or success message for security)

---

### Test Category 5: License Validation ✅

- [ ] **5.1** License Check After Login
  - [ ] After successful login
  - [ ] License status retrieved
  - [ ] License information displayed (plan, expiry, features)
  - [ ] Features enabled based on license

- [ ] **5.2** License Validation - Valid License
  - [ ] User has active subscription
  - [ ] License validation returns "ACTIVE"
  - [ ] All features available
  - [ ] License expiry date shown correctly

- [ ] **5.3** License Validation - Expired License
  - [ ] User has expired subscription
  - [ ] License validation returns "EXPIRED"
  - [ ] Appropriate message shown
  - [ ] Features disabled or limited
  - [ ] Reactivation prompt shown

- [ ] **5.4** License Validation - No License
  - [ ] User has no subscription
  - [ ] License validation returns "INVALID" or "NO_LICENSE"
  - [ ] Appropriate message shown
  - [ ] Features limited
  - [ ] Subscription prompt shown

- [ ] **5.5** License Validation - Offline Grace Period
  - [ ] Login successfully (online)
  - [ ] Close application
  - [ ] Disconnect internet
  - [ ] Launch application
  - [ ] App works offline (within 7-day grace period)
  - [ ] License status shown from cache

---

### Test Category 6: Application Features ✅

- [ ] **6.1** Pattern Upload
  - [ ] Can load pattern files
  - [ ] Pattern preview works
  - [ ] Pattern upload to device works
  - [ ] No errors during upload

- [ ] **6.2** WiFi Upload
  - [ ] WiFi upload feature accessible
  - [ ] Device discovery works
  - [ ] WiFi upload successful
  - [ ] No errors during upload

- [ ] **6.3** Media Upload
  - [ ] Media upload feature accessible
  - [ ] Media conversion works
  - [ ] Media upload successful
  - [ ] No errors during upload

- [ ] **6.4** Device Management
  - [ ] Device list displays correctly
  - [ ] Device connection works
  - [ ] Device information shown
  - [ ] Device management features work

---

### Test Category 7: License Status Dialog ✅

- [ ] **7.1** View License Status
  - [ ] Menu → License → View Status
  - [ ] License status dialog appears
  - [ ] Shows: Status, Plan, Expiry, Features
  - [ ] Information is accurate

- [ ] **7.2** Reactivate License
  - [ ] Click "Reactivate Account" button
  - [ ] Login dialog appears
  - [ ] Can re-authenticate
  - [ ] License status updates

- [ ] **7.3** Logout
  - [ ] Click "Logout" button
  - [ ] Confirmation dialog appears (if applicable)
  - [ ] Session cleared
  - [ ] Login dialog appears on next launch

---

### Test Category 8: Error Handling ✅

- [ ] **8.1** Server Unavailable
  - [ ] Stop license server
  - [ ] Attempt login
  - [ ] Appropriate error message shown
  - [ ] Graceful failure (no crash)

- [ ] **8.2** Invalid Server Response
  - [ ] Mock invalid response from server
  - [ ] Application handles gracefully
  - [ ] Error message shown
  - [ ] No crash

- [ ] **8.3** SSL Certificate Errors (if applicable)
  - [ ] Test with invalid certificate
  - [ ] Appropriate error shown
  - [ ] Application continues (or blocks appropriately)

- [ ] **8.4** Token Expiration
  - [ ] Wait for token to expire
  - [ ] Attempt API call
  - [ ] Token refresh triggered automatically
  - [ ] Or re-authentication required

---

### Test Category 9: Performance & Stability ✅

- [ ] **9.1** Application Startup Time
  - [ ] Launch application
  - [ ] Startup time acceptable (< 5 seconds)
  - [ ] No hang or freeze

- [ ] **9.2** Memory Usage
  - [ ] Check memory usage during normal operation
  - [ ] Memory usage reasonable (< 500 MB)
  - [ ] No memory leaks (check over time)

- [ ] **9.3** CPU Usage
  - [ ] Check CPU usage during normal operation
  - [ ] CPU usage reasonable (< 50% idle)
  - [ ] No excessive CPU usage

- [ ] **9.4** Long Running Session
  - [ ] Keep application running for 1+ hour
  - [ ] No crashes or errors
  - [ ] Features still work after extended use
  - [ ] Memory usage stable

---

### Test Category 10: Edge Cases ✅

- [ ] **10.1** Multiple Device Registrations
  - [ ] Login on Device 1
  - [ ] Login on Device 2
  - [ ] Both devices work correctly
  - [ ] Device limits respected (if applicable)

- [ ] **10.2** Rapid Login/Logout
  - [ ] Login quickly
  - [ ] Logout immediately
  - [ ] Login again
  - [ ] No race conditions
  - [ ] All operations complete successfully

- [ ] **10.3** Network Interruption During Login
  - [ ] Start login process
  - [ ] Disconnect network mid-way
  - [ ] Appropriate error shown
  - [ ] Can retry after reconnection

- [ ] **10.4** Concurrent Sessions
  - [ ] Login on multiple instances (if allowed)
  - [ ] Both sessions work independently
  - [ ] Or appropriate restriction shown

---

## Step 4: Testing Scenarios

### Scenario 1: First-Time User Flow

1. Launch application
2. Login dialog appears
3. Enter email: `test@example.com`
4. Enter password: `password123`
5. Click "Login"
6. Login successful
7. Main window opens
8. License validated
9. All features available
10. ✅ **Result**: Complete flow works

---

### Scenario 2: Returning User Flow

1. Launch application (after previous login)
2. Check for cached token
3. If token valid and within grace period:
   - Main window opens immediately
4. If token expired:
   - Login dialog appears
   - Re-authentication required
5. ✅ **Result**: Caching and re-authentication work

---

### Scenario 3: Offline Usage Flow

1. Login successfully (online)
2. Close application
3. Disconnect internet
4. Launch application
5. App works offline (within 7-day grace period)
6. After 7 days:
   - Re-authentication required
   - Online connection required
7. ✅ **Result**: Offline grace period works

---

### Scenario 4: License Expiration Flow

1. Login with user who has expiring license
2. License validated
3. Wait for license to expire (or manually expire in database)
4. Restart application
5. License validation fails
6. Appropriate message shown
7. Reactivation prompt displayed
8. ✅ **Result**: License expiration handled correctly

---

## Step 5: Test Data Setup

### Create Test Users in Database

**Using Artisan Tinker**:
```powershell
php artisan tinker
```

```php
// Test User 1: Active License
$user1 = \App\Models\User::create([
    'name' => 'Active User',
    'email' => 'active@example.com',
    'password' => bcrypt('password123'),
    'email_verified_at' => now(),
]);

// Create active subscription
\App\Models\Subscription::create([
    'user_id' => $user1->id,
    'plan' => 'monthly',
    'status' => 'active',
    'expires_at' => now()->addMonth(),
]);

// Test User 2: Expired License
$user2 = \App\Models\User::create([
    'name' => 'Expired User',
    'email' => 'expired@example.com',
    'password' => bcrypt('password123'),
    'email_verified_at' => now(),
]);

\App\Models\Subscription::create([
    'user_id' => $user2->id,
    'plan' => 'monthly',
    'status' => 'expired',
    'expires_at' => now()->subDay(),
]);

// Test User 3: No License
$user3 = \App\Models\User::create([
    'name' => 'No License User',
    'email' => 'nolicense@example.com',
    'password' => bcrypt('password123'),
    'email_verified_at' => now(),
]);
```

---

## Step 6: Debugging Tips

### Check License Server Logs

```powershell
# View Laravel logs
cat storage\logs\laravel.log

# Or tail logs in real-time
Get-Content storage\logs\laravel.log -Wait
```

### Check Upload Bridge Logs

**Logs Location**:
- Windows: `%USERPROFILE%\.upload_bridge\logs\`
- Or: `apps/upload-bridge/logs/`

### Test API Endpoints Directly

**Health Check**:
```powershell
curl http://localhost:8000/api/v2/health
```

**Login Endpoint**:
```powershell
curl -X POST http://localhost:8000/api/v2/auth/login `
  -H "Content-Type: application/json" `
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "device_id": "DEVICE_TEST",
    "device_name": "Test Device"
  }'
```

**License Validation**:
```powershell
curl -X POST http://localhost:8000/api/v2/license/validate `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -d '{
    "device_id": "DEVICE_TEST"
  }'
```

---

## Step 7: Common Issues & Solutions

### Issue 1: License Server Not Starting

**Symptoms**: `php artisan serve` fails

**Solutions**:
- Check PHP version: `php -v` (need 8.1+)
- Check port 8000 is available
- Try different port: `php artisan serve --port=8001`
- Check `.env` file exists and has `APP_KEY`

---

### Issue 2: Database Connection Failed

**Symptoms**: Migrations fail, "Access denied"

**Solutions**:
- Check MySQL is running in XAMPP
- Verify database credentials in `.env`
- Check database exists: `upload_bridge_license`
- Verify user has permissions: `root` user should work
- Check MySQL port: `3306` (default)

---

### Issue 3: Application Can't Connect to Server

**Symptoms**: Connection timeout, network error

**Solutions**:
- Verify server is running: `curl http://localhost:8000/api/v2/health`
- Check firewall allows localhost connections
- Verify `LICENSE_SERVER_URL` environment variable is set
- Check `config/app_config.yaml` has correct URL
- Test with browser: http://localhost:8000

---

### Issue 4: Login Fails with "Invalid Credentials"

**Symptoms**: Login returns 401 or "Invalid credentials"

**Solutions**:
- Verify user exists in database
- Check password is hashed correctly (use `bcrypt()`)
- Verify email is correct (case-sensitive)
- Check database: `SELECT * FROM users WHERE email = 'test@example.com';`
- Test API directly with curl

---

### Issue 5: License Validation Fails

**Symptoms**: License status returns "INVALID" or "NO_LICENSE"

**Solutions**:
- Check user has subscription: `SELECT * FROM subscriptions WHERE user_id = ?;`
- Verify subscription status is "active"
- Check subscription hasn't expired
- Verify license validation endpoint works with curl

---

## Step 8: Test Report Template

### Test Session Information

- **Date**: _______________
- **Tester**: _______________
- **License Server URL**: `http://localhost:8000`
- **License Server Version**: _______________
- **Upload Bridge Version**: `3.0.0`
- **OS**: _______________
- **Python Version**: _______________
- **PHP Version**: _______________

### Test Results Summary

| Category | Total | Passed | Failed | Skipped |
|----------|-------|--------|--------|---------|
| License Server Setup | ___ | ___ | ___ | ___ |
| Application Launch | ___ | ___ | ___ | ___ |
| Email/Password Auth | ___ | ___ | ___ | ___ |
| Magic Link Auth | ___ | ___ | ___ | ___ |
| License Validation | ___ | ___ | ___ | ___ |
| Application Features | ___ | ___ | ___ | ___ |
| License Status Dialog | ___ | ___ | ___ | ___ |
| Error Handling | ___ | ___ | ___ | ___ |
| Performance | ___ | ___ | ___ | ___ |
| Edge Cases | ___ | ___ | ___ | ___ |
| **TOTAL** | **___** | **___** | **___** | **___** |

### Issues Found

| # | Issue | Severity | Category | Status |
|---|-------|----------|----------|--------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

### Notes

- _______________
- _______________
- _______________

---

## Step 9: Quick Start Commands

### License Server

```powershell
# Start server
cd apps\web-dashboard
php artisan serve

# Run migrations
php artisan migrate --force

# Create test user
php artisan tinker
>>> \App\Models\User::create(['name' => 'Test', 'email' => 'test@example.com', 'password' => bcrypt('password123'), 'email_verified_at' => now()]);

# View logs
cat storage\logs\laravel.log
```

### Upload Bridge

```powershell
# Run application
cd apps\upload-bridge
python main.py

# Or run EXE
.\dist\UploadBridge.exe

# Set environment variable
$env:LICENSE_SERVER_URL = "http://localhost:8000"
```

---

## Summary

This guide provides comprehensive end-to-end manual testing for the entire Upload Bridge application with the license system running locally via XAMPP/MySQL.

**Key Testing Areas**:
1. ✅ License server setup and configuration
2. ✅ Application launch and initial setup
3. ✅ Authentication (email/password, magic link, OAuth)
4. ✅ License validation and management
5. ✅ Application features with license checks
6. ✅ Error handling and edge cases
7. ✅ Performance and stability
8. ✅ Offline grace period
9. ✅ License status and management UI
10. ✅ Multi-device scenarios

**Estimated Testing Time**: 4-6 hours for complete coverage

---

**Last Updated**: 2025-01-27  
**Version**: 3.0.0
