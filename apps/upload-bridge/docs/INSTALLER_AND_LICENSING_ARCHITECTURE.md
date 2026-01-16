# Installer and Licensing Architecture

**Upload Bridge v3.0.0**

---

## Overview

This document describes the complete architecture of the installer, executable build, and account-based licensing system for Upload Bridge. It covers the flow from installation through activation to app usage, including offline grace periods.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Installer Flow](#installer-flow)
3. [Application Launch Flow](#application-launch-flow)
4. [Authentication Methods](#authentication-methods)
5. [License Validation Flow](#license-validation-flow)
6. [Offline Grace Period](#offline-grace-period)
7. [Error Handling](#error-handling)
8. [Security Considerations](#security-considerations)

---

## Architecture Overview

### High-Level Flow

```
┌─────────────────────────────────────────────────────────┐
│  INSTALLATION PHASE                                     │
│  - Installer copies files                              │
│  - Creates shortcuts                                    │
│  - NO activation required                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  FIRST LAUNCH PHASE                                     │
│  - Executable starts                                   │
│  - License check runs                                  │
│  - No valid token found                                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  AUTHENTICATION PHASE                                   │
│  - Login dialog appears                                │
│  - User authenticates (Email/Password, Magic Link, OAuth)│
│  - Token received and encrypted                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  VALIDATION PHASE                                       │
│  - Online check to license server                      │
│  - License status retrieved                            │
│  - Validation timestamp saved                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  APP READY PHASE                                        │
│  - Main window opens                                   │
│  - 7-day offline grace period begins                   │
│  - All features unlocked                               │
└─────────────────────────────────────────────────────────┘
```

### Key Components

1. **Installer** (`apps/upload-bridge/installer/installer.py`):
   - File installation only
   - Creates shortcuts
   - Does NOT handle activation

2. **Executable** (`dist/UploadBridge.exe`):
   - Single-file executable (PyInstaller onefile)
   - Contains all dependencies
   - Handles authentication and license validation

3. **AuthManager** (`core/auth_manager.py`):
   - Handles login, token refresh, session management
   - Encrypts and stores tokens locally
   - Manages offline grace periods

4. **LicenseManager** (`core/license_manager.py`):
   - Validates license with online server
   - Manages grace period timestamps
   - Caches license status

5. **OAuthHandler** (`core/oauth_handler.py`):
   - Handles OAuth/PKCE flow
   - Manages local callback server
   - Exchanges authorization codes for tokens

---

## Installer Flow

### What the Installer Does

The installer (`installer/installer.py`) is responsible **only** for file installation:

1. **File Copying**:
   - Copies executable to install location
   - Creates application directories
   - Installs required files

2. **Shortcut Creation**:
   - Creates desktop shortcut
   - Creates Start Menu shortcut
   - Sets application icon

3. **No Activation**:
   - Does NOT request license keys
   - Does NOT handle authentication
   - Does NOT validate licenses

### Installer Behavior

```
User runs installer
    ↓
Installer GUI appears
    ↓
User selects install location
    ↓
Files copied to install location
    ↓
Shortcuts created
    ↓
Installation complete
    ↓
"Launch Application" button enabled
```

**Note**: The installer does **NOT** require:
- Internet connection
- License keys
- User authentication
- License activation

All authentication happens **after** installation on first app launch.

---

## Application Launch Flow

### First Launch (No Valid Token)

On first launch after installation:

```
Executable starts
    ↓
LicenseManager checks for valid token
    ↓
No token found (first launch)
    ↓
LicenseActivationDialog appears
    ↓
User logs in (Email/Password, Magic Link, or OAuth)
    ↓
Token received and encrypted
    ↓
License validated online
    ↓
Validation timestamp saved
    ↓
Main window opens
    ↓
7-day grace period begins
```

### Subsequent Launches (Valid Token)

After initial activation:

```
Executable starts
    ↓
LicenseManager checks for valid token
    ↓
Token found in encrypted storage
    ↓
Check if within grace period (< 7 days since last validation)
    ↓
If within grace period:
    → Main window opens immediately
Else:
    → LicenseActivationDialog appears (re-authentication required)
```

### Launch Decision Tree

```
Launch App
    ↓
┌─────────────────────────────────────┐
│ Token exists?                       │
├──────────┬──────────────────────────┤
│ No       │ Yes                      │
│ ↓        │ ↓                        │
│ Login    │ Check grace period       │
│ Dialog   │    ↓                     │
│          │ ┌──────────────────────┐ │
│          │ │ Within 7 days?       │ │
│          │ ├──────┬───────────────┤ │
│          │ │ Yes  │ No            │ │
│          │ │ ↓    │ ↓             │ │
│          │ │ Open │ Login Dialog  │ │
│          │ │ App  │               │ │
│          │ └──────┴───────────────┘ │
└──────────┴──────────────────────────┘
```

---

## Authentication Methods

### Method 1: Email + Password

**Flow**:
```
User enters email and password
    ↓
Credentials sent to Auth0 server
    ↓
Server validates credentials
    ↓
Access token and refresh token received
    ↓
Tokens encrypted and stored locally
```

**UI**: `ui/dialogs/license_activation_dialog.py` - "Email/Password" tab

### Method 2: Magic Link

**Flow**:
```
User enters email address
    ↓
Magic link sent to email
    ↓
User clicks link in email
    ↓
Browser opens to callback URL
    ↓
Authorization code received
    ↓
Code exchanged for tokens
    ↓
Tokens encrypted and stored locally
```

**UI**: `ui/dialogs/license_activation_dialog.py` - "Magic Link" tab

**Note**: Uses `webbrowser` standard library module to open email link.

### Method 3: OAuth (Google/GitHub)

**Flow** (PKCE with local callback server):

```
User clicks "Login with Google" or "Login with GitHub"
    ↓
PKCE code_verifier and code_challenge generated
    ↓
Local HTTP server starts on random port (127.0.0.1:XXXX)
    ↓
System browser opens to Auth0 Universal Login
    ↓
User authenticates with provider (Google/GitHub)
    ↓
Auth0 redirects to local callback server:
    http://127.0.0.1:XXXX/callback?code=...&state=...
    ↓
Authorization code received
    ↓
Code exchanged for tokens (with code_verifier)
    ↓
Local server shuts down
    ↓
Tokens encrypted and stored locally
```

**UI**: `ui/dialogs/login_dialog.py` - OAuth buttons

**Implementation**: `core/oauth_handler.py`

**Standard Library Modules Used**:
- `http.server` - Local callback server
- `webbrowser` - Opens browser for OAuth
- `socket` - Finds available port
- `threading` - Non-blocking server

---

## License Validation Flow

### Online Validation

After successful authentication:

```
Tokens received and encrypted
    ↓
LicenseManager validates license with server:
    POST /api/v2/license/validate
    Headers: Authorization: Bearer <access_token>
    ↓
Server responds with license status:
    {
        "status": "ACTIVE" | "EXPIRED" | "INVALID",
        "plan": "trial" | "monthly" | "yearly" | "perpetual",
        "expires_at": "2025-12-31T23:59:59Z",
        "features": [...]
    }
    ↓
License status cached locally
    ↓
Validation timestamp saved
    ↓
App ready (if status is ACTIVE)
```

### Validation Decision Tree

```
Authentication successful
    ↓
┌─────────────────────────────────────┐
│ Online check possible?              │
├──────────┬──────────────────────────┤
│ Yes      │ No (offline)             │
│ ↓        │ ↓                        │
│ Validate │ Check grace period       │
│ online   │    ↓                     │
│    ↓     │ ┌──────────────────────┐ │
│ ACTIVE?  │ │ Within 7 days?       │ │
│    ↓     │ ├──────┬───────────────┤ │
│ ┌──┴──┐  │ │ Yes  │ No            │ │
│ │Yes ││  │ │ ↓    │ ↓             │ │
│ │No  ││  │ │ Allow│ Require login │ │
│ └──┬──┘  │ └──────┴───────────────┘ │
│    ↓     └──────────────────────────┘
│ ┌─┴────────────────────┐
│ │ Yes: App ready       │
│ │ No: Show error       │
│ └──────────────────────┘
```

### Validation Response Handling

| Status   | Action                                    | User Experience                       |
| -------- | ----------------------------------------- | ------------------------------------- |
| ACTIVE   | App opens, grace period begins            | Main window appears immediately       |
| EXPIRED  | Show expiry message, require re-login     | Error dialog with reactivation button |
| INVALID  | Show invalid message, require re-login    | Error dialog with reactivation button |
| OFFLINE  | Check grace period (if recent validation) | App opens if within 7 days            |

---

## Offline Grace Period

### Purpose

The offline grace period allows the app to function **temporarily** without an internet connection after a successful online validation.

### Duration

- **Default**: 7 days from last successful validation
- **Configurable**: `LicenseManager.GRACE_PERIOD_DAYS = 7`

### How It Works

```
Online validation successful
    ↓
Validation timestamp saved:
    %USERPROFILE%\.upload_bridge\license\last_validation.json
    ↓
Contains:
    {
        "timestamp": "2025-01-27T12:00:00Z",
        "status": "ACTIVE",
        "plan": "yearly"
    }
    ↓
On subsequent launches:
    Check if (current_time - last_validation) < 7 days
    ↓
If within grace period:
    → Allow app to run (even offline)
Else:
    → Require re-authentication (online)
```

### Grace Period Flow

```
App launch (offline)
    ↓
Check for cached license
    ↓
┌─────────────────────────────────────┐
│ Last validation exists?             │
├──────────┬──────────────────────────┤
│ Yes      │ No                       │
│ ↓        │ ↓                        │
│ Check    │ Require online login     │
│ age      │                          │
│    ↓     │                          │
│ ┌──────────────────────┐            │
│ │ Within 7 days?       │            │
│ ├──────┬───────────────┤            │
│ │ Yes  │ No            │            │
│ │ ↓    │ ↓             │            │
│ │ Allow│ Require login │            │
│ └──────┴───────────────┘            │
└─────────────────────────────────────┘
```

### Important Notes

1. **Not Offline Activation**: The grace period is **not** offline activation. Initial validation **always** requires internet.

2. **Time-Based**: Grace period is based on **time since last validation**, not calendar dates.

3. **Revalidation**: When online, the app may attempt to refresh validation in the background.

4. **Security**: Tokens are encrypted and stored locally, but the grace period prevents indefinite offline use.

---

## Error Handling

### Network Errors

**Scenario**: Internet connection unavailable during first launch

**Handling**:
```
License check runs
    ↓
Network error detected
    ↓
Check if grace period available
    ↓
If no previous validation:
    → Show error: "Internet connection required for activation"
    → Disable app functionality
Else if within grace period:
    → Allow app to run (offline)
Else:
    → Show error: "Re-authentication required"
    → Require online login
```

### Authentication Failures

**Scenario**: Invalid credentials or expired tokens

**Handling**:
```
Login attempt
    ↓
Authentication fails
    ↓
Error message shown:
    - "Invalid email or password"
    - "Token expired, please log in again"
    - "Network error, please try again"
    ↓
User can retry or use different method
```

### SSL Certificate Errors

**Scenario**: `SSL: CERTIFICATE_VERIFY_FAILED` on some Windows machines

**Prevention**:
- Explicitly bundle `certifi` CA certificates in PyInstaller spec file
- Ensure `certifi.where()` is included in `datas`

**Handling**:
```
HTTPS request fails with SSL error
    ↓
Retry with bundled certificates
    ↓
If still fails:
    → Show error: "SSL verification failed"
    → Provide troubleshooting steps
```

### OAuth Callback Errors

**Scenario**: Local callback server fails to receive authorization code

**Handling**:
```
OAuth flow starts
    ↓
Local server starts
    ↓
Browser opens
    ↓
Timeout (60 seconds default)
    ↓
If no callback received:
    → Show error: "Authentication timed out"
    → Allow user to retry
    → Provide alternative methods (email/password)
```

---

## Security Considerations

### Token Storage

**Location**: `%USERPROFILE%\.upload_bridge\auth\token.enc`

**Encryption**:
- Tokens encrypted using `cryptography.fernet.Fernet`
- Key derived from device ID (PBKDF2)
- Tokens stored in encrypted form only

**Security Features**:
- Device-bound encryption key
- Tokens cannot be transferred between machines
- Encrypted storage prevents plaintext access

### Network Security

**HTTPS Only**:
- All API calls use HTTPS
- Certificate verification enabled
- Bundled CA certificates ensure verification

**OAuth Security**:
- PKCE flow prevents authorization code interception
- Local callback server (127.0.0.1) prevents external access
- State parameter prevents CSRF attacks

### Grace Period Security

**Limitations**:
- Maximum 7 days offline
- Time-based (not calendar-based)
- Requires periodic re-validation

**Benefits**:
- Prevents indefinite offline use
- Ensures license status is current
- Balances usability with security

---

## User Experience Flow

### Complete User Journey

```
1. Download installer
   ↓
2. Run installer
   - Select install location
   - Click "Install"
   - Wait for file copy
   - Installation complete
   ↓
3. Launch application (first time)
   - Click desktop shortcut or Start Menu entry
   - Executable starts
   ↓
4. Login dialog appears
   - Three tabs: Email/Password, Magic Link, OAuth
   - User selects preferred method
   ↓
5. User authenticates
   - Option A: Enter email and password → Click "Login"
   - Option B: Enter email → Click "Send Magic Link" → Click link in email
   - Option C: Click "Login with Google/GitHub" → Authenticate in browser
   ↓
6. License validation
   - Online check to license server
   - License status retrieved
   - Validation timestamp saved
   ↓
7. App ready
   - Main window opens
   - All features unlocked
   - 7-day offline grace period begins
   ↓
8. Subsequent launches
   - App starts immediately (if within grace period)
   - Or login dialog appears (if grace period expired)
```

### Error Scenarios

**Scenario 1**: No internet on first launch
- **Result**: Error message, app disabled
- **User Action**: Connect to internet and try again

**Scenario 2**: Invalid credentials
- **Result**: Error message on login dialog
- **User Action**: Retry with correct credentials or use different method

**Scenario 3**: Grace period expired (offline)
- **Result**: Login dialog appears
- **User Action**: Connect to internet and re-authenticate

**Scenario 4**: License expired
- **Result**: Error message, reactivation required
- **User Action**: Renew license or contact support

---

## Summary

### Key Takeaways

1. **Installer is simple**: Only handles file installation, no activation

2. **Authentication is online**: All authentication methods require internet connection

3. **Offline grace period**: App can run offline for 7 days after successful validation

4. **Multiple auth methods**: Email/password, magic link, and OAuth (Google/GitHub)

5. **Security-focused**: Encrypted token storage, HTTPS-only, PKCE OAuth flow

6. **User-friendly**: Clear error messages, multiple authentication options, automatic token refresh

### Architecture Benefits

- **Separation of concerns**: Installer separate from activation
- **Flexibility**: Multiple authentication methods
- **Security**: Encrypted storage, HTTPS, PKCE
- **Usability**: Offline grace period, clear error handling
- **Maintainability**: Modular design, clear separation

---

**Last Updated**: 2025-01-27  
**Version**: 3.0.0
