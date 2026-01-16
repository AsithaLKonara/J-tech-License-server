# Test Credentials for Local Development

## Primary Test User (Recommended)

**Email:** `test@example.com`  
**Password:** `testpassword123`

### Account Details
- **Name:** Test User
- **Status:** ACTIVE
- **Email Verified:** Yes
- **Subscription:** ACTIVE (Monthly plan - expires in 30 days)
- **License:** ACTIVE (Monthly plan)
- **Features:**
  - `pattern_upload`
  - `firmware_generation`
  - `device_management`

### Setup Instructions

1. **Ensure License Server is running:**
   ```powershell
   cd apps\web-dashboard
   php artisan serve --host=127.0.0.1 --port=8000
   ```

2. **Run Database Seeder:**
   ```powershell
   cd apps\web-dashboard
   php artisan db:seed --class=DatabaseSeeder
   ```

   **Expected Output:**
   ```
   Plans created: monthly, annual, lifetime
   Test user created: test@example.com / testpassword123
   Test user subscription: ACTIVE (monthly plan)
   Test user license: ACTIVE
   Super-admin created: admin@example.com / admin123
   ```

3. **Start Upload Bridge:**
   ```powershell
   cd apps\upload-bridge
   python main.py
   ```

4. **Login:**
   - Email: `test@example.com`
   - Password: `testpassword123`

### Testing Login via API

**PowerShell:**
```powershell
$loginBody = @{
    email = "test@example.com"
    password = "testpassword123"
    device_id = "TEST_DEVICE_$(Get-Date -Format 'yyyyMMddHHmmss')"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v2/auth/login" `
    -Method POST -Body $loginBody -ContentType "application/json"

$json = $response.Content | ConvertFrom-Json
$token = $json.session_token
Write-Host "Token: $token"
```

**Check License Info:**
```powershell
$headers = @{
    Authorization = "Bearer $token"
}

$licenseResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v2/license/info" `
    -Method GET -Headers $headers

$licenseResponse.Content
```

---

## Additional Test Users

### Super Admin
- **Email:** `admin@example.com`
- **Password:** `admin123`
- **Role:** SUPER_ADMIN
- **Status:** ACTIVE

### Test Users (from TestDataSeeder)
- **user1@test.com** / `password123` - Monthly plan
- **user2@test.com** / `password123` - Annual plan
- **user3@test.com** / `password123` - Lifetime plan
- **admin@test.com** / `password123` - Admin role
- **expired@test.com** / `password123` - Expired subscription (for testing)

---

## Troubleshooting

### Issue: Device Limit Reached

**Error:** `{"error":"Device limit reached","max_devices":1,"current_devices":1}`

**Solution:** Use a different `device_id` or delete existing devices:

```powershell
# Delete devices via API (requires admin token)
# Or reset database:
cd apps\web-dashboard
php artisan migrate:fresh --seed
```

### Issue: User Not Found

**Solution:** Run seeder again:
```powershell
cd apps\web-dashboard
php artisan db:seed --class=DatabaseSeeder
```

### Issue: License Not Active

**Check License Status:**
```powershell
# Via tinker (if available)
php artisan tinker

# In tinker:
$user = App\Models\User::where('email', 'test@example.com')->first();
$license = App\Models\License::where('user_id', $user->id)->first();
echo "License Status: " . $license->status;
```

**Recreate License:**
```powershell
php artisan db:seed --class=DatabaseSeeder
```

---

## Verification Checklist

- [ ] License server running on `http://127.0.0.1:8000`
- [ ] Health endpoint returns 200: `http://127.0.0.1:8000/api/v2/health`
- [ ] Test user exists in database
- [ ] Test user has active subscription
- [ ] Test user has active license
- [ ] Can login via API with credentials
- [ ] Can get license info with token
- [ ] Upload Bridge can connect to license server
- [ ] Upload Bridge login works with test credentials

---

**Last Updated:** 2024-01-XX  
**Status:** ✅ Test user ready for local development
