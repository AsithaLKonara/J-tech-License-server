# Production Readiness Checklist

**Upload Bridge v3.0.0**

---

## Status: ⚠️ **REQUIRES FIXES BEFORE PRODUCTION**

This document lists all items that need to be addressed before the application is production-ready.

---

## Critical Issues (Must Fix)

### 1. ❌ Hardcoded Localhost Defaults

**Location**: Multiple files use `http://localhost:8000` as default fallback

**Files Affected**:
- `core/auth_manager.py` (line 47)
- `core/license_manager.py` (line 52)
- `main.py` (line 232-233)
- `ui/dialogs/login_dialog.py` (line 407)

**Problem**: If config file is missing or misconfigured, app will try to connect to localhost instead of production server.

**Fix Required**:
```python
# Change from:
server_url = os.environ.get('LICENSE_SERVER_URL', 'http://localhost:8000')

# To:
PROD_SERVER_URL = 'https://j-tech-license-server-production.up.railway.app'
server_url = os.environ.get('LICENSE_SERVER_URL') or PROD_SERVER_URL
```

**Priority**: 🔴 **CRITICAL** - Must fix before production release

---

### 2. ❌ Debug Logging Enabled

**Location**: `config/app_config.yaml` (line 33)

**Problem**: 
```yaml
logging:
  level: "DEBUG"  # Should be "INFO" or "WARNING" for production
```

**Fix Required**: Change to `"INFO"` or `"WARNING"` for production builds.

**Priority**: 🟡 **HIGH** - Can cause performance issues and expose sensitive info

---

### 3. ❌ Test Credentials in Documentation

**Location**: `docs/LOGIN_CREDENTIALS.md`

**Problem**: Contains test credentials (`test@example.com`, `testpassword123`) that could confuse users or be used inappropriately.

**Fix Required**: 
- Add **⚠️ TEST ONLY** warning at top
- Move test credentials to separate `TESTING.md` file
- Or remove entirely if not needed

**Priority**: 🟡 **MEDIUM** - Documentation issue, not code

---

### 4. ⚠️ Configuration File Not Bundled

**Location**: `config/app_config.yaml`

**Problem**: Production server URL (`https://j-tech-license-server-production.up.railway.app`) is in config file, but config file may not be bundled correctly in EXE.

**Verification Needed**:
- ✅ Check `installer/windows/UploadBridge.spec` includes `config/` in `datas`
- ✅ Verify config file is actually bundled in EXE
- ✅ Test EXE can read config file from bundled location

**Priority**: 🟡 **HIGH** - If config file is missing, app will use localhost default

---

## Medium Priority Issues

### 5. ⚠️ Environment Variable Consistency

**Problem**: Code checks for `LICENSE_SERVER_URL` but config uses `auth_server_url`.

**Files**:
- Code: `os.environ.get('LICENSE_SERVER_URL', ...)`
- Config: `auth_server_url: "..."`

**Fix Required**: Ensure both are checked:
```python
server_url = (
    os.environ.get('LICENSE_SERVER_URL') or
    os.environ.get('AUTH_SERVER_URL') or
    config.get('auth_server_url') or
    PROD_SERVER_URL
)
```

**Priority**: 🟡 **MEDIUM** - May cause confusion but has fallbacks

---

### 6. ⚠️ Missing Production Environment Variables

**Location**: `scripts/set_env_permanent.ps1`, `scripts/setup_test_env.sh`

**Problem**: Environment setup scripts use test values:
- `AUTH0_DOMAIN = "dev-test-123.us.auth0.com"` (test)
- `LICENSE_SERVER_URL = "http://localhost:3000"` (dev)

**Fix Required**: Create production environment setup script with actual production values.

**Priority**: 🟡 **MEDIUM** - Documentation/setup issue

---

### 7. ⚠️ Debug Code in Production Build

**Location**: `main.py` (line 31-32)

**Code**:
```python
if os.environ.get("UPLOADBRIDGE_DEBUG"):
    os.environ.setdefault("QT_DEBUG_PLUGINS", "1")
```

**Status**: ✅ **OK** - Only runs if `UPLOADBRIDGE_DEBUG` is set, so safe for production.

**Priority**: 🟢 **LOW** - Already gated properly

---

## Low Priority / Nice to Have

### 8. ⚠️ Test Files May Be Bundled

**Location**: `test_*.py` files

