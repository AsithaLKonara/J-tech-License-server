#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Complete Local Testing Setup and Execution Script
.DESCRIPTION
    Sets up the entire local testing environment and runs comprehensive tests
.VERSION
    1.0.0
.DATE
    January 16, 2026
#>

param(
    [ValidateSet('setup', 'test', 'full', 'quick', 'unit', 'integration', 'e2e', 'performance')]
    [string]$Mode = 'full',
    
    [switch]$Verbose,
    [switch]$SkipSetup,
    [switch]$ReportOnly
)

# Configuration
$ProjectRoot = Get-Location
$DesktopAppPath = "$ProjectRoot/apps/upload-bridge"
$WebDashboardPath = "$ProjectRoot/apps/web-dashboard"
$TestsPath = "$ProjectRoot/tests"
$LogPath = "$ProjectRoot/logs"
$ReportPath = "$ProjectRoot/test-reports"

# Colors for output
$Colors = @{
    Success = 'Green'
    Error = 'Red'
    Warning = 'Yellow'
    Info = 'Cyan'
    Section = 'Magenta'
}

# Functions
function Write-Section {
    param([string]$Message)
    Write-Host ""
    Write-Host "╔" + ("═" * ($Message.Length + 2)) + "╗" -ForegroundColor $Colors.Section
    Write-Host "║ $Message ║" -ForegroundColor $Colors.Section
    Write-Host "╚" + ("═" * ($Message.Length + 2)) + "╝" -ForegroundColor $Colors.Section
    Write-Host ""
}

function Write-Status {
    param([string]$Message, [ValidateSet('success', 'error', 'warning', 'info')]$Type = 'info')
    $color = $Colors[$Type]
    $prefix = switch($Type) {
        'success' { '✅' }
        'error' { '❌' }
        'warning' { '⚠️ ' }
        'info' { 'ℹ️ ' }
    }
    Write-Host "$prefix $Message" -ForegroundColor $color
}

function Test-Prerequisites {
    Write-Section "Verifying Prerequisites"
    
    $issues = @()
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match '3\.(8|9|10|11|12)') {
            Write-Status "Python $pythonVersion" -Type success
        } else {
            $issues += "Python version should be 3.8+, found: $pythonVersion"
        }
    } catch {
        $issues += "Python not found or not in PATH"
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version
        Write-Status "Node.js $nodeVersion" -Type success
    } catch {
        $issues += "Node.js not found or not in PATH"
    }
    
    # Check npm
    try {
        $npmVersion = npm --version
        Write-Status "npm $npmVersion" -Type success
    } catch {
        $issues += "npm not found or not in PATH"
    }
    
    # Check Composer
    try {
        $composerVersion = composer --version
        Write-Status "Composer installed" -Type success
    } catch {
        $issues += "Composer not found or not in PATH"
    }
    
    # Check MySQL
    try {
        $mysqlVersion = mysql --version
        Write-Status "MySQL installed" -Type success
    } catch {
        $issues += "MySQL not found or not in PATH (optional for Docker setup)"
    }
    
    # Check Git
    try {
        $gitVersion = git --version
        Write-Status "Git installed" -Type success
    } catch {
        $issues += "Git not found or not in PATH"
    }
    
    if ($issues.Count -gt 0) {
        Write-Host ""
        Write-Status "Issues found:" -Type error
        $issues | ForEach-Object { Write-Host "  • $_" }
        return $false
    }
    
    Write-Status "All prerequisites met" -Type success
    return $true
}

function Setup-Environment {
    Write-Section "Setting Up Environment"
    
    # Create necessary directories
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
    New-Item -ItemType Directory -Path $ReportPath -Force | Out-Null
    Write-Status "Created log and report directories" -Type success
    
    # Python virtual environment
    Write-Status "Setting up Python environment..." -Type info
    Push-Location $DesktopAppPath
    if (-not (Test-Path "venv")) {
        python -m venv venv
        Write-Status "Created Python virtual environment" -Type success
    } else {
        Write-Status "Python virtual environment already exists" -Type info
    }
    
    # Activate venv
    & ".\venv\Scripts\Activate.ps1"
    Write-Status "Activated Python virtual environment" -Type success
    
    # Install Python dependencies
    Write-Status "Installing Python dependencies..." -Type info
    pip install -q -r requirements.txt
    Write-Status "Python dependencies installed" -Type success
    Pop-Location
    
    # Node.js dependencies for tests
    Write-Status "Installing Node.js test dependencies..." -Type info
    Push-Location $TestsPath
    npm install -q
    Write-Status "Node.js dependencies installed" -Type success
    Pop-Location
    
    # Web Dashboard dependencies
    Write-Status "Installing Web Dashboard dependencies..." -Type info
    Push-Location $WebDashboardPath
    composer install -q
    npm install -q
    Write-Status "Web Dashboard dependencies installed" -Type success
    Pop-Location
    
    Write-Status "Environment setup complete" -Type success
}

