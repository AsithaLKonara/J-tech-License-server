# Manual Setup and Run Guide - License Server + Upload Bridge

Complete step-by-step guide to manually set up and run both the License Server (Laravel web-dashboard) and Upload Bridge desktop application.

---

## Prerequisites

### Required Software
- **PHP 8.1+** - [Download PHP](https://www.php.net/downloads.php)
- **Composer** - [Download Composer](https://getcomposer.org/download/)
- **Python 3.10+** - [Download Python](https://www.python.org/downloads/)
- **MySQL 5.7+** or **SQLite** - [Download MySQL](https://dev.mysql.com/downloads/) or SQLite (usually pre-installed)

### Verify Installation

**Check PHP:**
```powershell
php --version
# Should show PHP 8.1 or higher
```

**Check Composer:**
```powershell
composer --version
# Should show Composer version
```

**Check Python:**
```powershell
python --version
# Should show Python 3.10 or higher
```

---

## Part 1: License Server Setup (Laravel Web Dashboard)

### Step 1: Navigate to License Server Directory

```powershell
cd C:\Users\asith\Documents\upload_bridge\apps\web-dashboard
```

### Step 2: Install PHP Dependencies

```powershell
composer install
```

**Expected Output:**
- Downloads all Laravel dependencies
- Creates `vendor/` directory
- May take a few minutes

### Step 3: Create Environment File

**Check if `.env` exists:**
```powershell
if (Test-Path .env) { Write-Host ".env exists" } else { Write-Host "Creating .env from .env.example" }
```

**If `.env` doesn't exist, create it:**
```powershell
Copy-Item .env.example .env
```

### Step 4: Generate Application Key

```powershell
php artisan key:generate
```

**Expected Output:**
```
Application key set successfully.
```

### Step 5: Configure Database in `.env`

**Edit `.env` file:**
```powershell
notepad .env
```

**Update database configuration:**
```env
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=upload_bridge_license
DB_USERNAME=root
DB_PASSWORD=your_password_here
```

**For SQLite (easier for development):**
```env
DB_CONNECTION=sqlite
DB_DATABASE=C:\Users\asith\Documents\upload_bridge\apps\web-dashboard\database\database.sqlite
```

**If using SQLite, create database file:**
```powershell
New-Item -ItemType File -Path database\database.sqlite -Force
```

### Step 6: Run Database Migrations

**First, ensure database exists:**
```powershell
# For MySQL - create database manually or use:
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS upload_bridge_license;"
```

**Run migrations:**
```powershell
php artisan migrate
```

**Expected Output:**
```
Migration table created successfully.
Migrating: 2024_01_01_000001_create_users_table
Migrated:  2024_01_01_000001_create_users_table
...
```

**If migrations fail, reset and try again:**
```powershell
php artisan migrate:fresh
```

### Step 7: (Optional) Seed Test Data

**Create a test user:**
```powershell
php artisan tinker
```

**In tinker, run:**
```php
\App\Models\User::create([
    'name' => 'Test User',
    'email' => 'test@example.com',
    'password' => bcrypt('password'),
    'email_verified_at' => now(),
]);

\App\Models\Subscription::create([
    'user_id' => 1,
    'plan_id' => 1,
    'status' => 'active',
    'starts_at' => now(),
    'ends_at' => now()->addYear(),
]);
```

**Or use seeders:**
```powershell
php artisan db:seed
```

### Step 8: Start License Server

**Start Laravel development server:**
```powershell
php artisan serve --host=127.0.0.1 --port=8000
```

**Expected Output:**
```
Laravel development server started: http://127.0.0.1:8000
```

**Keep this terminal window open!** The server runs in this window.

### Step 9: Verify License Server is Running

**Open new PowerShell window and test:**
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v2/health" -UseBasicParsing
```

**Expected Output:**
- Status code: 200
- Response: `{"status":"ok"}`

**Or visit in browser:**
- Open: http://127.0.0.1:8000
- Should see Laravel welcome page or dashboard

---

## Part 2: Upload Bridge Desktop Application Setup

### Step 1: Navigate to Upload Bridge Directory

**Open a NEW PowerShell window** (keep license server running in first window):

```powershell
cd C:\Users\asith\Documents\upload_bridge\apps\upload-bridge
```

### Step 2: Create Python Virtual Environment (Recommended)

**Create virtual environment:**
```powershell
python -m venv venv
```

**Activate virtual environment:**
```powershell
.\venv\Scripts\Activate.ps1
```

**If you get execution policy error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: Install Python Dependencies

**Install requirements:**
```powershell
pip install -r requirements.txt
```

**Expected Output:**
- Downloads all Python packages
- Installs PySide6, requests, and other dependencies
- May take a few minutes

**Verify key packages:**
```powershell
python -c "import PySide6; import requests; print('Dependencies OK')"
```

### Step 4: Configure Upload Bridge to Use License Server

**Check configuration:**
```powershell
notepad config\app_config.yaml
```

**Verify `auth_server_url` is set:**
```yaml
auth_server_url: "http://localhost:8000"
```

**Or check `config\auth_config.yaml`:**
```yaml
auth_server_url: "http://localhost:8000"
license_server_url: "http://localhost:8000"
```

**Alternative: Set environment variable:**
```powershell
$env:LICENSE_SERVER_URL = "http://localhost:8000"
$env:AUTH_SERVER_URL = "http://localhost:8000"
```

### Step 5: Verify License Server Connection

**Test connection before starting app:**
```powershell
python -c "import requests; r = requests.get('http://127.0.0.1:8000/api/v2/health'); print(f'Status: {r.status_code}')"
```

**Expected Output:**
```
Status: 200
```

**If connection fails:**
- Check if license server is running (Step 8 of Part 1)
- Verify firewall isn't blocking port 8000
- Check if port 8000 is already in use: `netstat -an | findstr :8000`

### Step 6: Start Upload Bridge Application

**Run the application:**
```powershell
python main.py
```

**Or use bootstrap:**
```powershell
python bootstrap.py
```

**Expected Output:**
- Application window should open
- If not authenticated, login dialog will appear
- Enter credentials from test user created in Step 7 of Part 1

---

## Part 3: Complete Running Setup

### Terminal 1: License Server (Laravel)
```powershell
cd C:\Users\asith\Documents\upload_bridge\apps\web-dashboard
php artisan serve --host=127.0.0.1 --port=8000
```

### Terminal 2: Upload Bridge (Python)
```powershell
cd C:\Users\asith\Documents\upload_bridge\apps\upload-bridge
python main.py
```

---

## Troubleshooting

### Issue: License Server Won't Start

**Problem: Port 8000 already in use**
```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use different port
php artisan serve --port=8001
# Then update Upload Bridge config to use port 8001
```

**Problem: Database connection failed**
```powershell
# Check database credentials in .env
# Test MySQL connection:
mysql -u root -p -e "SHOW DATABASES;"

# For SQLite, check file exists:
Test-Path database\database.sqlite
```

**Problem: Migration errors**
```powershell
# Reset database:
php artisan migrate:fresh

# Or rollback and re-run:
php artisan migrate:rollback
php artisan migrate
```

### Issue: Upload Bridge Can't Connect to License Server

**Problem: Connection refused**
- Verify license server is running: `Invoke-WebRequest http://127.0.0.1:8000/api/v2/health`
- Check firewall settings
- Verify `auth_server_url` in config files

**Problem: Authentication fails**
- Check if test user exists in database
- Verify password is correct
- Check license server logs for errors

**Problem: License validation fails**
- Ensure user has active subscription
- Check license status in database
- Verify `licenses` table has active record

### Issue: Python Dependencies Missing

**Problem: Import errors**
```powershell
# Reinstall dependencies:
pip install --upgrade -r requirements.txt

# Install missing packages:
pip install PySide6 requests
```

**Problem: Virtual environment issues**
```powershell
# Recreate virtual environment:
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Quick Start Scripts

### Create Start Scripts

**`start-license-server.ps1`** (in `apps/web-dashboard/`):
```powershell
cd $PSScriptRoot
Write-Host "Starting License Server..." -ForegroundColor Green
php artisan serve --host=127.0.0.1 --port=8000
```

**`start-upload-bridge.ps1`** (in `apps/upload-bridge/`):
```powershell
cd $PSScriptRoot
Write-Host "Starting Upload Bridge..." -ForegroundColor Green
if (Test-Path venv\Scripts\Activate.ps1) {
    .\venv\Scripts\Activate.ps1
}
python main.py
```

**`start-all.ps1`** (in project root):
```powershell
Write-Host "Starting License Server and Upload Bridge..." -ForegroundColor Green

# Start License Server in background
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\apps\web-dashboard'; php artisan serve --host=127.0.0.1 --port=8000"

# Wait for server to start
Start-Sleep -Seconds 3

# Start Upload Bridge
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\apps\upload-bridge'; python main.py"

Write-Host "Both applications started!" -ForegroundColor Green
```

---

## Verification Checklist

### License Server Verification
- [ ] PHP and Composer installed
- [ ] Dependencies installed (`composer install`)
- [ ] `.env` file configured
- [ ] Database created and migrated
- [ ] Test user created
- [ ] Server starts on port 8000
- [ ] Health endpoint returns 200: `http://127.0.0.1:8000/api/v2/health`

### Upload Bridge Verification
- [ ] Python 3.10+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Config files have `auth_server_url: "http://localhost:8000"`
- [ ] Can connect to license server
- [ ] Application window opens
- [ ] Login dialog appears
- [ ] Can authenticate with test user

---

## Common Workflow

### Daily Development Workflow

1. **Start License Server:**
   ```powershell
   cd apps\web-dashboard
   php artisan serve --host=127.0.0.1 --port=8000
   ```

2. **In new terminal, start Upload Bridge:**
   ```powershell
   cd apps\upload-bridge
   python main.py
   ```

3. **Use the applications:**
   - Upload Bridge connects to license server automatically
   - Login when prompted
   - Application opens after successful authentication

### Stop Applications

- **License Server:** Press `Ctrl+C` in the terminal running `php artisan serve`
- **Upload Bridge:** Close the application window or press `Ctrl+C` if running in terminal

---

## Database Management

### View Users
```powershell
php artisan tinker
```
```php
\App\Models\User::all();
```

### Create Test Subscription
```php
$user = \App\Models\User::find(1);
\App\Models\Subscription::create([
    'user_id' => $user->id,
    'plan_id' => 1,
    'status' => 'active',
    'starts_at' => now(),
    'ends_at' => now()->addYear(),
]);
```

### Check License Status
```php
$user = \App\Models\User::find(1);
$user->subscriptions;
$user->licenses;
```

---

## Environment Variables

### License Server (.env)
```env
APP_NAME="Upload Bridge License Server"
APP_ENV=local
APP_KEY=base64:...
APP_DEBUG=true
APP_URL=http://localhost:8000

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=upload_bridge_license
DB_USERNAME=root
DB_PASSWORD=

STRIPE_KEY=
STRIPE_SECRET=
STRIPE_WEBHOOK_SECRET=

MAIL_MAILER=smtp
MAIL_HOST=mailhog
MAIL_PORT=1025
MAIL_USERNAME=null
MAIL_PASSWORD=null
MAIL_FROM_ADDRESS="noreply@uploadbridge.com"
```

### Upload Bridge (Environment or Config)
```powershell
$env:LICENSE_SERVER_URL = "http://localhost:8000"
$env:AUTH_SERVER_URL = "http://localhost:8000"
```

Or in `config/app_config.yaml`:
```yaml
auth_server_url: "http://localhost:8000"
```

---

## Next Steps

1. **Create test user account** via license server web interface
2. **Login to Upload Bridge** with test credentials
3. **Verify license validation** works correctly
4. **Start developing** your LED patterns!

---

**Last Updated:** 2024-01-XX  
**Status:** Complete manual setup guide
