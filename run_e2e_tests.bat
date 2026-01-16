@echo off
echo ========================================
echo E2E Test Suite Runner
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Installing dependencies...
pip install -q mysql-connector-python requests pytest pytest-xdist pytest-cov
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed.
echo.

echo [2/3] Checking test files...
python -m pytest tests/e2e/ --collect-only -q > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Some test files may have import errors
    echo Continuing anyway...
)
echo.

echo [3/3] Running E2E tests...
echo ========================================
python -m pytest tests/e2e/ -v --tb=short
echo ========================================
echo.

echo Test execution complete!
pause
