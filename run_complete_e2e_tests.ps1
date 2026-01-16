# run_complete_e2e_tests.ps1
# Complete E2E Test Orchestration Script for License System

<#
.SYNOPSIS
    Orchestrates complete end-to-end tests for the Upload Bridge license system.
    Tests web dashboard (Laravel), license server API, and integration flows.

.DESCRIPTION
    This script:
    1. Sets up test infrastructure
    2. Starts required services (Laravel server, Vercel dev if local)
    3. Runs web dashboard E2E tests (Laravel Dusk)
    4. Runs API E2E tests (Node.js/Jest)
    5. Runs integration tests
    6. Generates comprehensive test report
    7. Cleans up services

.NOTES
    Requires:
    - PHP 8.1+ and Composer
    - Node.js and npm
    - Chrome/Chromium for Dusk tests
    - PowerShell 5.1+
#>

param(
    [switch]$SkipSetup,
    [switch]$SkipWebDashboard,
    [switch]$SkipAPI,
    [switch]$SkipIntegration,
    [string]$LicenseServerUrl = "https://j-tech-license-server.vercel.app",
    [string]$LaravelUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Get-Item $PSScriptRoot).FullName
$webDashboardDir = Join-Path $projectRoot "web-dashboard"
$licenseServerDir = Join-Path $projectRoot "apps\license-server"
$testResultsDir = Join-Path $projectRoot "test-results"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportFile = Join-Path $testResultsDir "e2e-report-$timestamp.html"

# Test results
$testResults = @{
    WebDashboard = @{ Passed = 0; Failed = 0; Total = 0; Details = @() }
    API = @{ Passed = 0; Failed = 0; Total = 0; Details = @() }
    Integration = @{ Passed = 0; Failed = 0; Total = 0; Details = @() }
    StartTime = Get-Date
    EndTime = $null
}

# Helper function for error handling
function Invoke-CheckedCommand {
    param(
        [string]$Command,
        [string]$Description,
        [string]$WorkingDirectory = $projectRoot
    )
    Write-Host ">>> $Description..." -ForegroundColor Cyan
    try {
        Push-Location $WorkingDirectory
        Invoke-Expression $Command
        if (${LASTEXITCODE} -ne 0 -and ${LASTEXITCODE} -ne $null) {
            Write-Warning "Command completed with exit code ${LASTEXITCODE}: $Command"
            return $false
        }
        Write-Host ">>> $Description succeeded." -ForegroundColor Green
        return $true
    } catch {
        Write-Warning "Error executing command: $Command. Details: $($_.Exception.Message)"
        return $false
    } finally {
        Pop-Location
    }
}

# Create test results directory
if (-not (Test-Path $testResultsDir)) {
    New-Item -ItemType Directory -Path $testResultsDir | Out-Null
}

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Complete E2E Test Suite" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# Phase 1: Infrastructure Setup
if (-not $SkipSetup) {
    Write-Host "--- Phase 1: Infrastructure Setup ---" -ForegroundColor Yellow

    # Check PHP
    Write-Host "Checking PHP..." -ForegroundColor DarkGray
    $phpVersion = php -v 2>&1 | Select-String -Pattern "PHP (\d+\.\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }
    if ($phpVersion) {
        Write-Host "PHP $phpVersion found" -ForegroundColor Green
    } else {
        Write-Warning "PHP not found. Web dashboard tests will be skipped."
        $SkipWebDashboard = $true
    }

    # Check Node.js
    Write-Host "Checking Node.js..." -ForegroundColor DarkGray
    $nodeVersion = node -v 2>&1
    if ($nodeVersion) {
        Write-Host "Node.js $nodeVersion found" -ForegroundColor Green
    } else {
        Write-Warning "Node.js not found. API tests will be skipped."
        $SkipAPI = $true
    }

    # Check Composer
    Write-Host "Checking Composer..." -ForegroundColor DarkGray
    $composerVersion = composer -V 2>&1 | Select-String -Pattern "Composer version"
    if ($composerVersion) {
        Write-Host "Composer found" -ForegroundColor Green
    } else {
        Write-Warning "Composer not found. Web dashboard tests will be skipped."
        $SkipWebDashboard = $true
    }

    # Setup web dashboard
    if (-not $SkipWebDashboard) {
        Write-Host "Setting up web dashboard..." -ForegroundColor DarkGray
        Push-Location $webDashboardDir
        
        # Install dependencies
        if (Test-Path "composer.json") {
            Invoke-CheckedCommand "composer install --no-interaction" "Installing web dashboard dependencies" $webDashboardDir
        }
        
        # Create SQLite database if needed
        $dbPath = Join-Path $webDashboardDir "database\database.sqlite"
        if (-not (Test-Path $dbPath)) {
            New-Item -ItemType File -Path $dbPath | Out-Null
            Write-Host "Created SQLite database" -ForegroundColor Green
        }
        
        # Run migrations
        Invoke-CheckedCommand "php artisan migrate:fresh --force" "Running migrations" $webDashboardDir
        
        Pop-Location
    }

    # Setup license server (if testing locally)
    if (-not $SkipAPI -and $LicenseServerUrl -like "http://localhost*") {
        Write-Host "Setting up license server..." -ForegroundColor DarkGray
        Push-Location $licenseServerDir
        
        if (Test-Path "package.json") {
            Invoke-CheckedCommand "npm install" "Installing license server dependencies" $licenseServerDir
        }
        
        Pop-Location
    }
}

