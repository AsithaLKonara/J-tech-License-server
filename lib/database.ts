/**
 * Database Interface - SQLite Implementation
 * Provides database operations for users, licenses, devices, and subscriptions
 */

import Database from 'better-sqlite3';
import { User, License, Device, Subscription } from './models';
import bcrypt from 'bcrypt';
import crypto from 'crypto';

const dbPath = process.env.DB_PATH || 'license.db';
const db = new Database(dbPath);

// Initialize tables
db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    email_verified INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
  );

  CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan_type TEXT NOT NULL,
    status TEXT NOT NULL,
    expires_at INTEGER,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
  );

  CREATE TABLE IF NOT EXISTS licenses (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    subscription_id TEXT,
    plan TEXT NOT NULL,
    features TEXT NOT NULL,
    expires_at INTEGER,
    status TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
  );

  CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    license_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    device_name TEXT,
    registered_at INTEGER NOT NULL,
    last_seen_at INTEGER NOT NULL,
    FOREIGN KEY (license_id) REFERENCES licenses(id),
    UNIQUE(license_id, device_id)
  );

  CREATE TABLE IF NOT EXISTS magic_links (
    token TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    used INTEGER DEFAULT 0
  );

  CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
  CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
  CREATE INDEX IF NOT EXISTS idx_licenses_user ON licenses(user_id);
`);

/**
 * Create a new user with email and password
 */
export async function createUser(email: string, password: string): Promise<User> {
  const passwordHash = await bcrypt.hash(password, 10);
  const id = `user_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
  const now = Date.now();

  db.prepare(`
    INSERT INTO users (id, email, password_hash, email_verified, created_at, updated_at)
    VALUES (?, ?, ?, 0, ?, ?)
  `).run(id, email, passwordHash, now, now);

  return {
    id,
    email,
    password_hash: passwordHash,
    email_verified: false,
    created_at: new Date(now),
    updated_at: new Date(now),
  };
}

/**
 * Get user by email
 */
export async function getUserByEmail(email: string): Promise<User | null> {
  const row = db.prepare('SELECT * FROM users WHERE email = ?').get(email) as any;
  if (!row) return null;

  return {
    id: row.id,
    email: row.email,
    password_hash: row.password_hash,
    email_verified: Boolean(row.email_verified),
    created_at: new Date(row.created_at),
    updated_at: new Date(row.updated_at),
  };
}

/**
 * Get user by ID
 */
export async function getUserById(id: string): Promise<User | null> {
  const row = db.prepare('SELECT * FROM users WHERE id = ?').get(id) as any;
  if (!row) return null;

  return {
    id: row.id,
    email: row.email,
    password_hash: row.password_hash,
    email_verified: Boolean(row.email_verified),
    created_at: new Date(row.created_at),
    updated_at: new Date(row.updated_at),
  };
}

/**
 * Verify password against hash
 */
export async function verifyPassword(user: User, password: string): Promise<boolean> {
  if (!user.password_hash) return false;
  return await bcrypt.compare(password, user.password_hash);
}

/**
 * Create magic link token
 */
export async function createMagicLink(email: string): Promise<string> {
  const token = crypto.randomBytes(32).toString('hex');
  const expiresAt = Date.now() + (15 * 60 * 1000); // 15 minutes

  db.prepare(`
    INSERT INTO magic_links (token, email, expires_at, used)
    VALUES (?, ?, ?, 0)
  `).run(token, email, expiresAt);

  return token;
}

/**
 * Verify magic link token
 */
export async function verifyMagicLink(token: string): Promise<{ email: string } | null> {
  const row = db.prepare(`
    SELECT email, expires_at, used FROM magic_links WHERE token = ?
  `).get(token) as any;

  if (!row) return null;
  if (row.used) return null;
  if (row.expires_at < Date.now()) return null;

  // Mark as used
  db.prepare('UPDATE magic_links SET used = 1 WHERE token = ?').run(token);

  return { email: row.email };
}

/**
 * Create subscription
 */
export async function createSubscription(
  userId: string,
  planType: 'monthly' | 'annual' | 'lifetime',
  expiresAt: number | null
): Promise<Subscription> {
  const id = `sub_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
  const now = Date.now();

  db.prepare(`
    INSERT INTO subscriptions (id, user_id, plan_type, status, expires_at, created_at)
    VALUES (?, ?, ?, 'active', ?, ?)
  `).run(id, userId, planType, expiresAt, now);

  return {
    id,
    user_id: userId,
    plan_type: planType,
    status: 'active',
    expires_at: expiresAt,
    created_at: now,
  };
}

/**
 * Get user's active subscription
 */
export async function getUserSubscription(userId: string): Promise<Subscription | null> {
  const row = db.prepare(`
    SELECT * FROM subscriptions 
    WHERE user_id = ? AND status = 'active'
    ORDER BY created_at DESC
    LIMIT 1
  `).get(userId) as any;

  if (!row) return null;

  return {
    id: row.id,
    user_id: row.user_id,
    plan_type: row.plan_type,
    status: row.status,
    expires_at: row.expires_at,
    created_at: row.created_at,
  };
}

/**
 * Create license from subscription
 */
export async function createLicenseFromSubscription(
  subscription: Subscription,
  plan: string,
  features: string[]
): Promise<License> {
  const id = `license_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
  const now = Date.now();
  const expiresAt = subscription.expires_at ? new Date(subscription.expires_at) : null;

  db.prepare(`
    INSERT INTO licenses (id, user_id, subscription_id, plan, features, expires_at, status, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
  `).run(
    id,
    subscription.user_id,
    subscription.id,
    plan,
    JSON.stringify(features),
    expiresAt ? expiresAt.getTime() : null,
    now,
    now
  );

  return {
    id,
    user_id: subscription.user_id,
    subscription_id: subscription.id,
    plan,
    features,
    expires_at: expiresAt,
    status: 'active',
    created_at: new Date(now),
    updated_at: new Date(now),
  };
}

