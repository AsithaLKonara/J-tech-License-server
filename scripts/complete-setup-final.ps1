# Complete Setup Script - Saves all output to file
$logFile = "C:\Users\asith\Documents\upload_bridge\complete-setup-results.txt"

function Write-ToLog {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Add-Content -Path $logFile -Value $logMessage
    Write-Host $logMessage
}

Write-ToLog "=========================================="
Write-ToLog "COMPLETE MIGRATION AND SEEDING SETUP"
Write-ToLog "=========================================="
Write-ToLog ""

$webDashboardPath = "C:\Users\asith\Documents\upload_bridge\apps\web-dashboard"
Push-Location $webDashboardPath

# Step 1: Migrations
Write-ToLog "[STEP 1] Running Migrations..."
$migrateOutput = php artisan migrate --force 2>&1 | Out-String
Write-ToLog $migrateOutput
Write-ToLog "Migration exit code: $LASTEXITCODE"
Write-ToLog ""

# Step 2: Check Tables
Write-ToLog "[STEP 2] Checking Database Tables..."
$tables = & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -P 3307 upload_bridge -e "SHOW TABLES;" 2>&1
foreach ($line in $tables) {
    if ($line -and $line -notmatch "Tables_in") {
        Write-ToLog "  Table: $line"
    }
}
Write-ToLog ""

# Step 3: Seeders
Write-ToLog "[STEP 3] Running Seeders..."
$seedOutput = php artisan db:seed 2>&1 | Out-String
Write-ToLog $seedOutput
Write-ToLog "Seeder exit code: $LASTEXITCODE"
Write-ToLog ""

# Step 4: Verify Data
Write-ToLog "[STEP 4] Verifying Seeded Data..."
$userCount = & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -P 3307 upload_bridge -e "SELECT COUNT(*) as count FROM users;" 2>&1
Write-ToLog "User count: $userCount"

$entitlementCount = & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -P 3307 upload_bridge -e "SELECT COUNT(*) as count FROM entitlements;" 2>&1
Write-ToLog "Entitlement count: $entitlementCount"

$users = & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -P 3307 upload_bridge -e "SELECT email, is_admin FROM users;" 2>&1
Write-ToLog "Users:"
foreach ($line in $users) {
    if ($line -and $line -notmatch "email") {
        Write-ToLog "  $line"
    }
}

Write-ToLog ""
Write-ToLog "=========================================="
Write-ToLog "SETUP COMPLETE!"
Write-ToLog "Results saved to: $logFile"
Write-ToLog "=========================================="

Pop-Location
