# E2E Test Runner Script for Windows
# Runs comprehensive E2E test suite

param(
    [string]$Category = "all",
    [switch]$Verbose,
    [switch]$Parallel,
    [switch]$Coverage,
    [int]$Workers = 0
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "E2E Test Suite Runner" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot

try {
    # Build pytest command
    $pytestCmd = @("pytest", "tests/e2e")
    
    if ($Verbose) {
        $pytestCmd += "-v"
    }
    
    if ($Category -ne "all") {
        $pytestCmd += "-m", $Category
    }
    
    if ($Parallel) {
        if ($Workers -gt 0) {
            $pytestCmd += "-n", $Workers.ToString()
        } else {
            $pytestCmd += "-n", "auto"
        }
    }
    
    if ($Coverage) {
        $pytestCmd += "--cov=apps/upload-bridge", "--cov=apps/web-dashboard", "--cov-report=html", "--cov-report=term-missing"
    }
    
    Write-Host "Running: $($pytestCmd -join ' ')" -ForegroundColor Yellow
    Write-Host ""
    
    # Run tests
    & python -m pytest $pytestCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "All tests passed!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "Some tests failed!" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "Error running tests: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}
