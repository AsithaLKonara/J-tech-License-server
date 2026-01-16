# Pre-Test Systematic Checks
# Comprehensive validation before manual E2E testing

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Pre-Test Systematic Checks" -ForegroundColor Cyan
Write-Host "Upload Bridge v3.0.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allChecksPassed = $true
$errors = @()
$warnings = @()

# Get project root directory (2 levels up from this script)
$scriptPath = $PSScriptRoot
$projectRoot = (Get-Item $scriptPath).Parent.Parent.Parent.FullName
$licenseServerPath = Join-Path $projectRoot "apps\web-dashboard"
$appPath = Join-Path $projectRoot "apps\upload-bridge"

Write-Host "Project Root: $projectRoot" -ForegroundColor Gray
Write-Host ""

# ============================================
# Section 1: License Server Checks
# ============================================
Write-Host "Section 1: License Server Checks" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow
Write-Host ""

# Check 1.1: XAMPP MySQL Running
Write-Host "1.1 Checking XAMPP MySQL..." -ForegroundColor Cyan
try {
    $mysqlProcess = Get-Process -Name "mysqld" -ErrorAction SilentlyContinue
    if ($mysqlProcess) {
        Write-Host "   ✅ MySQL service running" -ForegroundColor Green
    } else {
        Write-Host "   ❌ MySQL service NOT running" -ForegroundColor Red
        $errors += "XAMPP MySQL is not running. Start it from XAMPP Control Panel."
        $allChecksPassed = $false
    }
} catch {
    Write-Host "   ❌ Cannot check MySQL service" -ForegroundColor Red
    $errors += "Cannot verify MySQL service status."
    $allChecksPassed = $false
}

# Check 1.2: MySQL Connection
Write-Host "1.2 Checking MySQL connection..." -ForegroundColor Cyan
try {
    if (Get-Command mysql -ErrorAction SilentlyContinue) {
        $testConnection = & mysql -h 127.0.0.1 -P 3306 -u root -e "SELECT 1;" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ MySQL connection successful" -ForegroundColor Green
        } else {
            Write-Host "   ❌ MySQL connection failed" -ForegroundColor Red
            $errors += "Cannot connect to MySQL. Check credentials in XAMPP."
            $allChecksPassed = $false
        }
    } else {
        Write-Host "   ⚠️  MySQL client not in PATH (using XAMPP MySQL)" -ForegroundColor Yellow
        $warnings += "MySQL client not found in PATH. Using XAMPP MySQL directly."
    }
} catch {
    Write-Host "   ⚠️  Cannot test MySQL connection directly" -ForegroundColor Yellow
    $warnings += "Cannot verify MySQL connection directly. Will test via Laravel."
}

# Check 1.3: License Server Directory
Write-Host "1.3 Checking license server directory..." -ForegroundColor Cyan
if (Test-Path $licenseServerPath) {
    Write-Host "   ✅ License server directory exists" -ForegroundColor Green
    
    # Check .env file
    $envPath = Join-Path $licenseServerPath ".env"
    if (Test-Path $envPath) {
        Write-Host "   ✅ .env file exists" -ForegroundColor Green
        
        # Verify database config
        $envContent = Get-Content $envPath -Raw
        if ($envContent -match 'DB_DATABASE=upload_bridge_license') {
            Write-Host "   ✅ Database name configured correctly" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  Database name may not be configured" -ForegroundColor Yellow
            $warnings += "Database name in .env may not match expected: upload_bridge_license"
        }
        
        if ($envContent -match 'DB_CONNECTION=mysql') {
            Write-Host "   ✅ MySQL connection configured" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  May not be using MySQL" -ForegroundColor Yellow
            $warnings += "Database connection may not be set to MySQL"
        }
    } else {
        Write-Host "   ❌ .env file NOT found" -ForegroundColor Red
        $errors += ".env file not found in license server directory. Run setup-xampp.ps1 first."
        $allChecksPassed = $false
    }
    
    # Check composer.json
    $composerPath = Join-Path $licenseServerPath "composer.json"
    if (Test-Path $composerPath) {
        Write-Host "   ✅ composer.json exists" -ForegroundColor Green
    } else {
        Write-Host "   ❌ composer.json NOT found" -ForegroundColor Red
        $errors += "composer.json not found. License server may not be set up correctly."
        $allChecksPassed = $false
    }
    
    # Check vendor directory
    $vendorPath = Join-Path $licenseServerPath "vendor"
    if (Test-Path $vendorPath) {
        Write-Host "   ✅ Dependencies installed (vendor directory exists)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Dependencies NOT installed" -ForegroundColor Red
        $errors += "Composer dependencies not installed. Run: cd apps\web-dashboard && composer install"
        $allChecksPassed = $false
    }
} else {
    Write-Host "   ❌ License server directory NOT found" -ForegroundColor Red
    $errors += "License server directory not found at: $licenseServerPath"
    $allChecksPassed = $false
}

