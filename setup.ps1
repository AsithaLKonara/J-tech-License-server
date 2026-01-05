# Web Dashboard Setup Script for Windows
# Run this script to set up the Laravel web dashboard

Write-Host "Upload Bridge Web Dashboard Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Composer is installed
Write-Host "Checking for Composer..." -ForegroundColor Yellow
try {
    $composerVersion = composer --version 2>&1
    Write-Host "Composer found: $composerVersion" -ForegroundColor Green
} catch {
    Write-Host "Composer not found!" -ForegroundColor Red
    Write-Host "Please install Composer from https://getcomposer.org/download/" -ForegroundColor Yellow
    Write-Host "Or use: choco install composer" -ForegroundColor Yellow
    exit 1
}

# Check if PHP is installed
Write-Host "Checking for PHP..." -ForegroundColor Yellow
try {
    $phpVersion = php -v 2>&1 | Select-Object -First 1
    Write-Host "PHP found: $phpVersion" -ForegroundColor Green
} catch {
    Write-Host "PHP not found!" -ForegroundColor Red
    Write-Host "Please install PHP 8.1+ from https://www.php.net/downloads.php" -ForegroundColor Yellow
    exit 1
}

# Install Composer dependencies
Write-Host ""
Write-Host "Installing Composer dependencies..." -ForegroundColor Yellow
composer install
if ($LASTEXITCODE -ne 0) {
    Write-Host "Composer install failed!" -ForegroundColor Red
    exit 1
}
Write-Host "Dependencies installed successfully!" -ForegroundColor Green

# Create .env file if it doesn't exist
Write-Host ""
Write-Host "Setting up .env file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host ".env file created from .env.example" -ForegroundColor Green
    } else {
        Write-Host ".env.example not found. Creating basic .env file..." -ForegroundColor Yellow
        @"
APP_NAME="Upload Bridge"
APP_ENV=local
APP_KEY=
APP_DEBUG=true
APP_URL=http://localhost

DB_CONNECTION=sqlite
DB_DATABASE=database/database.sqlite
"@ | Out-File -FilePath ".env" -Encoding UTF8
        Write-Host ".env file created" -ForegroundColor Green
    }
} else {
    Write-Host ".env file already exists" -ForegroundColor Yellow
}

# Generate application key
Write-Host ""
Write-Host "Generating application key..." -ForegroundColor Yellow
php artisan key:generate
if ($LASTEXITCODE -ne 0) {
    Write-Host "Key generation failed!" -ForegroundColor Red
    exit 1
}
Write-Host "Application key generated!" -ForegroundColor Green

# Create SQLite database if using SQLite
Write-Host ""
Write-Host "Setting up database..." -ForegroundColor Yellow
$dbPath = "database/database.sqlite"
if (-not (Test-Path $dbPath)) {
    New-Item -ItemType File -Path $dbPath -Force | Out-Null
    Write-Host "SQLite database file created" -ForegroundColor Green
} else {
    Write-Host "Database file already exists" -ForegroundColor Yellow
}

# Run migrations
Write-Host ""
Write-Host "Running database migrations..." -ForegroundColor Yellow
php artisan migrate --force
if ($LASTEXITCODE -ne 0) {
    Write-Host "Migrations failed!" -ForegroundColor Red
    Write-Host "Please check your database configuration in .env" -ForegroundColor Yellow
    exit 1
}
Write-Host "Migrations completed!" -ForegroundColor Green

# Set storage permissions (Windows usually handles this automatically)
Write-Host ""
Write-Host "Checking storage permissions..." -ForegroundColor Yellow
$storageDirs = @("storage", "storage/app", "storage/framework", "storage/framework/cache", "storage/framework/sessions", "storage/framework/views", "storage/logs", "bootstrap/cache")
foreach ($dir in $storageDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "Storage directories ready" -ForegroundColor Green

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file and configure:" -ForegroundColor White
Write-Host "   - Database credentials" -ForegroundColor Gray
Write-Host "   - Stripe API keys" -ForegroundColor Gray
Write-Host "   - SMTP settings" -ForegroundColor Gray
Write-Host "   - APP_URL" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Create admin user:" -ForegroundColor White
Write-Host "   php artisan tinker" -ForegroundColor Gray
Write-Host "   Then run:" -ForegroundColor Gray
Write-Host "   \App\Models\User::create([..." -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start development server:" -ForegroundColor White
Write-Host "   php artisan serve" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Access at: http://localhost:8000" -ForegroundColor White
Write-Host ""
