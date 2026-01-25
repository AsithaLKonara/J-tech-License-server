<?php

namespace App\Services;

use App\Models\User;
use App\Models\Subscription;
use App\Models\License;
use App\Models\Entitlement;
use Illuminate\Support\Str;

class LicenseService
{
    public function generateLicenseFromSubscription(User $user, Subscription $subscription): License
    {
        $features = $subscription->getFeatures();

        // Deactivate old licenses
        $user->licenses()->where('status', 'active')->update(['status' => 'expired']);

        return License::create([
            'user_id' => $user->id,
            'subscription_id' => $subscription->id,
            'plan' => $subscription->plan_type,
            'features' => $features,
            'status' => 'active',
            'expires_at' => $subscription->expires_at,
        ]);
    }

    public function createFreeLicense(User $user): License
    {
        return License::create([
            'user_id' => $user->id,
            'plan' => 'free',
            'features' => ['pattern_upload'],
            'status' => 'active',
            'expires_at' => null,
        ]);
    }

    /**
     * Generate entitlement from subscription
     */
    public function generateEntitlementFromSubscription(User $user, Subscription $subscription): Entitlement
    {
        $features = $subscription->getFeatures();
        $planMap = [
            'monthly' => 'monthly',
            'annual' => 'yearly',
            'lifetime' => 'perpetual',
        ];

        // Deactivate old entitlements
        $user->entitlements()->where('status', 'active')->update(['status' => 'inactive']);

        return Entitlement::create([
            'id' => Str::uuid()->toString(),
            'user_id' => $user->id,
            'product_id' => 'upload-bridge',
            'plan' => $planMap[$subscription->plan_type] ?? 'monthly',
            'status' => 'active',
            'features' => $features,
            'max_devices' => $this->getMaxDevicesForPlan($subscription->plan_type),
            'stripe_customer_id' => $subscription->stripe_customer_id,
            'stripe_subscription_id' => $subscription->stripe_subscription_id,
            'expires_at' => $subscription->expires_at,
        ]);
    }

    /**
     * Get max devices for plan
     */
    private function getMaxDevicesForPlan(string $planType): int
    {
        return match($planType) {
            'monthly' => 2,
            'annual' => 5,
            'lifetime' => 10,
            default => 1,
        };
    }

    /**
     * Get active entitlement for user
     */
    public function getActiveEntitlement(User $user): ?Entitlement
    {
        return $user->activeEntitlement();
    }
}

