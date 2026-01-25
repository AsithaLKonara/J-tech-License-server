# Quick script to run migrations
# Assumes database already exists

Write-Host "Running Laravel migrations..." -ForegroundColor Yellow

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    exit 1
}

# Generate app key if needed
$envContent = Get-Content .env -Raw
if ($envContent -match 'APP_KEY=\s*$' -or $envContent -notmatch 'APP_KEY=') {
    Write-Host "Generating application key..." -ForegroundColor Yellow
    php artisan key:generate
}

# Run migrations
Write-Host "Running migrations..." -ForegroundColor Yellow
php artisan migrate --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "Migrations completed successfully!" -ForegroundColor Green
} else {
    Write-Host "Migrations failed. Check database connection and credentials." -ForegroundColor Red
    exit 1
}
