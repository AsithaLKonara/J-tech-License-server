<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use App\Models\User;
use App\Models\Entitlement;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

class DatabaseSeeder extends Seeder
{
    /**
     * Seed the application's database.
     */
    public function run(): void
    {
        // 1. Create Admins
        $this->call(AdminUserSeeder::class);

        // 2. Create Plans (if seeder exists)
        // $this->call(PlanSeeder::class);

        // 3. Create test user
        $user = User::firstOrCreate(
            ['email' => 'test@example.com'],
            [
                'id' => Str::uuid()->toString(),
                'name' => 'Test User',
                'password' => Hash::make('testpassword123'),
                'is_admin' => false,
            ]
        );

        // Create trial entitlement for test user if doesn't exist
        if (!$user->activeEntitlement()) {
            Entitlement::create([
                'id' => Str::uuid()->toString(),
                'user_id' => $user->id,
                'product_id' => 'upload-bridge',
                'plan' => 'trial',
                'status' => 'active',
                'features' => json_encode(['pattern_upload']),
                'max_devices' => 5,
                'expires_at' => now()->addDays(30),
            ]);
        }

        $this->command->info('Test user created: test@example.com / testpassword123');
    }
}
