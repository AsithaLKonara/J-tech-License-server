<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;
use App\Models\User;
use App\Models\Entitlement;

class ComprehensiveTestSeeder extends Seeder
{
    /**
     * Seed the database with admin and test users with various subscription types.
     */
    public function run(): void
    {
        // 1. Create Admin User
        $admin = User::firstOrCreate(
            ['email' => 'admin@example.com'],
            [
                'id' => Str::uuid()->toString(),
                'name' => 'Administrator',
                'password' => Hash::make('admin123'),
                'is_admin' => true,
            ]
        );
        $this->command->info("✓ Admin user created: admin@example.com / admin123");

        // 2. Create Trial User
        $trialUser = User::firstOrCreate(
            ['email' => 'trial@example.com'],
            [
                'id' => Str::uuid()->toString(),
                'name' => 'Trial User',
                'password' => Hash::make('password123'),
                'is_admin' => false,
            ]
        );
        
        if (!$trialUser->activeEntitlement()) {
            Entitlement::create([
                'id' => Str::uuid()->toString(),
                'user_id' => $trialUser->id,
                'product_id' => 'upload-bridge',
                'plan' => 'trial',
                'status' => 'active',
                'features' => json_encode(['pattern_upload']),
                'max_devices' => 1,
                'expires_at' => now()->addDays(7),
            ]);
        }
        $this->command->info("✓ Trial user created: trial@example.com / password123");

        // 3. Create Monthly Subscription User
        $monthlyUser = User::firstOrCreate(
            ['email' => 'monthly@example.com'],
            [
                'id' => Str::uuid()->toString(),
                'name' => 'Monthly Subscriber',
                'password' => Hash::make('password123'),
                'is_admin' => false,
            ]
        );
        
        if (!$monthlyUser->activeEntitlement()) {
            Entitlement::create([
                'id' => Str::uuid()->toString(),
                'user_id' => $monthlyUser->id,
                'product_id' => 'upload-bridge',
                'plan' => 'monthly',
                'status' => 'active',
                'features' => json_encode(['pattern_upload', 'wifi_upload']),
                'max_devices' => 3,
                'expires_at' => now()->addMonth(),
            ]);
        }
        $this->command->info("✓ Monthly user created: monthly@example.com / password123");

        // 4. Create Yearly Subscription User
        $yearlyUser = User::firstOrCreate(
            ['email' => 'yearly@example.com'],
            [
                'id' => Str::uuid()->toString(),
                'name' => 'Yearly Subscriber',
                'password' => Hash::make('password123'),
                'is_admin' => false,
            ]
        );
        
        if (!$yearlyUser->activeEntitlement()) {
            Entitlement::create([
                'id' => Str::uuid()->toString(),
                'user_id' => $yearlyUser->id,
                'product_id' => 'upload-bridge',
                'plan' => 'yearly',
                'status' => 'active',
                'features' => json_encode(['pattern_upload', 'wifi_upload', 'advanced_controls']),
                'max_devices' => 5,
                'expires_at' => now()->addYear(),
            ]);
        }
        $this->command->info("✓ Yearly user created: yearly@example.com / password123");

        // 5. Create Perpetual License User
        $perpetualUser = User::firstOrCreate(
            ['email' => 'perpetual@example.com'],
            [
                'id' => Str::uuid()->toString(),
                'name' => 'Perpetual License Holder',
                'password' => Hash::make('password123'),
                'is_admin' => false,
            ]
        );
        
        if (!$perpetualUser->activeEntitlement()) {
            Entitlement::create([
                'id' => Str::uuid()->toString(),
                'user_id' => $perpetualUser->id,
                'product_id' => 'upload-bridge',
                'plan' => 'perpetual',
                'status' => 'active',
                'features' => json_encode(['pattern_upload', 'wifi_upload', 'advanced_controls', 'ai_features']),
                'max_devices' => 10,
                'expires_at' => null, // Perpetual - never expires
            ]);
        }
        $this->command->info("✓ Perpetual user created: perpetual@example.com / password123");

        // 6. Keep existing test user
        $this->command->info("✓ Existing test user: test@example.com / testpassword123");

        // Summary
        $this->command->info("\n" . str_repeat('=', 60));
        $this->command->info("DATABASE SEEDED SUCCESSFULLY!");
        $this->command->info(str_repeat('=', 60));
        $this->command->table(
            ['Email', 'Password', 'Type', 'Plan'],
            [
                ['admin@example.com', 'admin123', 'Admin', 'N/A'],
                ['trial@example.com', 'password123', 'User', 'Trial (7 days)'],
                ['monthly@example.com', 'password123', 'User', 'Monthly'],
                ['yearly@example.com', 'password123', 'User', 'Yearly'],
                ['perpetual@example.com', 'password123', 'User', 'Perpetual'],
                ['test@example.com', 'testpassword123', 'User', 'Trial (30 days)'],
            ]
        );
    }
}
