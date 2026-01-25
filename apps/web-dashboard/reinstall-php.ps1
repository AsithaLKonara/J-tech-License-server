$phpUrl = "https://windows.php.net/downloads/releases/php-8.2.30-Win32-vs16-x64.zip"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootDir = (Resolve-Path "$scriptDir\..\..").Path
$zipPath = Join-Path $rootDir "php.zip"
$destinationPath = Join-Path $rootDir "php"

Write-Host "Downloading PHP from $phpUrl..."
Invoke-WebRequest -Uri $phpUrl -OutFile $zipPath

if (-not (Test-Path $zipPath)) {
    Write-Host "Download failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Extracting to $destinationPath..."
# Create directory if it doesn't exist (though it should)
if (-not (Test-Path $destinationPath)) {
    New-Item -ItemType Directory -Path $destinationPath | Out-Null
}

Expand-Archive -Path $zipPath -DestinationPath $destinationPath -Force

Write-Host "Cleaning up zip file..."
Remove-Item $zipPath

Write-Host "Verifying PHP installation..."
$phpExe = Join-Path $destinationPath "php.exe"

if (Test-Path $phpExe) {
    & $phpExe --version
    Write-Host "PHP Reinstalled Successfully!" -ForegroundColor Green
} else {
    Write-Host "PHP executable not found after extraction. Antivirus might have deleted it again." -ForegroundColor Red
}
