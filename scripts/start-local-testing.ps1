# Start Local E2E Testing Environment
# Starts web dashboard server and verifies all services are ready

$ErrorActionPreference = "Stop"
$projectRoot = (Get-Item $PSScriptRoot).Parent.FullName
$webDashboardDir = Join-Path $projectRoot "apps\web-dashboard"
$envFile = Join-Path $webDashboardDir ".env"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Local E2E Testing Environment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check PHP
$phpCheck = Get-Command php -ErrorAction SilentlyContinue
if (-not $phpCheck) {
    Write-Host "❌ PHP not found in PATH!" -ForegroundColor Red
    Write-Host "   Please install PHP 8.1+ and add it to PATH" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ PHP found: $(php -v | Select-Object -First 1)" -ForegroundColor Green

# Check Composer
$composerCheck = Get-Command composer -ErrorAction SilentlyContinue
if (-not $composerCheck) {
    Write-Host "❌ Composer not found in PATH!" -ForegroundColor Red
    Write-Host "   Please install Composer and add it to PATH" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Composer found: $(composer --version | Select-Object -First 1)" -ForegroundColor Green

# Check .env file
if (-not (Test-Path $envFile)) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "   Please run: .\scripts\setup-local-env.ps1" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ .env file found" -ForegroundColor Green

# Check APP_KEY
$envContent = Get-Content $envFile -Raw
if ($envContent -match 'APP_KEY=\s*$' -or $envContent -notmatch 'APP_KEY=base64:') {
    Write-Host "⚠️  APP_KEY not set. Generating..." -ForegroundColor Yellow
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

# Check if vendor directory exists
if (-not (Test-Path (Join-Path $webDashboardDir "vendor"))) {
    Write-Host "⚠️  Composer dependencies not installed. Installing..." -ForegroundColor Yellow
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
    Write-Host "✅ Composer dependencies installed" -ForegroundColor Green
}

# Check database connection
Write-Host ""
Write-Host "Checking database connection..." -ForegroundColor Yellow
Push-Location $webDashboardDir
try {
    php artisan db:show 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database connection successful" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Could not verify database connection" -ForegroundColor Yellow
        Write-Host "   Make sure MySQL is running and database 'upload_bridge' exists" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not verify database connection" -ForegroundColor Yellow
}
Pop-Location

# Check if port 8000 is available
Write-Host ""
Write-Host "Checking if port 8000 is available..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "⚠️  Port 8000 is already in use!" -ForegroundColor Yellow
    Write-Host "   Process: $($portInUse | Select-Object -First 1 | ForEach-Object { Get-Process -Id $_.OwningProcess | Select-Object -ExpandProperty ProcessName })" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        exit 1
    }
} else {
    Write-Host "✅ Port 8000 is available" -ForegroundColor Green
}

# Start Laravel server
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Laravel development server..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "API health check: http://localhost:8000/api/v2/health" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

Push-Location $webDashboardDir
php artisan serve --host=127.0.0.1 --port=8000
