# Environment Variables Setup - Complete ✅

**Upload Bridge v3.0.0**

---

## ✅ Setup Complete

All test environment variables have been configured!

---

## Environment Variables Set

| Variable | Value | Status |
|----------|-------|--------|
| `AUTH0_DOMAIN` | `dev-test-123.us.auth0.com` | ✅ Set |
| `AUTH0_CLIENT_ID` | `test-client-id-abc123` | ✅ Set |
| `AUTH0_AUDIENCE` | `https://api.test.example.com` | ✅ Set |
| `LICENSE_SERVER_URL` | `http://localhost:3000` | ✅ Set |
| `AUTH_SERVER_URL` | `http://localhost:3000` | ✅ Set |

---

## Quick Reference

### Verify Variables Are Set

```powershell
# Run verification script
.\apps\upload-bridge\scripts\verify_env.ps1

# Or check manually
$env:AUTH0_DOMAIN
$env:AUTH0_CLIENT_ID
```

### Set Variables for Current Session

```powershell
# Run setup script
.\apps\upload-bridge\scripts\setup_test_env.ps1
```

### Set Variables Permanently

```powershell
# Run permanent setup script
.\apps\upload-bridge\scripts\set_env_permanent.ps1

# Then restart your terminal/PowerShell
```

---

## What's Next?

### 1. Test Email/Password Login

**No Auth0 needed** - Just need backend server:

```powershell
# Backend server should be running at http://localhost:3000
python apps\upload-bridge\main.py
```

### 2. Test OAuth/Social Login

**Auth0 variables are set** - Can test OAuth flow:

```powershell
# Variables already set
python apps\upload-bridge\main.py
# Go to "Social Login" tab
```

### 3. Test Offline License Keys

**No setup needed**:

```powershell
python apps\upload-bridge\main.py
# Cancel login dialog
# Menu → License → Activate License...
# Enter: ULBP-9Q2Z-7K3M-4X1A
```

---

## Important Notes

### ⚠️ Test Values

The environment variables are set with **test values**:
- `AUTH0_DOMAIN`: `dev-test-123.us.auth0.com` (replace with your actual Auth0 domain)
- `AUTH0_CLIENT_ID`: `test-client-id-abc123` (replace with your actual client ID)

**For production**, replace these with your actual Auth0 credentials!

### 🔄 Restart Required

If you set variables permanently:
- **Restart your terminal/PowerShell** for changes to take effect
- Or use `setup_test_env.ps1` for current session only

### 📝 Update Values

To update values, edit:
- **Scripts**: `scripts/setup_test_env.ps1` or `scripts/set_env_permanent.ps1`
- **Config file**: `config/auth_config.yaml`
- **Or set manually**: `$env:AUTH0_DOMAIN="your-value"`

---

## Troubleshooting

### Variables Not Showing

**Check**: Run `verify_env.ps1` to see current values

**Solution**: 
- If using permanent setup, restart terminal
- If using session setup, run `setup_test_env.ps1` in same session

### Application Still Shows "Auth0 Not Configured"

**Check**: Variables are set correctly

**Solution**:
1. Verify: `$env:AUTH0_DOMAIN`
2. Restart application
3. Check config file: `config/auth_config.yaml`

### Want to Remove Variables

**Remove from current session**:
```powershell
Remove-Item Env:AUTH0_DOMAIN
Remove-Item Env:AUTH0_CLIENT_ID
```

**Remove permanently**:
```powershell
[System.Environment]::SetEnvironmentVariable('AUTH0_DOMAIN', $null, 'User')
[System.Environment]::SetEnvironmentVariable('AUTH0_CLIENT_ID', $null, 'User')
```

---

## Scripts Created

1. **`scripts/setup_test_env.ps1`** - Set variables for current session
2. **`scripts/setup_test_env.bat`** - Set variables for CMD session
3. **`scripts/setup_test_env.sh`** - Set variables for Linux/macOS
4. **`scripts/set_env_permanent.ps1`** - Set variables permanently
5. **`scripts/verify_env.ps1`** - Verify variables are set

---

## Summary

✅ **Environment variables configured**
✅ **Scripts created for easy setup**
✅ **Ready for testing**

**Next**: Run the application and test login functionality!

---

**Last Updated**: 2025-01-27

