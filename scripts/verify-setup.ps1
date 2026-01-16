# Quick Verification Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DATABASE SETUP VERIFICATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking database tables..." -ForegroundColor Yellow
$tables = & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -P 3307 upload_bridge -e "SHOW TABLES;" 2>&1
$tableCount = 0
foreach ($line in $tables) {
    if ($line -and $line -notmatch "Tables_in" -and $line.Trim()) {
        Write-Host "  ✓ $line" -ForegroundColor Green
        $tableCount++
    }
}
Write-Host "Total tables: $tableCount" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking users..." -ForegroundColor Yellow
$userCount = & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -P 3307 upload_bridge -e "SELECT COUNT(*) as count FROM users;" 2>&1
foreach ($line in $userCount) {
    if ($line -match '\d+') {
        Write-Host "  Users in database: $line" -ForegroundColor Green
    }
}
Write-Host ""

Write-Host "Checking entitlements..." -ForegroundColor Yellow
$entitlementCount = & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -P 3307 upload_bridge -e "SELECT COUNT(*) as count FROM entitlements;" 2>&1
foreach ($line in $entitlementCount) {
    if ($line -match '\d+') {
        Write-Host "  Entitlements in database: $line" -ForegroundColor Green
    }
}
Write-Host ""

Write-Host "Checking user details..." -ForegroundColor Yellow
$users = & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -P 3307 upload_bridge -e "SELECT email, is_admin FROM users LIMIT 10;" 2>&1
foreach ($line in $users) {
    if ($line -and $line -notmatch "email" -and $line.Trim()) {
        Write-Host "  $line" -ForegroundColor White
    }
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VERIFICATION COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
