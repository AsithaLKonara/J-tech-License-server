# Set Environment Variables Permanently (User-Level)
# Run this script as Administrator or User-level

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setting Permanent Environment Variables" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test Auth0 Configuration
$AUTH0_DOMAIN = "dev-test-123.us.auth0.com"
$AUTH0_CLIENT_ID = "test-client-id-abc123"
$AUTH0_AUDIENCE = "https://api.test.example.com"
$LICENSE_SERVER_URL = "http://localhost:3000"
$AUTH_SERVER_URL = "http://localhost:3000"

Write-Host "Setting environment variables..." -ForegroundColor Yellow

# Set User-level environment variables (permanent)
[System.Environment]::SetEnvironmentVariable('AUTH0_DOMAIN', $AUTH0_DOMAIN, 'User')
[System.Environment]::SetEnvironmentVariable('AUTH0_CLIENT_ID', $AUTH0_CLIENT_ID, 'User')
[System.Environment]::SetEnvironmentVariable('AUTH0_AUDIENCE', $AUTH0_AUDIENCE, 'User')
[System.Environment]::SetEnvironmentVariable('LICENSE_SERVER_URL', $LICENSE_SERVER_URL, 'User')
[System.Environment]::SetEnvironmentVariable('AUTH_SERVER_URL', $AUTH_SERVER_URL, 'User')

Write-Host "✅ Environment variables set permanently:" -ForegroundColor Green
Write-Host "   AUTH0_DOMAIN = $AUTH0_DOMAIN" -ForegroundColor Gray
Write-Host "   AUTH0_CLIENT_ID = $AUTH0_CLIENT_ID" -ForegroundColor Gray
Write-Host "   AUTH0_AUDIENCE = $AUTH0_AUDIENCE" -ForegroundColor Gray
Write-Host "   LICENSE_SERVER_URL = $LICENSE_SERVER_URL" -ForegroundColor Gray
Write-Host "   AUTH_SERVER_URL = $AUTH_SERVER_URL" -ForegroundColor Gray
Write-Host ""

Write-Host "⚠️  NOTE: These are TEST values!" -ForegroundColor Yellow
Write-Host "   Replace with your actual Auth0 credentials for production use." -ForegroundColor Yellow
Write-Host ""

Write-Host "💡 TIP: Restart your terminal/PowerShell for changes to take effect." -ForegroundColor Cyan
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