**Problem**: Test files may be included in EXE build if not explicitly excluded.

**Fix**: Ensure test files are excluded in PyInstaller spec or `.gitignore`.

**Priority**: 🟢 **LOW** - Doesn't affect functionality, just EXE size

---

### 9. ⚠️ Development Scripts in Documentation

**Location**: Various `*.md` files reference `localhost:3000`, `localhost:8000`

**Problem**: Documentation may confuse users about production setup.

**Fix**: Update docs to clearly distinguish development vs production.

**Priority**: 🟢 **LOW** - Documentation only

---

## Configuration Checklist

### Before Production Release:

- [ ] **Fix hardcoded localhost defaults** in:
  - [ ] `core/auth_manager.py`
  - [ ] `core/license_manager.py`
  - [ ] `main.py`
  - [ ] `ui/dialogs/login_dialog.py`
  - [ ] `ui/dialogs/license_activation_dialog.py`

- [ ] **Update logging level** in `config/app_config.yaml`:
  - [ ] Change `DEBUG` to `INFO` or `WARNING`

- [ ] **Verify production server URL**:
  - [ ] Confirm `https://j-tech-license-server-production.up.railway.app` is correct
  - [ ] Test connectivity from production environment
  - [ ] Verify SSL certificate is valid

- [ ] **Verify config file bundling**:
  - [ ] Check `config/app_config.yaml` is in PyInstaller spec `datas`
  - [ ] Test EXE can read config from bundled location
  - [ ] Verify fallback to production URL works if config missing

- [ ] **Clean up documentation**:
  - [ ] Remove or move test credentials to separate file
  - [ ] Add production deployment guide
  - [ ] Update README with production setup steps

- [ ] **Test production build**:
  - [ ] Build EXE with production config
  - [ ] Test on clean Windows machine (no Python installed)
  - [ ] Verify app connects to production server
  - [ ] Test login flow end-to-end
  - [ ] Verify license validation works

- [ ] **Environment variables**:
  - [ ] Document required production environment variables
  - [ ] Create production environment setup guide
  - [ ] Verify app works without environment variables (uses config/defaults)

---

## Production Build Steps

### 1. Update Configuration

**Edit `config/app_config.yaml`**:
```yaml
# Change logging level
logging:
  level: "INFO"  # Changed from "DEBUG"

# Verify production server URL
auth_server_url: "https://j-tech-license-server-production.up.railway.app"
```

### 2. Fix Code Defaults

**Update all files** to use production URL as default instead of localhost.

### 3. Rebuild EXE

```bash
cd apps/upload-bridge
python scripts/build_executable.py
```

### 4. Test Production Build

- Test on clean machine
- Verify server connectivity
- Test authentication flow
- Verify license validation

---

## Quick Fix Script

Create a script to fix all localhost defaults at once:

```python
# scripts/fix_production_defaults.py
import re
from pathlib import Path

PROD_URL = 'https://j-tech-license-server-production.up.railway.app'
FILES = [
    'core/auth_manager.py',
    'core/license_manager.py',
    'main.py',
    'ui/dialogs/login_dialog.py',
    'ui/dialogs/license_activation_dialog.py',
]

for file_path in FILES:
    full_path = Path('apps/upload-bridge') / file_path
    if full_path.exists():
        content = full_path.read_text(encoding='utf-8')
        # Replace localhost:8000 defaults
        content = re.sub(
            r"'http://localhost:8000'",
            f"'{PROD_URL}'",
            content
        )
        content = re.sub(
            r'"http://localhost:8000"',
            f'"{PROD_URL}"',
            content
        )
        full_path.write_text(content, encoding='utf-8')
        print(f"✅ Updated {file_path}")
```

---

## Summary

**Critical Fixes Needed**:
1. ❌ Hardcoded localhost defaults → Use production URL
2. ❌ Debug logging → Change to INFO/WARNING
3. ⚠️ Config file bundling verification
4. ⚠️ Environment variable consistency

**Estimated Time to Fix**: 2-3 hours

**Risk if Not Fixed**:
- App will try to connect to localhost in production ❌
- Debug logging will slow down production ❌
- Configuration may not work correctly ❌

**After Fixes**:
- ✅ Production-ready
- ✅ Proper error handling
- ✅ Correct server connectivity
- ✅ Appropriate logging levels

---

**Last Updated**: 2025-01-27  
**Version**: 3.0.0