# Phase 2: Start Services
Write-Host ""
Write-Host "--- Phase 2: Starting Services ---" -ForegroundColor Yellow

$laravelProcess = $null
$vercelProcess = $null

# Start Laravel server
if (-not $SkipWebDashboard) {
    Write-Host "Starting Laravel server..." -ForegroundColor DarkGray
    Push-Location $webDashboardDir
    $laravelProcess = Start-Process -FilePath "php" -ArgumentList "artisan serve" -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 3
    Write-Host "Laravel server started (PID: $($laravelProcess.Id))" -ForegroundColor Green
    Pop-Location
}

# Start Vercel dev (if testing locally)
if (-not $SkipAPI -and $LicenseServerUrl -like "http://localhost*") {
    Write-Host "Starting Vercel dev server..." -ForegroundColor DarkGray
    Push-Location $licenseServerDir
    $vercelProcess = Start-Process -FilePath "npx" -ArgumentList "vercel dev" -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 5
    Write-Host "Vercel dev server started (PID: $($vercelProcess.Id))" -ForegroundColor Green
    Pop-Location
}

# Wait for services to be ready
Write-Host "Waiting for services to be ready..." -ForegroundColor DarkGray
Start-Sleep -Seconds 5

# Phase 3: Run Web Dashboard Tests
if (-not $SkipWebDashboard) {
    Write-Host ""
    Write-Host "--- Phase 3: Web Dashboard E2E Tests ---" -ForegroundColor Yellow
    Push-Location $webDashboardDir

    $duskOutput = & php artisan dusk 2>&1 | Out-String
    $duskExitCode = $LASTEXITCODE

    if ($duskExitCode -eq 0) {
        Write-Host "Web dashboard tests passed" -ForegroundColor Green
        $match = $duskOutput | Select-String -Pattern "OK \((\d+) tests"
        if ($match) {
            $testResults.WebDashboard.Passed = [int]$match.Matches.Groups[1].Value
        } else {
            $testResults.WebDashboard.Passed = 0
        }
    } else {
        Write-Host "Web dashboard tests failed" -ForegroundColor Red
        $testResults.WebDashboard.Failed = 1
    }
    $testResults.WebDashboard.Total = $testResults.WebDashboard.Passed + $testResults.WebDashboard.Failed
    $testResults.WebDashboard.Details = $duskOutput

    Pop-Location
} else {
    Write-Host "Skipping web dashboard tests" -ForegroundColor DarkGray
}

