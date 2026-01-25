<?php

namespace App\Services;

use App\Models\User;
use App\Models\Entitlement;
use App\Models\Device;
use App\Models\MagicLink;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

class AuthService
{
    public function __construct(
        private TokenService $tokenService
    ) {}

    /**
     * Authenticate user with email and password
     */
    public function authenticate(string $email, string $password): ?User
    {
        $user = User::where('email', $email)->first();

        if (!$user || !Hash::check($password, $user->password)) {
            return null;
        }

        return $user;
    }

    /**
     * Authenticate user with magic link token
     */
    public function authenticateWithMagicLink(string $token): ?User
    {
        $magicLink = MagicLink::where('token', $token)->first();

        if (!$magicLink || !$magicLink->isValid() || $magicLink->used) {
            return null;
        }

        $user = User::where('email', $magicLink->email)->first();

        if (!$user) {
            // Create user if doesn't exist
            $user = User::create([
                'id' => Str::uuid()->toString(),
                'email' => $magicLink->email,
                'password' => Hash::make(Str::random(32)), // Random password
                'name' => null,
            ]);
        }

        // Mark magic link as used
        $magicLink->update(['used' => true]);

        return $user;
    }

    /**
     * Register device for user
     */
    public function registerDevice(User $user, string $deviceId, ?string $deviceName = null, ?string $entitlementId = null): array
    {
        $entitlement = $entitlementId 
            ? Entitlement::find($entitlementId)
            : $user->activeEntitlement();

        if (!$entitlement) {
            // Create trial entitlement if none exists
            $entitlement = $this->createTrialEntitlement($user);
        }

        // Check device limit
        if (!$user->is_admin && !$entitlement->canAddDevice()) {
            return [
                'success' => false,
                'error' => 'Device limit reached',
                'max_devices' => $entitlement->max_devices,
                'current_devices' => $entitlement->devices()->count(),
            ];
        }

        // Check if device already exists
        $existingDevice = Device::where('user_id', $user->id)
            ->where('device_id', $deviceId)
            ->first();

        if ($existingDevice) {
            // Update last seen
            $existingDevice->update([
                'last_seen_at' => now(),
                'device_name' => $deviceName ?? $existingDevice->device_name,
            ]);

            return [
                'success' => true,
                'device' => $existingDevice,
                'message' => 'Device updated',
            ];
        }

        // Create new device
        // Note: license_id is NOT NULL in schema, but we use entitlement_id
        // Find or create a dummy license for the foreign key constraint
        // Note: license_id is NOT NULL in schema, but we use entitlement_id
        // Find or create a dummy license for the foreign key constraint
        $license = \App\Models\License::where('user_id', $user->id)->first();
        if (!$license) {
            // Create a dummy license for this user if none exists
            $license = \App\Models\License::create([
                'id' => \Illuminate\Support\Str::uuid()->toString(),
                'user_id' => $user->id,
                'plan' => 'trial',
                'status' => 'active',
                'features' => json_encode(['pattern_upload']),
                'expires_at' => now()->addDays(30),
            ]);
        }
        
        $device = Device::create([
            'license_id' => $license->id, // Required by schema
            'user_id' => $user->id,
            'entitlement_id' => $entitlement->id,
            'device_id' => $deviceId,
            'device_name' => $deviceName ?? 'Unknown Device',
            'last_seen_at' => now(),
        ]);

        return [
            'success' => true,
            'device' => $device,
            'message' => 'Device registered',
        ];
    }

    /**
     * Create trial entitlement for user
     */
    private function createTrialEntitlement(User $user): Entitlement
    {
        return Entitlement::create([
            'id' => Str::uuid()->toString(),
            'user_id' => $user->id,
            'product_id' => 'upload-bridge',
            'plan' => 'trial',
            'status' => 'active',
            'features' => ['pattern_upload'],
            'max_devices' => 1,
            'expires_at' => now()->addDays(7), // 7 day trial
        ]);
    }

    /**
     * Get or create active entitlement for user
     */
    public function getOrCreateEntitlement(User $user): Entitlement
    {
        $entitlement = $user->activeEntitlement();

        if (!$entitlement) {
            $entitlement = $this->createTrialEntitlement($user);
        }

        return $entitlement;
    }
}
