<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\AuthService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ApiDeviceController extends Controller
{
    public function __construct(
        private AuthService $authService
    ) {}

    /**
     * Register device
     */
    public function register(Request $request): JsonResponse
    {
        $validator = \Validator::make($request->all(), [
            'device_id' => 'required|string',
            'device_name' => 'nullable|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'error' => 'Validation failed',
                'messages' => $validator->errors(),
            ], 400);
        }

        $user = $request->user();
        $result = $this->authService->registerDevice(
            $user,
            $request->device_id,
            $request->device_name
        );

        if (!$result['success']) {
            return response()->json([
                'error' => $result['error'] ?? 'Device registration failed',
                'max_devices' => $result['max_devices'] ?? null,
                'current_devices' => $result['current_devices'] ?? null,
            ], 403);
        }

        return response()->json([
            'message' => $result['message'],
            'device' => [
                'id' => $result['device']->id,
                'device_id' => $result['device']->device_id,
                'device_name' => $result['device']->device_name,
                'last_seen_at' => $result['device']->last_seen_at?->format('c'),
            ],
        ]);
    }

    /**
     * List user devices
     */
    public function index(Request $request): JsonResponse
    {
        $user = $request->user();
        $devices = $user->devices()->with('entitlement')->get();

        return response()->json([
            'devices' => $devices->map(function ($device) {
                return [
                    'id' => $device->id,
                    'device_id' => $device->device_id,
                    'device_name' => $device->device_name,
                    'last_seen_at' => $device->last_seen_at?->format('c'),
                    'entitlement_id' => $device->entitlement_id,
                ];
            }),
        ]);
    }

    /**
     * Remove device
     */
    public function destroy(Request $request, $id): JsonResponse
    {
        $user = $request->user();
        $device = $user->devices()->find($id);

        if (!$device) {
            return response()->json([
                'error' => 'Device not found',
            ], 404);
        }

        $device->delete();

        return response()->json([
            'message' => 'Device removed successfully',
        ]);
    }
}
