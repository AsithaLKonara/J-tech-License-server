# Simple migration test script
$ErrorActionPreference = "Continue"

Write-Host "Starting migration test..." -ForegroundColor Cyan

# Change to web-dashboard directory
Push-Location "apps\web-dashboard"

try {
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    Write-Host "Running migrations..." -ForegroundColor Yellow
    
    # Run migrations and capture output
    $output = php artisan migrate 2>&1
    Write-Host $output
    
    Write-Host "`nChecking migration status..." -ForegroundColor Yellow
    $status = php artisan migrate:status 2>&1
    Write-Host $status
    
    Write-Host "`nMigration test complete!" -ForegroundColor Green
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
} finally {
    Pop-Location
}