# Check 1.4: PHP and Composer
Write-Host "1.4 Checking PHP and Composer..." -ForegroundColor Cyan
try {
    $phpVersion = & php -v 2>&1 | Select-Object -First 1
    if ($phpVersion -match 'PHP (\d+)\.(\d+)') {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -ge 8 -and $minor -ge 1) {
            Write-Host "   ✅ PHP version OK: $phpVersion" -ForegroundColor Green
        } else {
            Write-Host "   ❌ PHP version too old: $phpVersion (need 8.1+)" -ForegroundColor Red
            $errors += "PHP version must be 8.1 or higher. Current: $phpVersion"
            $allChecksPassed = $false
        }
    } else {
        Write-Host "   ⚠️  Cannot parse PHP version: $phpVersion" -ForegroundColor Yellow
        $warnings += "Cannot verify PHP version"
    }
} catch {
    Write-Host "   ❌ PHP NOT found" -ForegroundColor Red
    $errors += "PHP not found in PATH. Install PHP 8.1+ or use XAMPP PHP."
    $allChecksPassed = $false
}

$composerFound = $false
if (Get-Command composer -ErrorAction SilentlyContinue) {
    Write-Host "   ✅ Composer found" -ForegroundColor Green
    $composerFound = $true
} elseif (Test-Path (Join-Path $projectRoot "composer.phar")) {
    Write-Host "   ✅ Composer.phar found" -ForegroundColor Green
    $composerFound = $true
} else {
    Write-Host "   ⚠️  Composer not in PATH, but composer.phar may be available" -ForegroundColor Yellow
    $warnings += "Composer not found in PATH. Using composer.phar if available."
}

# Check 1.5: Database Exists
Write-Host "1.5 Checking database exists..." -ForegroundColor Cyan
try {
    if (Get-Command mysql -ErrorAction SilentlyContinue) {
        $dbCheck = & mysql -h 127.0.0.1 -P 3306 -u root -e "SHOW DATABASES LIKE 'upload_bridge_license';" 2>&1
        if ($dbCheck -match 'upload_bridge_license') {
            Write-Host "   ✅ Database 'upload_bridge_license' exists" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Database 'upload_bridge_license' NOT found" -ForegroundColor Red
            $errors += "Database 'upload_bridge_license' does not exist. Run setup-xampp.ps1 or create manually."
            $allChecksPassed = $false
        }
    } else {
        Write-Host "   ⚠️  Cannot check database (MySQL client not in PATH)" -ForegroundColor Yellow
        $warnings += "Cannot verify database existence directly. Will test via Laravel."
    }
} catch {
    Write-Host "   ⚠️  Cannot check database directly" -ForegroundColor Yellow
    $warnings += "Cannot verify database existence. Will test via Laravel."
}

# Check 1.6: License Server Running
Write-Host "1.6 Checking license server is running..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v2/health" -Method GET -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ License server is running" -ForegroundColor Green
        
        # Parse response
        try {
            $healthData = $response.Content | ConvertFrom-Json
            Write-Host "   ✅ Health check endpoint responding correctly" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  Health check response may not be JSON" -ForegroundColor Yellow
            $warnings += "Health check response format may be unexpected"
        }
    } else {
        Write-Host "   ❌ License server returned unexpected status: $($response.StatusCode)" -ForegroundColor Red
        $errors += "License server health check returned status: $($response.StatusCode)"
        $allChecksPassed = $false
    }
} catch {
    Write-Host "   ❌ License server is NOT running" -ForegroundColor Red
    $errors += "License server is not running. Start with: cd apps\web-dashboard && php artisan serve"
    $allChecksPassed = $false
}

# Check 1.7: Test User Exists
Write-Host "1.7 Checking test user exists..." -ForegroundColor Cyan
try {
    if (Get-Command mysql -ErrorAction SilentlyContinue) {
        $userCheck = & mysql -h 127.0.0.1 -P 3306 -u root upload_bridge_license -e "SELECT email FROM users WHERE email = 'test@example.com';" 2>&1
        if ($userCheck -match 'test@example.com') {
            Write-Host "   ✅ Test user 'test@example.com' exists" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  Test user 'test@example.com' NOT found" -ForegroundColor Yellow
            $warnings += "Test user not found. You may need to create it manually or run seeders."
        }
    } else {
        Write-Host "   ⚠️  Cannot check test user (MySQL client not in PATH)" -ForegroundColor Yellow
        $warnings += "Cannot verify test user existence. Will test during login."
    }
} catch {
    Write-Host "   ⚠️  Cannot check test user directly" -ForegroundColor Yellow
    $warnings += "Cannot verify test user. Will test during login."
}

