# Complete Setup Verification Script
# Verifies all components are set up correctly and can communicate

$ErrorActionPreference = "Stop"
$projectRoot = (Get-Item $PSScriptRoot).Parent.FullName
$webDashboardDir = Join-Path $projectRoot "apps\web-dashboard"
$uploadBridgeDir = Join-Path $projectRoot "apps\upload-bridge"
$baseUrl = "http://localhost:8000"
$apiBaseUrl = "$baseUrl/api/v2"

$verificationResults = @{
    Prerequisites = @{ Passed = 0; Failed = 0; Total = 0 }
    Configuration = @{ Passed = 0; Failed = 0; Total = 0 }
    Database = @{ Passed = 0; Failed = 0; Total = 0 }
    API = @{ Passed = 0; Failed = 0; Total = 0 }
    Communication = @{ Passed = 0; Failed = 0; Total = 0 }
}

function Test-Prerequisite {
    param([string]$Name, [scriptblock]$Check)
    
    $verificationResults.Prerequisites.Total++
    Write-Host "Checking: $Name" -ForegroundColor Yellow
    
    try {
        $result = & $Check
        if ($result) {
            Write-Host "  ✅ $Name" -ForegroundColor Green
            $verificationResults.Prerequisites.Passed++
            return $true
        } else {
            Write-Host "  ❌ $Name" -ForegroundColor Red
            $verificationResults.Prerequisites.Failed++
            return $false
        }
    } catch {
        Write-Host "  ❌ $Name - $($_.Exception.Message)" -ForegroundColor Red
        $verificationResults.Prerequisites.Failed++
        return $false
    }
}

function Test-Configuration {
    param([string]$Name, [scriptblock]$Check)
    
    $verificationResults.Configuration.Total++
    Write-Host "Checking: $Name" -ForegroundColor Yellow
    
    try {
        $result = & $Check
        if ($result) {
            Write-Host "  ✅ $Name" -ForegroundColor Green
            $verificationResults.Configuration.Passed++
            return $true
        } else {
            Write-Host "  ❌ $Name" -ForegroundColor Red
            $verificationResults.Configuration.Failed++
            return $false
        }
    } catch {
        Write-Host "  ❌ $Name - $($_.Exception.Message)" -ForegroundColor Red
        $verificationResults.Configuration.Failed++
        return $false
    }
}

function Test-API {
    param([string]$Name, [string]$Method, [string]$Endpoint, [hashtable]$Headers = @{}, [string]$Body = $null, [int]$ExpectedStatus = 200)
    
    $verificationResults.API.Total++
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    
    try {
        $params = @{
            Uri = "$apiBaseUrl$Endpoint"
            Method = $Method
            Headers = $Headers
            ContentType = "application/json"
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = $Body
        }
        
        $response = Invoke-RestMethod @params
        $statusCode = 200
        
        Write-Host "  ✅ $Name (Status: $statusCode)" -ForegroundColor Green
        $verificationResults.API.Passed++
        return $response
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq $ExpectedStatus) {
            Write-Host "  ✅ $Name (Expected error: $statusCode)" -ForegroundColor Green
            $verificationResults.API.Passed++
            return $null
        } else {
            Write-Host "  ❌ $Name - Status: $statusCode, Error: $($_.Exception.Message)" -ForegroundColor Red
            $verificationResults.API.Failed++
            return $null
        }
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Complete Setup Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Prerequisites
Write-Host "1. Prerequisites" -ForegroundColor Cyan
Write-Host "===============" -ForegroundColor Cyan

Test-Prerequisite "PHP installed" { Get-Command php -ErrorAction SilentlyContinue }
Test-Prerequisite "Composer installed" { Get-Command composer -ErrorAction SilentlyContinue }
Test-Prerequisite "Python installed" { Get-Command python -ErrorAction SilentlyContinue }
Test-Prerequisite "MySQL client available" { Get-Command mysql -ErrorAction SilentlyContinue }

Write-Host ""

# 2. Configuration
Write-Host "2. Configuration" -ForegroundColor Cyan
Write-Host "================" -ForegroundColor Cyan

$envFile = Join-Path $webDashboardDir ".env"
Test-Configuration ".env file exists" { Test-Path $envFile }

if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    Test-Configuration "APP_KEY is set" { $envContent -match 'APP_KEY=base64:' }
    Test-Configuration "DB_CONNECTION is MySQL" { $envContent -match 'DB_CONNECTION=mysql' }
    Test-Configuration "APP_URL is localhost:8000" { $envContent -match 'APP_URL=http://localhost:8000' }
}

$authConfigFile = Join-Path $uploadBridgeDir "config\auth_config.yaml"
Test-Configuration "auth_config.yaml exists" { Test-Path $authConfigFile }

if (Test-Path $authConfigFile) {
    $authConfig = Get-Content $authConfigFile -Raw
    Test-Configuration "auth_server_url is localhost:8000" { $authConfig -match 'auth_server_url:\s*"http://localhost:8000"' }
}

Write-Host ""

# 3. Database
Write-Host "3. Database" -ForegroundColor Cyan
Write-Host "==========" -ForegroundColor Cyan

