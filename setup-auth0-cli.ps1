# Auth0 CLI Setup Script for Upload Bridge License Server
# 
# This script uses Auth0 CLI to configure Auth0 settings programmatically.
# It automates the setup process similar to how Vercel CLI works.
#
# Prerequisites:
#   1. Auth0 CLI installed (see AUTH0_CLI_SETUP.md)
#   2. Auth0 account created
#   3. Vercel deployment URL (optional, for callback URLs)

param(
    [string]$Auth0Domain = "",
    [string]$VercelUrl = "https://j-tech-licensing.vercel.app",
    [string]$AppName = "Upload Bridge License Server",
    [string]$ApiName = "Upload Bridge License API",
    [string]$ApiIdentifier = "https://j-tech-licensing.vercel.app"
)

Write-Host "🔐 Auth0 CLI Setup for Upload Bridge License Server" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Check if Auth0 CLI is installed
try {
    $auth0Version = auth0 --version 2>&1
    Write-Host "✅ Auth0 CLI found: $auth0Version" -ForegroundColor Green
} catch {
    Write-Host "❌ Auth0 CLI not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Auth0 CLI first:" -ForegroundColor Yellow
    Write-Host "  Option 1 (Scoop):" -ForegroundColor Gray
    Write-Host "    scoop bucket add auth0 https://github.com/auth0/scoop-auth0-cli.git" -ForegroundColor Gray
    Write-Host "    scoop install auth0" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Option 2 (npm):" -ForegroundColor Gray
    Write-Host "    npm install -g @auth0/auth0-cli" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Check if logged in
Write-Host "Checking Auth0 authentication..." -ForegroundColor Yellow
try {
    $tenant = auth0 tenants list 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Not authenticated. Please login:" -ForegroundColor Yellow
        Write-Host "   auth0 login" -ForegroundColor Gray
        Write-Host ""
        
        $login = Read-Host "Would you like to login now? (Y/n)"
        if ($login -eq "" -or $login -eq "Y" -or $login -eq "y") {
            auth0 login
            if ($LASTEXITCODE -ne 0) {
                Write-Host "❌ Login failed" -ForegroundColor Red
                exit 1
            }
        } else {
            exit 1
        }
    } else {
        Write-Host "✅ Authenticated with Auth0" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Failed to check authentication" -ForegroundColor Red
    exit 1
}

# Get Auth0 domain if not provided
if ([string]::IsNullOrWhiteSpace($Auth0Domain)) {
    Write-Host ""
    Write-Host "Auth0 Domain (e.g., your-tenant.auth0.com):" -ForegroundColor Yellow
    $Auth0Domain = Read-Host "Enter your Auth0 domain"
    
    if ([string]::IsNullOrWhiteSpace($Auth0Domain)) {
        Write-Host "❌ Auth0 domain is required" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Auth0 Domain: $Auth0Domain" -ForegroundColor Gray
Write-Host "  Vercel URL: $VercelUrl" -ForegroundColor Gray
Write-Host "  App Name: $AppName" -ForegroundColor Gray
Write-Host "  API Name: $ApiName" -ForegroundColor Gray
Write-Host "  API Identifier: $ApiIdentifier" -ForegroundColor Gray
Write-Host ""

# Check if Auth0 Deploy CLI is installed (optional but recommended)
$hasDeployCli = $false
try {
    $deployVersion = auth0-deploy --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $hasDeployCli = $true
        Write-Host "✅ Auth0 Deploy CLI found: $deployVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Auth0 Deploy CLI not found (optional)" -ForegroundColor Yellow
    Write-Host "   Install with: npm install -g auth0-deploy-cli" -ForegroundColor Gray
}

Write-Host ""
Write-Host "📋 Setup Steps:" -ForegroundColor Cyan
Write-Host ""

# Step 1: List existing applications
Write-Host "1. Checking existing applications..." -ForegroundColor Yellow
try {
    $apps = auth0 apps list --json 2>&1 | ConvertFrom-Json
    Write-Host "   Found $($apps.Count) existing application(s)" -ForegroundColor Gray
    
    $existingApp = $apps | Where-Object { $_.name -eq $AppName }
    if ($existingApp) {
        Write-Host "   ✅ Application '$AppName' already exists (ID: $($existingApp.client_id))" -ForegroundColor Green
        $appId = $existingApp.client_id
    } else {
        Write-Host "   ℹ️  Application '$AppName' not found - will need to be created manually or via Deploy CLI" -ForegroundColor Gray
        Write-Host "   (Auth0 CLI doesn't support creating apps with full config - use Dashboard or Deploy CLI)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  Could not list applications (may need Management API access)" -ForegroundColor Yellow
}

# Step 2: Provide configuration instructions
Write-Host ""
Write-Host "2. Configuration Instructions:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   Since Auth0 CLI has limitations for application creation, here's what to configure:" -ForegroundColor Gray
Write-Host ""
Write-Host "   📝 Application Settings (in Auth0 Dashboard):" -ForegroundColor Cyan
Write-Host "      Application Type: Native" -ForegroundColor Gray
Write-Host "      Allowed Callback URLs:" -ForegroundColor Gray
Write-Host "        - http://localhost:3000/callback" -ForegroundColor White
Write-Host "        - $VercelUrl/callback" -ForegroundColor White
Write-Host "      Allowed Logout URLs:" -ForegroundColor Gray
Write-Host "        - http://localhost:3000" -ForegroundColor White
Write-Host "        - $VercelUrl" -ForegroundColor White
Write-Host "      Allowed Web Origins:" -ForegroundColor Gray
Write-Host "        - http://localhost:3000" -ForegroundColor White
Write-Host "        - $VercelUrl" -ForegroundColor White
Write-Host "      Grant Types:" -ForegroundColor Gray
Write-Host "        - Authorization Code" -ForegroundColor White
Write-Host "        - Refresh Token" -ForegroundColor White
Write-Host ""

# Step 3: Use Deploy CLI if available
if ($hasDeployCli) {
    Write-Host "3. Using Auth0 Deploy CLI for configuration..." -ForegroundColor Yellow
    
    $configDir = Join-Path $PSScriptRoot "auth0-config"
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir | Out-Null
        Write-Host "   Created config directory: $configDir" -ForegroundColor Gray
    }
    
    Write-Host "   ⚠️  Configuration files need to be created manually" -ForegroundColor Yellow
    Write-Host "   See AUTH0_CLI_SETUP.md for example configuration" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "3. Skipping Deploy CLI configuration (not installed)" -ForegroundColor Gray
    Write-Host ""
}

# Step 4: Test authentication
Write-Host "4. Testing authentication flow..." -ForegroundColor Yellow
Write-Host "   Run 'auth0 test login' to test the authentication flow" -ForegroundColor Gray
Write-Host ""

# Summary
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Configure application in Auth0 Dashboard (see instructions above)" -ForegroundColor Gray
Write-Host "  2. Set environment variables:" -ForegroundColor Gray
Write-Host "     `$env:AUTH0_DOMAIN='$Auth0Domain'" -ForegroundColor White
Write-Host "     `$env:AUTH0_CLIENT_ID='<your-client-id>'" -ForegroundColor White
Write-Host "  3. Test authentication: auth0 test login" -ForegroundColor Gray
Write-Host "  4. Run tests: npm run test:auth0" -ForegroundColor Gray
Write-Host ""
Write-Host "For more details, see AUTH0_CLI_SETUP.md" -ForegroundColor Gray
Write-Host ""

