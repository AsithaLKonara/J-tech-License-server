# E2E Communication Test Script
# Tests communication between upload bridge desktop app and web dashboard

$ErrorActionPreference = "Stop"
$projectRoot = (Get-Item $PSScriptRoot).Parent.FullName
$baseUrl = "http://localhost:8000"
$apiBaseUrl = "$baseUrl/api/v2"

$testResults = @{
    Passed = 0
    Failed = 0
    Total = 0
    Details = @()
}

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers = @{},
        [string]$Body = $null,
        [int]$ExpectedStatus = 200
    )
    
    $testResults.Total++
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            ContentType = "application/json"
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = $Body
        }
        
        $response = Invoke-RestMethod @params
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq $ExpectedStatus -or -not $statusCode) {
            Write-Host "  ✅ PASSED" -ForegroundColor Green
            $testResults.Passed++
            $testResults.Details += @{
                Test = $Name
                Status = "PASSED"
                Response = $response
            }
            return $true
        } else {
            Write-Host "  ❌ FAILED - Expected status $ExpectedStatus, got $statusCode" -ForegroundColor Red
            $testResults.Failed++
            $testResults.Details += @{
                Test = $Name
                Status = "FAILED"
                Error = "Expected status $ExpectedStatus, got $statusCode"
            }
            return $false
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq $ExpectedStatus) {
            Write-Host "  ✅ PASSED (expected error)" -ForegroundColor Green
            $testResults.Passed++
            $testResults.Details += @{
                Test = $Name
                Status = "PASSED"
            }
            return $true
        } else {
            Write-Host "  ❌ FAILED - $($_.Exception.Message)" -ForegroundColor Red
            $testResults.Failed++
            $testResults.Details += @{
                Test = $Name
                Status = "FAILED"
                Error = $_.Exception.Message
            }
            return $false
        }
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "E2E Communication Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Testing communication with: $baseUrl" -ForegroundColor White
Write-Host ""

# Test 1: Health Check
Write-Host "1. Health Check Endpoint" -ForegroundColor Cyan
Test-Endpoint -Name "Health Check" -Method "GET" -Url "$apiBaseUrl/health"
Write-Host ""

# Test 2: Login (with test credentials)
Write-Host "2. Authentication Tests" -ForegroundColor Cyan
$loginBody = @{
    email = "user1@test.com"
    password = "password123"
} | ConvertTo-Json

$loginResponse = $null
try {
    $loginResponse = Invoke-RestMethod -Uri "$apiBaseUrl/auth/login" -Method "POST" -Body $loginBody -ContentType "application/json"
    Write-Host "  ✅ Login successful" -ForegroundColor Green
    $testResults.Passed++
    $testResults.Total++
    
    $sessionToken = $loginResponse.session_token
    $entitlementToken = $loginResponse.entitlement_token
    
    if ($sessionToken -and $entitlementToken) {
        Write-Host "  ✅ Tokens received" -ForegroundColor Green
        
        # Test 3: License Validation (with token)
        Write-Host ""
        Write-Host "3. License Validation Tests" -ForegroundColor Cyan
        
        $authHeaders = @{
            "Authorization" = "Bearer $entitlementToken"
        }
        
        Test-Endpoint -Name "License Validate" -Method "GET" -Url "$apiBaseUrl/license/validate" -Headers $authHeaders
        Test-Endpoint -Name "License Info" -Method "GET" -Url "$apiBaseUrl/license/info" -Headers $authHeaders
        
        # Test 4: Device Registration
        Write-Host ""
        Write-Host "4. Device Management Tests" -ForegroundColor Cyan
        
        $deviceBody = @{
            device_id = "TEST_DEVICE_$(Get-Date -Format 'yyyyMMddHHmmss')"
            device_name = "Test Device"
        } | ConvertTo-Json
        
        try {
            $deviceResponse = Invoke-RestMethod -Uri "$apiBaseUrl/devices/register" -Method "POST" -Body $deviceBody -ContentType "application/json" -Headers $authHeaders
            Write-Host "  ✅ Device registration successful" -ForegroundColor Green
            $testResults.Passed++
            $testResults.Total++
            
            # List devices
            Test-Endpoint -Name "List Devices" -Method "GET" -Url "$apiBaseUrl/devices" -Headers $authHeaders
            
        } catch {
            Write-Host "  ⚠️  Device registration failed: $($_.Exception.Message)" -ForegroundColor Yellow
            $testResults.Failed++
            $testResults.Total++
        }
        
    } else {
        Write-Host "  ⚠️  Tokens not received in login response" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "  ❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "     Make sure test data is seeded (user1@test.com / password123)" -ForegroundColor Yellow
    $testResults.Failed++
    $testResults.Total++
}

# Test 5: Invalid credentials
Write-Host ""
Write-Host "5. Error Handling Tests" -ForegroundColor Cyan
$invalidLoginBody = @{
    email = "invalid@test.com"
    password = "wrongpassword"
} | ConvertTo-Json

try {
    Invoke-RestMethod -Uri "$apiBaseUrl/auth/login" -Method "POST" -Body $invalidLoginBody -ContentType "application/json" -ErrorAction Stop
    Write-Host "  ❌ Should have failed with invalid credentials" -ForegroundColor Red
    $testResults.Failed++
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 401 -or $statusCode -eq 422) {
        Write-Host "  ✅ Correctly rejected invalid credentials" -ForegroundColor Green
        $testResults.Passed++
    } else {
        Write-Host "  ⚠️  Unexpected status code: $statusCode" -ForegroundColor Yellow
        $testResults.Failed++
    }
    $testResults.Total++
}

# Test 6: Unauthorized access
Write-Host ""
try {
    Invoke-RestMethod -Uri "$apiBaseUrl/license/validate" -Method "GET" -ErrorAction Stop
    Write-Host "  ❌ Should require authentication" -ForegroundColor Red
    $testResults.Failed++
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 401) {
        Write-Host "  ✅ Correctly requires authentication" -ForegroundColor Green
        $testResults.Passed++
    } else {
        Write-Host "  ⚠️  Unexpected status code: $statusCode" -ForegroundColor Yellow
        $testResults.Failed++
    }
    $testResults.Total++
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total Tests: $($testResults.Total)" -ForegroundColor White
Write-Host "Passed: $($testResults.Passed)" -ForegroundColor Green
Write-Host "Failed: $($testResults.Failed)" -ForegroundColor $(if ($testResults.Failed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($testResults.Failed -eq 0) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Some tests failed. Check the output above for details." -ForegroundColor Red
    exit 1
}
