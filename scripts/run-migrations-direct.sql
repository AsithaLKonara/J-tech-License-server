-- Direct SQL Migration Script
-- This creates all tables directly in MySQL

USE upload_bridge;

-- Create migrations table first
CREATE TABLE IF NOT EXISTS migrations (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    migration VARCHAR(255) NOT NULL,
    batch INT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NULL,
    auth0_id VARCHAR(255) NULL UNIQUE,
    email_verified_at TIMESTAMP NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    remember_token VARCHAR(100) NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    INDEX idx_email (email),
    INDEX idx_auth0_id (auth0_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    plan_type ENUM('monthly', 'annual', 'lifetime') NOT NULL,
    stripe_subscription_id VARCHAR(255) NULL,
    stripe_customer_id VARCHAR(255) NULL,
    status ENUM('active', 'canceled', 'expired') DEFAULT 'active',
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Licenses table
CREATE TABLE IF NOT EXISTS licenses (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    subscription_id BIGINT UNSIGNED NULL,
    plan VARCHAR(255) NOT NULL,
    features JSON,
    status ENUM('active', 'expired', 'revoked') DEFAULT 'active',
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Devices table
CREATE TABLE IF NOT EXISTS devices (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    license_id BIGINT UNSIGNED NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    device_name VARCHAR(255) NOT NULL,
    last_seen_at TIMESTAMP NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    FOREIGN KEY (license_id) REFERENCES licenses(id) ON DELETE CASCADE,
    INDEX idx_license_id (license_id),
    INDEX idx_device_id (device_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    subscription_id BIGINT UNSIGNED NULL,
    stripe_payment_intent_id VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Magic Links table
CREATE TABLE IF NOT EXISTS magic_links (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    INDEX idx_token (token),
    INDEX idx_email (email),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Entitlements table
CREATE TABLE IF NOT EXISTS entitlements (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    product_id VARCHAR(255) DEFAULT 'upload-bridge',
    plan ENUM('trial', 'monthly', 'yearly', 'perpetual') DEFAULT 'trial',
    status ENUM('active', 'inactive', 'cancelled', 'expired') DEFAULT 'active',
    features JSON DEFAULT ('[]'),
    max_devices INT DEFAULT 1,
    stripe_customer_id VARCHAR(255) NULL,
    stripe_subscription_id VARCHAR(255) NULL,
    stripe_price_id VARCHAR(255) NULL,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- API Sessions table
CREATE TABLE IF NOT EXISTS api_sessions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token_hash (token_hash),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Revoked Tokens table
CREATE TABLE IF NOT EXISTS revoked_tokens (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    reason TEXT NULL,
    revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token_hash (token_hash),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Update devices table (add entitlement_id and user_id if they don't exist)
SET @col_exists = (SELECT COUNT(*) FROM information_schema.columns 
                   WHERE table_schema = 'upload_bridge' AND table_name = 'devices' AND column_name = 'entitlement_id');
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE devices ADD COLUMN entitlement_id VARCHAR(255) NULL;', 
    'SELECT 1;');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists = (SELECT COUNT(*) FROM information_schema.columns 
                   WHERE table_schema = 'upload_bridge' AND table_name = 'devices' AND column_name = 'user_id');
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE devices ADD COLUMN user_id VARCHAR(255) NULL;', 
    'SELECT 1;');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add foreign keys if they don't exist
SET @fk_exists = (SELECT COUNT(*) FROM information_schema.table_constraints 
                  WHERE table_schema = 'upload_bridge' AND table_name = 'devices' AND constraint_name = 'devices_entitlement_id_foreign');
SET @sql = IF(@fk_exists = 0, 
    'ALTER TABLE devices ADD CONSTRAINT devices_entitlement_id_foreign FOREIGN KEY (entitlement_id) REFERENCES entitlements(id) ON DELETE CASCADE;', 
    'SELECT 1;');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @fk_exists = (SELECT COUNT(*) FROM information_schema.table_constraints 
                  WHERE table_schema = 'upload_bridge' AND table_name = 'devices' AND constraint_name = 'devices_user_id_foreign');
SET @sql = IF(@fk_exists = 0, 
    'ALTER TABLE devices ADD CONSTRAINT devices_user_id_foreign FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;', 
    'SELECT 1;');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add unique index if it doesn't exist
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.statistics 
                  WHERE table_schema = 'upload_bridge' AND table_name = 'devices' AND index_name = 'devices_user_device_unique');
SET @sql = IF(@idx_exists = 0, 
    'ALTER TABLE devices ADD UNIQUE INDEX devices_user_device_unique (user_id, device_id);', 
    'SELECT 1;');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Insert migration records
INSERT IGNORE INTO migrations (migration, batch) VALUES
('2024_01_01_000001_create_users_table', 1),
('2024_01_01_000002_create_subscriptions_table', 1),
('2024_01_01_000003_create_licenses_table', 1),
('2024_01_01_000004_create_devices_table', 1),
('2024_01_01_000005_create_payments_table', 1),
('2024_01_01_000006_create_magic_links_table', 1),
('2024_01_01_000007_create_entitlements_table', 1),
('2024_01_01_000008_create_sessions_table', 1),
('2024_01_01_000009_create_revoked_tokens_table', 1),
('2024_01_01_000010_update_devices_table', 1);

SELECT 'Migrations completed successfully!' as status;
