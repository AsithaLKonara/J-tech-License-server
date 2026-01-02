/**
 * JWT Token Validator for Auth0
 * Validates Auth0 JWT tokens and extracts user information
 */

import jwt from 'jsonwebtoken';
import jwksClient from 'jwks-rsa';

interface Auth0Config {
  domain: string;
  audience?: string;
  jwksUri?: string;
}

interface DecodedToken {
  sub: string;
  email?: string;
  email_verified?: boolean;
  aud?: string | string[];
  exp: number;
  iat: number;
  iss: string;
  [key: string]: any;
}

/**
 * Get Auth0 configuration from environment variables
 */
function getAuth0Config(): Auth0Config | null {
  const domain = process.env.AUTH0_DOMAIN;
  if (!domain) {
    return null;
  }

  return {
    domain,
    audience: process.env.AUTH0_AUDIENCE,
    jwksUri: process.env.AUTH0_JWKS_URI || `https://${domain}/.well-known/jwks.json`,
  };
}

/**
 * Get signing key from JWKS endpoint
 */
async function getSigningKey(jwksUri: string, kid: string): Promise<string> {
  const client = jwksClient({
    jwksUri,
    cache: true,
    cacheMaxAge: 86400000, // 24 hours
  });

  return new Promise((resolve, reject) => {
    client.getSigningKey(kid, (err, key) => {
      if (err) {
        reject(err);
        return;
      }
      const signingKey = key?.getPublicKey();
      if (!signingKey) {
        reject(new Error('Could not get signing key'));
        return;
      }
      resolve(signingKey);
    });
  });
}

/**
 * Verify and decode Auth0 JWT token
 */
export async function verifyAuth0Token(token: string): Promise<DecodedToken> {
  const config = getAuth0Config();
  
  if (!config) {
    // If Auth0 is not configured, we can't validate tokens
    // In development, we might want to allow this, but in production it's a security risk
    throw new Error('Auth0 is not configured. Set AUTH0_DOMAIN environment variable.');
  }

  // Decode token to get kid (key ID)
  const decoded = jwt.decode(token, { complete: true });
  if (!decoded || typeof decoded === 'string') {
    throw new Error('Invalid token format');
  }

  const kid = decoded.header.kid;
  if (!kid) {
    throw new Error('Token missing key ID');
  }

  // Get signing key from JWKS
  const signingKey = await getSigningKey(config.jwksUri!, kid);

  // Verify token
  const options: jwt.VerifyOptions = {
    algorithms: ['RS256'],
    issuer: `https://${config.domain}/`,
  };

  if (config.audience) {
    options.audience = config.audience;
  }

  try {
    const verified = jwt.verify(token, signingKey, options) as DecodedToken;
    return verified;
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      throw new Error('Token expired');
    }
    if (error instanceof jwt.JsonWebTokenError) {
      throw new Error(`Invalid token: ${error.message}`);
    }
    throw error;
  }
}

/**
 * Extract user information from decoded token
 */
export function extractUserInfo(decoded: DecodedToken): { sub: string; email: string } {
  const sub = decoded.sub;
  const email = decoded.email || decoded['https://upload-bridge.com/email'] || '';

  if (!sub) {
    throw new Error('Token missing subject (sub)');
  }

  if (!email) {
    throw new Error('Token missing email');
  }

  return { sub, email };
}

