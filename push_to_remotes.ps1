# Script to push to both sub-repositories in monorepo
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🚀 UPLOADING CHANGES TO GITHUB REPOSITORIES 🚀               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$repoPath = "c:\Users\asith\OneDrive\Documents\Projects\upload_bridge"
Set-Location $repoPath

# Check current status
Write-Host "📋 CURRENT REPOSITORY STATUS:" -ForegroundColor Yellow
git status --short
Write-Host ""

# Get commit count
$commitCount = (git rev-list --count origin/main..main 2>$null) -as [int]
Write-Host "📊 COMMITS AHEAD:" -ForegroundColor Yellow
Write-Host "  Ahead of origin/main: $commitCount commits" -ForegroundColor Green
Write-Host ""

# Show remotes
Write-Host "🔗 CONFIGURED REMOTES:" -ForegroundColor Yellow
git remote -v | ForEach-Object { Write-Host "  $_" -ForegroundColor Green }
Write-Host ""

# Show recent commits
Write-Host "📝 LAST 3 COMMITS:" -ForegroundColor Yellow
git log --oneline -3 | ForEach-Object { Write-Host "  $_" -ForegroundColor Cyan }
Write-Host ""

# Push to origin
Write-Host "⏳ PUSHING TO ORIGIN (Main Upload Bridge Repository)..." -ForegroundColor Cyan
Write-Host "  Repository: J-Tech-Pixel-LED---Upload-Bridge" -ForegroundColor Gray
Write-Host "  URL: https://github.com/AsithaLKonara/J-Tech-Pixel-LED---Upload-Bridge.git" -ForegroundColor Gray
Write-Host "  Branch: main" -ForegroundColor Gray
Write-Host ""

try {
    $output = git push origin main 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully pushed to origin/main" -ForegroundColor Green
        Write-Host "Output: $output" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  Push attempt returned code: $LASTEXITCODE" -ForegroundColor Yellow
        Write-Host "Output: $output" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Error pushing to origin: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "⏳ PUSHING TO LICENSE-SERVER (Web Dashboard Repository)..." -ForegroundColor Cyan
Write-Host "  Repository: J-tech-License-server" -ForegroundColor Gray
Write-Host "  URL: https://github.com/AsithaLKonara/J-tech-License-server.git" -ForegroundColor Gray
Write-Host "  Branch: main" -ForegroundColor Gray
Write-Host ""

try {
    $output = git push license-server main 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully pushed to license-server/main" -ForegroundColor Green
        Write-Host "Output: $output" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  Push attempt returned code: $LASTEXITCODE" -ForegroundColor Yellow
        Write-Host "Output: $output" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Error pushing to license-server: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Final status
Write-Host ""
Write-Host "✅ FINAL STATUS:" -ForegroundColor Green
Write-Host ""
Write-Host "Local Commits:" -ForegroundColor Yellow
git log --oneline origin/main..main 2>$null | ForEach-Object { Write-Host "  • $_" -ForegroundColor Cyan } -OutVariable localCommits
if ($null -eq $localCommits -or $localCommits.Count -eq 0) {
    Write-Host "  ✅ No local commits ahead - all changes synchronized!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Remote Status:" -ForegroundColor Yellow
Write-Host "  origin: $(git ls-remote origin main 2>$null | awk '{print $1}' | Select-Object -First 1)" -ForegroundColor Green
Write-Host "  license-server: $(git ls-remote license-server main 2>$null | awk '{print $1}' | Select-Object -First 1)" -ForegroundColor Green

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ PUSH OPERATION COMPLETE                                   ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
