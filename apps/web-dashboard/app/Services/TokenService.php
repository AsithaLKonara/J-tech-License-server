<?php

namespace App\Services;

use App\Models\User;
use App\Models\Entitlement;
use App\Models\ApiSession;
use App\Models\RevokedToken;
use Illuminate\Support\Str;
use Illuminate\Support\Facades\Hash;
use Carbon\Carbon;

class TokenService
{
    private string $sessionSecret;
    private int $sessionExpiryHours = 24 * 7; // 7 days
    private int $entitlementExpiryHours = 24; // 24 hours

    public function __construct()
    {
        $this->sessionSecret = config('app.key');
    }

    /**
     * Generate session token for user
     */
    public function generateSessionToken(User $user): string
    {
        $token = Str::random(64);
        $tokenHash = hash('sha256', $token);

        ApiSession::create([
            'user_id' => $user->id,
            'token_hash' => $tokenHash,
            'expires_at' => now()->addHours($this->sessionExpiryHours),
        ]);

        return $token;
    }

    /**
     * Validate session token
     */
    public function validateSessionToken(string $token): ?User
    {
        $tokenHash = hash('sha256', $token);

        // Check if token is revoked
        if (RevokedToken::where('token_hash', $tokenHash)->exists()) {
            return null;
        }

        $session = ApiSession::where('token_hash', $tokenHash)
            ->where('expires_at', '>', now())
            ->first();

        if (!$session) {
            return null;
        }

        return $session->user;
    }

    /**
     * Generate entitlement token (JWT-like structure)
     */
    public function generateEntitlementToken(User $user): array
    {
        // Admin override
        if ($user->is_admin) {
            return [
                'sub' => $user->id,
                'email' => $user->email,
                'plan' => 'admin_unlimited',
                'features' => ['pattern_upload'], // Admin has all features
                'max_devices' => 9999,
                'expires_at' => null,
                'iat' => now()->timestamp,
                'exp' => now()->addYears(100)->timestamp,
            ];
        }

        $entitlement = $user->activeEntitlement();

        if (!$entitlement || !$entitlement->isActive()) {
            // Return trial entitlement if no active entitlement
            return $this->generateTrialEntitlement($user);
        }

        $expiresAt = null;
        if ($entitlement->expires_at) {
            $expiresAtValue = $entitlement->expires_at;
            if ($expiresAtValue instanceof Carbon || $expiresAtValue instanceof \DateTimeInterface) {
                $expiresAt = $expiresAtValue->timestamp;
            } elseif (is_string($expiresAtValue)) {
                $expiresAt = Carbon::parse($expiresAtValue)->timestamp;
            } else {
                $expiresAt = Carbon::parse($expiresAtValue)->timestamp;
            }
        }

        return [
            'sub' => $user->id,
            'email' => $user->email,
            'plan' => $entitlement->plan,
            'features' => $entitlement->getFeatures(),
            'max_devices' => $entitlement->max_devices,
            'expires_at' => $expiresAt,
            'iat' => now()->timestamp,
            'exp' => $expiresAt ?: (now()->addHours($this->entitlementExpiryHours)->timestamp),
        ];
    }

    /**
     * Generate trial entitlement token
     */
    private function generateTrialEntitlement(User $user): array
    {
        return [
            'sub' => $user->id,
            'email' => $user->email,
            'plan' => 'trial',
            'features' => ['pattern_upload'],
            'max_devices' => 1,
            'expires_at' => null,
            'iat' => now()->timestamp,
            'exp' => now()->addDays(7)->timestamp, // 7 day trial
        ];
    }

    /**
     * Validate entitlement token
     */
    public function validateEntitlementToken(array $tokenData): bool
    {
        if (!isset($tokenData['exp']) || !isset($tokenData['sub'])) {
            return false;
        }

        // Check expiration
        if ($tokenData['exp'] < now()->timestamp) {
            return false;
        }

        return true;
    }

    /**
     * Revoke session token
     */
    public function revokeToken(string $token, ?string $reason = null): void
    {
        $tokenHash = hash('sha256', $token);

        // Get session before deleting
        $session = ApiSession::where('token_hash', $tokenHash)->first();
        
        if ($session) {
            // Add to revoked tokens
            RevokedToken::create([
                'token_hash' => $tokenHash,
                'user_id' => $session->user_id,
                'reason' => $reason,
            ]);

            // Delete session
            $session->delete();
        }
    }

    /**
     * Refresh session token
     */
    public function refreshSessionToken(string $oldToken): ?string
    {
        $user = $this->validateSessionToken($oldToken);
        if (!$user) {
            return null;
        }

        // Revoke old token
        $this->revokeToken($oldToken, 'refreshed');

        // Generate new token
        return $this->generateSessionToken($user);
    }
}
