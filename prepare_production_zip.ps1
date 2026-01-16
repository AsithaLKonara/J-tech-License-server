<#
.SYNOPSIS
Prepares the Laravel application for Shared Hosting (cPanel) deployment.
.DESCRIPTION
Creates a 'dist' directory with 'upload-bridge-core' and 'public_html' folders.
Automatically updates index.php to point to the correct core path.
#>

$ErrorActionPreference = "Stop"
$ScriptPath = $PSScriptRoot
$SourcePath = Join-Path $ScriptPath "apps\web-dashboard"
$DistPath = Join-Path $ScriptPath "dist"

Write-Host ">>> Starting Production Build Preparation..." -ForegroundColor Cyan

# 1. Clean Dist
if (Test-Path $DistPath) {
    Remove-Item $DistPath -Recurse -Force
    Write-Host "Cleaned old dist folder." -ForegroundColor Gray
}
New-Item -ItemType Directory -Path $DistPath | Out-Null

# 2. Copy Core
Write-Host "Copying logic files..." -ForegroundColor Green
$CorePath = Join-Path $DistPath "upload-bridge-core"
New-Item -ItemType Directory -Path $CorePath | Out-Null

# Exclude list
$Exclude = @(
    "node_modules", ".git", "tests", ".github", ".env", ".env.example",
    "*.php", "*.ps1", "*.sql" # Exclude all root-level utility scripts (except index.php which is managed differently)
)

# Explicitly KEEP index.php and artisan if needed
$Include = @("app", "bootstrap", "config", "database", "public", "resources", "routes", "storage", "vendor", "artisan", "composer.json")

Get-ChildItem $SourcePath -Exclude $Exclude | ForEach-Object {
    Copy-Item $_.FullName -Destination $CorePath -Recurse -Force
}

# 3. Separate Public Folder
Write-Host "Structuring public_html..." -ForegroundColor Green
$PublicSource = Join-Path $CorePath "public"
$PublicDest = Join-Path $DistPath "public_html"

Move-Item $PublicSource $PublicDest

# 4. Patch index.php
Write-Host "Patching public_html/index.php..." -ForegroundColor Yellow
$IndexFile = Join-Path $PublicDest "index.php"
$Content = Get-Content $IndexFile -Raw

# Replace paths
# Default: __DIR__.'/../vendor/autoload.php'
# Target:  __DIR__.'/../projects/upload-bridge-core/vendor/autoload.php'

$NewContent = $Content -replace "__DIR__\.'/../", "__DIR__.'/../projects/upload-bridge-core/"

Set-Content -Path $IndexFile -Value $NewContent

Write-Host ">>> BUILD COMPLETE!" -ForegroundColor Cyan
Write-Host "Upload contents of 'dist' as per SHARED_HOSTING_GUIDE.md" -ForegroundColor White
Write-Host "Location: $DistPath" -ForegroundColor White
