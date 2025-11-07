@echo off
setlocal
set APPDIR=%~dp0
cd /d "%APPDIR%"

echo ===== Upload Bridge DEBUG Launcher =====
echo Working dir: %APPDIR%

REM Force software OpenGL to avoid driver issues
set QT_OPENGL=software
set QT_DEBUG_PLUGINS=1
set UPLOADBRIDGE_DEBUG=1
set UPLOADBRIDGE_LOG_LEVEL=DEBUG
set "UPLOADBRIDGE_LOG_FILE=%APPDIR%UploadBridge.log"

REM Detect exe name
set EXE=UploadBridge.exe
if exist "%APPDIR%UploadBridge_Test.exe" set EXE=UploadBridge_Test.exe
if exist "%APPDIR%UploadBridge.exe" set EXE=UploadBridge.exe

echo Using EXE: %EXE%
echo QT_OPENGL=%QT_OPENGL%
echo QT_DEBUG_PLUGINS=%QT_DEBUG_PLUGINS%
echo UPLOADBRIDGE_LOG_FILE=%UPLOADBRIDGE_LOG_FILE%
echo -----------------------------------------

if not exist "%APPDIR%%EXE%" (
  echo ERROR: %EXE% not found next to this script.
  dir /b
  pause
  exit /b 1
)

"%APPDIR%%EXE%"
echo -----------------------------------------
echo Process exited with code %ERRORLEVEL%
echo If GUI did not appear, please attach UploadBridge.log from this folder.
pause


