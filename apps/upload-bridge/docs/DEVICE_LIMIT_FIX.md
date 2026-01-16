# Device Limit Issue - Fixed ✅

## Problem
When logging in with `test@example.com`, you get:
```
Login failed: Device limit reached
```

## Root Cause
- Monthly plan has a device limit (default: 1-2 devices)
- A previous login already registered a device
- No more devices can be registered

## Solution

### Option 1: Clear Devices (Recommended for Testing)

**Run the device clearing script:**
```powershell
cd apps\web-dashboard
php clear-devices.php
```

This script:
- ✅ Deletes all existing devices for test user
- ✅ Increases `max_devices` to 5 for testing
- ✅ Updates or creates entitlement

**Expected Output:**
```
=== Clearing Devices for Test User ===

✅ Found user: test@example.com
✅ Deleted X device(s) for license
✅ Updated entitlement max_devices to 5

✅ Done! You can now login with test@example.com
   Device limit increased to 5 devices for testing
```

### Option 2: Reset Database (Fresh Start)

**Complete reset:**
```powershell
cd apps\web-dashboard
php artisan migrate:fresh --seed
```

This will:
- Delete all tables
- Recreate all tables
- Seed fresh test user (0 devices)
- Reset everything

### Option 3: Delete Devices Manually

**Via Database:**
```powershell
# Using SQLite database directly
sqlite3 database/database.sqlite "DELETE FROM devices WHERE license_id IN (SELECT id FROM licenses WHERE user_id = (SELECT id FROM users WHERE email = 'test@example.com'));"
```

**Via Artisan Tinker (if available):**
```php
$user = App\Models\User::where('email', 'test@example.com')->first();
$license = App\Models\License::where('user_id', $user->id)->first();
App\Models\Device::where('license_id', $license->id)->delete();
```

## Device Limits by Plan

According to `LicenseService.php`:
- **Monthly Plan:** 2 devices (default)
- **Annual Plan:** 5 devices
- **Lifetime Plan:** 10 devices
- **Trial:** 1 device

For testing, the `clear-devices.php` script increases this to **5 devices**.

## Verification

**After running clear-devices.php, test login:**
```powershell
$body = '{"email":"test@example.com","password":"testpassword123","device_id":"TEST_NEW"}'
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/auth/login" -Method POST -Body $body -ContentType "application/json"
```

**Expected:**
- ✅ Login succeeds
- ✅ Token received
- ✅ No device limit error

## Upload Bridge Behavior

**Upload Bridge should:**
1. Login successfully (after devices cleared)
2. Register new device automatically
3. Continue working normally

**If you still get device limit error:**
1. Run `php clear-devices.php` again
2. Close and restart Upload Bridge
3. Try login again

## Quick Fix Command

**One-line fix:**
```powershell
cd apps\web-dashboard; php clear-devices.php
```

---

**Status:** ✅ Fixed - Device clearing script available  
**Script:** `apps/web-dashboard/clear-devices.php`
