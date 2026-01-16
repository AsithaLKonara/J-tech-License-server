# Account Login & License System Integration

**Upload Bridge v3.0.0**

---

## Overview

The license system now works seamlessly with the account-based login system. After logging in with email/password, magic link, or social login, your license is automatically validated.

---

## How It Works

### Login Flow

1. **User Opens Application**
   - Application checks for valid license (account-based or file-based)

2. **If No Valid License Found**
   - Login dialog appears
   - User can login using:
     - **Email/Password**: Direct login with email and password
     - **Magic Link**: Passwordless email link (requires Auth0 setup)
     - **Social Login**: Google, GitHub, etc. (OAuth)

3. **After Successful Login**
   - AuthManager stores session token and entitlement token
   - LicenseManager automatically validates account-based license
   - License info displayed to user
   - Application continues normally

### License Validation Priority

The license system checks licenses in this order:

1. **Account-Based License** (from AuthManager)
   - Checks if user has valid entitlement token
   - Validates token expiry
   - Refreshes token if needed
   - Returns license info from entitlement token

2. **File-Based License** (backward compatibility)
   - Checks for encrypted license file
   - Validates offline license keys
   - Falls back if account-based license not available

---

## Login Methods

### 1. Email/Password Login

**How to Use**:
1. Open login dialog
2. Go to "Email/Password" tab
3. Enter your email address
4. Enter your password
5. Click "Login"

**Backend**: Direct API call to `/api/v2/auth/login`

**License**: Automatically validated after login

---

### 2. Magic Link Login

**How to Use**:
1. Open login dialog
2. Go to "Magic Link" tab
3. Enter your email address
4. Click "Send Magic Link"
5. Check your email and click the link
6. Return to application

**Backend**: Auth0 Passwordless API (requires setup)

**License**: Automatically validated after authentication

---

### 3. Social Login (OAuth)

**How to Use**:
1. Open login dialog
2. Go to "Social Login" tab
3. Click "Login with Google" or "Login with GitHub"
4. Complete OAuth flow in browser
5. Return to application

**Backend**: Auth0 Universal Login with OAuth/PKCE

**License**: Automatically validated after OAuth callback

---

## License Information

After login, license information includes:

- **License ID**: User ID or account identifier
- **Product ID**: `upload_bridge_pro`
- **Plan**: Subscription plan (trial, monthly, yearly, perpetual)
- **Features**: List of enabled features
- **Expires At**: Expiration timestamp (if applicable)
- **User Email**: Account email address
- **Source**: `account` (for account-based licenses)

---

## Sample Test Credentials

### For Testing Email/Password Login

**Note**: These require a backend server with user accounts. For local testing, you can:

1. **Set up test server** at `http://localhost:3000`
2. **Create test account** via signup endpoint
3. **Use test credentials**:
   - Email: `test@example.com`
   - Password: `testpassword123`

### For Testing OAuth Login

**Requirements**:
- Auth0 account configured
- Environment variables set:
  - `AUTH0_DOMAIN`: Your Auth0 domain
  - `AUTH0_CLIENT_ID`: Your Auth0 client ID
  - `AUTH0_AUDIENCE`: (Optional) Your API audience

**Test Accounts**: Use Auth0 test users or social login providers

---

## Offline License Keys (Fallback)

If account login is not available, you can still use offline license keys:

**Sample Keys**:
- `ULBP-9Q2Z-7K3M-4X1A` - Pattern + WiFi
- `ULBP-1P4E-8C2J-7R6B` - Pattern + WiFi + Advanced Controls
- `ULBP-5X9K-3M7V-1Q4Z` - Pattern only

See [LICENSE_ACTIVATION_GUIDE.md](LICENSE_ACTIVATION_GUIDE.md) for full list.

---

## Configuration

### Server URL

Default: `http://localhost:3000`

Can be configured via:
- Environment variable: `LICENSE_SERVER_URL`
- Application config: `config/app_config.yaml`
- Code: `AuthManager(server_url="...")` or `LicenseManager(server_url="...")`

### Auth0 Configuration

Required for OAuth/Social login:

```bash
export AUTH0_DOMAIN="your-domain.auth0.com"
export AUTH0_CLIENT_ID="your-client-id"
export AUTH0_AUDIENCE="your-api-audience"  # Optional
```

---

## Troubleshooting

### "No license found" After Login

**Cause**: Server didn't return entitlement token

**Solutions**:
1. Check server logs for errors
2. Verify user account has active subscription
3. Check entitlement token format from server
4. Try logging out and back in

### License Validation Fails After Login

**Cause**: Entitlement token missing or invalid

**Solutions**:
1. Check `auth_manager.entitlement_token` is set
2. Verify token structure matches expected format
3. Check token expiry
4. Try refreshing token: `auth_manager.refresh_token()`

### Email/Password Login Not Working

**Cause**: Backend endpoint not available or incorrect

**Solutions**:
1. Verify server is running at configured URL
2. Check `/api/v2/auth/login` endpoint exists
3. Verify request format matches server expectations
4. Check server logs for errors

---

## Integration Points

### LicenseManager.validate_license()

Now checks account-based license first:

```python
from core.license_manager import LicenseManager

license_manager = LicenseManager()
is_valid, message, license_info = license_manager.validate_license()

if is_valid:
    if license_info.get('source') == 'account':
        print("Account-based license active")
    else:
        print("File-based license active")
```

### AuthManager Integration

LicenseManager automatically uses AuthManager:

```python
from core.auth_manager import AuthManager
from core.license_manager import LicenseManager

auth_manager = AuthManager()
license_manager = LicenseManager()

# After login, license is automatically validated
if auth_manager.has_valid_token():
    is_valid, _, info = license_manager.validate_license()
    # License info includes account details
```

---

## Backward Compatibility

The system maintains backward compatibility:

- **File-based licenses** still work
- **Offline license keys** still work
- **Account-based licenses** take priority when available
- **Graceful fallback** if account system unavailable

---

**Last Updated**: 2025-01-27  
**Version**: 3.0.0

