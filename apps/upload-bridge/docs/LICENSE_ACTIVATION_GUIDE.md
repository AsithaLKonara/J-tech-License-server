# License Activation Guide

**Upload Bridge v3.0.0**

---

## License System Overview

Upload Bridge uses **account-based license activation**. You activate your license by logging in with your email and password or using a magic link. No license keys are required.

---

## How to Activate License

### Method 1: Through Application Menu

1. **Open Upload Bridge**
2. **Go to Menu** → **License** → **Activate License...**
3. **Choose Login Method**:
   - **Email/Password**: Enter your email and password, then click "Activate"
   - **Magic Link**: Enter your email, click "Send Magic Link", then check your email and click the link
4. **Wait for Validation**: The app will validate your license with the server
5. **Verify Activation**: Go to **Menu** → **License** → **License Status** to confirm

### Method 2: On First Launch

When you first launch Upload Bridge after installation, you will be prompted to login. After successful login, your license will be automatically validated.

---

## Important Notes

### Account-Based Activation
- ✅ **Internet required** - License validation requires connection to license server
- ✅ **Account-bound** - License is tied to your account, not your device
- ✅ **Secure** - Authentication tokens stored encrypted in `~/.upload_bridge/auth/`
- ✅ **Offline Grace Period** - App works offline for 7 days after last successful validation

### License Storage
- **Location**: `%USERPROFILE%\.upload_bridge\` (Windows) or `~/.upload_bridge/` (Linux/Mac)
- **Files**:
  - `auth/token.enc` - Encrypted authentication token
  - `auth/session.json` - Session information
  - `license/license_cache.json` - Cached license information
  - `license/last_validation.json` - Last successful validation timestamp

### Offline Grace Period

After successful login and license validation, Upload Bridge can work offline for **7 days** without requiring internet connection. This allows you to:

- Use the app when internet is temporarily unavailable
- Work on airplanes or in areas with poor connectivity
- Continue working if the license server is temporarily down

**Note**: After 7 days offline, you must reconnect to the internet and validate your license again.

---

## License Status

### Viewing License Status

1. **Go to Menu** → **License** → **License Status**
2. The dialog shows:
   - **License Type**: Account-Based
   - **Status**: ACTIVE, EXPIRED, or INVALID
   - **Plan**: Your subscription plan (e.g., Professional, Enterprise)
   - **Expires**: Expiration date (or "Never" for perpetual licenses)
   - **Features**: List of enabled features

### License Statuses

- **ACTIVE**: License is valid and you can use all features
- **EXPIRED**: License has expired, please renew your subscription
- **INVALID**: License validation failed, please contact support

---

## Account Management

### Reactivate Account

If your license becomes invalid or expired:

1. **Go to Menu** → **License** → **License Status**
2. Click **"Reactivate Account"**
3. Login with your email and password or magic link
4. License will be revalidated automatically

### Logout / Deactivate

To logout and clear your session:

1. **Go to Menu** → **License** → **License Status**
2. Click **"Logout"**
3. Confirm logout
4. You will need to login again on next launch

Alternatively, use **Menu** → **License** → **Deactivate License** to logout directly.

---

## Troubleshooting

### "Authentication Required" Error

**Solutions**:
1. Ensure you have an active account with a paid subscription
2. Check your internet connection
3. Try logging in again via **Menu** → **License** → **Activate License...**
4. Verify your email and password are correct

### "License Validation Failed" Error

**Solutions**:
1. Check your internet connection
2. Verify your subscription is active (not expired or cancelled)
3. Try reactivating your account via **Menu** → **License** → **License Status** → **Reactivate Account**
4. Contact support if the issue persists

### "Unable to Connect to License Server" Error

**Solutions**:
1. Check your internet connection
2. Verify firewall/antivirus is not blocking the connection
3. If within grace period (7 days), app should still work offline
4. Try again later if server is temporarily unavailable

### License Expired

**Solutions**:
1. Renew your subscription through your account portal
2. After renewal, reactivate via **Menu** → **License** → **License Status** → **Reactivate Account**
3. Contact support if renewal doesn't resolve the issue

### Magic Link Not Received

**Solutions**:
1. Check your spam/junk folder
2. Verify email address is correct
3. Wait a few minutes and try again
4. Use email/password login instead

---

## Installation Flow

### Installer

The installer no longer requires license activation. Simply:

1. Run the installer
2. Choose installation location
3. Click "Install"
4. Click "Launch Upload Bridge" after installation completes
5. Login on first app launch

### First Launch

On first launch after installation:

1. Login dialog appears automatically
2. Enter your email and password (or use magic link)
3. License is validated automatically after login
4. App opens if license is ACTIVE

---

## Account Creation

If you don't have an account:

1. Visit the Upload Bridge website
2. Sign up for an account
3. Purchase a subscription plan
4. Return to the app and login

---

## Security

### Token Storage

- Authentication tokens are encrypted using device-bound keys
- Tokens are stored locally and never shared
- Each device has a unique encryption key based on hardware fingerprint

### Privacy

- Your password is never stored locally
- Only encrypted authentication tokens are saved
- License validation only sends device fingerprint (no personal data)

---

## Support

If you encounter issues with license activation:

1. Check this guide for common solutions
2. View license status via **Menu** → **License** → **License Status**
3. Contact support with:
   - Your email address
   - License status information
   - Error messages (if any)

---

**Last Updated**: 2025-01-27  
**Version**: 3.0.0
