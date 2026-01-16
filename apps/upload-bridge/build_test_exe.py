#!/usr/bin/env python3
"""
Build Test EXE - Complete executable with all test configurations
Packages Upload Bridge with test environment variables and configurations
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent
SPEC_FILE = PROJECT_ROOT / "installer" / "windows" / "UploadBridge.spec"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print(f"✅ PyInstaller found: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        return True

def create_test_config():
    """Create test configuration file that will be bundled"""
    config_dir = PROJECT_ROOT / "config"
    config_dir.mkdir(exist_ok=True)
    
    # Create test auth config with test values
    try:
        import yaml
        test_auth_config = {
            "auth0": {
                "domain": "dev-test-123.us.auth0.com",
                "client_id": "test-client-id-abc123",
                "audience": "https://api.test.example.com"
            },
            "auth_server_url": "https://j-tech-license-server.vercel.app",
            "token": {
                "lifetime_hours": 24,
                "refresh_threshold_hours": 1
            },
            "test_mode": True
        }
        
        auth_config_file = config_dir / "auth_config.yaml"
        with open(auth_config_file, 'w') as f:
            yaml.dump(test_auth_config, f, default_flow_style=False)
        
        print(f"✅ Created test config: {auth_config_file}")
        return auth_config_file
    except ImportError:
        print("⚠️  PyYAML not found, skipping config file creation")
        return None

def verify_spec_file():
    """Verify spec file exists"""
    if not SPEC_FILE.exists():
        print(f"❌ Spec file not found: {SPEC_FILE}")
        return False
    print(f"✅ Spec file found: {SPEC_FILE}")
    return True

def build_exe():
    """Build the EXE using PyInstaller"""
    print("=" * 60)
    print("Building Upload Bridge EXE")
    print("=" * 60)
    
    # Clean previous builds (skip if files are locked)
    if DIST_DIR.exists():
        print(f"🧹 Cleaning dist directory: {DIST_DIR}")
        try:
            shutil.rmtree(DIST_DIR)
        except PermissionError:
            print("⚠️  Could not clean dist directory (files may be in use)")
            print("   Continuing with build...")
            # Try to delete individual files
            try:
                for file in DIST_DIR.glob("*"):
                    try:
                        if file.is_file():
                            file.unlink()
                    except PermissionError:
                        pass  # Skip locked files
            except Exception:
                pass  # Continue anyway
    
    if BUILD_DIR.exists():
        print(f"🧹 Cleaning build directory: {BUILD_DIR}")
        try:
            shutil.rmtree(BUILD_DIR)
        except PermissionError:
            print("⚠️  Could not clean build directory (files may be in use)")
            print("   Continuing with build...")
    
    # Build command
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        str(SPEC_FILE)
    ]
    
    print(f"\n📦 Running: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=False
        )
        
        print("\n✅ Build completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        return False

def verify_exe():
    """Verify the EXE was created"""
    exe_file = DIST_DIR / "UploadBridge.exe"
    
    if exe_file.exists():
        size_mb = exe_file.stat().st_size / (1024 * 1024)
        print(f"\n✅ EXE created: {exe_file}")
        print(f"   Size: {size_mb:.2f} MB")
        return True
    else:
        print(f"\n❌ EXE not found: {exe_file}")
        return False

def create_test_readme():
    """Create README for test EXE"""
    readme_content = f"""# Upload Bridge Test EXE

**Version**: 3.0.0  
**Build Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Test Configuration Included

This EXE includes test environment variables and configurations:

- **Auth0 Domain**: dev-test-123.us.auth0.com
- **Auth0 Client ID**: test-client-id-abc123
- **License Server**: https://j-tech-license-server.vercel.app

## How to Use

1. **Run the EXE**: Double-click `UploadBridge.exe`

2. **Test Login Methods**:
   - **Email/Password**: Uses Vercel license server at https://j-tech-license-server.vercel.app
   - **Social Login**: Requires Auth0 account (test values configured)
   - **Magic Link**: Requires Auth0 Passwordless API
   - **Offline License**: Use key `ULBP-9Q2Z-7K3M-4X1A`

3. **Test License Activation**:
   - Menu → License → Activate License...
   - Enter offline license key
   - Or login with account-based license

## Test Credentials

### Email/Password Login
- Email: test@example.com
- Password: testpassword123
- (Uses Vercel license server - no local server needed)

### Offline License Keys
- `ULBP-9Q2Z-7K3M-4X1A` - Pattern + WiFi
- `ULBP-1P4E-8C2J-7R6B` - Pattern + WiFi + Advanced Controls
- `ULBP-5X9K-3M7V-1Q4Z` - Pattern only

