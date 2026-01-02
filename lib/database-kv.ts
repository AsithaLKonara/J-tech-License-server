/**
 * Database Interface - Vercel KV (Redis) Implementation
 * Provides database operations for users, licenses, devices, and subscriptions
 * Compatible with Vercel serverless functions
 */

import { kv } from '@vercel/kv';
import { User, License, Device, Subscription } from './models';
import bcrypt from 'bcrypt';
import crypto from 'crypto';

/**
 * Create a new user with email and password
 */
export async function createUser(email: string, password: string): Promise<User> {
  const passwordHash = await bcrypt.hash(password, 10);
  const id = `user_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
  const now = Date.now();

  const user: User = {
    id,
    email,
    password_hash: passwordHash,
    email_verified: false,
    created_at: new Date(now),
    updated_at: new Date(now),
  };

  // Store user by ID
  await kv.set(`user:${id}`, JSON.stringify(user));
  // Store user by email for lookup
  await kv.set(`user:email:${email}`, id);

  return user;
}

/**
 * Get user by email
 */
export async function getUserByEmail(email: string): Promise<User | null> {
  const userId = await kv.get<string>(`user:email:${email}`);
  if (!userId) return null;

  const userData = await kv.get<string>(`user:${userId}`);
  if (!userData) return null;

  const user = JSON.parse(userData);
  return {
    ...user,
    created_at: new Date(user.created_at),
    updated_at: new Date(user.updated_at),
  };
}

/**
 * Get user by ID
 */
export async function getUserById(id: string): Promise<User | null> {
  const userData = await kv.get<string>(`user:${id}`);
  if (!userData) return null;

  const user = JSON.parse(userData);
  return {
    ...user,
    created_at: new Date(user.created_at),
    updated_at: new Date(user.updated_at),
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

  await kv.set(`magic_link:${token}`, JSON.stringify({
    email,
    expires_at: expiresAt,
    used: false,
  }), { ex: 900 }); // 15 minutes TTL

  return token;
}

/**
 * Verify magic link token
 */
export async function verifyMagicLink(token: string): Promise<{ email: string } | null> {
  const data = await kv.get<string>(`magic_link:${token}`);
  if (!data) return null;

  const link = JSON.parse(data);
  if (link.used) return null;
  if (link.expires_at < Date.now()) return null;

  // Mark as used
  link.used = true;
  await kv.set(`magic_link:${token}`, JSON.stringify(link));

  return { email: link.email };
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

  const subscription: Subscription = {
    id,
    user_id: userId,
    plan_type: planType,
    status: 'active',
    expires_at: expiresAt,
    created_at: now,
  };

  // Store subscription
  await kv.set(`subscription:${id}`, JSON.stringify(subscription));
  // Store user's active subscription
  await kv.set(`user:${userId}:subscription`, id);

  return subscription;
}

/**
 * Get user's active subscription
 */
export async function getUserSubscription(userId: string): Promise<Subscription | null> {
  const subId = await kv.get<string>(`user:${userId}:subscription`);
  if (!subId) return null;

  const subData = await kv.get<string>(`subscription:${subId}`);
  if (!subData) return null;

  return JSON.parse(subData);
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

  const license: License = {
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

  // Store license
  await kv.set(`license:${id}`, JSON.stringify(license));
  // Store user's license
  await kv.set(`user:${subscription.user_id}:license`, id);

  return license;
}

/**
 * Get user's license
 */
export async function getUserLicense(userId: string): Promise<License | null> {
  const licenseId = await kv.get<string>(`user:${userId}:license`);
  if (!licenseId) return null;

  const licenseData = await kv.get<string>(`license:${licenseId}`);
  if (!licenseData) return null;

  const license = JSON.parse(licenseData);
  return {
    ...license,
    expires_at: license.expires_at ? new Date(license.expires_at) : null,
    created_at: new Date(license.created_at),
    updated_at: new Date(license.updated_at),
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
    const updated: License = {
      ...existing,
      plan,
      features,
      expires_at: expiresAt,
      updated_at: new Date(now),
    };

    await kv.set(`license:${existing.id}`, JSON.stringify(updated));
    return updated;
  } else {
    // Create new license
    const id = `license_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
    const license: License = {
      id,
      user_id: userId,
      plan,
      features,
      expires_at: expiresAt,
      status: 'active',
      created_at: new Date(now),
      updated_at: new Date(now),
    };

    await kv.set(`license:${id}`, JSON.stringify(license));
    await kv.set(`user:${userId}:license`, id);

    return license;
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
  const deviceKey = `device:${licenseId}:${deviceId}`;
  const existingData = await kv.get<string>(deviceKey);

  const now = Date.now();

  if (existingData) {
    // Update existing device
    const device = JSON.parse(existingData);
    device.device_name = deviceName;
    device.last_seen_at = now;

    await kv.set(deviceKey, JSON.stringify(device));
    return {
      ...device,
      registered_at: new Date(device.registered_at),
      last_seen_at: new Date(now),
    };
  } else {
    // Create new device
    const id = `device_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
    const device: Device = {
      id,
      license_id: licenseId,
      device_id: deviceId,
      device_name: deviceName,
      registered_at: new Date(now),
      last_seen_at: new Date(now),
    };

    await kv.set(deviceKey, JSON.stringify(device));
    return device;
  }
}

/**
 * Get device by license and device ID
 */
export async function getDevice(
  licenseId: string,
  deviceId: string
): Promise<Device | null> {
  const deviceKey = `device:${licenseId}:${deviceId}`;
  const deviceData = await kv.get<string>(deviceKey);
  if (!deviceData) return null;

  const device = JSON.parse(deviceData);
  return {
    ...device,
    registered_at: new Date(device.registered_at),
    last_seen_at: new Date(device.last_seen_at),
  };
}

/**
 * Check if license is valid (not expired, not revoked)
 */
export async function isLicenseValid(licenseId: string): Promise<boolean> {
  const licenseData = await kv.get<string>(`license:${licenseId}`);
  if (!licenseData) return false;

  const license = JSON.parse(licenseData);
  if (license.status !== 'active') return false;

  if (license.expires_at && new Date(license.expires_at).getTime() < Date.now()) {
    // Mark as expired
    license.status = 'expired';
    await kv.set(`license:${licenseId}`, JSON.stringify(license));
    return false;
  }

  return true;
}

/**
 * Initialize database (for development - seed test data)
 */
export async function initializeDatabase(): Promise<void> {
  console.log('Database initialized (Vercel KV)');
}

