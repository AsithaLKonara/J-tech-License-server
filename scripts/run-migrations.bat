@echo off
echo ========================================
echo Running Migrations and Seeders
echo ========================================
echo.

cd /d "%~dp0..\apps\web-dashboard"

echo Current directory: %CD%
echo.

echo Step 1: Running migrations...
php artisan migrate
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Migrations failed!
    pause
    exit /b 1
)

echo.
echo Step 2: Running seeders...
php artisan db:seed
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Seeding failed!
    pause
    exit /b 1
)

echo.
echo Step 3: Checking migration status...
php artisan migrate:status

echo.
echo ========================================
echo Migration and seeding complete!
echo ========================================
pause