# Phase 4: Run API Tests
if (-not $SkipAPI) {
    Write-Host ""
    Write-Host "--- Phase 4: API E2E Tests ---" -ForegroundColor Yellow
    
    # Set environment variable for API client
    $env:LICENSE_SERVER_URL = $LaravelUrl

    # Use new test suite runner
    $testRunnerPath = Join-Path $projectRoot "tests\run-complete-test-suite.js"
    if (Test-Path $testRunnerPath) {
        Write-Host "Running complete test suite..." -ForegroundColor DarkGray
        Push-Location (Join-Path $projectRoot "tests")
        $testOutput = & node run-complete-test-suite.js 2>&1 | Out-String
        $apiSuccess = $LASTEXITCODE -eq 0
        Pop-Location
        
        # Parse results from JSON report if available
        $jsonReportPath = Join-Path $projectRoot "test-results\test-report-*.json"
        $jsonReports = Get-ChildItem $jsonReportPath -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($jsonReports) {
            $jsonContent = Get-Content $jsonReports.FullName -Raw | ConvertFrom-Json
            $testResults.API.Passed = $jsonContent.passed
            $testResults.API.Failed = $jsonContent.failed
            $testResults.API.Total = $jsonContent.total
        } else {
            $testResults.API.Passed = if ($apiSuccess) { 1 } else { 0 }
            $testResults.API.Failed = if ($apiSuccess) { 0 } else { 1 }
            $testResults.API.Total = 1
        }
        $testResults.API.Details = $testOutput

        if ($testResults.API.Failed -eq 0) {
            Write-Host "API tests passed" -ForegroundColor Green
        } else {
            Write-Host "API tests failed" -ForegroundColor Red
        }
    } else {
        # Fallback to old method
        $apiTestFiles = @(
            "tests\api\auth-e2e.test.js",
            "tests\api\license-e2e.test.js",
            "tests\api\device-e2e.test.js"
        )

        $apiResults = @()
        $testRunnerPath = Join-Path $projectRoot "tests\run-test.js"
        foreach ($testFile in $apiTestFiles) {
            $testPath = Join-Path $projectRoot $testFile
            if (Test-Path $testPath) {
                Write-Host "Running $testFile..." -ForegroundColor DarkGray
                Push-Location $projectRoot
                $testOutput = & node $testRunnerPath $testPath 2>&1 | Out-String
                $apiResults += @{ File = $testFile; Output = $testOutput; Success = $LASTEXITCODE -eq 0 }
                Pop-Location
            }
        }

        $testResults.API.Passed = ($apiResults | Where-Object { $_.Success }).Count
        $testResults.API.Failed = ($apiResults | Where-Object { -not $_.Success }).Count
        $testResults.API.Total = $apiResults.Count
        $testResults.API.Details = $apiResults

        if ($testResults.API.Failed -eq 0) {
            Write-Host "API tests passed" -ForegroundColor Green
        } else {
            Write-Host "API tests failed" -ForegroundColor Red
        }
    }
} else {
    Write-Host "Skipping API tests" -ForegroundColor DarkGray
}

# Phase 5: Run Integration Tests
if (-not $SkipIntegration) {
    Write-Host ""
    Write-Host "--- Phase 5: Integration Tests ---" -ForegroundColor Yellow

    $integrationTestFiles = @(
        "tests\integration\auth-integration.test.js",
        "tests\integration\license-db.test.js",
        "tests\integration\database-e2e.test.js"
    )

    $integrationResults = @()
    $testRunnerPath = Join-Path $projectRoot "tests\run-test.js"
    foreach ($testFile in $integrationTestFiles) {
        $testPath = Join-Path $projectRoot $testFile
        if (Test-Path $testPath) {
            Write-Host "Running $testFile..." -ForegroundColor DarkGray
            Push-Location $projectRoot
            $testOutput = & node $testRunnerPath $testPath 2>&1 | Out-String
            $integrationResults += @{ File = $testFile; Output = $testOutput; Success = $LASTEXITCODE -eq 0 }
            Pop-Location
        }
    }

    $testResults.Integration.Passed = ($integrationResults | Where-Object { $_.Success }).Count
    $testResults.Integration.Failed = ($integrationResults | Where-Object { -not $_.Success }).Count
    $testResults.Integration.Total = $integrationResults.Count
    $testResults.Integration.Details = $integrationResults

    if ($testResults.Integration.Failed -eq 0) {
        Write-Host "Integration tests passed" -ForegroundColor Green
    } else {
        Write-Host "Integration tests failed" -ForegroundColor Red
    }
} else {
    Write-Host "Skipping integration tests" -ForegroundColor DarkGray
}

# Phase 6: Run Security Tests
Write-Host ""
Write-Host "--- Phase 6: Security Tests ---" -ForegroundColor Yellow

$securityTestFile = Join-Path $projectRoot "tests\security\api-security.test.js"
$testRunnerPath = Join-Path $projectRoot "tests\run-test.js"
if (Test-Path $securityTestFile) {
    Write-Host "Running security tests..." -ForegroundColor DarkGray
    Push-Location $projectRoot
    $securityOutput = & node $testRunnerPath $securityTestFile 2>&1 | Out-String
    $securitySuccess = $LASTEXITCODE -eq 0
    Pop-Location

    if ($securitySuccess) {
        Write-Host "Security tests passed" -ForegroundColor Green
    } else {
        Write-Host "Security tests failed" -ForegroundColor Red
    }
}

