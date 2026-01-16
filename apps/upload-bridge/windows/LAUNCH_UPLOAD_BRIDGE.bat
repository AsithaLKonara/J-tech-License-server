@echo off
setlocal
set APPDIR=%~dp0
cd /d "%APPDIR%"

REM Optional logging
set "UPLOADBRIDGE_LOG_LEVEL=INFO"
set "UPLOADBRIDGE_LOG_FILE=%APPDIR%UploadBridge.log"

REM Detect exe name (portable onedir uses UploadBridge_Test.exe)
set EXE=UploadBridge.exe
if exist "%APPDIR%UploadBridge_Test.exe" set EXE=UploadBridge_Test.exe
if exist "%APPDIR%UploadBridge.exe" set EXE=UploadBridge.exe

echo Starting Upload Bridge...
start "Upload Bridge" /D "%APPDIR%" "%APPDIR%%EXE%"
exit /b 0


