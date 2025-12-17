# Upload Bridge Enterprise Licensing System

## Overview

This is the enterprise-grade account-based licensing system for Upload Bridge, upgraded from file-based licensing to a modern, cloud-enforced system similar to Cursor, JetBrains, and Adobe.

## Architecture

```
┌─────────────────┐
│  Desktop App    │ ← PySide6 GUI
│  (Python)       │
└────────┬────────┘
         │ HTTP/HTTPS
         │ Auth0 JWT
         ▼
┌─────────────────┐
│  License Server │ ← Node.js/Express
│  (Backend)      │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│PostgreSQL│ │  Redis │
│Database │ │ Sessions│
└────────┘ └────────┘
         │
         ▼
┌─────────────────┐
│  Auth0          │ ← Authentication
│  Stripe         │ ← Payments
└─────────────────┘
```

## Features

### Phase 1: Backend Infrastructure ✅
- PostgreSQL database schema
- Auth0 authentication integration
- Entitlement API endpoints
- Token signing with ECDSA P-256

### Phase 2: Payment Integration ✅
- Stripe SDK integration
- Webhook handlers for subscription events
- Checkout session creation
- Billing portal integration

### Phase 3: Desktop Client ✅
- Authentication manager (Python)
- Login dialog with Auth0 support
- Token refresh and session management
- Feature flags system
- Backward compatibility with file-based licenses

### Phase 4: Web Dashboard ✅
- Dashboard backend API
- Device management
- Billing information
- Account settings
- Basic HTML/JavaScript frontend

### Phase 5: Cloud Services ✅
- Pattern sync service
- Preset library
- Format converter API
- Update delivery service

### Phase 6: Security Enhancements ✅
- Integrity heartbeat system
- Enhanced token security (nonces, device binding)
- Per-user rate limiting
- Token revocation list

## Setup

### Prerequisites

1. **PostgreSQL** - Database server
2. **Redis** (optional) - Session storage
3. **Auth0 Account** - Authentication provider
4. **Stripe Account** - Payment processing

### Installation

1. **Install Node.js dependencies:**
```bash
cd license_server
npm install
```

2. **Set up PostgreSQL database:**
```bash
createdb upload_bridge_licensing
psql upload_bridge_licensing < database/schema.sql
```

3. **Configure environment variables:**
Copy `.env.example` to `.env` and fill in:
- `DATABASE_URL` or `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `REDIS_URL` (optional)
- `AUTH0_DOMAIN`
- `AUTH0_AUDIENCE`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`

4. **Start the server:**
```bash
npm start
```

### Python Dependencies

Add to `requirements.txt`:
```
authlib>=1.2.0
requests>=2.31.0
```

## API Endpoints

### Authentication
- `POST /api/v2/auth/login` - Exchange Auth0 token for session
- `POST /api/v2/auth/refresh` - Refresh session token

### Entitlements
- `GET /api/v2/entitlements/current` - Get current entitlements
- `POST /api/v2/entitlements/token` - Get signed entitlement token

### Devices
- `GET /api/v2/devices` - List devices
- `POST /api/v2/devices/register` - Register device
- `DELETE /api/v2/devices/:id` - Revoke device

### Payments
- `POST /api/v2/checkout/create-session` - Create Stripe checkout
- `POST /api/v2/webhooks/stripe` - Stripe webhook handler

### Cloud Services
- `POST /api/v2/sync/upload` - Upload pattern
- `GET /api/v2/sync/list` - List patterns
- `GET /api/v2/presets` - List presets
- `POST /api/v2/convert` - Convert format

## Migration Path

1. **Phase 1-2:** Deploy backend, keep old system running
2. **Phase 3:** Update desktop client with dual-mode (account + file fallback)
3. **Phase 4:** Launch web dashboard
4. **Phase 5:** Migrate users to cloud services
5. **Phase 6:** Deprecate file-based licenses (6 months after launch)

## Security

- **ECDSA P-256** signing for tokens
- **Hardware-bound** encryption
- **Device binding** prevents license sharing
- **Token revocation** list
- **Integrity checks** detect tampering
- **Rate limiting** per user/plan

## License

MIT License
