# Migration and Seeding Script
# Runs Laravel migrations and seeders for the web-dashboard

param(
    [switch]$Fresh,
    [switch]$Seed,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "Laravel Migration and Seeding Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to web-dashboard directory
$webDashboardPath = "apps\web-dashboard"
if (-not (Test-Path $webDashboardPath)) {
    Write-Host "Error: web-dashboard directory not found!" -ForegroundColor Red
    Write-Host "Expected path: $webDashboardPath" -ForegroundColor Yellow
    exit 1
}

Push-Location $webDashboardPath

try {
    # Check if .env exists
    if (-not (Test-Path ".env")) {
        Write-Host "Warning: .env file not found!" -ForegroundColor Yellow
        if (Test-Path ".env.example") {
            Write-Host "Copying .env.example to .env..." -ForegroundColor Yellow
            Copy-Item ".env.example" ".env"
            Write-Host "Please configure .env file with your database settings!" -ForegroundColor Yellow
            Write-Host "See MYSQL_DATABASE_SETUP.md for instructions." -ForegroundColor Yellow
            exit 1
        } else {
            Write-Host "Error: .env.example not found either!" -ForegroundColor Red
            exit 1
        }
    }

    # Check database connection
    Write-Host "Checking database connection..." -ForegroundColor Yellow
    $dbConnection = php artisan tinker --execute="DB::connection()->getPdo(); exit;" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Cannot connect to database!" -ForegroundColor Red
        Write-Host "Please check your .env file configuration." -ForegroundColor Yellow
        Write-Host "See MYSQL_DATABASE_SETUP.md for setup instructions." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "Database connection: OK" -ForegroundColor Green
    Write-Host ""

    # Run migrations
    if ($Fresh) {
        if ($Force -or (Read-Host "This will drop all tables. Continue? (y/N)") -eq "y") {
            Write-Host "Running fresh migrations (dropping all tables)..." -ForegroundColor Yellow
            if ($Seed) {
                php artisan migrate:fresh --seed
            } else {
                php artisan migrate:fresh
            }
        } else {
            Write-Host "Cancelled." -ForegroundColor Yellow
            exit 0
        }
    } else {
        Write-Host "Running migrations..." -ForegroundColor Yellow
        php artisan migrate
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Migrations failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "Migrations completed successfully!" -ForegroundColor Green
    Write-Host ""

    # Run seeders (if not already run with --fresh --seed)
    if ($Seed -and -not ($Fresh)) {
        Write-Host "Running seeders..." -ForegroundColor Yellow
        php artisan db:seed
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: Seeding failed!" -ForegroundColor Red
            exit 1
        }
        Write-Host "Seeding completed successfully!" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host "Migration and seeding complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  - Verify data: php artisan tinker" -ForegroundColor White
    Write-Host "  - Start development server: php artisan serve" -ForegroundColor White

} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}
