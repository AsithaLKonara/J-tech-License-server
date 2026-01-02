/**
 * Get User Subscription Endpoint
 * GET /api/v2/subscriptions
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';
import { getUserSubscription } from '../../../lib/database-kv';
import { verifyToken } from '../../../lib/jwt-validator';

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
    const { session_token } = req.query;

    if (!session_token || typeof session_token !== 'string') {
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
}

