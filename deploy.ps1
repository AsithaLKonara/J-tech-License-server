# PowerShell Deployment Script for Vercel
# Quick deploy script for Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Upload Bridge License Server" -ForegroundColor Cyan
Write-Host "Vercel Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Yellow
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Host "❌ Node.js not found!" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Node.js found: $($node.Version)" -ForegroundColor Green
Write-Host ""

# Check npm
Write-Host "Checking npm..." -ForegroundColor Yellow
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npm) {
    Write-Host "❌ npm not found!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ npm found" -ForegroundColor Green
Write-Host ""

# Check Vercel CLI
Write-Host "Checking Vercel CLI..." -ForegroundColor Yellow
$vercel = Get-Command vercel -ErrorAction SilentlyContinue
if (-not $vercel) {
    Write-Host "⚠️  Vercel CLI not found. Installing..." -ForegroundColor Yellow
    npm install -g vercel
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install Vercel CLI" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Vercel CLI installed" -ForegroundColor Green
} else {
    Write-Host "✅ Vercel CLI found" -ForegroundColor Green
}
Write-Host ""

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Deploy
Write-Host "Deploying to Vercel..." -ForegroundColor Yellow
Write-Host "Follow the prompts:" -ForegroundColor Cyan
Write-Host "  - Set up and deploy? → Y" -ForegroundColor Gray
Write-Host "  - Link to existing project? → N (first time)" -ForegroundColor Gray
Write-Host "  - Project name? → upload-bridge-license (or press Enter)" -ForegroundColor Gray
Write-Host "  - Directory? → . (press Enter)" -ForegroundColor Gray
Write-Host ""

vercel --prod

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Copy the deployment URL from above" -ForegroundColor White
    Write-Host "  2. Update Upload Bridge config:" -ForegroundColor White
    Write-Host "     python ..\apps\upload-bridge\scripts\update_vercel_url.py <URL>" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. Test the deployment:" -ForegroundColor White
    Write-Host "     curl https://your-project.vercel.app/api/health" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    exit 1
}

