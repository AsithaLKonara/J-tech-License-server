# Test Connection to Local License Server
# Quick script to verify Upload Bridge can connect to local license server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Local License Server Connection" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$serverUrl = "http://localhost:8000"

# Test 1: Health Check
Write-Host "Test 1: Health Check Endpoint" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$serverUrl/api/v2/health" -Method GET -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Health check successful" -ForegroundColor Green
        Write-Host "   Response: $($response.Content)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Health check failed (Status: $($response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Cannot connect to license server" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure the license server is running:" -ForegroundColor Yellow
    Write-Host "   cd apps\web-dashboard" -ForegroundColor Cyan
    Write-Host "   php artisan serve" -ForegroundColor Cyan
    exit 1
}

Write-Host ""

# Test 2: Login Endpoint (without credentials)
Write-Host "Test 2: Login Endpoint Available" -ForegroundColor Yellow
try {
    $body = @{
        email = "test@example.com"
        password = "password123"
        device_id = "TEST_DEVICE"
        device_name = "Test Device"
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "$serverUrl/api/v2/auth/login" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Login endpoint working" -ForegroundColor Green
        $responseData = $response.Content | ConvertFrom-Json
        if ($responseData.session_token) {
            Write-Host "   Login successful!" -ForegroundColor Green
            Write-Host "   Session token received: $($responseData.session_token.Substring(0, 20))..." -ForegroundColor Gray
        }
    } elseif ($response.StatusCode -eq 401) {
        Write-Host "⚠️  Login endpoint exists but credentials invalid" -ForegroundColor Yellow
        Write-Host "   This is expected - endpoint is working correctly" -ForegroundColor Gray
    } else {
        Write-Host "❌ Unexpected response (Status: $($response.StatusCode))" -ForegroundColor Red
    }
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "⚠️  Invalid credentials (expected)" -ForegroundColor Yellow
        Write-Host "   Endpoint is working correctly" -ForegroundColor Gray
    } else {
        Write-Host "❌ Login endpoint error" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# Test 3: CORS Headers
Write-Host "Test 3: CORS Configuration" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$serverUrl/api/v2/health" -Method OPTIONS -UseBasicParsing -ErrorAction Stop
    $corsHeaders = $response.Headers["Access-Control-Allow-Origin"]
    if ($corsHeaders) {
        Write-Host "✅ CORS configured" -ForegroundColor Green
        Write-Host "   Allow-Origin: $corsHeaders" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  CORS headers not found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not check CORS (may not be critical)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Connection Test Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "If all tests passed, you can now:" -ForegroundColor Yellow
Write-Host "1. Set environment variable:" -ForegroundColor White
Write-Host "   `$env:LICENSE_SERVER_URL = 'http://localhost:8000'" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Run Upload Bridge application:" -ForegroundColor White
Write-Host "   python main.py" -ForegroundColor Cyan
Write-Host ""
