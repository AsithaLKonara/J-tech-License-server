import type { VercelRequest, VercelResponse } from '@vercel/node';

interface RefreshRequest {
  session_token: string;
  device_id: string;
}

interface RefreshResponse {
  session_token: string;
  entitlement_token: {
    sub: string;
    product: string;
    plan: string;
    features: string[];
    expires_at: number | null;
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

    // In production, validate the session token and get user info from database
    // For now, extract email from token (simple base64 decode)
    try {
      const tokenData = Buffer.from(body.session_token.replace('session_', ''), 'base64url').toString();
      const email = tokenData.split(':')[0];

      // Generate new session token
      const newSessionToken = `session_${Buffer.from(`${email}:${body.device_id}:${Date.now()}`).toString('base64url')}`;

      // Return refreshed token (in production, get from database)
      const response: RefreshResponse = {
        session_token: newSessionToken,
        entitlement_token: {
          sub: `user_${email.toLowerCase().replace(/[^a-z0-9]/g, '_')}`,
          product: 'upload_bridge_pro',
          plan: 'pro',
          features: ['pattern_upload', 'wifi_upload', 'advanced_controls'],
          expires_at: null
        }
      };

      return res.status(200).json(response);
    } catch (error) {
      return res.status(401).json({ error: 'Invalid session token' });
    }

  } catch (error) {
    console.error('Refresh error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
