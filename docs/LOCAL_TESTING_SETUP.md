# Local E2E Testing Setup Guide

Complete guide for setting up and running the Upload Bridge system locally for end-to-end testing.

## Overview

This guide sets up:
- **Web Dashboard** (Laravel) running on `http://localhost:8000`
- **Upload Bridge Desktop App** (Python) configured to connect to local server
- **MySQL Database** with test data seeded
- **E2E Test Suite** to verify all components communicate correctly

## Prerequisites

Before starting, ensure you have:

- **PHP 8.1+** installed and in PATH
- **Composer** installed and in PATH
- **MySQL 5.7+** or **MariaDB 10.3+** installed and running
- **Python 3.10+** installed and in PATH
- **Node.js 18+** (for E2E tests)
- **PowerShell 5.1+** (Windows) or Bash (Linux/Mac)

### Verify Prerequisites

Run the verification script:

```powershell
.\scripts\verify-setup.ps1
```

This will check all prerequisites and provide guidance on what's missing.

## Step-by-Step Setup

### Step 1: Setup Environment Configuration

Create the `.env` file for the web dashboard:

```powershell
.\scripts\setup-local-env.ps1
```

This script will:
- Create `.env` file with MySQL configuration
- Set `APP_URL=http://localhost:8000`
- Configure database connection
- Prompt for MySQL password if needed

**Manual Setup Alternative:**

If you prefer to create `.env` manually:

1. Navigate to `apps/web-dashboard/`
2. Create `.env` file (copy from example if available)
3. Set the following values:

```env
APP_NAME="Upload Bridge"
APP_ENV=local
APP_DEBUG=true
APP_URL=http://localhost:8000

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=upload_bridge
DB_USERNAME=root
DB_PASSWORD=your_password_here
```

### Step 2: Create MySQL Database

Create the database:

```sql
CREATE DATABASE upload_bridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**Using MySQL command line:**

```bash
mysql -u root -p -e "CREATE DATABASE upload_bridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

**Using MySQL Workbench or phpMyAdmin:**

1. Connect to MySQL server
2. Create new database named `upload_bridge`
3. Set charset to `utf8mb4` and collation to `utf8mb4_unicode_ci`

### Step 3: Install Dependencies

**Web Dashboard (Laravel):**

```powershell
cd apps\web-dashboard
composer install
```

**Upload Bridge (Python):**

```powershell
cd apps\upload-bridge
pip install -r requirements.txt
```

**E2E Tests (Node.js):**

```powershell
cd tests
npm install
```

### Step 4: Generate Application Key

```powershell
cd apps\web-dashboard
php artisan key:generate
```

This generates the `APP_KEY` required for Laravel encryption.

### Step 5: Run Database Migrations

```powershell
cd apps\web-dashboard
php artisan migrate --force
```

This creates all required database tables.

### Step 6: Seed Test Data

Seed the database with test users and subscriptions:

```powershell
cd apps\web-dashboard
php artisan db:seed --class=TestDataSeeder
```

**Test Users Created:**

- **Admin**: `admin@test.com` / `password123`
- **User 1**: `user1@test.com` / `password123` (Monthly subscription)
- **User 2**: `user2@test.com` / `password123` (Annual subscription)
- **User 3**: `user3@test.com` / `password123` (Lifetime subscription)
- **User 4**: `user4@test.com` / `password123` (No subscription)
- **User 5**: `user5@test.com` / `password123` (No subscription)

### Step 7: Verify Upload Bridge Configuration

The upload bridge should already be configured to use `http://localhost:8000`. Verify:

```yaml
# apps/upload-bridge/config/auth_config.yaml
auth_server_url: "http://localhost:8000"
license_server_url: "http://localhost:8000"
```

If needed, update these values to point to your local server.

## Running the System

### Start Web Dashboard

**Option 1: Using the orchestration script (recommended):**

```powershell
.\scripts\start-local-testing.ps1
```

