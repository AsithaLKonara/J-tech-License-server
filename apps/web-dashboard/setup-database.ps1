# Setup Database and Run Migrations
# This script sets up the local database and runs migrations

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Upload Bridge - Database Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please create .env file first." -ForegroundColor Yellow
    exit 1
}

# Check if PHP is available
$phpCheck = Get-Command php -ErrorAction SilentlyContinue
if (-not $phpCheck) {
    Write-Host "ERROR: PHP not found in PATH!" -ForegroundColor Red
    Write-Host "Please install PHP 8.1+ and add it to PATH." -ForegroundColor Yellow
    exit 1
}

Write-Host "PHP Version:" -ForegroundColor Green
php --version
Write-Host ""

# Check if composer dependencies are installed
if (-not (Test-Path vendor)) {
    Write-Host "Installing Composer dependencies..." -ForegroundColor Yellow
    if (Get-Command composer -ErrorAction SilentlyContinue) {
        composer install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Composer install failed!" -ForegroundColor Red
            Write-Host "Please run 'composer install' manually." -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "ERROR: Composer not found!" -ForegroundColor Red
        Write-Host "Please install Composer and run 'composer install' manually." -ForegroundColor Yellow
        Write-Host "Download from: https://getcomposer.org/download/" -ForegroundColor Cyan
        exit 1
    }
} else {
    Write-Host "Composer dependencies already installed." -ForegroundColor Green
}

# Generate application key if not set
Write-Host "Checking application key..." -ForegroundColor Yellow
$envContent = Get-Content .env -Raw
if ($envContent -match 'APP_KEY=\s*$' -or $envContent -notmatch 'APP_KEY=') {
    Write-Host "Generating application key..." -ForegroundColor Yellow
    php artisan key:generate
} else {
    Write-Host "Application key already set." -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Database Setup Instructions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Before running migrations, ensure:" -ForegroundColor Yellow
Write-Host "1. MySQL/MariaDB is running" -ForegroundColor White
Write-Host "2. Database 'upload_bridge' exists (or update DB_DATABASE in .env)" -ForegroundColor White
Write-Host "3. Database user has proper permissions" -ForegroundColor White
Write-Host ""

$createDb = Read-Host "Do you want to create the database? (y/n)"
if ($createDb -eq 'y' -or $createDb -eq 'Y') {
    Write-Host ""
    Write-Host "To create database, run in MySQL:" -ForegroundColor Yellow
    Write-Host "  CREATE DATABASE upload_bridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or use MySQL command line:" -ForegroundColor Yellow
    Write-Host "  mysql -u root -e 'CREATE DATABASE upload_bridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'" -ForegroundColor Cyan
    Write-Host ""
}

$runMigrations = Read-Host "Do you want to run migrations now? (y/n)"
if ($runMigrations -eq 'y' -or $runMigrations -eq 'Y') {
    Write-Host ""
    Write-Host "Running migrations..." -ForegroundColor Yellow
    php artisan migrate --force
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Migrations completed successfully!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        
        $runSeeders = Read-Host "Do you want to run seeders (test data)? (y/n)"
        if ($runSeeders -eq 'y' -or $runSeeders -eq 'Y') {
            Write-Host "Running seeders..." -ForegroundColor Yellow
            php artisan db:seed
            Write-Host "Seeders completed!" -ForegroundColor Green
        }
    } else {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "Migrations failed!" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "Common issues:" -ForegroundColor Yellow
        Write-Host "1. Database doesn't exist - create it first" -ForegroundColor White
        Write-Host "2. Wrong database credentials in .env" -ForegroundColor White
        Write-Host "3. Database user doesn't have permissions" -ForegroundColor White
        Write-Host "4. MySQL not running" -ForegroundColor White
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "To run migrations manually, use:" -ForegroundColor Yellow
    Write-Host "  php artisan migrate" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start the server: php artisan serve" -ForegroundColor White
Write-Host "2. Test API: curl http://localhost:8000/api/v2/health" -ForegroundColor White
Write-Host "3. Run tests: npm test (from tests directory)" -ForegroundColor White
Write-Host ""
