<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * Security Headers Middleware
 * 
 * Adds security headers to all HTTP responses:
 * - X-Frame-Options: Prevents clickjacking
 * - X-Content-Type-Options: Prevents MIME sniffing
 * - X-XSS-Protection: Enables XSS filter
 * - Strict-Transport-Security: Enforces HTTPS
 * - Content-Security-Policy: Controls resource loading
 * - Referrer-Policy: Controls referrer information
 * - Permissions-Policy: Controls browser features
 */
class SecurityHeaders
{
    /**
     * Handle an incoming request.
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
    public function handle(Request $request, Closure $next): Response
    {
        $response = $next($request);

        // X-Frame-Options: Prevent clickjacking
        $response->headers->set('X-Frame-Options', 'DENY', false);

        // X-Content-Type-Options: Prevent MIME sniffing
        $response->headers->set('X-Content-Type-Options', 'nosniff', false);

        // X-XSS-Protection: Enable XSS filter (legacy, but still useful)
        $response->headers->set('X-XSS-Protection', '1; mode=block', false);

        // Strict-Transport-Security: Enforce HTTPS (only in production with HTTPS)
        if ($request->secure() || config('app.env') === 'production') {
            $response->headers->set(
                'Strict-Transport-Security',
                'max-age=31536000; includeSubDomains; preload',
                false
            );
        }

        // Content-Security-Policy: Control resource loading
        // Adjust CSP policy based on your needs
        $csp = "default-src 'self'; " .
               "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com; " .
               "style-src 'self' 'unsafe-inline'; " .
               "img-src 'self' data: https:; " .
               "font-src 'self' data:; " .
               "connect-src 'self' https://api.stripe.com; " .
               "frame-src https://js.stripe.com https://hooks.stripe.com; " .
               "object-src 'none'; " .
               "base-uri 'self'; " .
               "form-action 'self'; " .
               "frame-ancestors 'none'; " .
               "upgrade-insecure-requests;";
        
        $response->headers->set('Content-Security-Policy', $csp, false);

        // Referrer-Policy: Control referrer information
        $response->headers->set('Referrer-Policy', 'strict-origin-when-cross-origin', false);

        // Permissions-Policy: Control browser features
        $permissionsPolicy = "geolocation=(), " .
                            "microphone=(), " .
                            "camera=(), " .
                            "payment=(), " .
                            "usb=(), " .
                            "magnetometer=(), " .
                            "gyroscope=(), " .
                            "accelerometer=()";
        $response->headers->set('Permissions-Policy', $permissionsPolicy, false);

        // Remove X-Powered-By header (if not already removed)
        $response->headers->remove('X-Powered-By');

        return $response;
    }
}