This script will:
- Check all prerequisites
- Generate APP_KEY if needed
- Install dependencies if missing
- Start Laravel server on port 8000

**Option 2: Manual start:**

```powershell
cd apps\web-dashboard
php artisan serve --host=127.0.0.1 --port=8000
```

The server will be available at: `http://localhost:8000`

### Start Upload Bridge Desktop App

```powershell
cd apps\upload-bridge
python main.py
```

The app will automatically connect to `http://localhost:8000` for authentication and license validation.

### Stop Services

**Stop web dashboard:**

```powershell
.\scripts\stop-local-testing.ps1
```

Or press `Ctrl+C` in the terminal running the server.

## Testing

### Test API Endpoints

**Health Check:**

```powershell
curl http://localhost:8000/api/v2/health
```

**Expected Response:**

```json
{
  "status": "ok",
  "timestamp": "2025-01-27T12:00:00Z"
}
```

### Run E2E Communication Tests

**PowerShell script:**

```powershell
.\scripts\test-e2e-communication.ps1
```

**Node.js test suite:**

```powershell
cd tests
node run-test.js tests/e2e/local-e2e.test.js
```

Or using npm:

```powershell
cd tests
npm run test:e2e
```

### Test Desktop App Login

1. Start web dashboard: `.\scripts\start-local-testing.ps1`
2. Start upload bridge app: `cd apps\upload-bridge && python main.py`
3. When login dialog appears, use:
   - Email: `user1@test.com`
   - Password: `password123`
4. Verify license is validated and displayed

## Verification Checklist

After setup, verify:

- [ ] MySQL database `upload_bridge` exists
- [ ] Web dashboard runs on `http://localhost:8000`
- [ ] API health endpoint responds: `GET /api/v2/health`
- [ ] Test users can log in via web dashboard UI
- [ ] Upload Bridge app connects to `http://localhost:8000`
- [ ] Authentication works from desktop app
- [ ] License validation works from desktop app
- [ ] Device registration works
- [ ] E2E tests pass

## Troubleshooting

### Database Connection Issues

**Error: "SQLSTATE[HY000] [2002] No connection could be made"**

- Check MySQL is running: `mysql -u root -p`
- Verify database exists: `SHOW DATABASES;`
- Check `.env` database credentials

### Port 8000 Already in Use

**Error: "Address already in use"**

- Find process using port: `Get-NetTCPConnection -LocalPort 8000`
- Stop the process or use a different port
- Update `APP_URL` in `.env` if using different port

### APP_KEY Not Set

**Error: "No application encryption key has been specified"**

```powershell
cd apps\web-dashboard
php artisan key:generate
```

### Migrations Fail

**Error: "SQLSTATE[42S01]: Base table or view already exists"**

- Drop and recreate database
- Or run: `php artisan migrate:fresh --force`

### Test Data Not Seeded

**No test users available**

```powershell
cd apps\web-dashboard
php artisan db:seed --class=TestDataSeeder
```

### Upload Bridge Can't Connect

**Error: "Cannot connect to license server"**

- Verify web dashboard is running: `curl http://localhost:8000/api/v2/health`
- Check `auth_config.yaml` has correct URL
- Check firewall isn't blocking localhost connections

## Next Steps

After successful setup:

1. **Run complete E2E tests**: `.\scripts\test-e2e-communication.ps1`
2. **Test desktop app features**: Create patterns, export, flash to hardware
3. **Test license flows**: Login, license validation, device registration
4. **Test subscription flows**: Create subscriptions, validate licenses

## Additional Resources

- [Quick Start Guide](LOCAL_TESTING_QUICKSTART.md)
- [Web Dashboard Documentation](../apps/web-dashboard/docs/)
- [Upload Bridge Documentation](../apps/upload-bridge/docs/)

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs: `apps/web-dashboard/storage/logs/laravel.log`
3. Run verification: `.\scripts\verify-setup.ps1`
4. Check database: `mysql -u root -p upload_bridge`
