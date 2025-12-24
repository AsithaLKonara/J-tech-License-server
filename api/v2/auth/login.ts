import type { VercelRequest, VercelResponse } from '@vercel/node';

interface LoginRequest {
  email: string;
  password: string;
  device_id?: string;
  device_name?: string;
}

interface User {
  id: string;
  email: string;
}

interface EntitlementToken {
  sub: string;
  product: string;
  plan: string;
  features: string[];
  expires_at: number | null;
}

interface LoginResponse {
  session_token: string;
  entitlement_token: EntitlementToken;
  user: User;
}

// In-memory user database (replace with real database in production)
const USERS: Record<string, { password: string; plan: string }> = {
  'test@example.com': {
    password: 'testpassword123', // In production, use hashed passwords
    plan: 'pro'
  },
  'demo@example.com': {
    password: 'demo123',
    plan: 'basic'
  }
};

// Feature sets based on plan
const PLAN_FEATURES: Record<string, string[]> = {
  'basic': ['pattern_upload'],
  'pro': ['pattern_upload', 'wifi_upload', 'advanced_controls'],
  'enterprise': ['pattern_upload', 'wifi_upload', 'advanced_controls', 'api_access', 'priority_support']
};

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

  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const body: LoginRequest = req.body;

    // Validate request body
    if (!body.email || !body.password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    const { email, password, device_id, device_name } = body;

    // Find user
    const user = USERS[email.toLowerCase()];
    
    if (!user || user.password !== password) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Generate session token (in production, use JWT or similar)
    const sessionToken = generateSessionToken(email, device_id || 'DEVICE_UNKNOWN');
    
    // Get user plan and features
    const plan = user.plan;
    const features = PLAN_FEATURES[plan] || PLAN_FEATURES['basic'];

    // Create entitlement token
    const entitlementToken: EntitlementToken = {
      sub: `user_${email.toLowerCase().replace(/[^a-z0-9]/g, '_')}`,
      product: 'upload_bridge_pro',
      plan: plan,
      features: features,
      expires_at: null // Never expires for demo (set expiration in production)
    };

    // Create user info
    const userInfo: User = {
      id: entitlementToken.sub,
      email: email
    };

    // Return success response
    const response: LoginResponse = {
      session_token: sessionToken,
      entitlement_token: entitlementToken,
      user: userInfo
    };

    return res.status(200).json(response);

  } catch (error) {
    console.error('Login error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

function generateSessionToken(email: string, deviceId: string): string {
  // Simple token generation (in production, use JWT with proper signing)
  const timestamp = Date.now();
  const data = `${email}:${deviceId}:${timestamp}`;
  const buffer = Buffer.from(data);
  return `session_${buffer.toString('base64url')}`;
}