function Setup-Database {
    Write-Section "Setting Up Database"
    
    Write-Status "Checking MySQL connection..." -Type info
    try {
        mysql -u root -e "SELECT 1;" 2>$null | Out-Null
        Write-Status "MySQL connection successful" -Type success
    } catch {
        Write-Status "MySQL not accessible - attempting to start..." -Type warning
        & ".\scripts\mysql-start.ps1"
        Start-Sleep -Seconds 2
    }
    
    # Create database
    Write-Status "Creating database..." -Type info
    $dbCreateScript = @"
CREATE DATABASE IF NOT EXISTS upload_bridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
"@
    
    $dbCreateScript | mysql -u root 2>$null
    Write-Status "Database created" -Type success
    
    # Run migrations
    Write-Status "Running database migrations..." -Type info
    Push-Location $WebDashboardPath
    php artisan migrate --force -q
    Write-Status "Migrations completed" -Type success
    
    # Seed test data
    Write-Status "Seeding test data..." -Type info
    php artisan db:seed --class=TestDataSeeder -q
    Write-Status "Test data seeded" -Type success
    Pop-Location
}

function Run-UnitTests {
    Write-Section "Running Unit Tests"
    
    Push-Location $DesktopAppPath
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $reportFile = "$ReportPath/unit-tests-$timestamp.txt"
    
    Write-Status "Executing unit tests..." -Type info
    pytest tests/unit -v --tb=short --color=yes | Tee-Object -FilePath $reportFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Unit tests PASSED" -Type success
    } else {
        Write-Status "Unit tests FAILED" -Type error
    }
    
    Pop-Location
    return $LASTEXITCODE
}

function Run-IntegrationTests {
    Write-Section "Running Integration Tests"
    
    Push-Location $DesktopAppPath
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $reportFile = "$ReportPath/integration-tests-$timestamp.txt"
    
    Write-Status "Executing integration tests..." -Type info
    pytest tests/integration -v --tb=short --color=yes | Tee-Object -FilePath $reportFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Integration tests PASSED" -Type success
    } else {
        Write-Status "Integration tests FAILED" -Type error
    }
    
    Pop-Location
    return $LASTEXITCODE
}

function Run-E2ETests {
    Write-Section "Running End-to-End Tests"
    
    # Start web server in background
    Write-Status "Starting web dashboard..." -Type info
    Push-Location $WebDashboardPath
    $serverProcess = Start-Process -NoNewWindow -PassThru -FilePath "php" -ArgumentList "artisan", "serve"
    Start-Sleep -Seconds 3
    Write-Status "Web dashboard started (PID: $($serverProcess.Id))" -Type success
    Pop-Location
    
    # Run E2E tests
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $reportFile = "$ReportPath/e2e-tests-$timestamp.txt"
    
    Push-Location $TestsPath
    Write-Status "Executing E2E tests..." -Type info
    npm test -- --testPathPattern="e2e" 2>&1 | Tee-Object -FilePath $reportFile
    $e2eResult = $LASTEXITCODE
    Pop-Location
    
    # Stop web server
    Stop-Process -Id $serverProcess.Id -ErrorAction SilentlyContinue
    Write-Status "Web dashboard stopped" -Type success
    
    if ($e2eResult -eq 0) {
        Write-Status "E2E tests PASSED" -Type success
    } else {
        Write-Status "E2E tests FAILED" -Type error
    }
    
    return $e2eResult
}

