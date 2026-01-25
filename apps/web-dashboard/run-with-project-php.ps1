# Run Laravel commands with project PHP
# This script uses the PHP installed in the project directory

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$phpPath = (Get-ChildItem -Path "$projectRoot\php" -Recurse -Filter "php.exe" -ErrorAction SilentlyContinue | Select-Object -First 1).FullName

if (-not $phpPath) {
    Write-Host "ERROR: PHP not found in project!" -ForegroundColor Red
    Write-Host "Please ensure PHP is installed in: $projectRoot\php" -ForegroundColor Yellow
    exit 1
}

Write-Host "Using PHP: $phpPath" -ForegroundColor Cyan
Write-Host ""

# Get command from arguments
$command = $args -join " "

if ($command) {
    & $phpPath artisan $command
} else {
    Write-Host "Usage: .\run-with-project-php.ps1 <artisan-command>" -ForegroundColor Yellow
    Write-Host "Example: .\run-with-project-php.ps1 migrate --force" -ForegroundColor Cyan
}
