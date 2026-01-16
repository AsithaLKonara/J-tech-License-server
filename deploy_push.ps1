#!/usr/bin/env pwsh
# Deployment Push Script for Upload Bridge Monorepo

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🚀 UPLOADING TO GITHUB REPOSITORIES 🚀                       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$repoPath = "c:\Users\asith\OneDrive\Documents\Projects\upload_bridge"
Set-Location $repoPath

# Before status
Write-Host "📊 PRE-PUSH STATUS:" -ForegroundColor Yellow
Write-Host "Branch: main" -ForegroundColor Gray
$statusBefore = git status --porcelain
if ($statusBefore -eq "") {
    Write-Host "Working tree: CLEAN ✅" -ForegroundColor Green
} else {
    Write-Host "Working tree: HAS CHANGES ⚠️" -ForegroundColor Yellow
}

$aheadCount = git rev-list --count origin/main..main 2>$null
Write-Host "Commits ahead of origin/main: $aheadCount" -ForegroundColor Green
Write-Host ""

# PUSH 1: Origin
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "⏳ PUSHING TO ORIGIN (Main Upload Bridge Repository)" -ForegroundColor Cyan
Write-Host "Repository: J-Tech-Pixel-LED---Upload-Bridge" -ForegroundColor Gray
Write-Host "URL: https://github.com/AsithaLKonara/J-Tech-Pixel-LED---Upload-Bridge.git" -ForegroundColor Gray
Write-Host ""

try {
    $pushOutput1 = git push origin main 2>&1
    $exitCode1 = $LASTEXITCODE
    
    if ($exitCode1 -eq 0) {
        Write-Host "✅ SUCCESSFULLY PUSHED TO ORIGIN" -ForegroundColor Green
        Write-Host "Output: $pushOutput1" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ Push to origin returned exit code: $exitCode1" -ForegroundColor Yellow
        Write-Host "Output: $pushOutput1" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ ERROR pushing to origin: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "⏳ PUSHING TO LICENSE-SERVER (Web Dashboard Repository)" -ForegroundColor Cyan
Write-Host "Repository: J-tech-License-server" -ForegroundColor Gray
Write-Host "URL: https://github.com/AsithaLKonara/J-tech-License-server.git" -ForegroundColor Gray
Write-Host ""

try {
    $pushOutput2 = git push license-server main 2>&1
    $exitCode2 = $LASTEXITCODE
    
    if ($exitCode2 -eq 0) {
        Write-Host "✅ SUCCESSFULLY PUSHED TO LICENSE-SERVER" -ForegroundColor Green
        Write-Host "Output: $pushOutput2" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ Push to license-server returned exit code: $exitCode2" -ForegroundColor Yellow
        Write-Host "Output: $pushOutput2" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ ERROR pushing to license-server: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📊 POST-PUSH STATUS:" -ForegroundColor Yellow
Write-Host ""

$statusAfter = git status
Write-Host $statusAfter

Write-Host ""
Write-Host "🔍 REMOTE VERIFICATION:" -ForegroundColor Yellow
Write-Host ""

$originHead = git ls-remote origin main 2>$null | awk '{print $1}'
$licenseHead = git ls-remote license-server main 2>$null | awk '{print $1}'
$localHead = git rev-parse HEAD

Write-Host "Local HEAD: $localHead" -ForegroundColor Green
Write-Host "Origin HEAD: $originHead" -ForegroundColor Green
Write-Host "License-Server HEAD: $licenseHead" -ForegroundColor Green

if ($localHead -eq $originHead) {
    Write-Host "✅ Origin is SYNCHRONIZED" -ForegroundColor Green
} else {
    Write-Host "⚠️ Origin may not be synchronized" -ForegroundColor Yellow
}

if ($localHead -eq $licenseHead) {
    Write-Host "✅ License-Server is SYNCHRONIZED" -ForegroundColor Green
} else {
    Write-Host "⚠️ License-Server may not be synchronized" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ DEPLOYMENT PUSH OPERATION COMPLETE                        ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Summary:" -ForegroundColor Yellow
Write-Host "  • Origin Push: $(if ($exitCode1 -eq 0) { '✅ SUCCESS' } else { '⚠️ CHECK STATUS' })" -ForegroundColor Gray
Write-Host "  • License-Server Push: $(if ($exitCode2 -eq 0) { '✅ SUCCESS' } else { '⚠️ CHECK STATUS' })" -ForegroundColor Gray
Write-Host "  • Total Commits Pushed: $aheadCount" -ForegroundColor Gray
Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Verify both repositories updated on GitHub" -ForegroundColor Gray
Write-Host "  2. Pull changes in staging environment" -ForegroundColor Gray
Write-Host "  3. Run staging deployment tests" -ForegroundColor Gray
Write-Host "  4. Plan production deployment" -ForegroundColor Gray
