# Setup Database and Seed Test Data
# Creates database, runs migrations, and seeds test data

$ErrorActionPreference = "Stop"
$projectRoot = (Get-Item $PSScriptRoot).Parent.FullName
$webDashboardDir = Join-Path $projectRoot "apps\web-dashboard"
$envFile = Join-Path $webDashboardDir ".env"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Database Setup and Seeding" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check .env exists
if (-not (Test-Path $envFile)) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "   Please run: .\scripts\setup-local-env.ps1 first" -ForegroundColor Yellow
    exit 1
}

# Read database config
$envContent = Get-Content $envFile -Raw
$dbHost = if ($envContent -match 'DB_HOST=([^\r\n]+)') { $matches[1] } else { '127.0.0.1' }
$dbPort = if ($envContent -match 'DB_PORT=([^\r\n]+)') { $matches[1] } else { '3306' }
$dbName = if ($envContent -match 'DB_DATABASE=([^\r\n]+)') { $matches[1] } else { 'upload_bridge' }
$dbUser = if ($envContent -match 'DB_USERNAME=([^\r\n]+)') { $matches[1] } else { 'root' }
$dbPass = if ($envContent -match 'DB_PASSWORD=([^\r\n]+)') { $matches[1] } else { '' }

Write-Host "Database Configuration:" -ForegroundColor Yellow
Write-Host "  Host: $dbHost" -ForegroundColor White
Write-Host "  Port: $dbPort" -ForegroundColor White
Write-Host "  Database: $dbName" -ForegroundColor White
Write-Host "  User: $dbUser" -ForegroundColor White
Write-Host ""

# Check if database exists
Write-Host "Checking if database exists..." -ForegroundColor Yellow
$mysqlAvailable = Get-Command mysql -ErrorAction SilentlyContinue

if ($mysqlAvailable) {
    $dbExists = $false
    try {
        if ($dbPass) {
            $result = & mysql -h $dbHost -P $dbPort -u $dbUser -p$dbPass -e "SHOW DATABASES LIKE '$dbName';" 2>&1
        } else {
            $result = & mysql -h $dbHost -P $dbPort -u $dbUser -e "SHOW DATABASES LIKE '$dbName';" 2>&1
        }
        
        if ($result -match $dbName) {
            $dbExists = $true
            Write-Host "✅ Database '$dbName' exists" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  Could not check database (this is okay if MySQL client is not in PATH)" -ForegroundColor Yellow
    }
    
    if (-not $dbExists) {
        Write-Host "Creating database '$dbName'..." -ForegroundColor Yellow
        $createDbSql = "CREATE DATABASE IF NOT EXISTS $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        
        try {
            if ($dbPass) {
                & mysql -h $dbHost -P $dbPort -u $dbUser -p$dbPass -e $createDbSql 2>&1 | Out-Null
            } else {
                & mysql -h $dbHost -P $dbPort -u $dbUser -e $createDbSql 2>&1 | Out-Null
            }
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Database created successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠️  Could not create database automatically" -ForegroundColor Yellow
                Write-Host "   Please create it manually:" -ForegroundColor Yellow
                Write-Host "   mysql -u $dbUser -p -e `"CREATE DATABASE $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`"" -ForegroundColor Cyan
                $continue = Read-Host "Continue anyway? (y/n)"
                if ($continue -ne 'y' -and $continue -ne 'Y') {
                    exit 1
                }
            }
        } catch {
            Write-Host "⚠️  Could not create database: $_" -ForegroundColor Yellow
            Write-Host "   Please create it manually:" -ForegroundColor Yellow
            Write-Host "   mysql -u $dbUser -p -e `"CREATE DATABASE $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`"" -ForegroundColor Cyan
            $continue = Read-Host "Continue anyway? (y/n)"
            if ($continue -ne 'y' -and $continue -ne 'Y') {
                exit 1
            }
        }
    }
} else {
    Write-Host "⚠️  MySQL client not found in PATH" -ForegroundColor Yellow
    Write-Host "   Please create the database manually:" -ForegroundColor Yellow
    Write-Host "   mysql -u $dbUser -p -e `"CREATE DATABASE $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`"" -ForegroundColor Cyan
    Write-Host ""
    $continue = Read-Host "Have you created the database? (y/n)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        Write-Host "Exiting. Please create the database first." -ForegroundColor Red
        exit 1
    }
}

# Check APP_KEY
Write-Host ""
Write-Host "Checking APP_KEY..." -ForegroundColor Yellow
if ($envContent -match 'APP_KEY=\s*$' -or $envContent -notmatch 'APP_KEY=base64:') {
    Write-Host "Generating APP_KEY..." -ForegroundColor Yellow
    Push-Location $webDashboardDir
    php artisan key:generate
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to generate APP_KEY!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Write-Host "✅ APP_KEY generated" -ForegroundColor Green
    Pop-Location
} else {
    Write-Host "✅ APP_KEY already set" -ForegroundColor Green
}

# Check dependencies
Write-Host ""
Write-Host "Checking Composer dependencies..." -ForegroundColor Yellow
if (-not (Test-Path (Join-Path $webDashboardDir "vendor"))) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    Push-Location $webDashboardDir
    composer install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
    Pop-Location
} else {
    Write-Host "✅ Dependencies already installed" -ForegroundColor Green
}

# Run migrations
Write-Host ""
Write-Host "Running migrations..." -ForegroundColor Yellow
Push-Location $webDashboardDir
php artisan migrate --force

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Migrations failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "1. Database doesn't exist - create it first" -ForegroundColor White
    Write-Host "2. Wrong database credentials in .env" -ForegroundColor White
    Write-Host "3. Database user doesn't have permissions" -ForegroundColor White
    Write-Host "4. MySQL not running" -ForegroundColor White
    Pop-Location
    exit 1
}

Write-Host "✅ Migrations completed" -ForegroundColor Green
Pop-Location

# Seed test data
Write-Host ""
Write-Host "Seeding test data..." -ForegroundColor Yellow
Push-Location $webDashboardDir
php artisan db:seed --class=TestDataSeeder

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Test data seeded successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Seeding may have failed (check if data already exists)" -ForegroundColor Yellow
}
Pop-Location

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Database setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Test users created:" -ForegroundColor Yellow
Write-Host "  - admin@test.com / password123 (Admin)" -ForegroundColor White
Write-Host "  - user1@test.com / password123 (Monthly)" -ForegroundColor White
Write-Host "  - user2@test.com / password123 (Annual)" -ForegroundColor White
Write-Host "  - user3@test.com / password123 (Lifetime)" -ForegroundColor White
Write-Host "  - user4@test.com / password123 (No subscription)" -ForegroundColor White
Write-Host "  - user5@test.com / password123 (No subscription)" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start server: .\scripts\start-local-testing.ps1" -ForegroundColor White
Write-Host "2. Test API: .\scripts\test-e2e-communication.ps1" -ForegroundColor White
Write-Host "3. Verify setup: .\scripts\verify-complete-setup.ps1" -ForegroundColor White
Write-Host ""
