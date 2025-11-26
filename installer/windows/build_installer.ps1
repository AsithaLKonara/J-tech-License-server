# Upload Bridge Windows Installer Build Script
# Requires WiX Toolset (https://wixtoolset.org/)

param(
    [string]$Version = "3.0.0",
    [string]$OutputDir = "dist",
    [switch]$Sign = $false,
    [string]$CertPath = "",
    [string]$CertPassword = ""
)

$ErrorActionPreference = "Stop"

Write-Host "Building Upload Bridge Windows Installer..." -ForegroundColor Cyan

# Check for WiX Toolset
$candle = Get-Command candle.exe -ErrorAction SilentlyContinue
$light = Get-Command light.exe -ErrorAction SilentlyContinue

if (-not $candle -or -not $light) {
    Write-Host "ERROR: WiX Toolset not found!" -ForegroundColor Red
    Write-Host "Please install WiX Toolset from: https://wixtoolset.org/" -ForegroundColor Yellow
    Write-Host "Or add WiX bin directory to PATH" -ForegroundColor Yellow
    exit 1
}

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

# Build MSI
$wxsFile = "windows\upload_bridge.wxs"
$wixobjFile = "$OutputDir\upload_bridge.wixobj"
$msiFile = "$OutputDir\upload_bridge_$Version.msi"

Write-Host "Compiling WiX source..." -ForegroundColor Yellow
& candle.exe -out $wixobjFile $wxsFile

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: WiX compilation failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Linking MSI..." -ForegroundColor Yellow
$lightArgs = @(
    "-out", $msiFile,
    $wixobjFile
)

if ($Sign -and $CertPath) {
    $lightArgs += "-ext", "WixUtilExtension"
    Write-Host "Signing will be done after linking..." -ForegroundColor Yellow
}

& light.exe $lightArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: MSI linking failed!" -ForegroundColor Red
    exit 1
}

# Sign MSI if requested
if ($Sign -and $CertPath) {
    Write-Host "Signing MSI..." -ForegroundColor Yellow
    if ($CertPassword) {
        & signtool.exe sign /f $CertPath /p $CertPassword /t http://timestamp.digicert.com $msiFile
    } else {
        & signtool.exe sign /f $CertPath /t http://timestamp.digicert.com $msiFile
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: MSI signing failed!" -ForegroundColor Yellow
    } else {
        Write-Host "MSI signed successfully!" -ForegroundColor Green
    }
}

Write-Host "`n✅ Installer built successfully: $msiFile" -ForegroundColor Green
Write-Host "`nTo install, run: msiexec /i `"$msiFile`"" -ForegroundColor Cyan

