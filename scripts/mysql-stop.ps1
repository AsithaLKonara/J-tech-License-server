# MySQL Server Stop Script for Windows
# This script helps stop MySQL service on Windows

param(
    [string]$ServiceName = "MySQL80",
    [switch]$XAMPP,
    [switch]$WAMP
)

Write-Host "MySQL Server Stop Script" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""

if ($XAMPP) {
    Write-Host "Stopping MySQL via XAMPP..." -ForegroundColor Yellow
    if (Test-Path "C:\xampp\xampp-control.exe") {
        Start-Process -FilePath "C:\xampp\xampp-control.exe" -ArgumentList "stopmysql"
        Write-Host "MySQL stopped via XAMPP Control Panel" -ForegroundColor Green
    } else {
        Write-Host "XAMPP not found at C:\xampp" -ForegroundColor Red
        exit 1
    }
}
elseif ($WAMP) {
    Write-Host "Stopping MySQL via WAMP..." -ForegroundColor Yellow
    $wampService = Get-Service -Name "wampmysqld*" -ErrorAction SilentlyContinue
    if ($wampService) {
        Stop-Service $wampService.Name
        Write-Host "MySQL stopped via WAMP service" -ForegroundColor Green
    } else {
        Write-Host "WAMP MySQL service not found" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "Checking MySQL service status..." -ForegroundColor Yellow
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    
    if (-not $service) {
        Write-Host "MySQL service '$ServiceName' not found." -ForegroundColor Red
        Write-Host "Available MySQL services:" -ForegroundColor Yellow
        Get-Service | Where-Object { $_.Name -like "*mysql*" } | ForEach-Object {
            Write-Host "  - $($_.Name)" -ForegroundColor Cyan
        }
        exit 1
    }
    
    if ($service.Status -eq 'Stopped') {
        Write-Host "MySQL service '$ServiceName' is already stopped." -ForegroundColor Green
    } else {
        Write-Host "Stopping MySQL service '$ServiceName'..." -ForegroundColor Yellow
        try {
            Stop-Service -Name $ServiceName
            Start-Sleep -Seconds 2
            if ((Get-Service -Name $ServiceName).Status -eq 'Stopped') {
                Write-Host "MySQL service stopped successfully!" -ForegroundColor Green
            } else {
                Write-Host "Failed to stop MySQL service." -ForegroundColor Red
                exit 1
            }
        } catch {
            Write-Host "Error stopping MySQL service: $_" -ForegroundColor Red
            Write-Host "You may need to run this script as Administrator." -ForegroundColor Yellow
            exit 1
        }
    }
}

Write-Host ""
Write-Host "MySQL server stopped!" -ForegroundColor Cyan
