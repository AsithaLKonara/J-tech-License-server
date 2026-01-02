# Setup Auth0 Configuration for Vercel (PowerShell)
# This script configures Auth0 environment variables in Vercel

$ErrorActionPreference = "Stop"

Write-Host "🔐 Setting up Auth0 configuration for Vercel..." -ForegroundColor Cyan

# Auth0 Configuration
$AUTH0_DOMAIN = "dev-oczlciw58f2a4oei.us.auth0.com"
$AUTH0_CLIENT_ID = "7kciWD98RzUsktuzXtJkfSmLcr80Ix2X"
$VERCEL_URL = "https://j-tech-licensing.vercel.app"

# Check if vercel CLI is installed
try {
    $null = Get-Command vercel -ErrorAction Stop
} catch {
    Write-Host "❌ Vercel CLI is not installed" -ForegroundColor Red
    Write-Host "   Install it with: npm install -g vercel" -ForegroundColor Yellow
    exit 1
}

# Check if logged in to Vercel
try {
    $null = vercel whoami 2>&1
} catch {
    Write-Host "⚠️  Not logged in to Vercel" -ForegroundColor Yellow
    Write-Host "   Run: vercel login" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Vercel CLI is ready" -ForegroundColor Green
Write-Host ""

# Function to set environment variable
function Set-VercelEnv {
    param(
        [string]$Name,
        [string]$Value,
        [string]$Environment
    )
    
    Write-Host "Setting $Name for $Environment..." -ForegroundColor Cyan
    try {
        # Try to remove existing first (ignore errors)
        vercel env rm $Name $Environment --yes 2>&1 | Out-Null
    } catch {
        # Ignore if doesn't exist
    }
    
    # Add new value
    echo $Value | vercel env add $Name $Environment
}

# Set environment variables for all environments
$environments = @("production", "preview", "development")

foreach ($env in $environments) {
    Write-Host "Setting environment variables for $($env.ToUpper())..." -ForegroundColor Cyan
    Set-VercelEnv -Name "AUTH0_DOMAIN" -Value $AUTH0_DOMAIN -Environment $env
    Set-VercelEnv -Name "AUTH0_CLIENT_ID" -Value $AUTH0_CLIENT_ID -Environment $env
    Write-Host ""
}

Write-Host "✅ Environment variables configured!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Configuration Summary:" -ForegroundColor Cyan
Write-Host "   AUTH0_DOMAIN: $AUTH0_DOMAIN"
Write-Host "   AUTH0_CLIENT_ID: $AUTH0_CLIENT_ID"
Write-Host "   Vercel URL: $VERCEL_URL"
Write-Host ""
Write-Host "🚀 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Redeploy to apply changes: vercel --prod"
Write-Host "   2. Test the health endpoint: Invoke-WebRequest -Uri $VERCEL_URL/api/health"
Write-Host "   3. See VERIFY_AUTH0_SETUP.md for testing instructions"

