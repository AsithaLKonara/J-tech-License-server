/**
 * Subscription Plan Logic
 * Defines features and expiry for different plan types
 */

const PLAN_FEATURES = {
  monthly: ['pattern_upload', 'wifi_upload'],
  annual: ['pattern_upload', 'wifi_upload', 'advanced_controls'],
  lifetime: ['pattern_upload', 'wifi_upload', 'advanced_controls', 'ai_features'],
};

const PLAN_DURATION = {
  monthly: 30 * 24 * 60 * 60 * 1000, // 30 days in milliseconds
  annual: 365 * 24 * 60 * 60 * 1000, // 365 days in milliseconds
  lifetime: null, // Never expires
};

/**
 * Get features for a plan type
 */
export function getPlanFeatures(planType: string): string[] {
  return PLAN_FEATURES[planType as keyof typeof PLAN_FEATURES] || [];
}

/**
 * Calculate expiry timestamp for a plan type
 */
export function calculateExpiry(planType: string): number | null {
  if (planType === 'lifetime') return null;
  const duration = PLAN_DURATION[planType as keyof typeof PLAN_DURATION];
  if (!duration) return null;
  return Date.now() + duration;
}

/**
 * Get plan name from plan type
 */
export function getPlanName(planType: string): string {
  const names: Record<string, string> = {
    monthly: 'Monthly',
    annual: 'Annual',
    lifetime: 'Lifetime',
  };
  return names[planType] || planType;
}

