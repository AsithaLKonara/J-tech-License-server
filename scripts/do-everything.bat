@echo off
echo ========================================
echo COMPLETE MIGRATION AND SEEDING PROCESS
echo ========================================
echo.

cd /d "%~dp0..\apps\web-dashboard"

echo [1/4] Running Migrations...
php artisan migrate --force
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Migrations failed with code %ERRORLEVEL%
) else (
    echo Migrations completed successfully!
)
echo.

echo [2/4] Running Seeders...
php artisan db:seed
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Seeders failed with code %ERRORLEVEL%
) else (
    echo Seeders completed successfully!
)
echo.

echo [3/4] Checking Migration Status...
php artisan migrate:status
echo.

echo [4/4] Verifying Database...
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -P 3307 upload_bridge -e "SHOW TABLES;"
echo.

echo ========================================
echo PROCESS COMPLETE
echo ========================================
echo.
pause
