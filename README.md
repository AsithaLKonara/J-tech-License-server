# Upload Bridge License Server

Vercel serverless functions for Upload Bridge license management and authentication.

## 🚀 Quick Deploy to Vercel

### Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI**: Install globally
   ```bash
   npm install -g vercel
   ```

### Deployment Steps

1. **Install Dependencies**:
   ```bash
   cd license-server
   npm install
   ```

2. **Deploy to Vercel**:
   ```bash
   vercel --prod
   ```

3. **Get Your Deployment URL**:
   After deployment, Vercel will provide a URL like:
   ```
   https://your-project-name.vercel.app
   ```

4. **Update Application Configuration**:
   Update `apps/upload-bridge/config/auth_config.yaml`:
   ```yaml
   auth_server_url: https://your-project-name.vercel.app
   ```

## 📋 API Endpoints

### POST `/api/v2/auth/login`

Authenticate user and return session/entitlement tokens.

**Request**:
```json
{
  "email": "test@example.com",
  "password": "testpassword123",
  "device_id": "DEVICE_XXXX",
  "device_name": "Windows Device"
}
```

**Response**:
```json
{
  "session_token": "session_...",
  "entitlement_token": {
    "sub": "user_test_example_com",
    "product": "upload_bridge_pro",
    "plan": "pro",
    "features": ["pattern_upload", "wifi_upload", "advanced_controls"],
    "expires_at": null
  },
  "user": {
    "id": "user_test_example_com",
    "email": "test@example.com"
  }
}
```

### POST `/api/v2/auth/refresh`

Refresh session token.

**Request**:
```json
{
  "session_token": "session_...",
  "device_id": "DEVICE_XXXX"
}
```

### GET `/api/health`

Health check endpoint.

**Response**:
```json
{
  "status": "ok",
  "service": "upload-bridge-license-server",
  "version": "1.0.0",
  "timestamp": "2025-01-27T12:00:00.000Z"
}
```

## 👤 Test Accounts

Default test accounts (configured in code):

- **Email**: `test@example.com`
  - **Password**: `testpassword123`
  - **Plan**: `pro`
  - **Features**: pattern_upload, wifi_upload, advanced_controls

- **Email**: `demo@example.com`
  - **Password**: `demo123`
  - **Plan**: `basic`
  - **Features**: pattern_upload

## 🔧 Configuration

### Environment Variables

Set these in Vercel dashboard (Settings → Environment Variables):

- `NODE_ENV`: `production`
- `JWT_SECRET`: (optional, for production JWT signing)
- `DATABASE_URL`: (optional, for production database)

### Production Setup

For production, you should:

1. **Replace in-memory user database** with a real database (PostgreSQL, MongoDB, etc.)
2. **Use password hashing** (bcrypt, argon2, etc.)
3. **Implement JWT tokens** with proper signing and expiration
4. **Add rate limiting** to prevent abuse
5. **Add CORS configuration** if needed
6. **Add logging and monitoring**

## 📝 Local Development

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Run locally**:
   ```bash
   cd license-server
   vercel dev
   ```

3. **Test endpoints**:
   ```bash
   curl -X POST http://localhost:3000/api/v2/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"testpassword123","device_id":"DEVICE_123","device_name":"Test Device"}'
   ```

## 🔒 Security Notes

⚠️ **This is a demo implementation**. For production:

- Use proper password hashing (bcrypt, argon2)
- Implement JWT with proper signing
- Add rate limiting
- Use HTTPS only
- Validate and sanitize all inputs
- Use a real database
- Add authentication middleware
- Implement proper error handling
- Add logging and monitoring

## 📚 Documentation

- [Vercel Serverless Functions](https://vercel.com/docs/functions)
- [Vercel CLI](https://vercel.com/docs/cli)

