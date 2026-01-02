# 🔄 Migration Plan: Remove Auth0, Use Direct JWT

## 📊 Current Architecture Analysis

### Current Flow (With Auth0)
```
User → Auth0 Login → Auth0 JWT Token → License Server → Session Token + Entitlement Token
```

### Proposed Flow (Direct JWT)
```
User → License Server Login → License Server JWT Token → Session Token + Entitlement Token
```

## ✅ Benefits of Removing Auth0

1. **Simpler Architecture**
   - No external dependency
   - Full control over authentication
   - Fewer moving parts

2. **Cost Savings**
   - No Auth0 subscription needed
   - No API call limits

3. **Easier Deployment**
   - No Auth0 configuration needed
   - No callback URL management
   - Simpler environment variables

4. **Better Control**
   - Custom user management
   - Custom password policies
   - Direct database integration

## ❌ What We Lose

1. **Social Login** (Google, GitHub, etc.)
   - Would need to implement OAuth providers directly
   - More complex to maintain

2. **Auth0 Universal Login UI**
   - Need to build custom login UI
   - More development work

3. **Passwordless/Magic Link**
   - Need to implement email verification
   - Need email service integration

4. **Built-in Security Features**
   - Rate limiting
   - Brute force protection
   - MFA (would need to implement)

## 🏗️ Implementation Plan

### Phase 1: Add Direct Authentication to License Server

#### 1.1 Update Login Endpoint

**Current**: Accepts `auth0_token`
**New**: Accepts `email` + `password`

```typescript
// New login endpoint
POST /api/v2/auth/login
{
  "email": "user@example.com",
  "password": "password123",
  "device_id": "DEVICE_123",
  "device_name": "Windows Device"
}
```

#### 1.2 Add User Management

- Password hashing (bcrypt/argon2)
- User registration endpoint
- Password reset endpoint
- Email verification (optional)

#### 1.3 JWT Token Generation

- Generate JWT tokens directly
- Sign with server's private key
- Include user info, license info in token

### Phase 2: Update Upload Bridge

#### 2.1 Remove Auth0 Dependencies

- Remove `oauth_handler.py`
- Remove Auth0 config from `auth_config.yaml`
- Simplify `login_dialog.py`

#### 2.2 Update AuthManager

- Remove Auth0 token exchange
- Direct email/password login
- Validate JWT tokens from license server

### Phase 3: Database Schema

#### 3.1 User Table

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  email_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.2 Session Management

- Store refresh tokens
- Track active sessions
- Device management

## 📝 Detailed Implementation

### Step 1: Add Password Hashing

```typescript
// lib/password.ts
import bcrypt from 'bcrypt';

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10);
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}
```

### Step 2: Update Login Endpoint

```typescript
// server.ts - Updated login endpoint
app.post('/api/v2/auth/login', async (req, res) => {
  const { email, password, device_id, device_name } = req.body;
  
  // Validate email/password
  if (!email || !password) {
    return res.status(400).json({ error: 'Email and password required' });
  }
  
  // Find user
  const user = await getUserByEmail(email);
  if (!user) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  
  // Verify password
  const isValid = await verifyPassword(password, user.password_hash);
  if (!isValid) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  
  // Generate JWT token
  const jwtToken = generateJWT({
    sub: user.id,
    email: user.email,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 3600 // 1 hour
  });
  
  // Get license
  const license = await getUserLicense(user.id);
  
  // Generate session and entitlement tokens
  const sessionToken = generateSessionToken(user.id, device_id);
  const entitlementToken = licenseToEntitlementToken(user.id, license);
  
  return res.json({
    jwt_token: jwtToken,
    session_token: sessionToken,
    entitlement_token: entitlementToken,
    user: { id: user.id, email: user.email }
  });
});
```

### Step 3: Add Registration Endpoint

