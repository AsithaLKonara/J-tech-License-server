<?php
/**
 * License Server API Client
 * Communicates with the license server API
 */

require_once __DIR__ . '/../includes/config.php';

class APIClient {
    private $baseUrl;

    public function __construct() {
        $this->baseUrl = rtrim(LICENSE_SERVER_URL, '/');
    }

    /**
     * Make HTTP request
     */
    private function request($method, $endpoint, $data = null) {
        $url = $this->baseUrl . $endpoint;
        
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/json',
            ],
            CURLOPT_TIMEOUT => 30,
        ]);

        if ($data !== null) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);

        if ($error) {
            throw new Exception("API request failed: $error");
        }

        $decoded = json_decode($response, true);
        if ($httpCode >= 400) {
            $errorMsg = $decoded['error'] ?? 'API request failed';
            throw new Exception($errorMsg, $httpCode);
        }

        return $decoded;
    }

    /**
     * Register user
     */
    public function register($email, $password) {
        return $this->request('POST', '/api/v2/auth/register', [
            'email' => $email,
            'password' => $password,
        ]);
    }

    /**
     * Login user
     */
    public function login($email, $password, $deviceId = null, $deviceName = null) {
        return $this->request('POST', '/api/v2/auth/login', [
            'email' => $email,
            'password' => $password,
            'device_id' => $deviceId,
            'device_name' => $deviceName,
        ]);
    }

    /**
     * Request magic link
     */
    public function requestMagicLink($email) {
        return $this->request('POST', '/api/v2/auth/magic-link', [
            'email' => $email,
        ]);
    }

    /**
     * Verify magic link
     */
    public function verifyMagicLink($token) {
        return $this->request('GET', '/api/v2/auth/verify-magic-link?token=' . urlencode($token));
    }

    /**
     * Refresh session token
     */
    public function refreshToken($sessionToken, $deviceId = null) {
        return $this->request('POST', '/api/v2/auth/refresh', [
            'session_token' => $sessionToken,
            'device_id' => $deviceId,
        ]);
    }

    /**
     * Get user subscription
     */
    public function getSubscription($sessionToken) {
        return $this->request('GET', '/api/v2/subscriptions?session_token=' . urlencode($sessionToken));
    }

    /**
     * Create subscription
     */
    public function createSubscription($sessionToken, $planType) {
        return $this->request('POST', '/api/v2/subscriptions/create', [
            'session_token' => $sessionToken,
            'plan_type' => $planType,
        ]);
    }
}

