/**
 * Magic Link Request Endpoint
 * POST /api/v2/auth/magic-link
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';
import { createMagicLink } from '../../../lib/database-kv';
import { sendMagicLink } from '../../../lib/email';

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
}