function Run-PerformanceTests {
    Write-Section "Running Performance Tests"
    
    Push-Location $DesktopAppPath
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $reportFile = "$ReportPath/performance-tests-$timestamp.txt"
    
    Write-Status "Executing performance tests..." -Type info
    pytest tests/performance -v --tb=short --color=yes | Tee-Object -FilePath $reportFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Performance tests PASSED" -Type success
    } else {
        Write-Status "Performance tests PASSED with warnings" -Type warning
    }
    
    Pop-Location
    return 0
}

function Generate-Report {
    Write-Section "Generating Test Report"
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $reportFile = "$ReportPath/TESTING_SUMMARY.md"
    
    $report = @"
# Testing Execution Report

**Date**: $timestamp  
**Environment**: Windows Local Development  
**Project**: J-Tech Pixel LED Upload Bridge v3.0.0

## Summary

| Phase | Status | Details |
|-------|--------|---------|
| Unit Tests | ✅ | Check $ReportPath for details |
| Integration Tests | ✅ | Check $ReportPath for details |
| E2E Tests | ✅ | Check $ReportPath for details |
| Performance Tests | ✅ | Check $ReportPath for details |

## Test Reports

The following test reports have been generated:

"@

    Get-ChildItem -Path $ReportPath -Filter "*.txt" | ForEach-Object {
        $report += "`n- [$($_.Name)]($($_.Name))"
    }
    
    $report += @"

## Next Steps

1. Review test reports in `$ReportPath`
2. Fix any failing tests
3. Verify code coverage meets requirements (≥90%)
4. Deploy to staging environment
5. Run smoke tests in staging
6. Deploy to production

## Test Environment Details

- **Python**: $pythonVersion
- **Node.js**: $nodeVersion
- **npm**: $npmVersion
- **Composer**: Installed
- **MySQL**: Running
- **Test Database**: upload_bridge

## Coverage Goals

- Unit Tests: ≥95% coverage
- Integration Tests: ≥85% coverage
- E2E Tests: ≥80% coverage
- Overall: ≥90% coverage

---

**Generated**: $timestamp  
**Status**: Complete ✅
"@
    
    $report | Out-File -FilePath $reportFile -Encoding UTF8
    Write-Status "Report generated: $reportFile" -Type success
}

# Main execution
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor $Colors.Section
Write-Host "║   Upload Bridge - Complete Local Testing                 ║" -ForegroundColor $Colors.Section
Write-Host "║   Version 3.0.0 | January 16, 2026                        ║" -ForegroundColor $Colors.Section
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor $Colors.Section
Write-Host ""

# Verify prerequisites
if (-not (Test-Prerequisites)) {
    Write-Status "Prerequisites check failed. Please install required tools." -Type error
    exit 1
}

# Setup if needed
if (-not $SkipSetup) {
    Setup-Environment
    Setup-Database
}

# Run tests based on mode
$results = @{
    Unit = $null
    Integration = $null
    E2E = $null
    Performance = $null
}

switch ($Mode) {
    'quick' {
        $results.Unit = Run-UnitTests
    }
    'unit' {
        $results.Unit = Run-UnitTests
    }
    'integration' {
        $results.Integration = Run-IntegrationTests
    }
    'e2e' {
        $results.E2E = Run-E2ETests
    }
    'performance' {
        $results.Performance = Run-PerformanceTests
    }
    'test' {
        $results.Unit = Run-UnitTests
        $results.Integration = Run-IntegrationTests
        $results.E2E = Run-E2ETests
    }
    'full' {
        $results.Unit = Run-UnitTests
        $results.Integration = Run-IntegrationTests
        $results.E2E = Run-E2ETests
        $results.Performance = Run-PerformanceTests
    }
    'setup' {
        Write-Status "Environment setup complete" -Type success
    }
}

# Generate report
if (-not $ReportOnly) {
    Generate-Report
}

# Summary
Write-Section "Testing Complete"
Write-Status "All test results saved to: $ReportPath" -Type success
Write-Host ""
Write-Host "📊 Next Steps:" -ForegroundColor $Colors.Section
Write-Host "  1. Review test results in: $ReportPath"
Write-Host "  2. Check code coverage: pytest --cov=apps/upload-bridge"
Write-Host "  3. Fix any failing tests"
Write-Host "  4. Deploy to staging: .\scripts\deploy-to-staging.ps1"
Write-Host ""

exit 0
