/**
 * Express Server for Upload Bridge License Server
 * Railway-compatible deployment
 */

import express, { Request, Response } from 'express';
import { verifyAuth0Token, extractUserInfo } from './lib/jwt-validator';
import {
  getOrCreateUserByAuth0Sub,
  getUserLicense,
  upsertUserLicense,
  registerDevice,
  isLicenseValid,
} from './lib/database';
import { EntitlementToken } from './lib/models';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());

// CORS middleware
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  next();
});

/**
 * Generate session token
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

// Health endpoint
app.get('/api/health', (req: Request, res: Response) => {
  res.status(200).json({
    status: 'ok',
    service: 'upload-bridge-license-server',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
  });
});

// Login endpoint
app.post('/api/v2/auth/login', async (req: Request, res: Response) => {
  try {
    const { auth0_token, device_id, device_name } = req.body;

    if (!auth0_token) {
      return res.status(400).json({ error: 'Auth0 token is required' });
    }

    // Verify Auth0 token
    let decoded;
    try {
      decoded = await verifyAuth0Token(auth0_token);
    } catch (error: any) {
      console.error('Token validation error:', error);
      return res.status(401).json({ error: `Invalid token: ${error.message}` });
    }

    // Extract user information
    let userInfo;
    try {
      userInfo = extractUserInfo(decoded);
    } catch (error: any) {
      return res.status(400).json({ error: error.message });
    }

    // Get or create user in database
    let user;
    try {
      user = await getOrCreateUserByAuth0Sub(userInfo.sub, userInfo.email);
    } catch (error: any) {
      console.error('Database error:', error);
      return res.status(500).json({ error: 'Database error' });
    }

    // Get user's license
    let license = await getUserLicense(user.id);

    // If no license exists, create a default one
    if (!license) {
      try {
        license = await upsertUserLicense(
          user.id,
          'pro', // Default plan
          ['pattern_upload', 'wifi_upload', 'advanced_controls'], // Default features
          null // Perpetual (no expiry)
        );
      } catch (error: any) {
        console.error('License creation error:', error);
        return res.status(500).json({ error: 'Failed to create license' });
      }
    }

    // Check if license is valid
    const isValid = await isLicenseValid(license.id);
    if (!isValid) {
      return res.status(403).json({ error: 'License is not valid (expired or revoked)' });
    }

    // Register device if device_id provided
    if (device_id) {
      try {
        await registerDevice(license.id, device_id, device_name || 'Unknown Device');
      } catch (error: any) {
        console.error('Device registration error:', error);
        // Don't fail login if device registration fails
      }
    }

    // Generate session token
    const sessionToken = generateSessionToken(user.id, device_id || 'unknown');

    // Create entitlement token
    const entitlementToken = licenseToEntitlementToken(user.id, license);

    // Return success response
    return res.status(200).json({
      session_token: sessionToken,
      entitlement_token: entitlementToken,
      user: {
        id: user.id,
        email: user.email,
      },
    });
  } catch (error: any) {
    console.error('Login error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

// Refresh endpoint
app.post('/api/v2/auth/refresh', async (req: Request, res: Response) => {
  try {
    const { session_token, device_id } = req.body;

    if (!session_token) {
      return res.status(400).json({ error: 'Session token is required' });
    }

    // Decode session token to get user ID
    try {
      const payload = JSON.parse(
        Buffer.from(session_token.replace('session_', ''), 'base64url').toString()
      );
      const userId = payload.user_id;

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
      const newSessionToken = generateSessionToken(userId, device_id || payload.device_id || 'unknown');

      // Create entitlement token
      const entitlementToken = licenseToEntitlementToken(userId, license);

      return res.status(200).json({
        session_token: newSessionToken,
        entitlement_token: entitlementToken,
      });
    } catch (error: any) {
      return res.status(401).json({ error: 'Invalid session token' });
    }
  } catch (error: any) {
    console.error('Refresh error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 License Server running on port ${PORT}`);
  console.log(`📍 Health: http://localhost:${PORT}/api/health`);
  console.log(`🔐 Login: http://localhost:${PORT}/api/v2/auth/login`);
});

