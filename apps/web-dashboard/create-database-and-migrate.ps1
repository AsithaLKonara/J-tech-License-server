# Complete Database Setup and Migration Script
# Creates database and runs all migrations

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Upload Bridge - Database Setup & Migration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
if (-not (Test-Path .env)) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path vendor)) {
    Write-Host "ERROR: Composer dependencies not installed!" -ForegroundColor Red
    Write-Host "Please run: composer install" -ForegroundColor Yellow
    exit 1
}

# Read database config from .env
$envContent = Get-Content .env -Raw
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

# Check if MySQL is available
$mysqlAvailable = $false
if (Get-Command mysql -ErrorAction SilentlyContinue) {
    $mysqlAvailable = $true
    Write-Host "✅ MySQL client found" -ForegroundColor Green
} else {
    Write-Host "⚠️  MySQL client not found in PATH" -ForegroundColor Yellow
    Write-Host "   You may need to create the database manually" -ForegroundColor Yellow
}

# Try to create database if MySQL is available
if ($mysqlAvailable) {
    Write-Host ""
    Write-Host "Creating database '$dbName'..." -ForegroundColor Yellow
    
    $createDbSql = "CREATE DATABASE IF NOT EXISTS $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    
    if ($dbPass) {
        $result = & mysql -h $dbHost -P $dbPort -u $dbUser -p$dbPass -e $createDbSql 2>&1
    } else {
        $result = & mysql -h $dbHost -P $dbPort -u $dbUser -e $createDbSql 2>&1
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database created successfully" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Could not create database automatically" -ForegroundColor Yellow
        Write-Host "   Error: $result" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please create the database manually:" -ForegroundColor Yellow
        Write-Host "   mysql -u $dbUser -p -e `"CREATE DATABASE $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`"" -ForegroundColor Cyan
        Write-Host ""
        $continue = Read-Host "Continue with migrations anyway? (y/n)"
        if ($continue -ne 'y' -and $continue -ne 'Y') {
            exit 1
        }
    }
} else {
    Write-Host ""
    Write-Host "Please create the database manually:" -ForegroundColor Yellow
    Write-Host "   mysql -u $dbUser -p -e `"CREATE DATABASE $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`"" -ForegroundColor Cyan
    Write-Host ""
    $continue = Read-Host "Have you created the database? (y/n)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        Write-Host "Exiting. Please create the database first." -ForegroundColor Red
        exit 1
    }
}

# Generate app key if needed
Write-Host ""
Write-Host "Checking application key..." -ForegroundColor Yellow
$envContent = Get-Content .env -Raw
if ($envContent -match 'APP_KEY=\s*$' -or $envContent -notmatch 'APP_KEY=base64:') {
    Write-Host "Generating application key..." -ForegroundColor Yellow
    php artisan key:generate
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to generate application key!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Application key generated" -ForegroundColor Green
} else {
    Write-Host "✅ Application key already set" -ForegroundColor Green
}

# Run migrations
Write-Host ""
Write-Host "Running migrations..." -ForegroundColor Yellow
php artisan migrate --force

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ Migrations completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    $runSeeders = Read-Host "Do you want to run seeders (test data)? (y/n)"
    if ($runSeeders -eq 'y' -or $runSeeders -eq 'Y') {
        Write-Host "Running seeders..." -ForegroundColor Yellow
        php artisan db:seed
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Seeders completed!" -ForegroundColor Green
        }
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Setup Complete!" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Start server: php artisan serve" -ForegroundColor White
    Write-Host "2. Test API: curl http://localhost:8000/api/v2/health" -ForegroundColor White
    Write-Host "3. Run tests: cd ../../tests && npm run test:automated" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "❌ Migrations failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "1. Database doesn't exist - create it first" -ForegroundColor White
    Write-Host "2. Wrong database credentials in .env" -ForegroundColor White
    Write-Host "3. Database user doesn't have permissions" -ForegroundColor White
    Write-Host "4. MySQL not running" -ForegroundColor White
    Write-Host ""
    Write-Host "Check logs: storage/logs/laravel.log" -ForegroundColor Yellow
    exit 1
}
