@echo off
title Create Final Package
color 0A

REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo.
echo  ██████╗ ██████╗ ███████╗ █████╗ ████████╗███████╗    ██████╗  █████╗  ██████╗██╗  ██╗ █████╗  ██████╗ ███████╗
echo  ██╔══██╗██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██╔════╝    ██╔══██╗██╔══██╗██╔════╝██║  ██║██╔══██╗██╔════╝ ██╔════╝
echo  ██████╔╝██████╔╝█████╗  ███████║   ██║   █████╗      ██████╔╝███████║██║     ███████║███████║██║  ███╗█████╗  
echo  ██╔══██╗██╔══██╗██╔══╝  ██╔══██║   ██║   ██╔══╝      ██╔══██╗██╔══██║██║     ██╔══██║██╔══██║██║   ██║██╔══╝  
echo  ██║  ██║██║  ██║███████╗██║  ██║   ██║   ███████╗    ██████╔╝██║  ██║╚██████╗██║  ██║██║  ██║╚██████╔╝███████╗
echo  ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
echo.
echo ========================================
echo  Upload Bridge - Final Package Creator
echo ========================================
echo.

echo Creating final package with all fixes...
echo.

python create_final_package.py

echo.
echo ========================================
echo Package Creation Complete!
echo ========================================
echo.
echo The final package ZIP file has been created.
echo You can now distribute this ZIP file to other PCs.
echo.
echo To use on another PC:
echo 1. Extract the ZIP file
echo 2. Run install_simple.bat
echo 3. Run LAUNCH_SAFE.bat
echo.
pause










