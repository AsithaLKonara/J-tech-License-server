# Setup Local Environment for E2E Testing
# Creates .env file for web dashboard with MySQL configuration

$ErrorActionPreference = "Stop"
$projectRoot = (Get-Item $PSScriptRoot).Parent.FullName
$webDashboardDir = Join-Path $projectRoot "apps\web-dashboard"
$envFile = Join-Path $webDashboardDir ".env"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Local E2E Testing Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env already exists
if (Test-Path $envFile) {
    Write-Host "⚠️  .env file already exists at: $envFile" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite it? (y/n)"
    if ($overwrite -ne 'y' -and $overwrite -ne 'Y') {
        Write-Host "Keeping existing .env file" -ForegroundColor Green
        exit 0
    }
    Write-Host "Backing up existing .env to .env.backup..." -ForegroundColor Yellow
    Copy-Item $envFile "$envFile.backup" -Force
}

Write-Host "Creating .env file for local testing..." -ForegroundColor Yellow

# Create .env content
$envContent = @"
APP_NAME="Upload Bridge"
APP_ENV=local
APP_KEY=
APP_DEBUG=true
APP_URL=http://localhost:8000

LOG_CHANNEL=stack
LOG_DEPRECATIONS_CHANNEL=null
LOG_LEVEL=debug

# Database Configuration (MySQL for local testing)
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=upload_bridge
DB_USERNAME=root
DB_PASSWORD=

# Broadcast Configuration
BROADCAST_DRIVER=log
CACHE_DRIVER=file
FILESYSTEM_DISK=local
QUEUE_CONNECTION=sync
SESSION_DRIVER=file
SESSION_LIFETIME=120

# Mail Configuration (for local testing - can use mailtrap or log)
MAIL_MAILER=smtp
MAIL_HOST=smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS="noreply@uploadbridge.local"
MAIL_FROM_NAME="${APP_NAME}"

# Stripe Configuration (for testing - use test keys)
STRIPE_KEY=pk_test_placeholder
STRIPE_SECRET=sk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder
STRIPE_PRICE_MONTHLY=price_placeholder
STRIPE_PRICE_ANNUAL=price_placeholder
STRIPE_PRICE_LIFETIME=price_placeholder

# Redis (optional for local testing)
REDIS_HOST=127.0.0.1
REDIS_PASSWORD=null
REDIS_PORT=6379

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Session Configuration
SESSION_SECURE_COOKIE=false
"@

# Write .env file
$envContent | Out-File -FilePath $envFile -Encoding UTF8 -NoNewline
Write-Host "✅ .env file created at: $envFile" -ForegroundColor Green

# Prompt for database password if needed
Write-Host ""
Write-Host "Database Configuration:" -ForegroundColor Yellow
Write-Host "  Host: 127.0.0.1" -ForegroundColor White
Write-Host "  Port: 3306" -ForegroundColor White
Write-Host "  Database: upload_bridge" -ForegroundColor White
Write-Host "  Username: root" -ForegroundColor White
$dbPassword = Read-Host "  Password (press Enter if no password)" -AsSecureString
if ($dbPassword.Length -gt 0) {
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($dbPassword)
    $plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    (Get-Content $envFile) -replace 'DB_PASSWORD=', "DB_PASSWORD=$plainPassword" | Set-Content $envFile
    Write-Host "✅ Database password configured" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Environment setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Generate APP_KEY: cd apps\web-dashboard && php artisan key:generate" -ForegroundColor White
Write-Host "2. Create database: mysql -u root -p -e 'CREATE DATABASE upload_bridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'" -ForegroundColor White
Write-Host "3. Run migrations: cd apps\web-dashboard && php artisan migrate --force" -ForegroundColor White
Write-Host "4. Seed test data: cd apps\web-dashboard && php artisan db:seed --class=TestDataSeeder" -ForegroundColor White
Write-Host ""
