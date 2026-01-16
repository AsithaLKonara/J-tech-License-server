# Check MySQL Availability and Provide Instructions
# Diagnoses MySQL setup and provides guidance

$ErrorActionPreference = "Stop"
$projectRoot = (Get-Item $PSScriptRoot).Parent.FullName
$webDashboardDir = Join-Path $projectRoot "apps\web-dashboard"
$envFile = Join-Path $webDashboardDir ".env"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MySQL Availability Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$checks = @{
    MySQLService = $false
    MySQLPort = $false
    MySQLClient = $false
    PHPMySQLExtension = $false
    DatabaseConnection = $false
    DatabaseExists = $false
}

# 1. Check MySQL Service
Write-Host "1. Checking MySQL Service..." -ForegroundColor Yellow
$mysqlServices = Get-Service -Name "*mysql*" -ErrorAction SilentlyContinue
if ($mysqlServices) {
    $runningServices = $mysqlServices | Where-Object { $_.Status -eq 'Running' }
    if ($runningServices) {
        Write-Host "   ✅ MySQL service found and running:" -ForegroundColor Green
        $runningServices | ForEach-Object { Write-Host "      - $($_.Name) ($($_.Status))" -ForegroundColor White }
        $checks.MySQLService = $true
    } else {
        Write-Host "   ⚠️  MySQL service found but not running:" -ForegroundColor Yellow
        $mysqlServices | ForEach-Object { Write-Host "      - $($_.Name) ($($_.Status))" -ForegroundColor White }
        Write-Host "      Start with: Start-Service -Name '$($mysqlServices[0].Name)'" -ForegroundColor Cyan
    }
} else {
    Write-Host "   ⚠️  No MySQL service found in Windows Services" -ForegroundColor Yellow
    Write-Host "      (MySQL might be running as a standalone process)" -ForegroundColor Gray
}

