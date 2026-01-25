@echo off
REM Run database migrations and seed test data
echo Running database migrations...
c:\Users\asith\Documents\Projects\upload_bridge\php\php.exe artisan migrate:fresh --force

echo.
echo Seeding database with test data...
c:\Users\asith\Documents\Projects\upload_bridge\php\php.exe artisan db:seed --force

echo.
echo Done! Test user created: test@example.com / testpassword123
