/**
 * Database Interface
 * Provides database operations for users, licenses, and devices
 * 
 * TODO: Replace in-memory implementation with real database (PostgreSQL/SQLite)
 */

import { User, License, Device } from './models';

// In-memory database (for development/testing)
// TODO: Replace with real database connection
const users: Map<string, User> = new Map();
const licenses: Map<string, License> = new Map();
const devices: Map<string, Device> = new Map();
const userLicenses: Map<string, string> = new Map(); // user_id -> license_id

/**
 * Get user by Auth0 subject (sub)
 */
export async function getUserByAuth0Sub(auth0Sub: string): Promise<User | null> {
  // TODO: Replace with real database query
  for (const user of users.values()) {
    if (user.auth0_sub === auth0Sub) {
      return user;
    }
  }
  return null;
}

/**
 * Get or create user by Auth0 subject
 */
export async function getOrCreateUserByAuth0Sub(
  auth0Sub: string,
  email: string
): Promise<User> {
  // Check if user exists
  let user = await getUserByAuth0Sub(auth0Sub);
  
  if (!user) {
    // Create new user
    user = {
      id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      email,
      auth0_sub: auth0Sub,
      created_at: new Date(),
    };
    users.set(user.id, user);
  } else {
    // Update email if changed
    if (user.email !== email) {
      user.email = email;
      users.set(user.id, user);
    }
  }
  
  return user;
}

/**
 * Get user's license
 */
export async function getUserLicense(userId: string): Promise<License | null> {
  // TODO: Replace with real database query
  const licenseId = userLicenses.get(userId);
  if (!licenseId) {
    return null;
  }
  
  return licenses.get(licenseId) || null;
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
  // TODO: Replace with real database query
  const existingLicenseId = userLicenses.get(userId);
  
  let license: License;
  if (existingLicenseId && licenses.has(existingLicenseId)) {
    // Update existing license
    license = licenses.get(existingLicenseId)!;
    license.plan = plan;
    license.features = features;
    license.expires_at = expiresAt;
    license.updated_at = new Date();
    licenses.set(license.id, license);
  } else {
    // Create new license
    license = {
      id: `license_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      user_id: userId,
      plan,
      features,
      expires_at: expiresAt,
      status: 'active',
      created_at: new Date(),
      updated_at: new Date(),
    };
    licenses.set(license.id, license);
    userLicenses.set(userId, license.id);
  }
  
  return license;
}

/**
 * Register device for license
 */
export async function registerDevice(
  licenseId: string,
  deviceId: string,
  deviceName: string
): Promise<Device> {
  // TODO: Replace with real database query
  const deviceKey = `${licenseId}_${deviceId}`;
  
  let device = devices.get(deviceKey);
  if (!device) {
    device = {
      id: `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      license_id: licenseId,
      device_id: deviceId,
      device_name: deviceName,
      registered_at: new Date(),
      last_seen_at: new Date(),
    };
    devices.set(deviceKey, device);
  } else {
    // Update last seen
    device.last_seen_at = new Date();
    device.device_name = deviceName;
    devices.set(deviceKey, device);
  }
  
  return device;
}

/**
 * Get device by license and device ID
 */
export async function getDevice(
  licenseId: string,
  deviceId: string
): Promise<Device | null> {
  // TODO: Replace with real database query
  const deviceKey = `${licenseId}_${deviceId}`;
  return devices.get(deviceKey) || null;
}

/**
 * Check if license is valid (not expired, not revoked)
 */
export async function isLicenseValid(licenseId: string): Promise<boolean> {
  // TODO: Replace with real database query
  const license = licenses.get(licenseId);
  if (!license) {
    return false;
  }
  
  if (license.status !== 'active') {
    return false;
  }
  
  if (license.expires_at && license.expires_at < new Date()) {
    return false;
  }
  
  return true;
}

/**
 * Initialize database (for development - seed test data)
 */
export async function initializeDatabase(): Promise<void> {
  // TODO: Replace with real database initialization
  // For now, this is a no-op for in-memory database
  console.log('Database initialized (in-memory mode)');
}

