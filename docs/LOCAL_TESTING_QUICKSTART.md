# Local E2E Testing Quick Start

Quick reference guide for setting up and running local E2E tests.

## Quick Setup (5 minutes)

### 1. Setup Environment

```powershell
.\scripts\setup-local-env.ps1
```

### 2. Create Database

```sql
CREATE DATABASE upload_bridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Or using command line:

```bash
mysql -u root -p -e "CREATE DATABASE upload_bridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 3. Install & Configure

```powershell
cd apps\web-dashboard
composer install
php artisan key:generate
php artisan migrate --force
php artisan db:seed --class=TestDataSeeder
```

### 4. Start Server

```powershell
.\scripts\start-local-testing.ps1
```

### 5. Test Connection

```powershell
.\scripts\test-e2e-communication.ps1
```

## Quick Commands

### Start Services

```powershell
# Start web dashboard
.\scripts\start-local-testing.ps1

# Start upload bridge app (in another terminal)
cd apps\upload-bridge
python main.py
```

### Stop Services

```powershell
# Stop web dashboard
.\scripts\stop-local-testing.ps1
```

### Run Tests

```powershell
# PowerShell E2E tests
.\scripts\test-e2e-communication.ps1

# Node.js E2E tests
cd tests
node run-test.js tests/e2e/local-e2e.test.js
```

### Verify Setup

```powershell
.\scripts\verify-setup.ps1
```

## Test Credentials

Use these credentials for testing:

| Email | Password | Subscription |
|-------|----------|--------------|
| `admin@test.com` | `password123` | Admin |
| `user1@test.com` | `password123` | Monthly |
| `user2@test.com` | `password123` | Annual |
| `user3@test.com` | `password123` | Lifetime |
| `user4@test.com` | `password123` | None |
| `user5@test.com` | `password123` | None |

## API Endpoints

Base URL: `http://localhost:8000`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/health` | GET | Health check |
| `/api/v2/auth/login` | POST | User login |
| `/api/v2/auth/refresh` | POST | Refresh token |
| `/api/v2/license/validate` | GET | Validate license |
| `/api/v2/license/info` | GET | Get license info |
| `/api/v2/devices/register` | POST | Register device |
| `/api/v2/devices` | GET | List devices |

## Quick Test

```powershell
# 1. Start server
.\scripts\start-local-testing.ps1

# 2. In another terminal, test login
$body = @{
    email = "user1@test.com"
    password = "password123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v2/auth/login" -Method POST -Body $body -ContentType "application/json"
```

## Troubleshooting

### Server won't start

```powershell
# Check if port is in use
Get-NetTCPConnection -LocalPort 8000

# Verify setup
.\scripts\verify-setup.ps1
```

### Database connection fails

```powershell
# Test MySQL connection
mysql -u root -p

# Check database exists
SHOW DATABASES;
```

### Tests fail

```powershell
# Verify server is running
curl http://localhost:8000/api/v2/health

# Check test data is seeded
cd apps\web-dashboard
php artisan tinker
>>> \App\Models\User::count()
```

## Full Documentation

For detailed setup instructions, see [LOCAL_TESTING_SETUP.md](LOCAL_TESTING_SETUP.md).
