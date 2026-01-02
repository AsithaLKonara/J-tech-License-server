/**
 * JWT Token Validator - Simple JWT Implementation
 * Replaces Auth0 JWT validation with simple JWT signing/verification
 */

import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'change-this-secret-key';

/**
 * Sign a JWT token
 */
export function signToken(payload: any, expiresIn: string | number = '7d'): string {
  if (!JWT_SECRET) {
    throw new Error('JWT_SECRET is not configured');
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const options: any = { expiresIn };
  return jwt.sign(payload, JWT_SECRET, options);
}

/**
 * Verify and decode a JWT token
 */
export function verifyToken(token: string): any {
  if (!JWT_SECRET) {
    throw new Error('JWT_SECRET is not configured');
  }
  try {
    return jwt.verify(token, JWT_SECRET);
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
