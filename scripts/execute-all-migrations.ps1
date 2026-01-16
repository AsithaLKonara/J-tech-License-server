# Comprehensive Migration and Seeding Script
# This script runs everything and saves output to a log file

$ErrorActionPreference = "Continue"
$logFile = "C:\Users\asith\Documents\upload_bridge\migration-execution.log"

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $logFile -Value $logMessage
}

Write-Log "=========================================="
Write-Log "Starting Complete Migration Process"
Write-Log "=========================================="

# Navigate to web-dashboard
$webDashboardPath = "C:\Users\asith\Documents\upload_bridge\apps\web-dashboard"
if (-not (Test-Path $webDashboardPath)) {
    Write-Log "ERROR: web-dashboard directory not found!"
    exit 1
}

Push-Location $webDashboardPath
Write-Log "Changed to directory: $(Get-Location)"

# Check .env file
if (-not (Test-Path ".env")) {
    Write-Log "ERROR: .env file not found!"
    Pop-Location
    exit 1
}

Write-Log "Checking database configuration..."
$envContent = Get-Content ".env" -Raw
if ($envContent -match "DB_CONNECTION=mysql" -and $envContent -match "DB_PORT=3307") {
    Write-Log "Database configuration: OK (MySQL on port 3307)"
} else {
    Write-Log "WARNING: Database configuration may not be correct"
}

# Test database connection
Write-Log "Testing database connection..."
try {
    $testResult = & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -P 3307 -e "SELECT 1;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Database connection: OK"
    } else {
        Write-Log "WARNING: Database connection test returned code: $LASTEXITCODE"
    }
} catch {
    Write-Log "WARNING: Could not test database connection: $_"
}

# Step 1: Run Migrations
Write-Log ""
Write-Log "=========================================="
Write-Log "STEP 1: Running Migrations"
Write-Log "=========================================="

$migrationOutput = php artisan migrate --force 2>&1
$migrationExitCode = $LASTEXITCODE

foreach ($line in $migrationOutput) {
    Write-Log $line
}

if ($migrationExitCode -eq 0) {
    Write-Log "Migrations completed successfully!"
} else {
    Write-Log "ERROR: Migrations failed with exit code: $migrationExitCode"
    # Continue anyway to check what was created
}

# Check what tables exist
Write-Log ""
Write-Log "Checking created tables..."
$tables = & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -P 3307 upload_bridge -e "SHOW TABLES;" 2>&1
foreach ($table in $tables) {
    if ($table -and $table -notmatch "Tables_in") {
        Write-Log "  Table found: $table"
    }
}

# Step 2: Run Seeders
Write-Log ""
Write-Log "=========================================="
Write-Log "STEP 2: Running Seeders"
Write-Log "=========================================="

$seederOutput = php artisan db:seed 2>&1
$seederExitCode = $LASTEXITCODE

foreach ($line in $seederOutput) {
    Write-Log $line
}

if ($seederExitCode -eq 0) {
    Write-Log "Seeders completed successfully!"
} else {
    Write-Log "WARNING: Seeders returned exit code: $seederExitCode"
}

# Step 3: Check Migration Status
Write-Log ""
Write-Log "=========================================="
Write-Log "STEP 3: Checking Migration Status"
Write-Log "=========================================="

$statusOutput = php artisan migrate:status 2>&1
foreach ($line in $statusOutput) {
    Write-Log $line
}

# Step 4: Verify Seeded Data
Write-Log ""
Write-Log "=========================================="
Write-Log "STEP 4: Verifying Seeded Data"
Write-Log "=========================================="

$userCount = & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -P 3307 upload_bridge -e "SELECT COUNT(*) as count FROM users;" 2>&1
Write-Log "Users in database: $userCount"

$entitlementCount = & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -P 3307 upload_bridge -e "SELECT COUNT(*) as count FROM entitlements;" 2>&1
Write-Log "Entitlements in database: $entitlementCount"

$users = & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -P 3307 upload_bridge -e "SELECT email, is_admin FROM users;" 2>&1
Write-Log "User details:"
foreach ($user in $users) {
    if ($user -and $user -notmatch "email") {
        Write-Log "  $user"
    }
}

# Final Summary
Write-Log ""
Write-Log "=========================================="
Write-Log "MIGRATION PROCESS COMPLETE"
Write-Log "=========================================="
Write-Log "Log file saved to: $logFile"
Write-Log ""

Pop-Location
