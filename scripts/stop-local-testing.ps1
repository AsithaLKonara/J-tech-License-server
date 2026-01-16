# Stop Local E2E Testing Environment
# Stops any running Laravel servers on port 8000

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Stopping Local E2E Testing Environment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Find processes using port 8000
$connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($connections) {
    $processes = $connections | ForEach-Object {
        Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
    } | Select-Object -Unique
    
    foreach ($process in $processes) {
        Write-Host "Stopping process: $($process.ProcessName) (PID: $($process.Id))" -ForegroundColor Yellow
        try {
            Stop-Process -Id $process.Id -Force -ErrorAction Stop
            Write-Host "✅ Stopped $($process.ProcessName)" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Could not stop $($process.ProcessName): $_" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "✅ All processes on port 8000 stopped" -ForegroundColor Green
} else {
    Write-Host "✅ No processes found on port 8000" -ForegroundColor Green
}

Write-Host ""
