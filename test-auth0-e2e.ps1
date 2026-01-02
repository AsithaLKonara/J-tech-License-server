# Comprehensive Auth0 and License Server E2E Test Script
# Tests the complete authentication flow and license-server endpoints

Write-Host "🧪 Auth0 and License Server E2E Test Suite" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "package.json")) {
    Write-Host "❌ Error: package.json not found. Please run this script from the license-server directory." -ForegroundColor Red
    exit 1
}

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Set default license server URL if not set
if (-not $env:LICENSE_SERVER_URL) {
    $env:LICENSE_SERVER_URL = "https://j-tech-licensing.vercel.app"
    Write-Host "ℹ️  Using default license server URL: $env:LICENSE_SERVER_URL" -ForegroundColor Gray
} else {
    Write-Host "ℹ️  Using license server URL from environment: $env:LICENSE_SERVER_URL" -ForegroundColor Gray
}

# Check if Auth0 domain is set
if (-not $env:AUTH0_DOMAIN) {
    Write-Host ""
    Write-Host "⚠️  Warning: AUTH0_DOMAIN environment variable is not set" -ForegroundColor Yellow
    Write-Host "   Some tests will be skipped. Set it to test Auth0 integration:" -ForegroundColor Yellow
    Write-Host "   `$env:AUTH0_DOMAIN='your-tenant.auth0.com'" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "ℹ️  Auth0 Domain: $env:AUTH0_DOMAIN" -ForegroundColor Gray
}

# Check if test token is set
if (-not $env:TEST_AUTH0_TOKEN) {
    Write-Host "ℹ️  TEST_AUTH0_TOKEN not set - real token test will be skipped" -ForegroundColor Gray
    Write-Host "   To test with a real token, set: `$env:TEST_AUTH0_TOKEN='your-token-here'" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "🚀 Running tests..." -ForegroundColor Green
Write-Host ""

# Run the test suite
try {
    npx ts-node test-auth0-e2e.ts
    $testExitCode = $LASTEXITCODE
} catch {
    Write-Host "❌ Test execution failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan

if ($testExitCode -eq 0) {
    Write-Host "✅ All tests completed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Some tests failed. Please review the output above." -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Troubleshooting Tips:" -ForegroundColor Yellow
    Write-Host "   1. Verify the license server is deployed and accessible" -ForegroundColor Gray
    Write-Host "   2. Check that AUTH0_DOMAIN is set correctly" -ForegroundColor Gray
    Write-Host "   3. Ensure Auth0 callback URLs are configured in Auth0 Dashboard" -ForegroundColor Gray
    Write-Host "   4. Check Vercel environment variables are set" -ForegroundColor Gray
}

exit $testExitCode

