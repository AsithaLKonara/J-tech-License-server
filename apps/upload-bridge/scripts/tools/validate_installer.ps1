param(
    [string]$Installer = ".\dist\UploadBridge_Setup_3.0.0.exe"
)

$ErrorActionPreference = "Stop"

function Write-Result($ok, $msg) {
    if ($ok) { Write-Host "[OK]  $msg" -ForegroundColor Green }
    else { Write-Host "[ERR] $msg" -ForegroundColor Red }
}

function Assert-True($cond, $msg) {
    if ($cond) { Write-Result $true $msg } else { Write-Result $false $msg; throw "Assertion failed: $msg" }
}

# Resolve paths
$installerPath = (Resolve-Path $Installer).Path
$installDir    = Join-Path $Env:ProgramFiles "Upload Bridge"
$exePath       = Join-Path $installDir "UploadBridge.exe"
$vbsPath       = Join-Path $installDir "LAUNCH_UPLOAD_BRIDGE.vbs"
$batPath       = Join-Path $installDir "LAUNCH_UPLOAD_BRIDGE.bat"
$debugBatPath  = Join-Path $installDir "LAUNCH_UPLOAD_BRIDGE_DEBUG.bat"
$keysPath      = Join-Path $installDir "LICENSE_KEYS.txt"
$desktopLnk    = Join-Path ([Environment]::GetFolderPath('CommonDesktopDirectory')) "Upload Bridge.lnk"
$startLnk      = Join-Path ([Environment]::GetFolderPath('CommonStartMenu')) "Programs\Upload Bridge\Upload Bridge.lnk"

# 0) Pre-clean (uninstall if already installed)
if (Test-Path $installDir) {
    $unins = Get-ChildItem -Path $installDir -Filter "unins*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($unins) {
        Write-Host "Pre-clean: Uninstalling previous version..."
        & $unins.FullName /VERYSILENT /NORESTART | Out-Null
        Start-Sleep -Seconds 3
    }
}
if (Test-Path $installDir) { Remove-Item -Recurse -Force $installDir -ErrorAction SilentlyContinue }

# 1) Install silently
Write-Host "Installing from: $installerPath"
& $installerPath /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- | Out-Null
Start-Sleep -Seconds 3

# 2) Validate files
Assert-True (Test-Path $exePath)                  "EXE installed: $exePath"
Assert-True (Test-Path $vbsPath)                  "Launcher VBS present"
Assert-True (Test-Path $batPath)                  "Launcher BAT present"
Assert-True (Test-Path $debugBatPath)             "Debug launcher present"
Assert-True (Test-Path $keysPath)                 "LICENSE_KEYS.txt present"

# 3) Validate shortcuts
Assert-True (Test-Path $desktopLnk)               "Desktop shortcut created"
Assert-True (Test-Path $startLnk)                 "Start menu shortcut created"

# 4) Validate file associations (HKCR)
$binDefault = (Get-ItemProperty -Path "Registry::HKEY_CLASSES_ROOT\.bin" -ErrorAction SilentlyContinue).'(default)'
$binCommand = (Get-ItemProperty -Path "Registry::HKEY_CLASSES_ROOT\UploadBridge.binfile\shell\open\command" -ErrorAction SilentlyContinue).'(default)'
Assert-True ($binDefault -eq "UploadBridge.binfile") "HKCR\.bin associated"
Assert-True ($binCommand -like "*LAUNCH_UPLOAD_BRIDGE.vbs*`" `"%1`"") "Open command uses VBS with %1"

$datDefault = (Get-ItemProperty -Path "Registry::HKEY_CLASSES_ROOT\.dat" -ErrorAction SilentlyContinue).'(default)'
$ledsDefault= (Get-ItemProperty -Path "Registry::HKEY_CLASSES_ROOT\.leds" -ErrorAction SilentlyContinue).'(default)'
Assert-True ($datDefault -eq "UploadBridge.datfile")  "HKCR\.dat associated"
Assert-True ($ledsDefault -eq "UploadBridge.ledsfile") "HKCR\.leds associated"

# 4b) Test double-click launch via file association
$testFile = Join-Path $env:TEMP "test_uploadbridge.bin"
Set-Content -Path $testFile -Value "TESTDATA" -Encoding ASCII
Write-Host "Testing file association launch for $testFile..."
Start-Process $testFile | Out-Null
Start-Sleep -Seconds 3
$proc = Get-Process -Name "UploadBridge" -ErrorAction SilentlyContinue | Select-Object -First 1
Assert-True ($proc -ne $null) "UploadBridge launched via .bin association"
if ($proc) { Stop-Process -Id $proc.Id -Force }
Remove-Item $testFile -Force -ErrorAction SilentlyContinue

# 5) Optional smoke check: ensure the EXE starts (non-blocking)
Write-Host "Launching once (non-blocking)..."
Start-Process -FilePath $exePath -WorkingDirectory $installDir | Out-Null
Start-Sleep -Seconds 2

# 6) Uninstall silently
$unins = Get-ChildItem -Path $installDir -Filter "unins*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
Assert-True $null -ne $unins "Uninstaller present"
& $unins.FullName /VERYSILENT /NORESTART | Out-Null
Start-Sleep -Seconds 3

# 7) Validate cleanup
Assert-True (-not (Test-Path $installDir)) "Install folder removed"
Write-Result $true "Validation completed successfully."


