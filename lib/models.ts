/**
 * Database Models and Interfaces
 * TypeScript interfaces for user, license, and device data
 */

export interface User {
  id: string;
  email: string;
  auth0_sub: string;
  created_at: Date;
}

export interface License {
  id: string;
  user_id: string;
  plan: string;
  features: string[];
  expires_at: Date | null;
  status: 'active' | 'expired' | 'revoked' | 'suspended';
  created_at: Date;
  updated_at: Date;
}

export interface Device {
  id: string;
  license_id: string;
  device_id: string;
  device_name: string;
  registered_at: Date;
  last_seen_at: Date;
}

export interface EntitlementToken {
  sub: string;
  product: string;
  plan: string;
  features: string[];
  expires_at: number | null;
  issued_at?: number;
}

export interface SessionToken {
  token: string;
  user_id: string;
  device_id: string;
  expires_at: Date;
  created_at: Date;
}

