# Enable MySQL Extension in PHP
# Automatically configures php.ini to enable pdo_mysql extension

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Enable MySQL Extension in PHP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Find PHP installation
try {
    $phpPath = (Get-Command php).Source
    $phpDir = Split-Path $phpPath
    Write-Host "PHP Installation: $phpDir" -ForegroundColor White
} catch {
    Write-Host "❌ PHP not found in PATH!" -ForegroundColor Red
    Write-Host "   Please install PHP and add it to PATH" -ForegroundColor Yellow
    exit 1
}

# Check if extension exists
$extDir = "$phpDir\ext"
if (-not (Test-Path "$extDir\php_pdo_mysql.dll")) {
    Write-Host "❌ php_pdo_mysql.dll not found in $extDir" -ForegroundColor Red
    Write-Host "   Please install PHP with MySQL support" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ MySQL extension found: $extDir\php_pdo_mysql.dll" -ForegroundColor Green

# Find or create php.ini
$iniFile = "$phpDir\php.ini"
if (-not (Test-Path $iniFile)) {
    Write-Host "php.ini not found. Creating from template..." -ForegroundColor Yellow
    
    if (Test-Path "$phpDir\php.ini-development") {
        Copy-Item "$phpDir\php.ini-development" $iniFile
        Write-Host "✅ Created php.ini from php.ini-development" -ForegroundColor Green
    } elseif (Test-Path "$phpDir\php.ini-production") {
        Copy-Item "$phpDir\php.ini-production" $iniFile
        Write-Host "✅ Created php.ini from php.ini-production" -ForegroundColor Green
    } else {
        Write-Host "❌ No php.ini template found" -ForegroundColor Red
        Write-Host "   Please create php.ini manually" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "✅ php.ini found: $iniFile" -ForegroundColor Green
}

# Backup php.ini
$backupFile = "$iniFile.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
Copy-Item $iniFile $backupFile -Force
Write-Host "✅ Backup created: $backupFile" -ForegroundColor Green

# Read php.ini content
$content = Get-Content $iniFile -Raw

# Update extension_dir
Write-Host ""
Write-Host "Updating extension_dir..." -ForegroundColor Yellow
$content = $content -replace ';extension_dir = "ext"', "extension_dir = `"$extDir`""
$content = $content -replace 'extension_dir = "C:\\php\\ext"', "extension_dir = `"$extDir`""
$content = $content -replace 'extension_dir = "ext"', "extension_dir = `"$extDir`""

# Enable pdo_mysql extension
Write-Host "Enabling pdo_mysql extension..." -ForegroundColor Yellow
if ($content -match ';extension=pdo_mysql') {
    $content = $content -replace ';extension=pdo_mysql', 'extension=pdo_mysql'
    Write-Host "✅ Uncommented extension=pdo_mysql" -ForegroundColor Green
} elseif ($content -match 'extension=pdo_mysql') {
    Write-Host "✅ extension=pdo_mysql already enabled" -ForegroundColor Green
} else {
    # Add extension if not found
    $content += "`nextension=pdo_mysql`n"
    Write-Host "✅ Added extension=pdo_mysql" -ForegroundColor Green
}

# Write updated php.ini
Set-Content $iniFile $content -NoNewline

# Verify extension loads
Write-Host ""
Write-Host "Verifying extension loads..." -ForegroundColor Yellow
$phpModules = php -m 2>&1
if ($phpModules -match "pdo_mysql") {
    Write-Host "✅ pdo_mysql extension is now loaded!" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ MySQL extension enabled successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Extension still not loading" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check extension_dir in php.ini points to: $extDir" -ForegroundColor White
    Write-Host "2. Verify php_pdo_mysql.dll exists in: $extDir" -ForegroundColor White
    Write-Host "3. Check for errors: php -m" -ForegroundColor White
    Write-Host "4. Restart any running PHP processes" -ForegroundColor White
    exit 1
}
