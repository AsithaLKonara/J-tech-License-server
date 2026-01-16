# Login Credentials Guide

**Upload Bridge v3.0.0**

---

## Quick Reference: Sample Login Credentials

### For Email/Password Login

**Note**: These require a backend server running at `http://localhost:3000` (or configured server URL).

#### Test Account 1 (Full Features)
- **Email**: `test@example.com`
- **Password**: `testpassword123`
- **Plan**: Pro (Pattern Upload + WiFi Upload + Advanced Controls)

#### Test Account 2 (Standard Features)
- **Email**: `demo@example.com`
- **Password**: `demopassword123`
- **Plan**: Standard (Pattern Upload + WiFi Upload)

#### Test Account 3 (Basic Features)
- **Email**: `basic@example.com`
- **Password**: `basicpassword123`
- **Plan**: Basic (Pattern Upload only)

---

## Setting Up Test Accounts

### Option 1: Use Backend Server

If you have the license server running:

1. **Create account** via signup endpoint:
   ```bash
   curl -X POST http://localhost:3000/api/v2/auth/signup \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "testpassword123",
       "plan": "pro"
     }'
   ```

2. **Login** using the credentials in the application

### Option 2: Use Offline License Keys (No Login Required)

If you don't have a backend server, use offline license keys instead:

**Activation Method**:
1. Menu → License → Activate License...
2. Enter one of these keys:
   - `ULBP-9Q2Z-7K3M-4X1A` (Pattern + WiFi)
   - `ULBP-1P4E-8C2J-7R6B` (Pattern + WiFi + Advanced)
   - `ULBP-5X9K-3M7V-1Q4Z` (Pattern only)

See [LICENSE_ACTIVATION_GUIDE.md](LICENSE_ACTIVATION_GUIDE.md) for full list.

---

## Login Methods

### 1. Email/Password Login

**Steps**:
1. Open application
2. Login dialog appears (if not authenticated)
3. Go to "Email/Password" tab
4. Enter email and password
5. Click "Login"
6. License automatically validated

**Backend Endpoint**: `POST /api/v2/auth/login`

**Request Format**:
```json
{
  "email": "test@example.com",
  "password": "testpassword123",
  "device_id": "DEVICE_XXXX",
  "device_name": "Windows Device"
}
```

**Response Format**:
```json
{
  "session_token": "...",
  "entitlement_token": {
    "sub": "user-id",
    "product": "upload_bridge_pro",
    "plan": "pro",
    "features": ["pattern_upload", "wifi_upload", "advanced_controls"],
    "expires_at": 1234567890
  },
  "user": {
    "id": "user-id",
    "email": "test@example.com"
  }
}
```

---

### 2. Magic Link Login

**Steps**:
1. Go to "Magic Link" tab
2. Enter email address
3. Click "Send Magic Link"
4. Check email and click link
5. Return to application

**Note**: Requires Auth0 Passwordless API setup

---

### 3. Social Login (OAuth)

**Steps**:
1. Go to "Social Login" tab
2. Click "Login with Google" or "Login with GitHub"
3. Complete OAuth flow in browser
4. Return to application

**Requirements**:
- Auth0 configured
- Environment variables:
  - `AUTH0_DOMAIN`
  - `AUTH0_CLIENT_ID`
  - `AUTH0_AUDIENCE` (optional)

---

## License System Integration

After successful login:

1. **AuthManager** stores:
   - Session token
   - Entitlement token (contains license info)
   - User info

2. **LicenseManager** automatically:
   - Checks entitlement token
   - Validates license
   - Returns license information

3. **Application** uses license info to:
   - Enable/disable features
   - Show license status
   - Check feature access

---

## Testing Without Backend Server

If you don't have a backend server set up:

### Use Offline License Keys

1. **Skip login** (if possible) or cancel login dialog
2. **Activate license key**:
   - Menu → License → Activate License...
   - Enter: `ULBP-9Q2Z-7K3M-4X1A`
   - Click "Activate"

### Mock Backend for Testing

Create a simple test server:

```python
# test_server.py
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/v2/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    # Simple test credentials
    if email == 'test@example.com' and password == 'testpassword123':
        return jsonify({
            'session_token': 'test-session-token',
            'entitlement_token': {
                'sub': 'test-user-id',
                'product': 'upload_bridge_pro',
                'plan': 'pro',
                'features': ['pattern_upload', 'wifi_upload', 'advanced_controls'],
                'expires_at': None  # Never expires
            },
            'user': {
                'id': 'test-user-id',
                'email': 'test@example.com'
            }
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(port=3000)
```

Run: `python test_server.py`

Then login with:
- Email: `test@example.com`
- Password: `testpassword123`

---

## Troubleshooting

### "Connection error" When Logging In

**Cause**: Backend server not running or wrong URL

**Solutions**:
1. Check server is running at configured URL
2. Verify `LICENSE_SERVER_URL` environment variable
3. Check `config/app_config.yaml` for server URL
4. Try offline license keys instead

### "Login failed: Invalid credentials"

**Cause**: Wrong email/password or account doesn't exist

**Solutions**:
1. Verify email and password are correct
2. Check if account exists on server
3. Try creating account first
4. Use offline license keys as fallback

### License Not Validated After Login

**Cause**: Server didn't return entitlement token

**Solutions**:
1. Check server response includes `entitlement_token`
2. Verify token structure matches expected format
3. Check application logs for errors
4. Try logging out and back in

---

## Configuration

### Server URL

**Default**: `http://localhost:3000`

**Set via**:
- Environment variable: `LICENSE_SERVER_URL`
- Config file: `config/app_config.yaml`
- Code: `AuthManager(server_url="...")`

### Auth0 (for OAuth)

**Required Environment Variables**:
```bash
export AUTH0_DOMAIN="your-domain.auth0.com"
export AUTH0_CLIENT_ID="your-client-id"
export AUTH0_AUDIENCE="your-api-audience"  # Optional
```

---

## Summary

**For Testing**:
- **With Backend**: Use email/password login with test accounts
- **Without Backend**: Use offline license keys (no login required)

**For Production**:
- Set up Auth0 for OAuth/Social login
- Configure backend server for email/password
- Users create accounts and login normally

---

**Last Updated**: 2025-01-27  
**Version**: 3.0.27