## Files Included

- Main executable: `UploadBridge.exe`
- Configuration files: `config/`
- Firmware templates: `firmware/templates/`
- License keys: `config/license_keys.yaml`

## Troubleshooting

### EXE Won't Start
- Check Windows Event Viewer for errors
- Verify all dependencies are included
- Try running from command line: `UploadBridge.exe`

### Login Not Working
- Check internet connection (for Email/Password - uses Vercel server)
- Check Auth0 configuration (for OAuth)
- Use offline license keys as fallback

### License Not Validating
- Check license key format
- Verify license server URL
- Try offline license activation

## Support

For issues or questions, check:
- `docs/TEST_ENVIRONMENT_SETUP.md`
- `docs/AUTH0_SETUP_GUIDE.md`
- `docs/LOGIN_CREDENTIALS.md`

---
**This is a TEST build with test configurations.**
**Replace Auth0 credentials for production use.**
"""
    
    readme_file = DIST_DIR / "TEST_README.txt"
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    
    # Create simple user guide
    user_guide_content = """═══════════════════════════════════════════════════════════════
  Upload Bridge - Test Version
  Quick Start Guide
═══════════════════════════════════════════════════════════════

🎯 WHAT YOU NEED:
  ✅ Just this EXE file (UploadBridge.exe)
  ✅ Windows 10/11
  ✅ Internet connection (for login)
  
  ❌ NO installation needed
  ❌ NO configuration needed
  ❌ NO setup required

🚀 QUICK START:

1. Double-click "UploadBridge.exe"
   → Application starts automatically

2. Login (choose one):

   A) Email/Password:
      Email: test@example.com
      Password: testpassword123
      → Click "Login"

   B) Offline License:
      → Cancel login dialog
      → Menu → License → Activate License...
      → Enter: ULBP-9Q2Z-7K3M-4X1A
      → Click "Activate"

3. Start Using!
   → Everything is ready!

═══════════════════════════════════════════════════════════════

📝 TEST CREDENTIALS:

Email/Password:
  • test@example.com / testpassword123
  • demo@example.com / demo123

Offline Keys:
  • ULBP-9Q2Z-7K3M-4X1A (Pattern + WiFi)
  • ULBP-1P4E-8C2J-7R6B (Pattern + WiFi + Advanced)
  • ULBP-5X9K-3M7V-1Q4Z (Pattern only)

═══════════════════════════════════════════════════════════════

❓ PROBLEMS?

Won't Start?
  → Check Windows Event Viewer
  → Try running from command line

Login Failed?
  → Check internet connection
  → Try offline license key

Need Help?
  → Contact support with error details

═══════════════════════════════════════════════════════════════

✅ EVERYTHING IS INCLUDED IN THE EXE:
  • All software components
  • All configuration
  • License server connection
  • Test accounts

🎯 JUST RUN IT - THAT'S ALL!

═══════════════════════════════════════════════════════════════
"""
    
    user_guide_file = DIST_DIR / "QUICK_START.txt"
    with open(user_guide_file, 'w') as f:
        f.write(user_guide_content)
    
    print(f"✅ Created test README: {readme_file}")
    print(f"✅ Created user guide: {user_guide_file}")

def main():
    """Main build process"""
    print("\n" + "=" * 60)
    print("Upload Bridge - Test EXE Builder")
    print("=" * 60 + "\n")
    
    # Check PyInstaller
    if not check_pyinstaller():
        print("❌ Failed to install PyInstaller")
        return 1
    
    # Create test config
    create_test_config()
    
    # Verify spec file
    if not verify_spec_file():
        print("\n❌ Spec file not found!")
        print(f"   Expected: {SPEC_FILE}")
        return 1
    
    # Build EXE
    if not build_exe():
        print("\n❌ Build failed!")
        return 1
    
    # Verify EXE
    if not verify_exe():
        print("\n❌ EXE verification failed!")
        return 1
    
    # Create test README
    create_test_readme()
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ BUILD COMPLETE!")
    print("=" * 60)
    print(f"\n📦 EXE Location: {DIST_DIR / 'UploadBridge.exe'}")
    print(f"📄 Test README: {DIST_DIR / 'TEST_README.txt'}")
    print("\n🚀 Ready for testing!")
    print("\nNext steps:")
    print("  1. Run: dist\\UploadBridge.exe")
    print("  2. Test login methods")
    print("  3. Test license activation")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

