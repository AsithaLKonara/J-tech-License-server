<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\LicenseService;
use App\Services\TokenService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ApiLicenseController extends Controller
{
    public function __construct(
        private LicenseService $licenseService,
        private TokenService $tokenService
    ) {}

    /**
     * Validate entitlement token
     */
    public function validateLicense(Request $request): JsonResponse
    {
        $validator = \Validator::make($request->all(), [
            'entitlement_token' => 'required|array',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'error' => 'Validation failed',
                'messages' => $validator->errors(),
            ], 400);
        }

        $isValid = $this->tokenService->validateEntitlementToken($request->entitlement_token);

        return response()->json([
            'valid' => $isValid,
            'timestamp' => now()->format('c'),
        ]);
    }

    /**
     * Get license information
     */
    public function info(Request $request): JsonResponse
    {
        $user = $request->user();
        $entitlement = $this->licenseService->getActiveEntitlement($user);

        if (!$entitlement) {
            return response()->json([
                'error' => 'No active entitlement found',
            ], 404);
        }

        return response()->json([
            'entitlement' => [
                'id' => $entitlement->id,
                'plan' => $entitlement->plan,
                'status' => $entitlement->status,
                'features' => $entitlement->getFeatures(),
                'max_devices' => $entitlement->max_devices,
                'current_devices' => $entitlement->devices()->count(),
                'expires_at' => $entitlement->expires_at?->format('c'),
                'is_active' => $entitlement->isActive(),
            ],
        ]);
    }

    /**
     * Verify license status (used by desktop app)
     */
    public function verify(Request $request): JsonResponse
    {
        $user = $request->user(); // From API middleware

        // Admin override
        if ($user->is_admin) {
            return response()->json([
                'status' => 'ACTIVE',
                'plan' => 'admin_unlimited',
                'features' => ['pattern_upload'],
                'expires_at' => now()->addYears(100)->toIso8601String(),
                'starts_at' => now()->toIso8601String(),
                'message' => 'Admin Unlimited Access',
            ]);
        }

        $entitlement = $user->activeEntitlement();

        if (!$entitlement || !$entitlement->isActive()) {
            return response()->json([
                'status' => 'INACTIVE',
                'message' => 'No active license found',
            ], 403);
        }

        return response()->json([
            'status' => 'ACTIVE',
            'plan' => $entitlement->plan,
            'features' => $entitlement->getFeatures(),
            'expires_at' => $entitlement->expires_at?->toIso8601String(),
            'starts_at' => $entitlement->created_at?->toIso8601String(),
            'message' => 'License is ACTIVE',
        ]);
    }
}
