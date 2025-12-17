-- Upload Bridge Enterprise Licensing Database Schema
-- PostgreSQL Database Schema for Account-Based Licensing System

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users Table
-- Stores user accounts linked to Auth0
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    auth0_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index on email for fast lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_auth0_id ON users(auth0_id);

-- Entitlements Table
-- Stores user entitlements (subscriptions, licenses)
CREATE TABLE entitlements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    product_id VARCHAR(100) NOT NULL DEFAULT 'upload_bridge_pro',
    plan VARCHAR(50) NOT NULL, -- 'trial', 'monthly', 'yearly', 'perpetual'
    features JSONB DEFAULT '[]',
    max_devices INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'expired', 'revoked', 'cancelled', 'payment_failed'
    stripe_subscription_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_plan CHECK (plan IN ('trial', 'monthly', 'yearly', 'perpetual')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'expired', 'revoked', 'cancelled', 'payment_failed'))
);

-- Create indexes for entitlements
CREATE INDEX idx_entitlements_user_id ON entitlements(user_id);
CREATE INDEX idx_entitlements_status ON entitlements(status);
CREATE INDEX idx_entitlements_stripe_subscription ON entitlements(stripe_subscription_id);
CREATE INDEX idx_entitlements_expires_at ON entitlements(expires_at);

-- Devices Table
-- Tracks devices bound to user entitlements
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    entitlement_id UUID REFERENCES entitlements(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL, -- Hardware fingerprint
    device_name VARCHAR(255),
    last_seen TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, device_id)
);

-- Create indexes for devices
CREATE INDEX idx_devices_user_id ON devices(user_id);
CREATE INDEX idx_devices_entitlement_id ON devices(entitlement_id);
CREATE INDEX idx_devices_device_id ON devices(device_id);
CREATE INDEX idx_devices_last_seen ON devices(last_seen);

-- Sessions Table
-- Stores active user sessions (can also use Redis, but keeping SQL for consistency)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for sessions
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- Cloud Patterns Table (for Phase 5)
-- Stores user patterns synced to cloud
CREATE TABLE cloud_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    pattern_data JSONB NOT NULL,
    file_size BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for cloud patterns
CREATE INDEX idx_cloud_patterns_user_id ON cloud_patterns(user_id);
CREATE INDEX idx_cloud_patterns_created_at ON cloud_patterns(created_at);

-- Presets Table (for Phase 5)
-- Stores curated and user-contributed presets
CREATE TABLE presets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- NULL for curated presets
    name VARCHAR(255) NOT NULL,
    description TEXT,
    preset_data JSONB NOT NULL,
    category VARCHAR(100),
    is_curated BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT FALSE,
    download_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for presets
CREATE INDEX idx_presets_user_id ON presets(user_id);
CREATE INDEX idx_presets_category ON presets(category);
CREATE INDEX idx_presets_is_curated ON presets(is_curated);
CREATE INDEX idx_presets_is_public ON presets(is_public);

-- Token Revocation List (for Phase 6)
-- Stores revoked tokens to prevent reuse
CREATE TABLE revoked_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    revoked_at TIMESTAMP DEFAULT NOW(),
    reason VARCHAR(255)
);

-- Create index for revoked tokens
CREATE INDEX idx_revoked_tokens_token_hash ON revoked_tokens(token_hash);
CREATE INDEX idx_revoked_tokens_user_id ON revoked_tokens(user_id);

-- Integrity Heartbeat Table (for Phase 6)
-- Stores integrity check data for anomaly detection
CREATE TABLE integrity_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    state_hash VARCHAR(255) NOT NULL,
    signature VARCHAR(255),
    is_suspicious BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for integrity checks
CREATE INDEX idx_integrity_checks_user_id ON integrity_checks(user_id);
CREATE INDEX idx_integrity_checks_device_id ON integrity_checks(device_id);
CREATE INDEX idx_integrity_checks_is_suspicious ON integrity_checks(is_suspicious);
CREATE INDEX idx_integrity_checks_created_at ON integrity_checks(created_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entitlements_updated_at BEFORE UPDATE ON entitlements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_devices_last_seen BEFORE UPDATE ON devices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cloud_patterns_updated_at BEFORE UPDATE ON cloud_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_presets_updated_at BEFORE UPDATE ON presets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Cleanup function for expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM sessions WHERE expires_at < NOW();
END;
$$ language 'plpgsql';

-- View for active entitlements
CREATE OR REPLACE VIEW active_entitlements AS
SELECT 
    e.*,
    u.email,
    u.auth0_id,
    COUNT(d.id) as active_devices
FROM entitlements e
JOIN users u ON e.user_id = u.id
LEFT JOIN devices d ON e.id = d.entitlement_id
WHERE e.status = 'active'
    AND (e.expires_at IS NULL OR e.expires_at > NOW())
GROUP BY e.id, u.email, u.auth0_id;
