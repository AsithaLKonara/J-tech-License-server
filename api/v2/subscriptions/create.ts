/**
 * Create Subscription Endpoint
 * POST /api/v2/subscriptions/create
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';
import {
  createSubscription,
  createLicenseFromSubscription,
} from '../../../lib/database-kv';
import { getPlanFeatures, calculateExpiry } from '../../../lib/subscriptions';
import { verifyToken } from '../../../lib/jwt-validator';

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
    const { session_token, plan_type } = req.body;

    if (!session_token || !plan_type) {
      return res.status(400).json({ error: 'Session token and plan type are required' });
    }

    // Verify session token
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
}

