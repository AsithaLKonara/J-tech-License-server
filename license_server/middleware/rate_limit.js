/**
 * Per-User Rate Limiting Middleware
 * Rate limits by user_id with plan-based tiers
 */

const rateLimit = require('express-rate-limit');

class UserRateLimiter {
    constructor() {
        // Rate limit stores (in production, use Redis)
        this.userLimits = new Map();
        
        // Plan-based rate limits (requests per 15 minutes)
        this.planLimits = {
            trial: 50,
            monthly: 200,
            yearly: 500,
            perpetual: 1000
        };
    }

    /**
     * Get rate limit for user's plan
     */
    getUserLimit(userId, plan) {
        const limit = this.planLimits[plan] || this.planLimits.monthly;
        return limit;
    }

    /**
     * Create rate limiter middleware for specific plan
     */
    createLimiter(plan) {
        const limit = this.planLimits[plan] || this.planLimits.monthly;
        
        return rateLimit({
            windowMs: 15 * 60 * 1000, // 15 minutes
            max: limit,
            keyGenerator: (req) => {
                // Use user_id if available, otherwise fall back to IP
                return req.user?.id || req.ip;
            },
            message: `Too many requests. Limit: ${limit} per 15 minutes for ${plan} plan.`
        });
    }

    /**
     * Dynamic rate limiter based on user's plan
     */
    dynamicLimiter() {
        return async (req, res, next) => {
            if (!req.user) {
                // Fall back to IP-based limiting for unauthenticated requests
                return next();
            }

            // Get user's plan from entitlement
            try {
                // This would query database for user's plan
                // For now, use default
                const plan = req.user.plan || 'monthly';
                const limit = this.planLimits[plan] || this.planLimits.monthly;
                
                // Check rate limit
                const key = `user:${req.user.id}`;
                const now = Date.now();
                const windowMs = 15 * 60 * 1000;
                
                if (!this.userLimits.has(key)) {
                    this.userLimits.set(key, { count: 0, resetAt: now + windowMs });
                }
                
                const limitData = this.userLimits.get(key);
                
                if (now > limitData.resetAt) {
                    limitData.count = 0;
                    limitData.resetAt = now + windowMs;
                }
                
                if (limitData.count >= limit) {
                    return res.status(429).json({
                        error: 'Too many requests',
                        limit: limit,
                        plan: plan,
                        retry_after: Math.ceil((limitData.resetAt - now) / 1000)
                    });
                }
                
                limitData.count++;
                next();
            } catch (error) {
                console.error('Rate limit check error:', error);
                next(); // Allow request on error
            }
        };
    }
}

module.exports = UserRateLimiter;