Write-Host ""

# ============================================
# Section 2: Upload Bridge Application Checks
# ============================================
Write-Host "Section 2: Upload Bridge Application Checks" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow
Write-Host ""

# Check 2.1: Python Version
Write-Host "2.1 Checking Python version..." -ForegroundColor Cyan
try {
    $pythonVersion = & python --version 2>&1
    if ($pythonVersion -match 'Python (\d+)\.(\d+)') {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -ge 3 -and $minor -ge 10) {
            Write-Host "   ✅ Python version OK: $pythonVersion" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Python version too old: $pythonVersion (need 3.10+)" -ForegroundColor Red
            $errors += "Python version must be 3.10 or higher. Current: $pythonVersion"
            $allChecksPassed = $false
        }
    } else {
        Write-Host "   ⚠️  Cannot parse Python version: $pythonVersion" -ForegroundColor Yellow
        $warnings += "Cannot verify Python version"
    }
} catch {
    Write-Host "   ❌ Python NOT found" -ForegroundColor Red
    $errors += "Python not found in PATH. Install Python 3.10+ from python.org"
    $allChecksPassed = $false
}

# Check 2.2: Application Directory
Write-Host "2.2 Checking application directory..." -ForegroundColor Cyan
if (Test-Path $appPath) {
    Write-Host "   ✅ Application directory exists" -ForegroundColor Green
    
    # Check main.py
    $mainPath = Join-Path $appPath "main.py"
    if (Test-Path $mainPath) {
        Write-Host "   ✅ main.py exists" -ForegroundColor Green
    } else {
        Write-Host "   ❌ main.py NOT found" -ForegroundColor Red
        $errors += "main.py not found in application directory"
        $allChecksPassed = $false
    }
    
    # Check requirements.txt
    $requirementsPath = Join-Path $appPath "requirements.txt"
    if (Test-Path $requirementsPath) {
        Write-Host "   ✅ requirements.txt exists" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  requirements.txt NOT found" -ForegroundColor Yellow
        $warnings += "requirements.txt not found"
    }
} else {
    Write-Host "   ❌ Application directory NOT found" -ForegroundColor Red
    $errors += "Application directory not found at: $appPath"
    $allChecksPassed = $false
}

# Check 2.3: Dependencies Installed
Write-Host "2.3 Checking Python dependencies..." -ForegroundColor Cyan
$requiredPackages = @("PySide6", "requests", "cryptography", "numpy")
$allPackagesInstalled = $true

foreach ($package in $requiredPackages) {
    try {
        # PySide6 needs special handling
        if ($package -eq "PySide6") {
            $importTest = & python -c "import PySide6; print('OK')" 2>&1
        } else {
            $importTest = & python -c "import $($package.ToLower()); print('OK')" 2>&1
        }
        if ($importTest -match 'OK' -or $LASTEXITCODE -eq 0) {
            Write-Host "   ✅ $package installed" -ForegroundColor Green
        } else {
            Write-Host "   ❌ $package NOT installed" -ForegroundColor Red
            $allPackagesInstalled = $false
        }
    } catch {
        Write-Host "   ❌ $package NOT installed" -ForegroundColor Red
        $allPackagesInstalled = $false
    }
}

if (-not $allPackagesInstalled) {
    $errors += "Some Python dependencies are not installed. Run: pip install -r requirements.txt"
    $allChecksPassed = $false
}

# Check 2.4: Configuration Files
Write-Host "2.4 Checking configuration files..." -ForegroundColor Cyan
$configPath = Join-Path $appPath "config\app_config.yaml"
if (Test-Path $configPath) {
    Write-Host "   ✅ app_config.yaml exists" -ForegroundColor Green
    
    # Check license server URL
    $configContent = Get-Content $configPath -Raw
    if ($configContent -match 'auth_server_url') {
        Write-Host "   ✅ License server URL configured" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  License server URL may not be configured" -ForegroundColor Yellow
        $warnings += "License server URL may not be in config file"
    }
} else {
    Write-Host "   ⚠️  app_config.yaml NOT found" -ForegroundColor Yellow
    $warnings += "app_config.yaml not found. Will use environment variables or defaults."
}

