<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class CheckSubscription
{
    public function handle(Request $request, Closure $next): Response
    {
        // Only check for subscription-required routes
        $subscriptionRoutes = ['subscription', 'licenses', 'devices'];
        
        if (in_array($request->route()->getName(), $subscriptionRoutes)) {
            $user = $request->user();
            if ($user && !$user->activeSubscription() && !$user->activeLicense()) {
                return redirect()->route('subscription')
                    ->with('error', 'Please subscribe to access this feature.');
            }
        }

        return $next($request);
    }
}

