# MySQL Server Start Script for Windows
# This script helps start MySQL service on Windows

param(
    [string]$ServiceName = "MySQL80",
    [switch]$XAMPP,
    [switch]$WAMP
)

Write-Host "MySQL Server Management Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

if ($XAMPP) {
    Write-Host "Starting MySQL via XAMPP..." -ForegroundColor Yellow
    $xamppPath = "C:\xampp\mysql\bin\mysqld.exe"
    
    if (Test-Path $xamppPath) {
        Start-Process -FilePath "C:\xampp\xampp-control.exe" -ArgumentList "startmysql"
        Write-Host "MySQL started via XAMPP Control Panel" -ForegroundColor Green
    } else {
        Write-Host "XAMPP not found at C:\xampp" -ForegroundColor Red
        Write-Host "Please update the path or install XAMPP" -ForegroundColor Yellow
        exit 1
    }
}
elseif ($WAMP) {
    Write-Host "Starting MySQL via WAMP..." -ForegroundColor Yellow
    $wampPath = "C:\wamp64\bin\mysql\mysql8.0.xx\bin\mysqld.exe"
    
    # WAMP uses a service, try to start it
    $wampService = Get-Service -Name "wampmysqld*" -ErrorAction SilentlyContinue
    if ($wampService) {
        Start-Service $wampService.Name
        Write-Host "MySQL started via WAMP service" -ForegroundColor Green
    } else {
        Write-Host "WAMP MySQL service not found" -ForegroundColor Red
        Write-Host "Please start WAMP Server manually" -ForegroundColor Yellow
        exit 1
    }
}
else {
    # Try to start MySQL service
    Write-Host "Checking MySQL service status..." -ForegroundColor Yellow
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    
    if (-not $service) {
        Write-Host "MySQL service '$ServiceName' not found." -ForegroundColor Red
        Write-Host "Available MySQL services:" -ForegroundColor Yellow
        Get-Service | Where-Object { $_.Name -like "*mysql*" } | ForEach-Object {
            Write-Host "  - $($_.Name)" -ForegroundColor Cyan
        }
        Write-Host ""
        Write-Host "Usage:" -ForegroundColor Yellow
        Write-Host "  .\mysql-start.ps1 -ServiceName 'MySQL80'" -ForegroundColor White
        exit 1
    }
    
    if ($service.Status -eq 'Running') {
        Write-Host "MySQL service '$ServiceName' is already running." -ForegroundColor Green
    } else {
        Write-Host "Starting MySQL service '$ServiceName'..." -ForegroundColor Yellow
        try {
            Start-Service -Name $ServiceName
            Start-Sleep -Seconds 2
            if ((Get-Service -Name $ServiceName).Status -eq 'Running') {
                Write-Host "MySQL service started successfully!" -ForegroundColor Green
            } else {
                Write-Host "Failed to start MySQL service." -ForegroundColor Red
                exit 1
            }
        } catch {
            Write-Host "Error starting MySQL service: $_" -ForegroundColor Red
            Write-Host "You may need to run this script as Administrator." -ForegroundColor Yellow
            exit 1
        }
    }
}

Write-Host ""
Write-Host "Testing MySQL connection..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

try {
    $result = Test-NetConnection -ComputerName localhost -Port 3306 -WarningAction SilentlyContinue
    if ($result.TcpTestSucceeded) {
        Write-Host "MySQL is listening on port 3306" -ForegroundColor Green
    } else {
        Write-Host "MySQL may not be fully started yet. Wait a few seconds and try again." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Could not test connection (this is okay if MySQL is still starting)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "MySQL server management complete!" -ForegroundColor Cyan
