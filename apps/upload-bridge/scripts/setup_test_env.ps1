# Setup Test Environment Variables for Upload Bridge
# PowerShell script for Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Upload Bridge - Test Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test Auth0 Configuration (for OAuth/Social Login testing)
Write-Host "Setting Auth0 test configuration..." -ForegroundColor Yellow

# Sample Auth0 values for testing (replace with your actual Auth0 credentials)
$env:AUTH0_DOMAIN = "dev-test-123.us.auth0.com"
$env:AUTH0_CLIENT_ID = "test-client-id-abc123"
$env:AUTH0_AUDIENCE = "https://api.test.example.com"

# License Server URL (default: localhost:3000)
$env:LICENSE_SERVER_URL = "http://localhost:3000"
$env:AUTH_SERVER_URL = "http://localhost:3000"

Write-Host "✅ Environment variables set:" -ForegroundColor Green
Write-Host "   AUTH0_DOMAIN = $env:AUTH0_DOMAIN" -ForegroundColor Gray
Write-Host "   AUTH0_CLIENT_ID = $env:AUTH0_CLIENT_ID" -ForegroundColor Gray
Write-Host "   AUTH0_AUDIENCE = $env:AUTH0_AUDIENCE" -ForegroundColor Gray
Write-Host "   LICENSE_SERVER_URL = $env:LICENSE_SERVER_URL" -ForegroundColor Gray
Write-Host ""

Write-Host "⚠️  NOTE: These are TEST values!" -ForegroundColor Yellow
Write-Host "   Replace with your actual Auth0 credentials for production use." -ForegroundColor Yellow
Write-Host ""

Write-Host "To use these variables in this PowerShell session:" -ForegroundColor Cyan
Write-Host "   .\apps\upload-bridge\scripts\setup_test_env.ps1" -ForegroundColor White
Write-Host ""

Write-Host "To set permanently (User-level):" -ForegroundColor Cyan
Write-Host "   .\apps\upload-bridge\scripts\set_env_permanent.ps1" -ForegroundColor White
Write-Host ""

Write-Host "To verify variables are set:" -ForegroundColor Cyan
Write-Host "   .\apps\upload-bridge\scripts\verify_env.ps1" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Environment setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