```typescript
app.post('/api/v2/auth/register', async (req, res) => {
  const { email, password, device_id, device_name } = req.body;
  
  // Validate input
  if (!email || !password) {
    return res.status(400).json({ error: 'Email and password required' });
  }
  
  // Check if user exists
  const existing = await getUserByEmail(email);
  if (existing) {
    return res.status(409).json({ error: 'User already exists' });
  }
  
  // Hash password
  const passwordHash = await hashPassword(password);
  
  // Create user
  const user = await createUser(email, passwordHash);
  
  // Create default license
  const license = await upsertUserLicense(
    user.id,
    'pro',
    ['pattern_upload', 'wifi_upload', 'advanced_controls'],
    null
  );
  
  // Generate tokens
  const jwtToken = generateJWT({ sub: user.id, email: user.email });
  const sessionToken = generateSessionToken(user.id, device_id);
  const entitlementToken = licenseToEntitlementToken(user.id, license);
  
  return res.status(201).json({
    jwt_token: jwtToken,
    session_token: sessionToken,
    entitlement_token: entitlementToken,
    user: { id: user.id, email: user.email }
  });
});
```

### Step 4: JWT Token Generation

```typescript
// lib/jwt-generator.ts
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';
const JWT_EXPIRY = 3600; // 1 hour

export function generateJWT(payload: {
  sub: string;
  email: string;
  [key: string]: any;
}): string {
  return jwt.sign(
    {
      ...payload,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + JWT_EXPIRY,
      iss: 'j-tech-license-server',
      aud: 'upload-bridge'
    },
    JWT_SECRET,
    { algorithm: 'HS256' }
  );
}

export function verifyJWT(token: string): any {
  return jwt.verify(token, JWT_SECRET, {
    algorithms: ['HS256'],
    issuer: 'j-tech-license-server',
    audience: 'upload-bridge'
  });
}
```

## 🔄 Migration Steps

### Step 1: Add New Endpoints (Backward Compatible)

1. Add `/api/v2/auth/register` endpoint
2. Update `/api/v2/auth/login` to accept email/password
3. Keep Auth0 token support temporarily (for migration)

### Step 2: Update Database

1. Add `password_hash` column to users table
2. Add password reset tokens table
3. Migrate existing users (if any)

### Step 3: Update Upload Bridge

1. Remove Auth0 OAuth handler
2. Update login dialog to use email/password only
3. Update AuthManager to use new endpoints

### Step 4: Remove Auth0 Code

1. Remove `jwt-validator.ts` (Auth0 JWKS validation)
2. Remove Auth0 environment variables
3. Remove Auth0 configuration files

## 📋 New API Endpoints

### POST `/api/v2/auth/register`
Register new user

**Request**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "device_id": "DEVICE_123",
  "device_name": "Windows Device"
}
```

**Response**:
```json
{
  "jwt_token": "eyJhbGc...",
  "session_token": "session_...",
  "entitlement_token": {...},
  "user": {"id": "...", "email": "user@example.com"}
}
```

### POST `/api/v2/auth/login` (Updated)
Login with email/password

**Request**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "device_id": "DEVICE_123",
  "device_name": "Windows Device"
}
```

### POST `/api/v2/auth/refresh`
Refresh JWT token using refresh token

### POST `/api/v2/auth/reset-password`
Request password reset

### POST `/api/v2/auth/verify-email`
Verify email address

## 🔒 Security Considerations

1. **Password Hashing**: Use bcrypt or argon2
2. **JWT Secret**: Use strong secret, store in environment
3. **Rate Limiting**: Add rate limiting to login endpoints
4. **HTTPS Only**: Enforce HTTPS in production
5. **Token Expiry**: Short-lived access tokens, longer refresh tokens
6. **Password Policy**: Enforce strong passwords

## 📦 Dependencies to Add

```json
{
  "dependencies": {
    "bcrypt": "^5.1.1",
    "jsonwebtoken": "^9.0.2"
  },
  "devDependencies": {
    "@types/bcrypt": "^5.0.2",
    "@types/jsonwebtoken": "^9.0.5"
  }
}
```

## ⚠️ Breaking Changes

1. **Social Login**: Will no longer work (unless re-implemented)
2. **Magic Link**: Will no longer work (unless re-implemented)
3. **Existing Users**: Need to set passwords or migrate
4. **Auth0 Tokens**: Will no longer be accepted

## 🎯 Recommendation

**Pros**:
- ✅ Simpler architecture
- ✅ Full control
- ✅ Cost savings
- ✅ Easier deployment

**Cons**:
- ❌ Lose social login
- ❌ Need to implement security features
- ❌ More development work

**Verdict**: **GOOD IDEA** if:
- You don't need social login
- You want full control
- You want to reduce dependencies
- You're okay with email/password only

---

**Status**: 📋 Planning Phase  
**Estimated Effort**: 2-3 days  
**Risk Level**: Medium (breaking changes)

