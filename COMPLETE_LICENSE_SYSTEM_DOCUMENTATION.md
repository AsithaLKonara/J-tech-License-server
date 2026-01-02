# 📋 Complete License System Documentation

**Upload Bridge License System - Complete Architecture Overview**

---

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Upload Bridge  │◄───────►│  License Server  │◄───────►│     Auth0       │
│   (Desktop)     │         │   (Railway)      │         │  (OAuth/SSO)    │
└─────────────────┘         └──────────────────┘         └─────────────────┘
       │                            │
       │                            │
       ▼                            ▼
┌─────────────────┐         ┌──────────────────┐
│  Local Storage  │         │  In-Memory DB     │
│  (Encrypted)    │         │  (Users/Licenses) │
└─────────────────┘         └──────────────────┘
```

---

## 🔐 Authentication Flow

### Current Flow (With Auth0)

```
1. User → Auth0 Login (OAuth PKCE)
   ↓
2. Auth0 → Issues JWT Token
   ↓
3. Upload Bridge → Sends Auth0 Token to License Server
   ↓
4. License Server → Validates Auth0 Token (JWKS)
   ↓
5. License Server → Creates/Retrieves User
   ↓
6. License Server → Gets/Creates License
   ↓
7. License Server → Issues Session Token + Entitlement Token
   ↓
8. Upload Bridge → Stores Tokens Locally
   ↓
