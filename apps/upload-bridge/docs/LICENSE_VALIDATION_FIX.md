# License Validation Fix - "Unauthorized" Error

## Problem
When trying to use Upload Bridge, you get:
```
License validation failed:
Unauthorized

Please ensure you have an active paid plan
```

## Root Cause
The license verification endpoint checks:
1. User status must be `ACTIVE`
2. Active subscription must exist (status: `active`, not expired)
3. Active license must exist (status: `active`, not expired)

Sometimes after database resets or migrations, the subscription/license relationship might not be properly linked.

## Solution

### Quick Fix Script

**Run the license fix script:**
```powershell
cd apps\web-dashboard
php fix-test-user-license.php
```

This script:
- ✅ Ensures user status is `ACTIVE`
- ✅ Creates/verifies active subscription
- ✅ Creates/verifies active license
- ✅ Links license to subscription
- ✅ Creates/verifies active entitlement
- ✅ Verifies all queries work correctly

**Expected Output:**
```
=== Fixing Test User License ===

✅ Found user: test@example.com
✅ Subscription exists: monthly - active
✅ License exists: monthly - active
✅ Entitlement exists: monthly - active

=== Verification ===
✅ activeSubscription() would return: monthly - active
✅ License query returns: monthly - active

✅ Done! Test user should now work with license verification.
```

### Alternative: Reset Everything

**Complete fresh start:**
```powershell
cd apps\web-dashboard
php artisan migrate:fresh --seed
```

This recreates:
- All tables
- Test user with active subscription
- Test user with active license
- All properly linked

## Verification

### Test API Endpoints

**1. Login:**
```powershell
$body = '{"email":"test@example.com","password":"testpassword123","device_id":"TEST_001"}'
$login = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/auth/login" -Method POST -Body $body -ContentType "application/json"
$token = $login.session_token
```

**2. Verify License:**
```powershell
$headers = @{ Authorization = "Bearer $token" }
$verifyBody = '{"device_fingerprint":"TEST_FINGERPRINT"}'
$verify = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/license/verify" -Method POST -Body $verifyBody -ContentType "application/json" -Headers $headers

# Should return:
# {
#   "status": "ACTIVE",
#   "plan": "monthly",
#   "features": [...],
#   ...
# }
```

**Expected Results:**
- ✅ Login: 200 OK
- ✅ License Verify: 200 OK
- ✅ Status: ACTIVE
- ✅ Plan: monthly

## How License Verification Works

### API Endpoint: `/api/v2/license/verify`

**Checks (in order):**
1. **User Authentication** - Must have valid JWT token
2. **User Status** - Must be `ACTIVE` (not SUSPENDED)
3. **Active Subscription** - Must exist with:
   - Status: `active`
   - Expires_at: null OR future date
4. **Active License** - Must exist with:
   - Status: `active` (case-insensitive: 'active' or 'ACTIVE')
   - Expires_at: null OR future date
   - Linked to subscription
5. **Device Fingerprint** - Optional, but if set, must match

### User Model Methods

**`activeSubscription()`** - Returns active subscription:
```php
->where('status', 'active')
->where(function ($query) {
    $query->whereNull('expires_at')
        ->orWhere('expires_at', '>', now());
})
->latest()
->first();
```

**License Query** - Returns active license:
```php
->whereIn('status', ['active', 'ACTIVE'])
->where(function ($query) {
    $query->whereNull('expires_at')
        ->orWhere('expires_at', '>', now());
})
->latest()
->first();
```

## Test User Setup

After running `fix-test-user-license.php`, the test user has:

**User:**
- Email: `test@example.com`
- Status: `ACTIVE`
- Role: `USER`

**Subscription:**
- Plan: `monthly`
- Status: `active`
- Expires: 30 days from now

**License:**
- Plan: `monthly`
- Status: `active`
- Linked to subscription
- Features: `pattern_upload`, `firmware_generation`, `device_management`
- Expires: 30 days from now

**Entitlement:**
- Plan: `monthly`
- Status: `active`
- Max Devices: 5 (for testing)
- Features: Same as license

## Troubleshooting

### Issue: Still Getting "Unauthorized"

**Check 1: User Status**
```php
$user = User::where('email', 'test@example.com')->first();
echo "Status: " . $user->status; // Should be "ACTIVE"
```

**Check 2: Subscription**
```php
$sub = $user->activeSubscription();
if (!$sub) {
    echo "❌ No active subscription";
} else {
    echo "✅ Subscription: {$sub->plan_type} - {$sub->status}";
}
```

**Check 3: License**
```php
$license = $user->licenses()
    ->whereIn('status', ['active', 'ACTIVE'])
    ->where(function ($query) {
        $query->whereNull('expires_at')
            ->orWhere('expires_at', '>', now());
    })
    ->first();
    
if (!$license) {
    echo "❌ No active license";
} else {
    echo "✅ License: {$license->plan} - {$license->status}";
}
```

**Solution:**
```powershell
cd apps\web-dashboard
php fix-test-user-license.php
```

### Issue: License Status Mismatch

**Problem:** License status might be stored as uppercase `'ACTIVE'` but query expects lowercase `'active'`.

**Solution:** The code handles both cases:
- License model uses `whereIn('status', ['active', 'ACTIVE'])`
- Case-insensitive check: `strtoupper($license->status) === 'ACTIVE'`

But ensure license is stored as lowercase `'active'` for consistency.

### Issue: Subscription Not Found

**Check:** The subscription must be linked to the user:
```php
$sub = Subscription::where('user_id', $user->id)
    ->where('status', 'active')
    ->first();
```

**Solution:** Run fix script or reseed:
```powershell
php artisan db:seed --class=DatabaseSeeder
```

## Quick Fix Commands

**Fix License:**
```powershell
cd apps\web-dashboard
php fix-test-user-license.php
```

**Reset Everything:**
```powershell
cd apps\web-dashboard
php artisan migrate:fresh --seed
```

**Clear Devices + Fix License:**
```powershell
cd apps\web-dashboard
php clear-devices.php
php fix-test-user-license.php
```

---

**Status:** ✅ Fixed - License validation working  
**Scripts:** 
- `apps/web-dashboard/fix-test-user-license.php` - Fixes license validation
- `apps/web-dashboard/clear-devices.php` - Clears devices