$verificationResults.Database.Total++
Write-Host "Checking: Database connection" -ForegroundColor Yellow
Push-Location $webDashboardDir
try {
    php artisan db:show 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Database connection successful" -ForegroundColor Green
        $verificationResults.Database.Passed++
        
        # Check if migrations have run
        $verificationResults.Database.Total++
        Write-Host "Checking: Database migrations" -ForegroundColor Yellow
        $migrationCheck = php artisan migrate:status 2>&1
        if ($LASTEXITCODE -eq 0 -and $migrationCheck -match 'Ran') {
            Write-Host "  ✅ Migrations have been run" -ForegroundColor Green
            $verificationResults.Database.Passed++
        } else {
            Write-Host "  ⚠️  Migrations may not have been run" -ForegroundColor Yellow
            $verificationResults.Database.Failed++
        }
        
        # Check if test data is seeded
        $verificationResults.Database.Total++
        Write-Host "Checking: Test data seeded" -ForegroundColor Yellow
        $userCount = php artisan tinker --execute="echo \App\Models\User::count();" 2>&1
        if ($userCount -match '^\d+$' -and [int]$userCount -gt 0) {
            Write-Host "  ✅ Test data found ($userCount users)" -ForegroundColor Green
            $verificationResults.Database.Passed++
        } else {
            Write-Host "  ⚠️  No test data found (run: php artisan db:seed --class=TestDataSeeder)" -ForegroundColor Yellow
            $verificationResults.Database.Failed++
        }
    } else {
        Write-Host "  ❌ Database connection failed" -ForegroundColor Red
        $verificationResults.Database.Failed++
    }
} catch {
    Write-Host "  ❌ Database check failed: $($_.Exception.Message)" -ForegroundColor Red
    $verificationResults.Database.Failed++
}
Pop-Location

Write-Host ""

# 4. API (if server is running)
Write-Host "4. API Endpoints" -ForegroundColor Cyan
Write-Host "================" -ForegroundColor Cyan

$serverRunning = $false
try {
    $healthCheck = Invoke-RestMethod -Uri "$apiBaseUrl/health" -Method GET -TimeoutSec 2 -ErrorAction Stop
    $serverRunning = $true
    Write-Host "✅ Server is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Server is not running (start with: .\scripts\start-local-testing.ps1)" -ForegroundColor Yellow
    Write-Host "   Skipping API tests..." -ForegroundColor Yellow
}

if ($serverRunning) {
    Test-API "Health Check" "GET" "/health"
    
    # Test login
    $loginBody = @{
        email = "user1@test.com"
        password = "password123"
    } | ConvertTo-Json
    
    $loginResponse = Test-API "User Login" "POST" "/auth/login" -Body $loginBody
    
    if ($loginResponse -and $loginResponse.entitlement_token) {
        $token = $loginResponse.entitlement_token
        $authHeaders = @{ "Authorization" = "Bearer $token" }
        
        Test-API "License Validation" "GET" "/license/validate" -Headers $authHeaders
        Test-API "License Info" "GET" "/license/info" -Headers $authHeaders
        Test-API "List Devices" "GET" "/devices" -Headers $authHeaders
    }
    
    # Test error handling
    $invalidLoginBody = @{
        email = "invalid@test.com"
        password = "wrongpassword"
    } | ConvertTo-Json
    
    Test-API "Invalid Login Rejection" "POST" "/auth/login" -Body $invalidLoginBody -ExpectedStatus 401
    Test-API "Unauthorized Access Protection" "GET" "/license/validate" -ExpectedStatus 401
}

Write-Host ""

# 5. Communication
Write-Host "5. Inter-System Communication" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

if ($serverRunning) {
    $verificationResults.Communication.Total++
    Write-Host "Testing: Desktop app can connect to web dashboard" -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod -Uri "$apiBaseUrl/health" -Method GET -ErrorAction Stop
        Write-Host "  ✅ Connection successful" -ForegroundColor Green
        $verificationResults.Communication.Passed++
    } catch {
        Write-Host "  ❌ Connection failed: $($_.Exception.Message)" -ForegroundColor Red
        $verificationResults.Communication.Failed++
    }
} else {
    Write-Host "⚠️  Server not running - cannot test communication" -ForegroundColor Yellow
    $verificationResults.Communication.Total++
    $verificationResults.Communication.Failed++
}

Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$categories = @("Prerequisites", "Configuration", "Database", "API", "Communication")
$allPassed = $true

foreach ($category in $categories) {
    $results = $verificationResults[$category]
    $status = if ($results.Failed -eq 0) { "✅" } else { "❌" }
    $color = if ($results.Failed -eq 0) { "Green" } else { "Red" }
    
    Write-Host "$status $category`: $($results.Passed)/$($results.Total) passed" -ForegroundColor $color
    
    if ($results.Failed -gt 0) {
        $allPassed = $false
    }
}

Write-Host ""

$totalPassed = ($verificationResults.Values | ForEach-Object { $_.Passed } | Measure-Object -Sum).Sum
$totalFailed = ($verificationResults.Values | ForEach-Object { $_.Failed } | Measure-Object -Sum).Sum
$totalTests = ($verificationResults.Values | ForEach-Object { $_.Total } | Measure-Object -Sum).Sum

Write-Host "Overall: $totalPassed/$totalTests tests passed" -ForegroundColor $(if ($totalFailed -eq 0) { "Green" } else { "Yellow" })
Write-Host ""

if ($allPassed) {
    Write-Host "✅ All verifications passed! System is ready for E2E testing." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Start server: .\scripts\start-local-testing.ps1" -ForegroundColor White
    Write-Host "2. Run E2E tests: .\scripts\test-e2e-communication.ps1" -ForegroundColor White
    Write-Host "3. Start desktop app: cd apps\upload-bridge && python main.py" -ForegroundColor White
    exit 0
} else {
    Write-Host "❌ Some verifications failed. Please fix the issues above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "- Run: .\scripts\setup-local-env.ps1" -ForegroundColor White
    Write-Host "- Create database: mysql -u root -p -e 'CREATE DATABASE upload_bridge...'" -ForegroundColor White
    Write-Host "- Run migrations: cd apps\web-dashboard && php artisan migrate --force" -ForegroundColor White
    Write-Host "- Seed test data: cd apps\web-dashboard && php artisan db:seed --class=TestDataSeeder" -ForegroundColor White
    exit 1
}
