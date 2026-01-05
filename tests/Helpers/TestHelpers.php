<?php

namespace Tests\Helpers;

use App\Models\User;
use App\Models\Subscription;
use App\Models\License;
use App\Models\Device;
use App\Models\Payment;
use App\Models\MagicLink;
use Illuminate\Support\Facades\Hash;

class TestHelpers
{
    /**
     * Create a test user.
     */
    public static function createUser(array $attributes = []): User
    {
        return User::create(array_merge([
            'name' => 'Test User',
            'email' => 'test' . uniqid() . '@test.com',
            'password' => Hash::make('password123'),
            'is_admin' => false,
        ], $attributes));
    }

    /**
     * Create a test admin user.
     */
    public static function createAdmin(array $attributes = []): User
    {
        return self::createUser(array_merge([
            'name' => 'Test Admin',
            'email' => 'admin' . uniqid() . '@test.com',
            'is_admin' => true,
        ], $attributes));
    }

    /**
     * Create a test subscription.
     */
    public static function createSubscription(User $user, array $attributes = []): Subscription
    {
        return Subscription::create(array_merge([
            'user_id' => $user->id,
            'plan_type' => 'monthly',
            'status' => 'active',
            'expires_at' => now()->addMonth(),
        ], $attributes));
    }

    /**
     * Create a test license.
     */
    public static function createLicense(User $user, ?Subscription $subscription = null, array $attributes = []): License
    {
        if (!$subscription) {
            $subscription = self::createSubscription($user);
        }

        return License::create(array_merge([
            'user_id' => $user->id,
            'subscription_id' => $subscription->id,
            'plan' => $subscription->plan_type,
            'features' => ['pattern_upload', 'wifi_upload'],
            'status' => 'active',
            'expires_at' => $subscription->expires_at,
        ], $attributes));
    }

    /**
     * Create a test device.
     */
    public static function createDevice(License $license, array $attributes = []): Device
    {
        return Device::create(array_merge([
            'license_id' => $license->id,
            'device_id' => 'device_' . uniqid(),
            'device_name' => 'Test Device',
            'last_seen_at' => now(),
        ], $attributes));
    }

    /**
     * Create a test payment.
     */
    public static function createPayment(User $user, ?Subscription $subscription = null, array $attributes = []): Payment
    {
        return Payment::create(array_merge([
            'user_id' => $user->id,
            'subscription_id' => $subscription?->id,
            'amount' => 29.99,
            'currency' => 'USD',
            'status' => 'completed',
        ], $attributes));
    }

    /**
     * Create a test magic link.
     */
    public static function createMagicLink(string $email, array $attributes = []): MagicLink
    {
        return MagicLink::create(array_merge([
            'email' => $email,
            'token' => \Illuminate\Support\Str::random(64),
            'expires_at' => now()->addHour(),
            'used' => false,
        ], $attributes));
    }

    /**
     * Login as a user via Dusk.
     */
    public static function loginAs(\Laravel\Dusk\Browser $browser, User $user): void
    {
        $browser->visit('/login')
            ->type('email', $user->email)
            ->type('password', 'password123')
            ->press('Login')
            ->waitForLocation('/dashboard');
    }

    /**
     * Login as admin via Dusk.
     */
    public static function loginAsAdmin(\Laravel\Dusk\Browser $browser): void
    {
        $admin = User::where('is_admin', true)->first();
        if (!$admin) {
            $admin = self::createAdmin(['email' => 'admin@test.com']);
        }
        self::loginAs($browser, $admin);
    }
}
