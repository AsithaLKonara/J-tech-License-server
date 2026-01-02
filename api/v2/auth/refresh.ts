import type { VercelRequest, VercelResponse } from '@vercel/node';
import {
  getUserLicense,
  isLicenseValid,
  getDevice,
} from '../../lib/database';
import { EntitlementToken } from '../../lib/models';

interface RefreshRequest {
  session_token: string;
  device_id: string;
}

interface RefreshResponse {
  session_token: string;
  entitlement_token: EntitlementToken;
}

/**
 * Parse session token to extract user ID
 * TODO: Use proper JWT for session tokens
 */
function parseSessionToken(sessionToken: string): { userId: string; deviceId: string } | null {
  try {
    const payload = Buffer.from(sessionToken.replace('session_', ''), 'base64url').toString('utf-8');
    const data = JSON.parse(payload);
    return {
      userId: data.user_id,
      deviceId: data.device_id,
    };
  } catch (error) {
    return null;
  }
}

/**
 * Generate new session token
 */
function generateSessionToken(userId: string, deviceId: string): string {
  const payload = {
    user_id: userId,
    device_id: deviceId,
    created_at: Date.now(),
  };
  return `session_${Buffer.from(JSON.stringify(payload)).toString('base64url')}`;
}

/**
 * Convert license to entitlement token
 */
function licenseToEntitlementToken(
  userId: string,
  license: { plan: string; features: string[]; expires_at: Date | null }
): EntitlementToken {
  return {
    sub: userId,
    product: 'upload_bridge_pro',
    plan: license.plan,
    features: license.features,
    expires_at: license.expires_at ? Math.floor(license.expires_at.getTime() / 1000) : null,
    issued_at: Math.floor(Date.now() / 1000),
  };
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse
): Promise<VercelResponse> {
  // Add CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const body: RefreshRequest = req.body;

    if (!body.session_token || !body.device_id) {
      return res.status(400).json({ error: 'Session token and device ID are required' });
    }

    // Parse session token to get user ID
    const sessionData = parseSessionToken(body.session_token);
    if (!sessionData) {
      return res.status(401).json({ error: 'Invalid session token' });
    }

    // Verify device ID matches
    if (sessionData.deviceId !== body.device_id) {
      return res.status(403).json({ error: 'Device ID mismatch' });
    }

    // Get user's license
    const license = await getUserLicense(sessionData.userId);
    if (!license) {
      return res.status(404).json({ error: 'No license found for user' });
    }

    // Check if license is valid
    const isValid = await isLicenseValid(license.id);
    if (!isValid) {
      return res.status(403).json({ error: 'License is not valid (expired or revoked)' });
    }

    // Verify device is registered (optional check)
    const device = await getDevice(license.id, body.device_id);
    if (!device) {
      // Device not registered - this might be okay for refresh, but log it
      console.warn(`Device ${body.device_id} not registered for license ${license.id}`);
    }

    // Generate new session token
    const newSessionToken = generateSessionToken(sessionData.userId, body.device_id);

    // Create entitlement token from current license
    const entitlementToken = licenseToEntitlementToken(sessionData.userId, license);

    const response: RefreshResponse = {
      session_token: newSessionToken,
      entitlement_token: entitlementToken,
    };

    return res.status(200).json(response);

  } catch (error: any) {
    console.error('Refresh error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
