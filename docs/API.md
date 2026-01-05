# Upload Bridge License Server API Documentation

**Version**: 2.0  
**Base URL**: `https://yourdomain.com/api/v2`  
**Last Updated**: 2025-01-27

---

## Overview

The Upload Bridge License Server API provides authentication, license management, and device management endpoints for the Upload Bridge desktop application. All API endpoints use JSON for request and response formats.

## Authentication

The API uses token-based authentication. After logging in, you receive a `session_token` that must be included in subsequent requests using the `Authorization` header:

```
Authorization: Bearer <session_token>
```

## Base URL and Versioning

- **Base URL**: Your web dashboard URL (e.g., `https://yourdomain.com`)
- **API Version**: `/api/v2`
- **Full Endpoint**: `{BASE_URL}/api/v2/{endpoint}`

## Endpoints

### Health Check

#### GET /api/v2/health

Public endpoint to check API health status.

**Request:**
```http
GET /api/v2/health
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-01-27T12:00:00Z",
  "version": "2.0"
}
```

**Status Codes:**
- `200 OK` - API is healthy

---

### Authentication

#### POST /api/v2/auth/login

Authenticate user with email/password or magic link token.

**Request Body (Email/Password):**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "device_id": "DEVICE_ABC123",
  "device_name": "My Computer"
}
```

**Request Body (Magic Link):**
```json
{
  "magic_link_token": "token_from_email",
  "device_id": "DEVICE_ABC123",
  "device_name": "My Computer"
}
```

**Response (Success):**
```json
{
  "session_token": "random_token_string",
  "entitlement_token": {
    "sub": "user_id",
    "email": "user@example.com",
    "plan": "monthly",
    "features": ["pattern_upload", "wifi_upload"],
    "max_devices": 2,
    "expires_at": 1234567890,
    "iat": 1234567890,
    "exp": 1234567890
  },
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "name": "User Name"
  }
}
```

**Status Codes:**
- `200 OK` - Login successful
- `400 Bad Request` - Missing required fields
- `401 Unauthorized` - Invalid credentials
- `403 Forbidden` - Device limit exceeded

**Error Response:**
```json
{
  "error": "Invalid email or password"
}
```

---

#### POST /api/v2/auth/refresh

Refresh session token and get updated entitlement token.

**Request Body:**
```json
{
  "session_token": "current_session_token",
  "device_id": "DEVICE_ABC123"
}
```

**Response:**
```json
{
  "session_token": "new_session_token",
  "entitlement_token": {
    "sub": "user_id",
    "email": "user@example.com",
    "plan": "monthly",
    "features": ["pattern_upload", "wifi_upload"],
    "max_devices": 2,
    "expires_at": 1234567890,
    "iat": 1234567890,
    "exp": 1234567890
  }
}
```

**Status Codes:**
- `200 OK` - Token refreshed successfully
- `400 Bad Request` - Missing session token
- `401 Unauthorized` - Invalid or expired token

---

#### POST /api/v2/auth/logout

Revoke session token (logout).

**Request Body:**
```json
{
  "session_token": "session_token_to_revoke"
}
```

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

**Status Codes:**
- `200 OK` - Logout successful
- `400 Bad Request` - Missing session token

---

#### POST /api/v2/auth/magic-link/verify

Verify magic link token (alternative to login endpoint).

**Request Body:**
```json
{
  "magic_link_token": "token_from_email",
  "device_id": "DEVICE_ABC123",
  "device_name": "My Computer"
}
```

**Response:** Same as `/api/v2/auth/login`

**Status Codes:**
- `200 OK` - Magic link verified and login successful
- `400 Bad Request` - Missing magic link token
- `401 Unauthorized` - Invalid or expired magic link token

---

### License Management

#### GET /api/v2/license/validate

Validate entitlement token (requires authentication).

**Headers:**
```
Authorization: Bearer <session_token>
```

**Request Body:**
```json
{
  "entitlement_token": {
    "sub": "user_id",
    "plan": "monthly",
    "exp": 1234567890
  }
}
```

**Response:**
```json
{
  "valid": true,
  "timestamp": "2025-01-27T12:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Validation successful
- `400 Bad Request` - Missing entitlement token
- `401 Unauthorized` - Invalid session token

---

#### GET /api/v2/license/info

Get license information for authenticated user (requires authentication).

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response:**
```json
{
  "entitlement": {
    "id": "entitlement_id",
    "plan": "monthly",
    "status": "active",
    "features": ["pattern_upload", "wifi_upload"],
    "max_devices": 2,
    "current_devices": 1,
    "expires_at": "2025-02-27T12:00:00Z",
    "is_active": true
  }
}
```

**Status Codes:**
- `200 OK` - License info retrieved
- `401 Unauthorized` - Invalid session token
- `404 Not Found` - No active entitlement found

---

### Device Management

#### POST /api/v2/devices/register

Register a new device for authenticated user (requires authentication).

**Headers:**
```
Authorization: Bearer <session_token>
```

**Request Body:**
```json
{
  "device_id": "DEVICE_ABC123",
  "device_name": "My Computer"
}
```

**Response:**
```json
{
  "message": "Device registered",
  "device": {
    "id": 1,
    "device_id": "DEVICE_ABC123",
    "device_name": "My Computer",
    "last_seen_at": "2025-01-27T12:00:00Z"
  }
}
```

**Status Codes:**
- `200 OK` - Device registered successfully
- `400 Bad Request` - Missing device_id
- `401 Unauthorized` - Invalid session token
- `403 Forbidden` - Device limit exceeded

**Error Response (Device Limit):**
```json
{
  "error": "Device limit reached",
  "max_devices": 2,
  "current_devices": 2
}
```

---

#### GET /api/v2/devices

List all devices for authenticated user (requires authentication).

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response:**
```json
{
  "devices": [
    {
      "id": 1,
      "device_id": "DEVICE_ABC123",
      "device_name": "My Computer",
      "last_seen_at": "2025-01-27T12:00:00Z",
      "entitlement_id": "entitlement_id"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Devices retrieved successfully
- `401 Unauthorized` - Invalid session token

---

#### DELETE /api/v2/devices/{id}

Remove a device (requires authentication).

**Headers:**
```
Authorization: Bearer <session_token>
```

**Parameters:**
- `id` (path) - Device ID to delete

**Response:**
```json
{
  "message": "Device removed successfully"
}
```

**Status Codes:**
- `200 OK` - Device removed successfully
- `401 Unauthorized` - Invalid session token
- `404 Not Found` - Device not found

---

## Error Codes

### HTTP Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request format or missing required fields
- `401 Unauthorized` - Authentication required or invalid credentials
- `403 Forbidden` - Access denied (e.g., device limit exceeded)
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Error Response Format

All error responses follow this format:

```json
{
  "error": "Error message description",
  "messages": {
    "field_name": ["Validation error message"]
  }
}
```

---

## Authentication Flow

### Email/Password Login Flow

1. User provides email and password
2. Client sends `POST /api/v2/auth/login` with credentials
3. Server validates credentials and creates session
4. Server returns `session_token` and `entitlement_token`
5. Client stores tokens for subsequent requests
6. Client includes `Authorization: Bearer <session_token>` in API requests

### Magic Link Login Flow

1. User requests magic link via web interface (`POST /magic-link`)
2. Server sends email with magic link token
3. User clicks link in email
4. Client sends `POST /api/v2/auth/login` with `magic_link_token`
5. Server validates token and creates session
6. Server returns `session_token` and `entitlement_token`
7. Client stores tokens for subsequent requests

### Token Refresh Flow

1. Client detects token is about to expire
2. Client sends `POST /api/v2/auth/refresh` with current `session_token`
3. Server validates token and generates new tokens
4. Server returns new `session_token` and updated `entitlement_token`
5. Client updates stored tokens

---

## Rate Limiting

Currently, rate limiting is not implemented but is planned for production. Recommended limits:

- **Authentication endpoints**: 5 requests per minute per IP
- **License endpoints**: 60 requests per minute per user
- **Device endpoints**: 30 requests per minute per user

---

## Examples

### Complete Login Flow (cURL)

```bash
# Login
curl -X POST http://localhost:8000/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "device_id": "DEVICE_ABC123",
    "device_name": "My Computer"
  }'

# Use session token for authenticated requests
curl -X GET http://localhost:8000/api/v2/license/info \
  -H "Authorization: Bearer <session_token>"
```

### Python Example

```python
import requests

# Login
response = requests.post('http://localhost:8000/api/v2/auth/login', json={
    'email': 'user@example.com',
    'password': 'password123',
    'device_id': 'DEVICE_ABC123',
    'device_name': 'My Computer'
})

data = response.json()
session_token = data['session_token']
entitlement_token = data['entitlement_token']

# Get license info
headers = {'Authorization': f'Bearer {session_token}'}
license_response = requests.get(
    'http://localhost:8000/api/v2/license/info',
    headers=headers
)
```

### JavaScript Example

```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/api/v2/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123',
    device_id: 'DEVICE_ABC123',
    device_name: 'My Computer'
  })
});

const loginData = await loginResponse.json();
const sessionToken = loginData.session_token;

// Get license info
const licenseResponse = await fetch('http://localhost:8000/api/v2/license/info', {
  headers: { 'Authorization': `Bearer ${sessionToken}` }
});
```

---

## Support

For API support, please contact support or check the documentation.

**Last Updated**: 2025-01-27
