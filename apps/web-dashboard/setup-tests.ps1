# Setup and Run E2E Tests Script
# This script sets up the test environment and runs Dusk tests

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "E2E Testing Setup and Execution" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if PHP is installed
Write-Host "Checking PHP installation..." -ForegroundColor Yellow
try {
    $phpVersion = php --version 2>&1
    Write-Host "PHP found: $($phpVersion -split "`n" | Select-Object -First 1)" -ForegroundColor Green
} catch {
    Write-Host "PHP is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install PHP 8.1+ first. See INSTALL_PHP.md for instructions." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Quick install options:" -ForegroundColor Cyan
    Write-Host "1. Using Winget: winget install PHP.PHP" -ForegroundColor White
    Write-Host "2. Download from: https://windows.php.net/download/" -ForegroundColor White
    Write-Host "3. Or use XAMPP/Laragon" -ForegroundColor White
    exit 1
}

# Check if Composer is installed
Write-Host ""
Write-Host "Checking Composer installation..." -ForegroundColor Yellow
try {
    $composerVersion = composer --version 2>&1
    Write-Host "Composer found: $($composerVersion -split "`n" | Select-Object -First 1)" -ForegroundColor Green
} catch {
    Write-Host "Composer is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Installing Composer..." -ForegroundColor Yellow
    
    # Try to install via winget
    try {
        winget install Composer.Composer
        Write-Host "Composer installed. Please restart your terminal and run this script again." -ForegroundColor Green
        exit 0
    } catch {
        Write-Host "Failed to install Composer automatically." -ForegroundColor Red
        Write-Host "Please install Composer manually from: https://getcomposer.org/download/" -ForegroundColor Yellow
        exit 1
    }
}

# Navigate to web-dashboard directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$dashboardPath = Join-Path $scriptPath "web-dashboard"

if (-not (Test-Path $dashboardPath)) {
    Write-Host "Error: web-dashboard directory not found at $dashboardPath" -ForegroundColor Red
    exit 1
}

Set-Location $dashboardPath
Write-Host ""
Write-Host "Working directory: $dashboardPath" -ForegroundColor Cyan

# Install Composer dependencies
Write-Host ""
Write-Host "Installing Composer dependencies..." -ForegroundColor Yellow
composer install --no-interaction
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install Composer dependencies." -ForegroundColor Red
    exit 1
}
Write-Host "Dependencies installed successfully." -ForegroundColor Green

# Install Dusk
Write-Host ""
Write-Host "Installing Laravel Dusk..." -ForegroundColor Yellow
php artisan dusk:install --no-interaction
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install Dusk. Continuing anyway..." -ForegroundColor Yellow
}

# Setup test environment
Write-Host ""
Write-Host "Setting up test environment..." -ForegroundColor Yellow

# Create .env from .env.dusk.local if it doesn't exist
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.dusk.local") {
        Copy-Item ".env.dusk.local" ".env"
        Write-Host "Created .env from .env.dusk.local" -ForegroundColor Green
    } else {
        Write-Host "Warning: .env.dusk.local not found. Creating basic .env..." -ForegroundColor Yellow
        @"
APP_ENV=testing
APP_DEBUG=true
APP_KEY=
DB_CONNECTION=sqlite
DB_DATABASE=database/database.sqlite
"@ | Out-File -FilePath ".env" -Encoding UTF8
    }
}

# Generate app key if not set
$envContent = Get-Content ".env" -Raw
if ($envContent -notmatch "APP_KEY=base64:") {
    Write-Host "Generating application key..." -ForegroundColor Yellow
    php artisan key:generate
}

# Create SQLite database
$dbPath = "database/database.sqlite"
if (-not (Test-Path $dbPath)) {
    Write-Host "Creating SQLite database..." -ForegroundColor Yellow
    New-Item -ItemType File -Path $dbPath -Force | Out-Null
    Write-Host "Database created." -ForegroundColor Green
}

# Run migrations
Write-Host ""
Write-Host "Running database migrations..." -ForegroundColor Yellow
php artisan migrate --force
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to run migrations." -ForegroundColor Red
    exit 1
}
Write-Host "Migrations completed." -ForegroundColor Green

# Check if ChromeDriver is available
Write-Host ""
Write-Host "Checking ChromeDriver..." -ForegroundColor Yellow
try {
    $chromeDriver = Get-Command chromedriver -ErrorAction Stop
    Write-Host "ChromeDriver found." -ForegroundColor Green
} catch {
    Write-Host "ChromeDriver not found. Dusk will attempt to download it automatically." -ForegroundColor Yellow
}

# Run tests
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running E2E Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

php artisan dusk

$testExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($testExitCode -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
} else {
    Write-Host "Some tests failed. Check output above." -ForegroundColor Red
    Write-Host "Screenshots (if any) are in: tests/Browser/screenshots/" -ForegroundColor Yellow
    Write-Host "Console logs (if any) are in: tests/Browser/console/" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan

exit $testExitCode