9. License Manager → Validates License from Tokens
```

### Components

#### 1. **Auth0 Integration** (`apps/license-server/lib/jwt-validator.ts`)
- Validates Auth0 JWT tokens using JWKS (JSON Web Key Set)
- Extracts user information (sub, email)
- Verifies token signature, expiry, issuer, audience

#### 2. **License Server** (`apps/license-server/server.ts`)
- Express.js server deployed on Railway
- Endpoints:
  - `POST /api/v2/auth/login` - Authenticate with Auth0 token
  - `POST /api/v2/auth/refresh` - Refresh session token
  - `GET /api/health` - Health check

#### 3. **Upload Bridge Auth Manager** (`apps/upload-bridge/core/auth_manager.py`)
- Manages authentication state
- Stores session and entitlement tokens
- Handles token refresh
- Provides feature checking via `EntitlementManager`

---

## 📦 License Types

### 1. **Account-Based License** (Primary)

**Source**: Entitlement token from License Server  
**Storage**: In-memory (via AuthManager)  
**Validation**: Real-time via entitlement token

**Flow**:
1. User logs in via Auth0
2. License Server issues entitlement token
3. Token contains: `plan`, `features`, `expires_at`
4. License Manager validates token
5. Features checked from token

**Token Structure**:
```json
{
  "sub": "user_123",
  "product": "upload_bridge_pro",
  "plan": "pro",
  "features": ["pattern_upload", "wifi_upload", "advanced_controls"],
  "expires_at": null,
  "issued_at": 1234567890
}
```

### 2. **File-Based License** (Fallback)

**Source**: Offline license keys  
**Storage**: Encrypted file (`~/.upload_bridge/license/license.enc`)  
**Validation**: Local + optional server validation

**Flow**:
1. User enters license key (e.g., `ULBP-9Q2Z-7K3M-4X1A`)
2. License Manager validates key against `config/license_keys.yaml`
3. License encrypted and saved to disk
4. License bound to device (hardware fingerprint)
5. Validated locally (with 7-day cache)

**License Key Format**:
- Format: `ULBP-XXXX-XXXX-XXXX`
- Stored in: `apps/upload-bridge/config/license_keys.yaml`
- Features defined per key

**Example License Data**:
```json
{
  "license": {
    "license_id": "ULBP-9Q2Z-7K3M-4X1A",
    "product_id": "upload_bridge_pro",
    "features": ["pattern_upload", "wifi_upload"],
    "expires_at": null,
    "device_id": "DEVICE_ABC123",
    "issued_to_email": null
  },
  "integrity_hash": "abc123...",
  "signature": "..."
}
```

---

## 🗄️ Database Schema (In-Memory)

### User Model
```typescript
interface User {
  id: string;                    // e.g., "user_1234567890_abc123"
  email: string;                 // e.g., "user@example.com"
  auth0_sub: string;             // Auth0 subject ID
  created_at: Date;
}
```

### License Model
```typescript
interface License {
  id: string;                    // e.g., "license_1234567890_xyz789"
  user_id: string;               // Foreign key to User
  plan: string;                  // "pro", "basic", "standard"
  features: string[];             // ["pattern_upload", "wifi_upload", ...]
  expires_at: Date | null;        // null = perpetual
  status: 'active' | 'expired' | 'revoked' | 'suspended';
  created_at: Date;
  updated_at: Date;
}
```

### Device Model
```typescript
interface Device {
  id: string;                    // e.g., "device_1234567890_def456"
  license_id: string;            // Foreign key to License
  device_id: string;             // Hardware fingerprint
  device_name: string;           // e.g., "Windows Device"
  registered_at: Date;
  last_seen_at: Date;
}
```

**Storage**: Currently in-memory (Map-based)  
**TODO**: Migrate to PostgreSQL/SQLite

---

## 🔑 License Server API

### POST `/api/v2/auth/login`

**Purpose**: Authenticate user and get license tokens

**Request**:
```json
{
  "auth0_token": "eyJhbGc...",
  "device_id": "DEVICE_ABC123",
  "device_name": "Windows Device"
}
```

**Response**:
```json
{
  "session_token": "session_eyJ1c2VyX2lkIjoi...",
  "entitlement_token": {
    "sub": "user_123",
    "product": "upload_bridge_pro",
    "plan": "pro",
    "features": ["pattern_upload", "wifi_upload", "advanced_controls"],
    "expires_at": null,
    "issued_at": 1234567890
  },
  "user": {
    "id": "user_123",
    "email": "user@example.com"
  }
}
```

**Process**:
1. Validate Auth0 token (JWKS)
2. Extract user info (sub, email)
3. Get or create user in database
4. Get or create license (default: pro plan)
5. Validate license status
6. Register device
7. Generate session token
8. Create entitlement token
9. Return tokens

### POST `/api/v2/auth/refresh`

**Purpose**: Refresh session token

**Request**:
```json
{
  "session_token": "session_...",
  "device_id": "DEVICE_ABC123"
}
```

**Response**:
```json
{
  "session_token": "session_...",
  "entitlement_token": { ... }
}
```

**Process**:
1. Decode session token
2. Get user ID
3. Get user's license
4. Validate license
5. Generate new session token
6. Return new tokens

---

## 🛡️ License Manager (Upload Bridge)

### Location
`apps/upload-bridge/core/license_manager.py`

### Key Methods

#### `validate_license(force_online: bool = False)`
**Purpose**: Validate license (account-based first, then file-based)

**Returns**: `(is_valid: bool, message: str, license_info: dict)`

**Priority**:
1. **Account-Based License** (from AuthManager)
   - Checks entitlement token
   - Validates expiry
   - Returns immediately if valid
2. **File-Based License** (fallback)
   - Loads from encrypted file
   - Validates locally
   - Optionally validates with server

#### `_validate_account_based_license()`
**Purpose**: Validate license from AuthManager entitlement token

**Process**:
1. Get AuthManager instance
2. Check if has valid token
3. Get entitlement token
4. Convert to license format
5. Check expiry
6. Return license info

#### `_validate_license_locally(license_data)`
**Purpose**: Perform local validation checks

**Checks**:
1. Format validation
2. Expiry check
3. Device binding
4. Integrity hash (tamper detection)
5. Signature verification (if present)

#### `save_license(license_data, validate_online=True)`
**Purpose**: Save license to encrypted file

**Process**:
1. Validate format
2. Optional server validation
3. Bind to device
4. Calculate integrity hash
5. Encrypt and save
6. Save to cache

#### `load_cached_license()`
**Purpose**: Load license from encrypted file or cache

**Priority**:
1. Encrypted file (`license.enc`)
2. Cache file (`license_cache.json`)

---

## 🔒 Security Features

### 1. **Device Binding**
- License bound to hardware fingerprint
- Device ID generated from: `machine_id + node_id + system_id`
- Prevents license sharing across devices

### 2. **Encryption**
- License encrypted using device-bound key
- Key derived from device ID (PBKDF2, 100k iterations)
- Uses Fernet (symmetric encryption)

### 3. **Integrity Hash**
- SHA-256 hash of critical fields
- Detects tampering
- Stored with license data

### 4. **Token Security**
- Session tokens: Base64-encoded JSON (simple)
- Entitlement tokens: JSON structure (not JWT)
- Auth0 tokens: JWT (signed by Auth0)

### 5. **Cache Validation**
- 7-day cache validity
- Offline mode support
- Server validation when cache stale

---

## 📊 Feature Management

### Available Features

1. **`pattern_upload`** - Pattern file upload capability
2. **`wifi_upload`** - WiFi upload functionality
3. **`advanced_controls`** - Advanced control features

### Feature Checking

**In Upload Bridge**:
```python
from core.auth_manager import AuthManager

auth_manager = AuthManager()
entitlement_manager = EntitlementManager(auth_manager)

# Check if feature enabled
if entitlement_manager.is_feature_enabled('pattern_upload'):
    # Enable feature
    pass
