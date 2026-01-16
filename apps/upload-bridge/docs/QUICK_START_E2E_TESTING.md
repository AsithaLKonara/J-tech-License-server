# Quick Start: E2E Manual Testing

**Fast setup guide for testing Upload Bridge with local license server**

---

## Prerequisites Checklist

- [ ] XAMPP installed and running
- [ ] MySQL service started (XAMPP Control Panel)
- [ ] Apache service started (XAMPP Control Panel)
- [ ] Composer installed (`composer --version`)
- [ ] PHP 8.1+ installed (check: `php -v`)

---

## Step 1: Setup License Server (5 minutes)

### 1.1 Navigate to License Server

```powershell
cd apps\web-dashboard
```

### 1.2 Run Setup Script

```powershell
.\setup-xampp.ps1
```

This script will:
- ✅ Create `.env` file
- ✅ Check MySQL connection
- ✅ Create database `upload_bridge_license`
- ✅ Install Composer dependencies
- ✅ Generate application key
- ✅ Run database migrations
- ✅ Create test user (`test@example.com` / `password123`)

### 1.3 Start License Server

```powershell
php artisan serve
```

**Server starts at**: http://localhost:8000

### 1.4 Verify Server is Running

**Option A: PowerShell**
```powershell
curl http://localhost:8000/api/v2/health
```

**Option B: Browser**
Open: http://localhost:8000/api/v2/health

**Expected Response**:
```json
{
  "status": "ok",
  "timestamp": "2025-01-27T12:00:00Z"
}
```

---

## Step 2: Configure Upload Bridge (2 minutes)

### 2.1 Set Environment Variable

**PowerShell**:
```powershell
$env:LICENSE_SERVER_URL = "http://localhost:8000"
$env:AUTH_SERVER_URL = "http://localhost:8000"
```

**Or Update Config File**:
Edit `apps/upload-bridge/config/app_config.yaml`:
```yaml
auth_server_url: "http://localhost:8000"
license_server_url: "http://localhost:8000"
```

### 2.2 Test Connection

```powershell
cd apps\upload-bridge
.\scripts\test-local-connection.ps1
```

This verifies:
- ✅ Health check endpoint works
- ✅ Login endpoint is accessible
- ✅ CORS is configured

---

## Step 3: Run Upload Bridge Application

### 3.1 Launch Application

```powershell
cd apps\upload-bridge
python main.py
```

**Or if you have EXE built**:
```powershell
.\dist\UploadBridge.exe
```

### 3.2 First Launch - Login

When application starts:
1. Login dialog should appear
2. Go to "Email/Password" tab
3. Enter:
   - **Email**: `test@example.com`
   - **Password**: `password123`
4. Click "Login"
5. Should successfully authenticate
6. Main window should open

---

## Step 4: Basic Testing Checklist

### ✅ Test 1: Successful Login

- [ ] Login dialog appears
- [ ] Enter test credentials
- [ ] Click "Login"
- [ ] Loading indicator shows
- [ ] Login successful
- [ ] Main window opens
- [ ] No errors in console

### ✅ Test 2: Invalid Credentials

- [ ] Enter wrong password
- [ ] Click "Login"
- [ ] Error message shown: "Invalid email or password"
- [ ] Can retry login

### ✅ Test 3: License Status

- [ ] After successful login
- [ ] Menu → License → View Status
- [ ] License status dialog shows:
  - Status: ACTIVE
  - Plan: monthly (or whatever was created)
  - Expiry date
  - Features list

### ✅ Test 4: Application Features

- [ ] Pattern upload tab works
- [ ] WiFi upload tab works (if licensed)
- [ ] Media upload tab works (if licensed)
- [ ] All licensed features accessible

### ✅ Test 5: Offline Grace Period

- [ ] Login successfully (online)
- [ ] Close application
- [ ] Stop license server (`Ctrl+C` in server terminal)
- [ ] Disconnect internet (optional)
- [ ] Launch application again
- [ ] App should work offline (within 7-day grace period)
- [ ] License status shown from cache

---

## Step 5: Advanced Testing

See full testing guide: [E2E_MANUAL_TESTING_GUIDE.md](E2E_MANUAL_TESTING_GUIDE.md)

### Test Scenarios:
1. **Magic Link Authentication** - Test passwordless login
2. **License Expiration** - Test expired license handling
3. **Multiple Devices** - Test device limits
4. **Error Handling** - Test network failures, invalid responses
5. **Performance** - Test startup time, memory usage

---

## Troubleshooting

### Problem: License Server Won't Start

**Solution**:
```powershell
# Check PHP version
php -v

# Try different port
php artisan serve --port=8001

# Check if port 8000 is in use
netstat -ano | findstr :8000
```

---

### Problem: Database Connection Failed

**Solution**:
1. Check XAMPP MySQL is running
2. Verify database exists in phpMyAdmin
3. Check `.env` file has correct credentials:
   ```env
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_DATABASE=upload_bridge_license
   DB_USERNAME=root
   DB_PASSWORD=
   ```

---

### Problem: Application Can't Connect

**Solution**:
1. Verify server is running: `curl http://localhost:8000/api/v2/health`
2. Check environment variable is set:
   ```powershell
   echo $env:LICENSE_SERVER_URL
   ```
3. Test connection script:
   ```powershell
   .\scripts\test-local-connection.ps1
   ```

---

### Problem: Login Fails

**Solution**:
1. Check test user exists in database:
   ```sql
   SELECT * FROM users WHERE email = 'test@example.com';
   ```
2. Verify password is hashed (use `bcrypt()`)
3. Check server logs: `apps\web-dashboard\storage\logs\laravel.log`

---

## Quick Commands Reference

### License Server

```powershell
# Start server
cd apps\web-dashboard
php artisan serve

# View logs
Get-Content storage\logs\laravel.log -Wait

# Create test user (if needed)
php artisan tinker
>>> \App\Models\User::create(['name' => 'Test', 'email' => 'test@example.com', 'password' => bcrypt('password123'), 'email_verified_at' => now()]);

# Reset database (if needed)
php artisan migrate:fresh --seed
```

### Upload Bridge

```powershell
# Set environment variable
$env:LICENSE_SERVER_URL = "http://localhost:8000"

# Run application
python main.py

# Test connection
.\scripts\test-local-connection.ps1
```

---

## Test Credentials

**Default Test User**:
- **Email**: `test@example.com`
- **Password**: `password123`
- **License**: Active monthly subscription

**Create Additional Test Users**:
See [E2E_MANUAL_TESTING_GUIDE.md](E2E_MANUAL_TESTING_GUIDE.md) Step 5

---

## Next Steps

Once basic testing is complete:

1. ✅ **Full E2E Testing** - Follow complete guide
2. ✅ **Test All Authentication Methods** - Email/Password, Magic Link, OAuth
3. ✅ **Test License Scenarios** - Active, Expired, No License
4. ✅ **Test Error Handling** - Network failures, invalid responses
5. ✅ **Performance Testing** - Startup time, memory usage, long sessions
6. ✅ **Edge Cases** - Multiple devices, rapid login/logout, network interruptions

---

**Total Setup Time**: ~10 minutes  
**Basic Test Time**: ~15 minutes  
**Full E2E Test Time**: 4-6 hours

---

**Last Updated**: 2025-01-27  
**Version**: 3.0.0
