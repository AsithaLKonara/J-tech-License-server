# MySQL Server Status Script for Windows
# This script checks MySQL service status and connection

param(
    [string]$ServiceName = "MySQL80"
)

Write-Host "MySQL Server Status" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host ""

# Check service status
Write-Host "Service Status:" -ForegroundColor Yellow
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if (-not $service) {
    Write-Host "  MySQL service '$ServiceName' not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "Available MySQL services:" -ForegroundColor Yellow
    $mysqlServices = Get-Service | Where-Object { $_.Name -like "*mysql*" }
    if ($mysqlServices) {
        $mysqlServices | ForEach-Object {
            $statusColor = if ($_.Status -eq 'Running') { 'Green' } else { 'Red' }
            Write-Host "  - $($_.Name): $($_.Status)" -ForegroundColor $statusColor
        }
    } else {
        Write-Host "  No MySQL services found." -ForegroundColor Red
    }
} else {
    $statusColor = if ($service.Status -eq 'Running') { 'Green' } else { 'Red' }
    Write-Host "  Service: $($service.Name)" -ForegroundColor White
    Write-Host "  Status: $($service.Status)" -ForegroundColor $statusColor
    Write-Host "  Display Name: $($service.DisplayName)" -ForegroundColor White
}

Write-Host ""

# Check port
Write-Host "Port Status:" -ForegroundColor Yellow
try {
    $result = Test-NetConnection -ComputerName localhost -Port 3306 -WarningAction SilentlyContinue
    if ($result.TcpTestSucceeded) {
        Write-Host "  Port 3306: Listening" -ForegroundColor Green
    } else {
        Write-Host "  Port 3306: Not accessible" -ForegroundColor Red
    }
} catch {
    Write-Host "  Port 3306: Could not test" -ForegroundColor Yellow
}

Write-Host ""

# Check MySQL command
Write-Host "MySQL Command:" -ForegroundColor Yellow
$mysqlPath = Get-Command mysql -ErrorAction SilentlyContinue
if ($mysqlPath) {
    Write-Host "  mysql command: Available" -ForegroundColor Green
    Write-Host "  Path: $($mysqlPath.Source)" -ForegroundColor White
    $version = & mysql --version 2>&1
    Write-Host "  Version: $version" -ForegroundColor White
} else {
    Write-Host "  mysql command: Not found in PATH" -ForegroundColor Red
    Write-Host "  (This is okay if you're using XAMPP/WAMP)" -ForegroundColor Yellow
}

Write-Host ""

# Test connection (if credentials are available)
Write-Host "Connection Test:" -ForegroundColor Yellow
$envFile = "apps\web-dashboard\.env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    $dbUser = $null
    $dbPass = $null
    $dbName = $null
    
    if ($envContent -match "DB_USERNAME=([^\r\n]+)") {
        $dbUser = $matches[1].Trim()
    }
    if ($envContent -match "DB_PASSWORD=([^\r\n]+)") {
        $dbPass = $matches[1].Trim()
    }
    if ($envContent -match "DB_DATABASE=([^\r\n]+)") {
        $dbName = $matches[1].Trim()
    }
    
    if ($dbUser -and $dbName) {
        Write-Host "  Database: $dbName" -ForegroundColor White
        Write-Host "  Username: $dbUser" -ForegroundColor White
        Write-Host "  (Run 'php artisan tinker' to test actual connection)" -ForegroundColor Yellow
    } else {
        Write-Host "  .env file found but database config not detected" -ForegroundColor Yellow
    }
} else {
    Write-Host "  .env file not found at: $envFile" -ForegroundColor Yellow
    Write-Host "  (Configure database settings to enable connection test)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Status check complete!" -ForegroundColor Cyan