```

**In License Manager**:
```python
license_manager = LicenseManager.instance()
is_valid, message, license_info = license_manager.validate_license()

if license_info:
    features = license_info['license'].get('features', [])
    if 'pattern_upload' in features:
        # Enable feature
        pass
```

---

## 🔄 License Validation Priority

### Priority Order

1. **Account-Based License** (Highest Priority)
   - From AuthManager entitlement token
   - Real-time validation
   - Always checked first

2. **File-Based License** (Fallback)
   - From encrypted license file
   - Local validation
   - Server validation optional

### Validation Flow

```
Start
  ↓
Check AuthManager.has_valid_token()
  ↓ Yes
Get entitlement_token
  ↓
Check expiry
  ↓ Valid
Return account-based license ✅
  ↓ No/Expired
Check encrypted license file
  ↓ Exists
Load and decrypt
  ↓
Validate locally
  ↓ Valid
Check cache age
  ↓ Recent (< 7 days)
Return file-based license ✅
  ↓ Stale
Validate with server
  ↓ Valid
Update cache
Return file-based license ✅
  ↓ Invalid
Return error ❌
```

---

## 📁 File Structure

### License Server
```
apps/license-server/
├── server.ts                 # Express server
├── lib/
│   ├── models.ts             # TypeScript interfaces
│   ├── database.ts           # In-memory database
│   └── jwt-validator.ts      # Auth0 token validation
└── package.json
```

### Upload Bridge
```
apps/upload-bridge/
├── core/
│   ├── license_manager.py    # License validation
│   ├── auth_manager.py       # Authentication
│   └── feature_flags.py      # Feature checking
├── config/
│   └── license_keys.yaml     # Offline license keys
└── ~/.upload_bridge/
    └── license/
        ├── license.enc        # Encrypted license
        └── license_cache.json # Cache file
```

---

## 🧪 Test Accounts & Keys

### Test License Keys (Offline)

| Key | Features |
|-----|----------|
| `ULBP-9Q2Z-7K3M-4X1A` | Pattern + WiFi |
| `ULBP-1P4E-8C2J-7R6B` | Pattern + WiFi + Advanced |
| `ULBP-5X9K-3M7V-1Q4Z` | Pattern only |

### Default License (Account-Based)

When user logs in via Auth0:
- **Plan**: `pro`
- **Features**: `["pattern_upload", "wifi_upload", "advanced_controls"]`
- **Expires**: `null` (perpetual)

---

## 🔧 Configuration

### License Server Environment Variables

```bash
AUTH0_DOMAIN=dev-oczlciw58f2a4oei.us.auth0.com
AUTH0_AUDIENCE=https://j-tech-license-server-production.up.railway.app
PORT=3000
```

### Upload Bridge Configuration

**`config/auth_config.yaml`**:
```yaml
auth_server_url: "https://j-tech-license-server-production.up.railway.app"
auth0_domain: "dev-oczlciw58f2a4oei.us.auth0.com"
auth0_client_id: "AVLPE7EULVWdJV5NIzFI56EAeHmnt2Um"
```

**`config/app_config.yaml`**:
```yaml
auth:
  audience: "https://j-tech-license-server-production.up.railway.app"
```

---

## 🚀 Deployment

### License Server
- **Platform**: Railway
- **URL**: `https://j-tech-license-server-production.up.railway.app`
- **Framework**: Express.js
- **Database**: In-memory (TODO: PostgreSQL)

### Upload Bridge
- **Platform**: Desktop (Windows/Mac/Linux)
- **Storage**: Local filesystem
- **Encryption**: Device-bound

---

## 📝 Current Limitations

1. **In-Memory Database**
   - Data lost on server restart
   - TODO: Migrate to PostgreSQL/SQLite

2. **Simple Session Tokens**
   - Base64-encoded JSON (not JWT)
   - TODO: Use proper JWT for session tokens

3. **No Password Authentication**
   - Only Auth0 OAuth
   - TODO: Add email/password login

4. **No License Management UI**
   - Manual database operations
   - TODO: Admin dashboard

5. **No License Expiry Management**
   - Default licenses are perpetual
   - TODO: Add expiry handling

---

## 🔮 Future Enhancements

1. **Database Migration**
   - PostgreSQL for production
   - SQLite for development

2. **Direct JWT Authentication**
   - Remove Auth0 dependency
   - Self-hosted authentication

3. **License Management**
   - Admin dashboard
   - License creation/revocation
   - Usage analytics

4. **Enhanced Security**
   - MFA support
   - Rate limiting
   - Brute force protection

5. **Feature Flags**
   - Dynamic feature enabling
   - A/B testing support

---

**Last Updated**: 2025-01-02  
**Version**: 1.0.0  
**Status**: Production (Railway)

