@echo off
REM Setup Test Environment Variables for Upload Bridge
REM Batch script for Windows CMD

echo ========================================
echo Upload Bridge - Test Environment Setup
echo ========================================
echo.

REM Test Auth0 Configuration (for OAuth/Social Login testing)
echo Setting Auth0 test configuration...

REM Sample Auth0 values for testing (replace with your actual Auth0 credentials)
set AUTH0_DOMAIN=dev-test-123.us.auth0.com
set AUTH0_CLIENT_ID=test-client-id-abc123
set AUTH0_AUDIENCE=https://api.test.example.com

REM License Server URL (default: localhost:3000)
set LICENSE_SERVER_URL=http://localhost:3000
set AUTH_SERVER_URL=http://localhost:3000

echo.
echo Environment variables set:
echo    AUTH0_DOMAIN = %AUTH0_DOMAIN%
echo    AUTH0_CLIENT_ID = %AUTH0_CLIENT_ID%
echo    AUTH0_AUDIENCE = %AUTH0_AUDIENCE%
echo    LICENSE_SERVER_URL = %LICENSE_SERVER_URL%
echo.

echo NOTE: These are TEST values!
echo    Replace with your actual Auth0 credentials for production use.
echo.

echo To use these variables in this CMD session:
echo    scripts\setup_test_env.bat
echo.

echo To set permanently (User-level):
echo    setx AUTH0_DOMAIN "%AUTH0_DOMAIN%"
echo    setx AUTH0_CLIENT_ID "%AUTH0_CLIENT_ID%"
echo.

echo ========================================
echo Environment setup complete!
echo ========================================

