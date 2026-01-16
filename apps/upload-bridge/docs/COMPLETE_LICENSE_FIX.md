# Complete License Validation Fix

## Problem
Getting error when starting Upload Bridge:
```
License validation failed:
Unauthorized

Please ensure you have an active paid plan
```

## Root Causes Identified

1. **Device Fingerprint Mismatch** - License was bound to a previous device
2. **Missing/Inactive Subscription** - No active subscription found
3. **Missing/Inactive License** - No active license found
4. **User Status** - User status not ACTIVE
5. **Device Limit** - Too many devices registered

## Complete Fix Script

**Run this to fix ALL issues:**
```powershell
cd apps\web-dashboard
php fix-all-license-issues.php
```

**What it does:**
- ✅ Sets user status to ACTIVE
- ✅ Creates/fixes active subscription
- ✅ Creates/fixes active license
- ✅ Clears device fingerprint (allows new device binding)
- ✅ Deletes all existing devices
- ✅ Creates/fixes active entitlement
- ✅ Sets max_devices to 5 for testing

**Expected Output:**
```
=== Complete License Fix (All Issues) ===

✅ User: test@example.com
✅ User status: ACTIVE
✅ Fixed subscription
✅ Fixed license (cleared device fingerprint)
✅ Deleted X device(s)
✅ Fixed entitlement

✅ All issues fixed!
   - User: ACTIVE
   - Subscription: active
   - License: active (no device fingerprint)
   - Devices: cleared
   - Entitlement: active (5 devices max)

✅ Ready to use with Upload Bridge!
```

## Individual Fix Scripts

### Fix Device Fingerprint Only
```powershell
cd apps\web-dashboard
php reset-license-fingerprint.php
```

### Fix License Only
```powershell
cd apps\web-dashboard
php fix-test-user-license.php
```

### Clear Devices Only
```powershell
cd apps\web-dashboard
php clear-devices.php
```

## Verification

**After running fix script, test:**
```powershell
# Login
$body = '{"email":"test@example.com","password":"testpassword123","device_id":"TEST"}'
$login = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/auth/login" -Method POST -Body $body -ContentType "application/json"

# Verify License
$headers = @{ Authorization = "Bearer $($login.session_token)" }
$verify = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/license/verify" -Method POST -Body '{"device_fingerprint":"NEW"}' -ContentType "application/json" -Headers $headers

# Should return:
# Status: ACTIVE
# Plan: monthly
```

## Using with Upload Bridge

1. **Run fix script:**
   ```powershell
   cd apps\web-dashboard
   php fix-all-license-issues.php
   ```

2. **Start Upload Bridge:**
   ```powershell
   cd apps\upload-bridge
   python main.py
   ```

3. **Login:**
   - Email: `test@example.com`
   - Password: `testpassword123`

4. **Expected:**
   - ✅ Login succeeds
   - ✅ License validation passes
   - ✅ Status: ACTIVE
   - ✅ Application opens

## Common Issues & Solutions

### Issue: "Device fingerprint mismatch"
**Solution:**
```powershell
php reset-license-fingerprint.php
```

### Issue: "No active subscription"
**Solution:**
```powershell
php fix-all-license-issues.php
```

### Issue: "Device limit reached"
**Solution:**
```powershell
php clear-devices.php
```

### Issue: "User not found"
**Solution:**
```powershell
php artisan db:seed --class=DatabaseSeeder
```

## Quick Reset (Everything)

**Complete fresh start:**
```powershell
cd apps\web-dashboard
php artisan migrate:fresh --seed
php fix-all-license-issues.php
```

This will:
1. Reset all tables
2. Seed test user
3. Fix all license issues
4. Clear device fingerprint
5. Set max devices to 5

## Test Credentials

- **Email:** `test@example.com`
- **Password:** `testpassword123`
- **Subscription:** Active monthly plan
- **License:** Active monthly license
- **Max Devices:** 5 (for testing)

---

**Status:** ✅ Fixed - All scripts available  
**Main Fix Script:** `apps/web-dashboard/fix-all-license-issues.php`