# Check 2.5: Environment Variables
Write-Host "2.5 Checking environment variables..." -ForegroundColor Cyan
$envServerUrl = $env:LICENSE_SERVER_URL
if ($envServerUrl) {
    Write-Host "   ✅ LICENSE_SERVER_URL set: $envServerUrl" -ForegroundColor Green
    
    # Verify it points to localhost
    if ($envServerUrl -match 'localhost:8000' -or $envServerUrl -match '127\.0\.0\.1:8000') {
        Write-Host "   ✅ License server URL points to local server" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  License server URL does not point to localhost:8000" -ForegroundColor Yellow
        $warnings += "LICENSE_SERVER_URL points to: $envServerUrl (expected localhost:8000 for local testing)"
    }
} else {
    Write-Host "   ⚠️  LICENSE_SERVER_URL NOT set" -ForegroundColor Yellow
    $warnings += "LICENSE_SERVER_URL environment variable not set. Will use config file or defaults."
}

# Check 2.6: API Connection Test
Write-Host "2.6 Testing API connection..." -ForegroundColor Cyan
$testServerUrl = if ($envServerUrl) { $envServerUrl } else { "http://localhost:8000" }
try {
    $response = Invoke-WebRequest -Uri "$testServerUrl/api/v2/health" -Method GET -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Can connect to license server API" -ForegroundColor Green
    } else {
        Write-Host "   ❌ API connection returned status: $($response.StatusCode)" -ForegroundColor Red
        $errors += "Cannot connect to license server API. Status: $($response.StatusCode)"
        $allChecksPassed = $false
    }
} catch {
    Write-Host "   ❌ Cannot connect to license server API" -ForegroundColor Red
    $errors += "Cannot connect to license server API. Make sure server is running at: $testServerUrl"
    $allChecksPassed = $false
}

Write-Host ""

# ============================================
# Section 3: Code Quality Checks
# ============================================
Write-Host "Section 3: Code Quality Checks" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow
Write-Host ""

# Check 3.1: Linting (if available)
Write-Host "3.1 Checking for linting tools..." -ForegroundColor Cyan
if (Get-Command flake8 -ErrorAction SilentlyContinue) {
    Write-Host "   ✅ flake8 available" -ForegroundColor Green
    Write-Host "   ⚠️  Run: flake8 apps\upload-bridge --max-line-length=120" -ForegroundColor Yellow
    # Note: Not running automatically as it can be slow
} else {
    Write-Host "   ⚠️  flake8 not installed (optional)" -ForegroundColor Yellow
}

# Check 3.2: Type Checking (if available)
Write-Host "3.2 Checking for type checking..." -ForegroundColor Cyan
if (Get-Command mypy -ErrorAction SilentlyContinue) {
    Write-Host "   ✅ mypy available" -ForegroundColor Green
    Write-Host "   ⚠️  Run: mypy apps\upload-bridge" -ForegroundColor Yellow
} else {
    Write-Host "   ⚠️  mypy not installed (optional)" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# Summary
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Pre-Test Check Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($allChecksPassed) {
    Write-Host "✅ All critical checks PASSED" -ForegroundColor Green
} else {
    Write-Host "❌ Some critical checks FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Errors found:" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "   • $error" -ForegroundColor Red
    }
}

if ($warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠️  Warnings:" -ForegroundColor Yellow
    foreach ($warning in $warnings) {
        Write-Host "   • $warning" -ForegroundColor Yellow
    }
}

Write-Host ""

# ============================================
# Next Steps
# ============================================
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""

if ($allChecksPassed) {
    Write-Host "✅ Ready for manual testing!" -ForegroundColor Green
    Write-Host ""
    Write-Host "1. Start license server (if not already running):" -ForegroundColor White
    Write-Host "   cd apps\web-dashboard" -ForegroundColor Cyan
    Write-Host "   php artisan serve" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Run Upload Bridge application:" -ForegroundColor White
    Write-Host "   cd apps\upload-bridge" -ForegroundColor Cyan
    Write-Host "   python main.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "3. Test login:" -ForegroundColor White
    Write-Host "   Email: test@example.com" -ForegroundColor Cyan
    Write-Host "   Password: password123" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "4. Follow testing guide:" -ForegroundColor White
    Write-Host "   docs\E2E_MANUAL_TESTING_GUIDE.md" -ForegroundColor Cyan
} else {
    Write-Host "❌ Fix errors before testing:" -ForegroundColor Red
    Write-Host ""
    foreach ($error in $errors) {
        Write-Host "   • $error" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "After fixing errors, run this script again to verify." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

# Exit with appropriate code
if ($allChecksPassed) {
    exit 0
} else {
    exit 1
}
