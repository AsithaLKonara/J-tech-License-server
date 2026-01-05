<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;
use App\Models\User;
use App\Models\Subscription;
use App\Models\License;
use App\Models\Device;
use App\Models\Payment;

class TestDataSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        // Create admin user
        $admin = User::create([
            'name' => 'Test Admin',
            'email' => 'admin@test.com',
            'password' => Hash::make('password123'),
            'is_admin' => true,
        ]);

        // Create regular users with subscriptions
        for ($i = 1; $i <= 5; $i++) {
            $user = User::create([
                'name' => "Test User {$i}",
                'email' => "user{$i}@test.com",
                'password' => Hash::make('password123'),
                'is_admin' => false,
            ]);

            // Create subscription for some users
            if ($i <= 3) {
                $planTypes = ['monthly', 'annual', 'lifetime'];
                $subscription = Subscription::create([
                    'user_id' => $user->id,
                    'plan_type' => $planTypes[$i - 1],
                    'status' => 'active',
                    'expires_at' => $planTypes[$i - 1] === 'lifetime' ? null : now()->addMonth(),
                ]);

                // Create license
                $license = License::create([
                    'user_id' => $user->id,
                    'subscription_id' => $subscription->id,
                    'plan' => $subscription->plan_type,
                    'features' => ['pattern_upload', 'wifi_upload'],
                    'status' => 'active',
                    'expires_at' => $subscription->expires_at,
                ]);

                // Create devices for some licenses
                if ($i <= 2) {
                    Device::create([
                        'license_id' => $license->id,
                        'device_id' => "device_{$i}_1",
                        'device_name' => "Device {$i}-1",
                        'last_seen_at' => now(),
                    ]);

                    if ($i === 1) {
                        Device::create([
                            'license_id' => $license->id,
                            'device_id' => "device_{$i}_2",
                            'device_name' => "Device {$i}-2",
                            'last_seen_at' => now(),
                        ]);
                    }
                }

                // Create payments
                Payment::create([
                    'user_id' => $user->id,
                    'subscription_id' => $subscription->id,
                    'amount' => 29.99,
                    'currency' => 'USD',
                    'status' => 'completed',
                ]);
            }
        }

        // Create expired subscription
        $expiredUser = User::create([
            'name' => 'Expired User',
            'email' => 'expired@test.com',
            'password' => Hash::make('password123'),
            'is_admin' => false,
        ]);

        $expiredSubscription = Subscription::create([
            'user_id' => $expiredUser->id,
            'plan_type' => 'monthly',
            'status' => 'canceled',
            'expires_at' => now()->subMonth(),
        ]);

        License::create([
            'user_id' => $expiredUser->id,
            'subscription_id' => $expiredSubscription->id,
            'plan' => 'monthly',
            'features' => ['pattern_upload'],
            'status' => 'expired',
            'expires_at' => now()->subMonth(),
        ]);
    }
}
