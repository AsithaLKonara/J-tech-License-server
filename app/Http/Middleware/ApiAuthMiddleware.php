<?php

namespace App\Http\Middleware;

use App\Services\TokenService;
use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class ApiAuthMiddleware
{
    public function __construct(
        private TokenService $tokenService
    ) {}

    /**
     * Handle an incoming request.
     */
    public function handle(Request $request, Closure $next): Response
    {
        $token = $request->bearerToken() 
            ?? $request->header('Authorization')
            ?? $request->input('session_token');

        // Remove "Bearer " prefix if present
        if ($token && str_starts_with($token, 'Bearer ')) {
            $token = substr($token, 7);
        }

        if (!$token) {
            return response()->json([
                'error' => 'Unauthorized',
                'message' => 'Session token required',
            ], 401);
        }

        $user = $this->tokenService->validateSessionToken($token);

        if (!$user) {
            return response()->json([
                'error' => 'Unauthorized',
                'message' => 'Invalid or expired token',
            ], 401);
        }

        // Attach user to request
        $request->setUserResolver(function () use ($user) {
            return $user;
        });

        return $next($request);
    }
}