# Phase 7: Run User Journey Tests
Write-Host ""
Write-Host "--- Phase 7: User Journey Tests ---" -ForegroundColor Yellow

$journeyTestFiles = @(
    "tests\e2e\complete-user-journey.test.js",
    "tests\e2e\license-renewal-journey.test.js",
    "tests\e2e\error-handling.test.js"
)

$journeyResults = @()
$testRunnerPath = Join-Path $projectRoot "tests\run-test.js"
foreach ($testFile in $journeyTestFiles) {
    $testPath = Join-Path $projectRoot $testFile
    if (Test-Path $testPath) {
        Write-Host "Running $testFile..." -ForegroundColor DarkGray
        Push-Location $projectRoot
        $testOutput = & node $testRunnerPath $testPath 2>&1 | Out-String
        $journeyResults += @{ File = $testFile; Output = $testOutput; Success = $LASTEXITCODE -eq 0 }
        Pop-Location
    }
}

# Cleanup: Stop Services
Write-Host ""
Write-Host "--- Cleanup: Stopping Services ---" -ForegroundColor Yellow

if ($laravelProcess -and -not $laravelProcess.HasExited) {
    Write-Host "Stopping Laravel server..." -ForegroundColor DarkGray
    Stop-Process -Id $laravelProcess.Id -Force -ErrorAction SilentlyContinue
}

if ($vercelProcess -and -not $vercelProcess.HasExited) {
    Write-Host "Stopping Vercel dev server..." -ForegroundColor DarkGray
    Stop-Process -Id $vercelProcess.Id -Force -ErrorAction SilentlyContinue
}

# Generate Report
$testResults.EndTime = Get-Date
$duration = $testResults.EndTime - $testResults.StartTime

$totalPassed = $testResults.WebDashboard.Passed + $testResults.API.Passed + $testResults.Integration.Passed
$totalFailed = $testResults.WebDashboard.Failed + $testResults.API.Failed + $testResults.Integration.Failed
$totalTests = $totalPassed + $totalFailed

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Test Results Summary" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Web Dashboard: $($testResults.WebDashboard.Passed) passed, $($testResults.WebDashboard.Failed) failed" -ForegroundColor $(if ($testResults.WebDashboard.Failed -eq 0) { "Green" } else { "Red" })
Write-Host "API Tests: $($testResults.API.Passed) passed, $($testResults.API.Failed) failed" -ForegroundColor $(if ($testResults.API.Failed -eq 0) { "Green" } else { "Red" })
Write-Host "Integration Tests: $($testResults.Integration.Passed) passed, $($testResults.Integration.Failed) failed" -ForegroundColor $(if ($testResults.Integration.Failed -eq 0) { "Green" } else { "Red" })
Write-Host "Total: $totalPassed passed, $totalFailed failed" -ForegroundColor $(if ($totalFailed -eq 0) { "Green" } else { "Red" })
Write-Host "Duration: $($duration.TotalSeconds) seconds" -ForegroundColor Cyan
Write-Host ""

# Generate HTML report
$htmlReport = @"
<!DOCTYPE html>
<html>
<head>
    <title>E2E Test Report - $timestamp</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .passed { color: green; }
        .failed { color: red; }
        .section { margin: 20px 0; }
        pre { background: #f0f0f0; padding: 10px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>E2E Test Report</h1>
    <p>Generated: $($testResults.StartTime)</p>
    <p>Duration: $($duration.TotalSeconds) seconds</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: $totalTests</p>
        <p class="passed">Passed: $totalPassed</p>
        <p class="failed">Failed: $totalFailed</p>
    </div>
    
    <div class="section">
        <h2>Web Dashboard Tests</h2>
        <p>Passed: $($testResults.WebDashboard.Passed), Failed: $($testResults.WebDashboard.Failed)</p>
        <pre>$($testResults.WebDashboard.Details)</pre>
    </div>
    
    <div class="section">
        <h2>API Tests</h2>
        <p>Passed: $($testResults.API.Passed), Failed: $($testResults.API.Failed)</p>
    </div>
    
    <div class="section">
        <h2>Integration Tests</h2>
        <p>Passed: $($testResults.Integration.Passed), Failed: $($testResults.Integration.Failed)</p>
    </div>
</body>
</html>
"@

$htmlReport | Out-File -FilePath $reportFile -Encoding UTF8
Write-Host "Test report saved to: $reportFile" -ForegroundColor Cyan

# Exit with appropriate code
if ($totalFailed -gt 0) {
    exit 1
} else {
    exit 0
}
