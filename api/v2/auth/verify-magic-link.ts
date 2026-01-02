/**
 * Magic Link Verification Endpoint
 * GET /api/v2/auth/verify-magic-link
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';
import crypto from 'crypto';
import {
  verifyMagicLink,
  getUserByEmail,
  createUser,
  getUserLicense,
  upsertUserLicense,
  isLicenseValid,
} from '../../../lib/database-kv';
import { signToken } from '../../../lib/jwt-validator';
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
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { token } = req.query;

    if (!token || typeof token !== 'string') {
      return res.status(400).json({ error: 'Token is required' });
    }

    // Verify magic link
    const result = await verifyMagicLink(token);
    if (!result) {
      return res.status(400).json({ error: 'Invalid or expired token' });
    }

    // Get or create user
    let user = await getUserByEmail(result.email);
    if (!user) {
      // Create user without password for magic link
      user = await createUser(result.email, crypto.randomBytes(32).toString('hex'));
    }

    // Get user's license
    let license = await getUserLicense(user.id);

    // If no license exists, create a default free one
    if (!license) {
      license = await upsertUserLicense(
        user.id,
        'free',
        ['pattern_upload'],
        null
      );
    }

    // Check if license is valid
    const isValidLicense = await isLicenseValid(license.id);
    if (!isValidLicense) {
      return res.status(403).json({ error: 'License is not valid' });
    }

    // Generate session token
    const sessionToken = signToken({
      user_id: user.id,
      device_id: 'unknown',
      created_at: Date.now(),
    }, '7d');

    // Create entitlement token
    const entitlementToken = licenseToEntitlementToken(user.id, license);

    // Return tokens (can also redirect to app with tokens)
    return res.status(200).json({
      session_token: sessionToken,
      entitlement_token: entitlementToken,
      user: {
        id: user.id,
        email: user.email,
      },
    });
  } catch (error: any) {
    console.error('Magic link verification error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

