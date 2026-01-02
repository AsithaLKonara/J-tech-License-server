/**
 * Token Refresh Endpoint
 * POST /api/v2/auth/refresh
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';
import { getUserById, getUserLicense, isLicenseValid } from '../../../lib/database-kv';
import { signToken, verifyToken } from '../../../lib/jwt-validator';
import { EntitlementToken } from '../../../lib/models';

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
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { session_token, device_id } = req.body;

    if (!session_token) {
      return res.status(400).json({ error: 'Session token is required' });
    }

    // Verify session token
    let payload: any;
    try {
      payload = verifyToken(session_token);
    } catch (error: any) {
      return res.status(401).json({ error: 'Invalid session token' });
    }

    const userId = payload.user_id;

    // Get user
    const user = await getUserById(userId);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Get user's license
    const license = await getUserLicense(userId);
    if (!license) {
      return res.status(404).json({ error: 'License not found' });
    }

    // Check if license is valid
    const isValid = await isLicenseValid(license.id);
    if (!isValid) {
      return res.status(403).json({ error: 'License is not valid' });
    }

    // Generate new session token
    const newSessionToken = signToken({
      user_id: userId,
      device_id: device_id || payload.device_id || 'unknown',
      created_at: Date.now(),
    }, '7d');

    // Create entitlement token
    const entitlementToken = licenseToEntitlementToken(userId, license);

    return res.status(200).json({
      session_token: newSessionToken,
      entitlement_token: entitlementToken,
    });
  } catch (error: any) {
    console.error('Refresh error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
