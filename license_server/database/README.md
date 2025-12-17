# Database Schema and Migrations

This directory contains the PostgreSQL database schema and migration scripts for the Upload Bridge Enterprise Licensing System.

## Setup

1. Create a PostgreSQL database:
```bash
createdb upload_bridge_licensing
```

2. Run the schema:
```bash
psql upload_bridge_licensing < schema.sql
```

3. Run migrations in order:
```bash
psql upload_bridge_licensing < migrations/001_initial_schema.sql
```

## Schema Overview

### Core Tables

- **users** - User accounts linked to Auth0
- **entitlements** - User entitlements (subscriptions/licenses)
- **devices** - Devices bound to user entitlements
- **sessions** - Active user sessions

### Cloud Services Tables (Phase 5)

- **cloud_patterns** - User patterns synced to cloud
- **presets** - Curated and user-contributed presets

### Security Tables (Phase 6)

- **revoked_tokens** - Revoked tokens to prevent reuse
- **integrity_checks** - Integrity check data for anomaly detection

## Environment Variables

Set these in your `.env` file:

```
DATABASE_URL=postgresql://user:password@localhost:5432/upload_bridge_licensing
DB_HOST=localhost
DB_PORT=5432
DB_NAME=upload_bridge_licensing
DB_USER=your_user
DB_PASSWORD=your_password
```

## Migrations

Migrations are numbered sequentially. Always run them in order.

## Views

- **active_entitlements** - View of all active entitlements with device counts
