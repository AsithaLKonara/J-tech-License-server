# Verify Environment Variables
# Quick script to check if test environment variables are set

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Environment Variables Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$vars = @{
    'AUTH0_DOMAIN' = $env:AUTH0_DOMAIN
    'AUTH0_CLIENT_ID' = $env:AUTH0_CLIENT_ID
    'AUTH0_AUDIENCE' = $env:AUTH0_AUDIENCE
    'LICENSE_SERVER_URL' = $env:LICENSE_SERVER_URL
    'AUTH_SERVER_URL' = $env:AUTH_SERVER_URL
}

$allSet = $true
foreach ($key in $vars.Keys) {
    $value = $vars[$key]
    if ($value) {
        Write-Host "✅ $key = $value" -ForegroundColor Green
    } else {
        Write-Host "❌ $key = (not set)" -ForegroundColor Red
        $allSet = $false
    }
}

Write-Host ""

if ($allSet) {
    Write-Host "✅ All environment variables are set!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some environment variables are missing." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To set them, run:" -ForegroundColor Cyan
    Write-Host "   .\apps\upload-bridge\scripts\setup_test_env.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Or set permanently:" -ForegroundColor Cyan
    Write-Host "   .\apps\upload-bridge\scripts\set_env_permanent.ps1" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

