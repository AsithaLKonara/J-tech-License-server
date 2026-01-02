/**
 * Express Server for Upload Bridge License Server
 * Email-based authentication with subscriptions
 */

import express, { Request, Response } from 'express';
import crypto from 'crypto';
import {
  createUser,
  getUserByEmail,
  getUserById,
  verifyPassword,
  createMagicLink,
  verifyMagicLink,
  createSubscription,
  getUserSubscription,
  createLicenseFromSubscription,
  getUserLicense,
  upsertUserLicense,
  registerDevice,
  isLicenseValid,
} from './lib/database';
import { sendMagicLink } from './lib/email';
import { getPlanFeatures, calculateExpiry } from './lib/subscriptions';
import { signToken } from './lib/jwt-validator';
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
  return signToken(payload, '7d');
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

// Register endpoint
app.post('/api/v2/auth/register', async (req: Request, res: Response) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    // Check if user already exists
    const existingUser = await getUserByEmail(email);
    if (existingUser) {
      return res.status(400).json({ error: 'User already exists' });
    }

    // Create user
    const user = await createUser(email, password);

    // Generate session token
    const sessionToken = generateSessionToken(user.id, 'unknown');

    return res.status(200).json({
      session_token: sessionToken,
      user: {
        id: user.id,
        email: user.email,
      },
    });
  } catch (error: any) {
    console.error('Registration error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

// Login endpoint
app.post('/api/v2/auth/login', async (req: Request, res: Response) => {
  try {
    const { email, password, device_id, device_name } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    // Get user
    const user = await getUserByEmail(email);
    if (!user) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    // Verify password
    const isValid = await verifyPassword(user, password);
    if (!isValid) {
      return res.status(401).json({ error: 'Invalid email or password' });
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

// Magic link request endpoint
app.post('/api/v2/auth/magic-link', async (req: Request, res: Response) => {
  try {
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({ error: 'Email is required' });
    }

    // Create magic link token
    const token = await createMagicLink(email);

    // Send email
    try {
      await sendMagicLink(email, token);
    } catch (error: any) {
      console.error('Email sending error:', error);
      return res.status(500).json({ error: 'Failed to send email' });
    }

    return res.status(200).json({
      message: 'Magic link sent to your email',
    });
  } catch (error: any) {
    console.error('Magic link error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

// Magic link verification endpoint
app.get('/api/v2/auth/verify-magic-link', async (req: Request, res: Response) => {
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
    const sessionToken = generateSessionToken(user.id, 'unknown');

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
      const { verifyToken } = await import('./lib/jwt-validator');
      const payload = verifyToken(session_token) as any;
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

// Create subscription endpoint
app.post('/api/v2/subscriptions/create', async (req: Request, res: Response) => {
  try {
    const { session_token, plan_type } = req.body;

    if (!session_token || !plan_type) {
      return res.status(400).json({ error: 'Session token and plan type are required' });
    }

    // Verify session token
    const { verifyToken } = await import('./lib/jwt-validator');
    let payload: any;
    try {
      payload = verifyToken(session_token);
    } catch (error: any) {
      return res.status(401).json({ error: 'Invalid session token' });
    }

    const userId = payload.user_id;

    // Validate plan type
    if (!['monthly', 'annual', 'lifetime'].includes(plan_type)) {
      return res.status(400).json({ error: 'Invalid plan type. Must be monthly, annual, or lifetime' });
    }

    // Calculate expiry
    const expiresAt = calculateExpiry(plan_type);

    // Create subscription
    const subscription = await createSubscription(userId, plan_type, expiresAt);

    // Get plan features
    const features = getPlanFeatures(plan_type);

    // Create license from subscription
    const license = await createLicenseFromSubscription(subscription, plan_type, features);

    return res.status(200).json({
      subscription: {
        id: subscription.id,
        plan_type: subscription.plan_type,
        status: subscription.status,
        expires_at: subscription.expires_at,
      },
      license: {
        id: license.id,
        plan: license.plan,
        features: license.features,
        expires_at: license.expires_at,
      },
    });
  } catch (error: any) {
    console.error('Subscription creation error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

// Get user's subscription endpoint
app.get('/api/v2/subscriptions', async (req: Request, res: Response) => {
  try {
    const { session_token } = req.query;

    if (!session_token || typeof session_token !== 'string') {
      return res.status(400).json({ error: 'Session token is required' });
    }

    // Verify session token
    const { verifyToken } = await import('./lib/jwt-validator');
    let payload: any;
    try {
      payload = verifyToken(session_token);
    } catch (error: any) {
      return res.status(401).json({ error: 'Invalid session token' });
    }

    const userId = payload.user_id;

    // Get subscription
    const subscription = await getUserSubscription(userId);

    if (!subscription) {
      return res.status(404).json({ error: 'No active subscription found' });
    }

    return res.status(200).json({
      subscription: {
        id: subscription.id,
        plan_type: subscription.plan_type,
        status: subscription.status,
        expires_at: subscription.expires_at,
        created_at: subscription.created_at,
      },
    });
  } catch (error: any) {
    console.error('Get subscription error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 License Server running on port ${PORT}`);
  console.log(`📍 Health: http://localhost:${PORT}/api/health`);
  console.log(`🔐 Login: http://localhost:${PORT}/api/v2/auth/login`);
});
