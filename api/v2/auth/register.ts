/**
 * User Registration Endpoint
 * POST /api/v2/auth/register
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';
import { createUser } from '../../../lib/database-kv';
import { signToken } from '../../../lib/jwt-validator';

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
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    // Check if user already exists
    const { getUserByEmail } = await import('../../../lib/database-kv');
    const existingUser = await getUserByEmail(email);
    if (existingUser) {
      return res.status(400).json({ error: 'User already exists' });
    }

    // Create user
    const user = await createUser(email, password);

    // Generate session token
    const sessionToken = signToken({
      user_id: user.id,
      device_id: 'unknown',
      created_at: Date.now(),
    }, '7d');

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
}

