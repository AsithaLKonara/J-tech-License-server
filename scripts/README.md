# Local E2E Testing Scripts

This directory contains PowerShell scripts for setting up and running local end-to-end tests.

## Setup Scripts

### `setup-local-env.ps1`
Creates the `.env` file for the web dashboard with MySQL configuration.

**Usage:**
```powershell
.\scripts\setup-local-env.ps1
```

**What it does:**
- Creates `.env` file in `apps/web-dashboard/`
- Configures MySQL database connection
- Sets `APP_URL=http://localhost:8000`
- Prompts for MySQL password if needed

### `setup-database-and-seed.ps1`
Sets up the database, runs migrations, and seeds test data.

**Usage:**
```powershell
.\scripts\setup-database-and-seed.ps1
```

**What it does:**
- Creates MySQL database if it doesn't exist
- Generates APP_KEY if needed
- Installs Composer dependencies if needed
- Runs database migrations
- Seeds test data (TestDataSeeder)

## Service Management Scripts

### `start-local-testing.ps1`
Starts the web dashboard server for local testing.

**Usage:**
```powershell
.\scripts\start-local-testing.ps1
```

**What it does:**
- Checks all prerequisites (PHP, Composer, etc.)
- Generates APP_KEY if needed
- Installs dependencies if missing
- Verifies database connection
- Starts Laravel server on port 8000

**Note:** Press `Ctrl+C` to stop the server.

### `stop-local-testing.ps1`
Stops any running Laravel servers on port 8000.

**Usage:**
```powershell
.\scripts\stop-local-testing.ps1
```

## Verification Scripts

### `verify-setup.ps1`
Verifies all prerequisites and configuration are correct.

**Usage:**
```powershell
.\scripts\verify-setup.ps1
```

**What it checks:**
- PHP, Composer, Python, MySQL installed
- `.env` file exists and is configured
- `auth_config.yaml` points to localhost:8000
- Composer dependencies installed
- Database connection works
- Port 8000 is available

### `verify-complete-setup.ps1`
Comprehensive verification of the complete setup including API tests.

**Usage:**
```powershell
.\scripts\verify-complete-setup.ps1
```

**What it checks:**
- All prerequisites
- Configuration files
- Database setup and migrations
- API endpoints (if server is running)
- Inter-system communication

## Testing Scripts

### `test-e2e-communication.ps1`
Tests communication between desktop app and web dashboard.

**Usage:**
```powershell
.\scripts\test-e2e-communication.ps1
```

**Prerequisites:**
- Web dashboard server must be running
- Test data must be seeded

**What it tests:**
- Health check endpoint
- User login
- License validation
- License info
- Device registration
- List devices
- Error handling (invalid login, unauthorized access)

## Quick Start Workflow

1. **Setup environment:**
   ```powershell
   .\scripts\setup-local-env.ps1
   ```

2. **Setup database:**
   ```powershell
   .\scripts\setup-database-and-seed.ps1
   ```

3. **Verify setup:**
   ```powershell
   .\scripts\verify-complete-setup.ps1
   ```

4. **Start server:**
   ```powershell
   .\scripts\start-local-testing.ps1
   ```

5. **Test communication (in another terminal):**
   ```powershell
   .\scripts\test-e2e-communication.ps1
   ```

## Script Dependencies

All scripts assume:
- PowerShell 5.1+ (Windows) or PowerShell Core (Linux/Mac)
- Scripts are run from the project root directory
- Required tools (PHP, Composer, Python, MySQL) are in PATH

## Troubleshooting

### Script fails with "command not found"
- Ensure you're running from the project root
- Check that required tools are in your PATH

### Database connection fails
- Verify MySQL is running
- Check database credentials in `.env`
- Ensure database exists

### Port 8000 already in use
- Stop any existing servers: `.\scripts\stop-local-testing.ps1`
- Or use a different port and update `APP_URL` in `.env`

## Related Documentation

- [Local Testing Setup Guide](../docs/LOCAL_TESTING_SETUP.md)
- [Quick Start Guide](../docs/LOCAL_TESTING_QUICKSTART.md)