# 2. Check MySQL Port
Write-Host ""
Write-Host "2. Checking MySQL Port (3306)..." -ForegroundColor Yellow
try {
    $portTest = Test-NetConnection -ComputerName 127.0.0.1 -Port 3306 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($portTest) {
        Write-Host "   ✅ Port 3306 is open and accepting connections" -ForegroundColor Green
        $checks.MySQLPort = $true
    } else {
        Write-Host "   ❌ Port 3306 is not accessible" -ForegroundColor Red
        Write-Host "      MySQL server is not running or not listening on port 3306" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Could not test port 3306: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Check MySQL Client
Write-Host ""
Write-Host "3. Checking MySQL Client..." -ForegroundColor Yellow
$mysqlClient = Get-Command mysql -ErrorAction SilentlyContinue
if ($mysqlClient) {
    Write-Host "   ✅ MySQL client found: $($mysqlClient.Source)" -ForegroundColor Green
    $checks.MySQLClient = $true
} else {
    Write-Host "   ⚠️  MySQL client not found in PATH" -ForegroundColor Yellow
    Write-Host "      (Not required if using Laravel, but helpful for manual database operations)" -ForegroundColor Gray
}

# 4. Check PHP MySQL Extension
Write-Host ""
Write-Host "4. Checking PHP MySQL Extension..." -ForegroundColor Yellow
try {
    $phpModules = php -m 2>&1
    if ($phpModules -match "pdo_mysql") {
        Write-Host "   ✅ PHP pdo_mysql extension is loaded" -ForegroundColor Green
        $checks.PHPMySQLExtension = $true
    } else {
        Write-Host "   ❌ PHP pdo_mysql extension is NOT loaded" -ForegroundColor Red
        Write-Host "      Run: .\scripts\enable-mysql-extension.ps1" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   ❌ Could not check PHP extensions: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. Check Database Configuration
Write-Host ""
Write-Host "5. Checking Database Configuration..." -ForegroundColor Yellow
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    $dbHost = if ($envContent -match 'DB_HOST=([^\r\n]+)') { $matches[1] } else { '127.0.0.1' }
    $dbPort = if ($envContent -match 'DB_PORT=([^\r\n]+)') { $matches[1] } else { '3306' }
    $dbName = if ($envContent -match 'DB_DATABASE=([^\r\n]+)') { $matches[1] } else { 'upload_bridge' }
    $dbUser = if ($envContent -match 'DB_USERNAME=([^\r\n]+)') { $matches[1] } else { 'root' }
    $dbPass = if ($envContent -match 'DB_PASSWORD=([^\r\n]+)') { $matches[1] } else { '' }
    $dbConnection = if ($envContent -match 'DB_CONNECTION=([^\r\n]+)') { $matches[1] } else { 'mysql' }
    
    Write-Host "   Configuration:" -ForegroundColor White
    Write-Host "      Connection: $dbConnection" -ForegroundColor Gray
    Write-Host "      Host: $dbHost" -ForegroundColor Gray
    Write-Host "      Port: $dbPort" -ForegroundColor Gray
    Write-Host "      Database: $dbName" -ForegroundColor Gray
    Write-Host "      Username: $dbUser" -ForegroundColor Gray
    
    if ($dbConnection -ne 'mysql') {
        Write-Host "   ⚠️  Database connection is set to '$dbConnection', not 'mysql'" -ForegroundColor Yellow
    } else {
        Write-Host "   ✅ Database connection configured for MySQL" -ForegroundColor Green
    }
} else {
    Write-Host "   ❌ .env file not found" -ForegroundColor Red
    Write-Host "      Run: .\scripts\setup-local-env.ps1" -ForegroundColor Cyan
}

# 6. Test Database Connection
Write-Host ""
Write-Host "6. Testing Database Connection..." -ForegroundColor Yellow
if ($checks.MySQLPort -and $checks.PHPMySQLExtension -and (Test-Path $envFile)) {
    Push-Location $webDashboardDir
    try {
        $dbTest = php artisan db:show 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Database connection successful!" -ForegroundColor Green
            $checks.DatabaseConnection = $true
            
            # Check if database exists
            Write-Host ""
            Write-Host "7. Checking if database exists..." -ForegroundColor Yellow
            try {
                $migrationStatus = php artisan migrate:status 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "   ✅ Database exists and migrations can be checked" -ForegroundColor Green
                    $checks.DatabaseExists = $true
                } else {
                    if ($migrationStatus -match "Unknown database" -or $migrationStatus -match "doesn't exist") {
                        Write-Host "   ❌ Database '$dbName' does not exist" -ForegroundColor Red
                        Write-Host "      Create it with:" -ForegroundColor Yellow
                        if ($checks.MySQLClient) {
                            if ($dbPass) {
                                Write-Host "      mysql -u $dbUser -p -e `"CREATE DATABASE $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`"" -ForegroundColor Cyan
                            } else {
                                Write-Host "      mysql -u $dbUser -e `"CREATE DATABASE $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`"" -ForegroundColor Cyan
                            }
                        } else {
                            Write-Host "      Connect to MySQL and run:" -ForegroundColor Cyan
                            Write-Host "      CREATE DATABASE $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" -ForegroundColor Cyan
                        }
                    } else {
                        Write-Host "   ⚠️  Could not check database: $migrationStatus" -ForegroundColor Yellow
                    }
                }
            } catch {
                Write-Host "   ⚠️  Could not check database existence" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   ❌ Database connection failed" -ForegroundColor Red
            Write-Host "      Error: $dbTest" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ❌ Could not test database connection: $($_.Exception.Message)" -ForegroundColor Red
    }
    Pop-Location
} else {
    Write-Host "   ⚠️  Skipping connection test (prerequisites not met)" -ForegroundColor Yellow
}

# Summary and Instructions
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary & Instructions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allChecksPassed = $checks.Values | Where-Object { $_ -eq $true } | Measure-Object | Select-Object -ExpandProperty Count
$totalChecks = $checks.Values.Count

if ($checks.MySQLService -and $checks.MySQLPort -and $checks.PHPMySQLExtension -and $checks.DatabaseConnection -and $checks.DatabaseExists) {
    Write-Host "✅ All checks passed! MySQL is ready for use." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Run migrations: cd apps\web-dashboard && php artisan migrate --force" -ForegroundColor White
    Write-Host "2. Seed test data: cd apps\web-dashboard && php artisan db:seed --class=TestDataSeeder" -ForegroundColor White
    Write-Host "3. Start server: .\scripts\start-local-testing.ps1" -ForegroundColor White
    Write-Host "4. Run tests: .\scripts\test-e2e-communication.ps1" -ForegroundColor White
} else {
    Write-Host "⚠️  Some checks failed. Follow the instructions below:" -ForegroundColor Yellow
    Write-Host ""
    
    if (-not $checks.MySQLService -and -not $checks.MySQLPort) {
        Write-Host "[!] MySQL Server Not Running" -ForegroundColor Cyan
        Write-Host "   To start MySQL:" -ForegroundColor White
        Write-Host ""
        Write-Host "   Option 1: XAMPP" -ForegroundColor Yellow
        Write-Host "      - Open XAMPP Control Panel" -ForegroundColor Gray
        Write-Host "      - Click 'Start' next to MySQL" -ForegroundColor Gray
        Write-Host ""
        Write-Host "   Option 2: WAMP" -ForegroundColor Yellow
        Write-Host "      - Open WAMP Control Panel" -ForegroundColor Gray
        Write-Host "      - Click 'Start MySQL Service'" -ForegroundColor Gray
        Write-Host ""
        Write-Host "   Option 3: Standalone MySQL" -ForegroundColor Yellow
        Write-Host "      - Open Services (services.msc)" -ForegroundColor Gray
        Write-Host "      - Find MySQL service and start it" -ForegroundColor Gray
        Write-Host ""
        Write-Host "   Option 4: MySQL Command Line" -ForegroundColor Yellow
        Write-Host "      - Navigate to MySQL bin directory" -ForegroundColor Gray
        Write-Host "      - Run: mysqld --console" -ForegroundColor Gray
        Write-Host ""
    }
    
    if (-not $checks.PHPMySQLExtension) {
        Write-Host "[!] PHP MySQL Extension Not Enabled" -ForegroundColor Cyan
        Write-Host "   The pdo_mysql extension needs to be enabled in php.ini" -ForegroundColor White
        Write-Host ""
        Write-Host "   Quick fix:" -ForegroundColor Yellow
        Write-Host "   1. Find php.ini: php --ini" -ForegroundColor Gray
        Write-Host "   2. Edit php.ini and uncomment: extension=pdo_mysql" -ForegroundColor Gray
        Write-Host "   3. Update extension_dir to point to PHP ext folder" -ForegroundColor Gray
        Write-Host "   4. Restart any running PHP processes" -ForegroundColor Gray
        Write-Host ""
        Write-Host "   Or run the helper script (if available):" -ForegroundColor Yellow
        Write-Host "   .\scripts\enable-mysql-extension.ps1" -ForegroundColor Cyan
        Write-Host ""
    }
    
    if (-not $checks.DatabaseExists -and $checks.DatabaseConnection) {
        Write-Host "[!] Database Does Not Exist" -ForegroundColor Cyan
        Write-Host "   Create the database:" -ForegroundColor White
        Write-Host ""
        if ($checks.MySQLClient) {
            Write-Host "   Using MySQL client:" -ForegroundColor Yellow
            if ($dbPass) {
                Write-Host "   mysql -u $dbUser -p -e `"CREATE DATABASE $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`"" -ForegroundColor Cyan
            } else {
                Write-Host "   mysql -u $dbUser -e `"CREATE DATABASE $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`"" -ForegroundColor Cyan
            }
        } else {
            Write-Host "   Connect to MySQL (using any MySQL client) and run:" -ForegroundColor Yellow
            Write-Host "   CREATE DATABASE $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" -ForegroundColor Cyan
        }
        Write-Host ""
        $setupScriptMsg = '   Run setup script:'
        Write-Host $setupScriptMsg -ForegroundColor Yellow
        Write-Host '   .\scripts\setup-database-and-seed.ps1' -ForegroundColor Cyan
        Write-Host ""
    }
    
    if (-not $checks.DatabaseConnection -and $checks.MySQLPort -and $checks.PHPMySQLExtension) {
        Write-Host "[!] Database Connection Failed" -ForegroundColor Cyan
        Write-Host "   Check:" -ForegroundColor White
        Write-Host "   - Database credentials in .env file" -ForegroundColor Gray
        Write-Host "   - Database user has proper permissions" -ForegroundColor Gray
        Write-Host "   - Database name is correct" -ForegroundColor Gray
        Write-Host ""
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Check Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Return exit code based on status
if ($checks.MySQLService -and $checks.MySQLPort -and $checks.PHPMySQLExtension -and $checks.DatabaseConnection -and $checks.DatabaseExists) {
    exit 0
} else {
    exit 1
}
