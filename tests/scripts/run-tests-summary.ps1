# Test Summary Script
# Runs all tests and provides a summary

$ErrorActionPreference = "Continue"

# Set environment
$env:LICENSE_SERVER_URL = if ($env:LICENSE_SERVER_URL) { $env:LICENSE_SERVER_URL } else { "http://localhost:8000" }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Upload Bridge Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check API is running
Write-Host "Checking API accessibility..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$env:LICENSE_SERVER_URL/api/v2/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ API is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ API is not accessible at $env:LICENSE_SERVER_URL" -ForegroundColor Red
    Write-Host "Please ensure the application is running." -ForegroundColor Yellow
    exit 1
}

# Change to tests directory
$TestsDir = Join-Path $PSScriptRoot ".."
Push-Location $TestsDir

# Test files to run
$testFiles = @(
    @{ File = "tests/api/health-e2e.test.js"; Name = "Health Check Tests" },
    @{ File = "tests/api/allAPIs.test.js"; Name = "All APIs Tests" },
    @{ File = "tests/api/auth-e2e.test.js"; Name = "Authentication Tests" }
)

$totalPassed = 0
$totalFailed = 0
$results = @()

foreach ($test in $testFiles) {
    Write-Host ""
    Write-Host "Running: $($test.Name)" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    $output = node run-test.js $test.File 2>&1 | Out-String
    
    if ($output -match "Tests: (\d+) passed, (\d+) failed") {
        $passed = [int]$matches[1]
        $failed = [int]$matches[2]
        $totalPassed += $passed
        $totalFailed += $failed
        
        $result = @{
            Name = $test.Name
            Passed = $passed
            Failed = $failed
            Output = $output
        }
        $results += $result
        
        if ($failed -eq 0) {
            Write-Host "  ✓ PASSED: $passed tests" -ForegroundColor Green
        } else {
            Write-Host "  ✗ FAILED: $passed passed, $failed failed" -ForegroundColor Red
            # Show error summary
            $errorLines = $output | Select-String -Pattern "Errors:" -Context 0,10
            if ($errorLines) {
                Write-Host "  Errors:" -ForegroundColor Red
                $errorLines | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
            }
        }
    } else {
        Write-Host "  Warning: Could not parse test results" -ForegroundColor Yellow
    }
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total Passed: $totalPassed" -ForegroundColor Green
Write-Host "Total Failed: $totalFailed" -ForegroundColor $(if ($totalFailed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($totalFailed -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some tests failed. Review output above." -ForegroundColor Red
    exit 1
}

Pop-Location
