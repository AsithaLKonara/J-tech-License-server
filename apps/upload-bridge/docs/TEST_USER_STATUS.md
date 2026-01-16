# Test User Status - Local Development

## ✅ Test User Created Successfully

**Email:** `test@example.com`  
**Password:** `testpassword123`

**Status:**
- ✅ User account created
- ✅ Active subscription (monthly plan)
- ✅ Active license (monthly plan)
- ✅ License server running on `http://127.0.0.1:8000`

## ⚠️ Current Issue: Device Limit

The test user has a **device limit of 1**, and there's already a device registered from a previous login.

### Solutions

#### Option 1: Login Without Device ID (Recommended for Testing)

**In Upload Bridge:**
- The app should handle this automatically
- You can login and it will manage device registration

**Via API:**
```powershell
# Login without device_id
$body = '{"email":"test@example.com","password":"testpassword123"}'
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/auth/login" -Method POST -Body $body -ContentType "application/json"
```

#### Option 2: Reset Database (Fresh Start)

```powershell
cd apps\web-dashboard
php artisan migrate:fresh --seed
```

This will:
- Delete all existing devices
- Recreate test user with fresh subscription/license
- Reset device count to 0

#### Option 3: Increase Device Limit for Testing

Edit the entitlement or modify the monthly plan to allow more devices during testing.

## ✅ Testing with Upload Bridge

1. **Start License Server:**
   ```powershell
   cd apps\web-dashboard
   php artisan serve --host=127.0.0.1 --port=8000
   ```

2. **Start Upload Bridge:**
   ```powershell
   cd apps\upload-bridge
   python main.py
   ```

3. **Login Dialog will appear:**
   - Email: `test@example.com`
   - Password: `testpassword123`

4. **Expected Behavior:**
   - ✅ Login succeeds
   - ✅ License validation passes
   - ✅ Application opens
   - ✅ License status shows: ACTIVE

## 📋 Quick Verification

**Check if test user exists:**
```powershell
cd apps\web-dashboard
php create-test-user.php
```

**Reset everything (fresh start):**
```powershell
cd apps\web-dashboard
php artisan migrate:fresh --seed
```

**Expected Output:**
```
Plans created: monthly, annual, lifetime
Test user created: test@example.com / testpassword123
Test user subscription: ACTIVE (monthly plan)
Test user license: ACTIVE
Super-admin created: admin@example.com / admin123
```

## 🎯 Next Steps

1. **Reset database** (if you want fresh device count):
   ```powershell
   cd apps\web-dashboard
   php artisan migrate:fresh --seed
   ```

2. **Start Upload Bridge** and login with:
   - Email: `test@example.com`
   - Password: `testpassword123`

3. **Verify license is active** in the application

---

**Status:** ✅ Test user ready - Use Upload Bridge to login (it handles device registration automatically)
