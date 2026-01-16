# PowerShell Test Runner
# Runs all E2E tests for the Upload Bridge application

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Configuration
$API_URL = if ($env:LICENSE_SERVER_URL) { $env:LICENSE_SERVER_URL } else { "http://localhost:8000" }
$env:LICENSE_SERVER_URL = $API_URL

Write-ColorOutput Green "========================================"
Write-ColorOutput Green "Upload Bridge Test Suite"
Write-ColorOutput Green "========================================"
Write-Output ""

# Check if API is accessible
Write-ColorOutput Yellow "Checking API accessibility..."
try {
    $response = Invoke-WebRequest -Uri "$API_URL/api/v2/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-ColorOutput Green "✓ API is accessible"
    } else {
        Write-ColorOutput Red "✗ API returned status code: $($response.StatusCode)"
        exit 1
    }
} catch {
    Write-ColorOutput Red "✗ API is not accessible at $API_URL"
    Write-Output "Error: $_"
    Write-Output "Please ensure the application is running before running tests."
    exit 1
}

# Test results tracking
$script:Passed = 0
$script:Failed = 0

# Function to run a test file
function Run-Test {
    param(
        [string]$TestFile,
        [string]$TestName
    )
    
    Write-Output ""
    Write-ColorOutput Yellow "Running: $TestName"
    Write-Output "----------------------------------------"
    
    $testPath = Join-Path $PSScriptRoot ".." $TestFile
    $testPath = Resolve-Path $testPath -ErrorAction SilentlyContinue
    
    if (-not $testPath) {
        Write-ColorOutput Yellow "⚠ Test file not found: $TestFile (skipping)"
        return
    }
    
    Push-Location (Split-Path $testPath -Parent)
    try {
        $env:LICENSE_SERVER_URL = $API_URL
        $result = node run-test.js $TestFile 2>&1
        $exitCode = $LASTEXITCODE
        
        Write-Output $result
        
        if ($exitCode -eq 0) {
            Write-ColorOutput Green "✓ $TestName PASSED"
            $script:Passed++
            return $true
        } else {
            Write-ColorOutput Red "✗ $TestName FAILED"
            $script:Failed++
            return $false
        }
    } finally {
        Pop-Location
    }
}

# Change to tests directory
$TestsDir = Join-Path $PSScriptRoot ".."
Push-Location $TestsDir

try {
    # Health Check Tests
    Write-Output ""
    Write-ColorOutput Green "=== Health Check Tests ==="
    Run-Test "tests/api/health-e2e.test.js" "Health Check E2E Tests"
    
    # Authentication Tests
    Write-Output ""
    Write-ColorOutput Green "=== Authentication Tests ==="
    Run-Test "tests/api/auth-e2e.test.js" "Authentication E2E Tests"
    
    # License Tests
    Write-Output ""
    Write-ColorOutput Green "=== License Tests ==="
    Run-Test "tests/api/license-e2e.test.js" "License E2E Tests"
    
    # Device Tests
    Write-Output ""
    Write-ColorOutput Green "=== Device Tests ==="
    Run-Test "tests/api/device-e2e.test.js" "Device E2E Tests"
    
    # All APIs Tests
    Write-Output ""
    Write-ColorOutput Green "=== All APIs Tests ==="
    Run-Test "tests/api/allAPIs.test.js" "All APIs Tests"
    
    # Security Tests
    Write-Output ""
    Write-ColorOutput Green "=== Security Tests ==="
    if (Test-Path "tests/security/security-tests.test.js") {
        Run-Test "tests/security/security-tests.test.js" "Security Tests"
    } else {
        Write-ColorOutput Yellow "⚠ Security tests not found, skipping..."
    }
    
    # Summary
    Write-Output ""
    Write-ColorOutput Green "========================================"
    Write-ColorOutput Green "Test Summary"
    Write-ColorOutput Green "========================================"
    Write-Output "Passed: $script:Passed"
    Write-ColorOutput $(if ($script:Failed -eq 0) { "Green" } else { "Red" }) "Failed: $script:Failed"
    Write-Output ""
    
    if ($script:Failed -eq 0) {
        Write-ColorOutput Green "All tests passed! ✓"
        exit 0
    } else {
        Write-ColorOutput Red "Some tests failed. Please review the output above."
        exit 1
    }
} finally {
    Pop-Location
}
