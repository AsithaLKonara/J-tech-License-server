<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;
use App\Models\User;

class AdminUserSeeder extends Seeder
{
    /**
     * Run the database seeds.
     * 
     * Creates an initial admin user for production.
     * 
     * Usage: php artisan db:seed --class=AdminUserSeeder
     * 
     * Note: Change the default password immediately after first login!
     */
    public function run(): void
    {
        // Only create admin user if it doesn't exist
        $adminEmail = env('ADMIN_EMAIL', 'admin@example.com');
        $adminName = env('ADMIN_NAME', 'Administrator');
        $adminPassword = env('ADMIN_PASSWORD', 'changeme');

        if (User::where('email', $adminEmail)->exists()) {
            $this->command->info("Admin user with email {$adminEmail} already exists. Skipping creation.");
            return;
        }

        User::create([
            'id' => \Illuminate\Support\Str::uuid()->toString(),
            'name' => $adminName,
            'email' => $adminEmail,
            'password' => Hash::make($adminPassword),
            'is_admin' => true,
        ]);

        $this->command->info("Admin user created successfully!");
        $this->command->warn("Email: {$adminEmail}");
        $this->command->warn("Password: {$adminPassword}");
        $this->command->warn("IMPORTANT: Change the password immediately after first login!");
    }
}