/**
 * Get user's license
 */
export async function getUserLicense(userId: string): Promise<License | null> {
  const row = db.prepare(`
    SELECT * FROM licenses 
    WHERE user_id = ? AND status = 'active'
    ORDER BY created_at DESC
    LIMIT 1
  `).get(userId) as any;

  if (!row) return null;

  return {
    id: row.id,
    user_id: row.user_id,
    subscription_id: row.subscription_id,
    plan: row.plan,
    features: JSON.parse(row.features),
    expires_at: row.expires_at ? new Date(row.expires_at) : null,
    status: row.status,
    created_at: new Date(row.created_at),
    updated_at: new Date(row.updated_at),
  };
}

/**
 * Create or update user license
 */
export async function upsertUserLicense(
  userId: string,
  plan: string,
  features: string[],
  expiresAt: Date | null = null
): Promise<License> {
  const existing = await getUserLicense(userId);
  const now = Date.now();

  if (existing) {
    // Update existing license
    db.prepare(`
      UPDATE licenses 
      SET plan = ?, features = ?, expires_at = ?, updated_at = ?
      WHERE id = ?
    `).run(
      plan,
      JSON.stringify(features),
      expiresAt ? expiresAt.getTime() : null,
      now,
      existing.id
    );

    return {
      ...existing,
      plan,
      features,
      expires_at: expiresAt,
      updated_at: new Date(now),
    };
  } else {
    // Create new license
    const id = `license_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;

    db.prepare(`
      INSERT INTO licenses (id, user_id, plan, features, expires_at, status, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
    `).run(
      id,
      userId,
      plan,
      JSON.stringify(features),
      expiresAt ? expiresAt.getTime() : null,
      now,
      now
    );

    return {
      id,
      user_id: userId,
      plan,
      features,
      expires_at: expiresAt,
      status: 'active',
      created_at: new Date(now),
      updated_at: new Date(now),
    };
  }
}

/**
 * Register device for license
 */
export async function registerDevice(
  licenseId: string,
  deviceId: string,
  deviceName: string
): Promise<Device> {
  const deviceKey = `${licenseId}_${deviceId}`;
  const existing = db.prepare(`
    SELECT * FROM devices WHERE license_id = ? AND device_id = ?
  `).get(licenseId, deviceId) as any;

  const now = Date.now();

  if (existing) {
    // Update existing device
    db.prepare(`
      UPDATE devices 
      SET device_name = ?, last_seen_at = ?
      WHERE license_id = ? AND device_id = ?
    `).run(deviceName, now, licenseId, deviceId);

    return {
      id: existing.id,
      license_id: existing.license_id,
      device_id: existing.device_id,
      device_name: deviceName,
      registered_at: new Date(existing.registered_at),
      last_seen_at: new Date(now),
    };
  } else {
    // Create new device
    const id = `device_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;

    db.prepare(`
      INSERT INTO devices (id, license_id, device_id, device_name, registered_at, last_seen_at)
      VALUES (?, ?, ?, ?, ?, ?)
    `).run(id, licenseId, deviceId, deviceName, now, now);

    return {
      id,
      license_id: licenseId,
      device_id: deviceId,
      device_name: deviceName,
      registered_at: new Date(now),
      last_seen_at: new Date(now),
    };
  }
}

/**
 * Get device by license and device ID
 */
export async function getDevice(
  licenseId: string,
  deviceId: string
): Promise<Device | null> {
  const row = db.prepare(`
    SELECT * FROM devices WHERE license_id = ? AND device_id = ?
  `).get(licenseId, deviceId) as any;

  if (!row) return null;

  return {
    id: row.id,
    license_id: row.license_id,
    device_id: row.device_id,
    device_name: row.device_name,
    registered_at: new Date(row.registered_at),
    last_seen_at: new Date(row.last_seen_at),
  };
}

/**
 * Check if license is valid (not expired, not revoked)
 */
export async function isLicenseValid(licenseId: string): Promise<boolean> {
  const row = db.prepare('SELECT status, expires_at FROM licenses WHERE id = ?').get(licenseId) as any;
  if (!row) return false;

  if (row.status !== 'active') return false;

  if (row.expires_at && row.expires_at < Date.now()) {
    // Mark as expired
    db.prepare('UPDATE licenses SET status = ? WHERE id = ?').run('expired', licenseId);
    return false;
  }

  return true;
}

/**
 * Initialize database (for development - seed test data)
 */
export async function initializeDatabase(): Promise<void> {
  console.log('Database initialized (SQLite)');
}
