<?php
/**
 * Authentication Class
 * Handles user authentication and session management
 */

require_once __DIR__ . '/database.php';
require_once __DIR__ . '/api-client.php';

class Auth {
    private $db;
    private $api;

    public function __construct() {
        $this->db = new Database();
        $this->api = new APIClient();
    }

    /**
     * Start session
     */
    public function startSession() {
        if (session_status() === PHP_SESSION_NONE) {
            session_name(SESSION_NAME);
            session_start();
        }
    }

    /**
     * Register user
     */
    public function register($email, $password) {
        try {
            $response = $this->api->register($email, $password);
            
            // Store session
            $this->storeSession(
                $response['user']['id'],
                $response['session_token'],
                $response['user']['email']
            );

            return [
                'success' => true,
                'user' => $response['user'],
                'session_token' => $response['session_token'],
            ];
        } catch (Exception $e) {
            return [
                'success' => false,
                'error' => $e->getMessage(),
            ];
        }
    }

    /**
     * Login user
     */
    public function login($email, $password, $rememberMe = false) {
        try {
            $deviceId = $_SERVER['HTTP_USER_AGENT'] ?? 'web-browser';
            $deviceName = 'Web Browser';

            $response = $this->api->login($email, $password, $deviceId, $deviceName);
            
            // Store session
            $lifetime = $rememberMe ? SESSION_LIFETIME * 2 : SESSION_LIFETIME;
            $this->storeSession(
                $response['user']['id'],
                $response['session_token'],
                $response['user']['email'],
                $lifetime
            );

            return [
                'success' => true,
                'user' => $response['user'],
                'entitlement_token' => $response['entitlement_token'],
            ];
        } catch (Exception $e) {
            return [
                'success' => false,
                'error' => $e->getMessage(),
            ];
        }
    }

    /**
     * Request magic link
     */
    public function requestMagicLink($email) {
        try {
            $response = $this->api->requestMagicLink($email);
            return [
                'success' => true,
                'message' => $response['message'] ?? 'Magic link sent',
            ];
        } catch (Exception $e) {
            return [
                'success' => false,
                'error' => $e->getMessage(),
            ];
        }
    }

    /**
     * Verify magic link
     */
    public function verifyMagicLink($token) {
        try {
            $response = $this->api->verifyMagicLink($token);
            
            // Store session
            $this->storeSession(
                $response['user']['id'],
                $response['session_token'],
                $response['user']['email']
            );

            return [
                'success' => true,
                'user' => $response['user'],
                'entitlement_token' => $response['entitlement_token'],
            ];
        } catch (Exception $e) {
            return [
                'success' => false,
                'error' => $e->getMessage(),
            ];
        }
    }

    /**
     * Store session in database and PHP session
     */
    private function storeSession($userId, $token, $email, $lifetime = null) {
        $lifetime = $lifetime ?? SESSION_LIFETIME;
        $expiresAt = time() + $lifetime;

        // Store in database
        $this->db->createSession($userId, $token, $expiresAt);

        // Store in PHP session
        $_SESSION['user_id'] = $userId;
        $_SESSION['user_email'] = $email;
        $_SESSION['session_token'] = $token;
        $_SESSION['expires_at'] = $expiresAt;
    }

    /**
     * Check if user is logged in
     */
    public function isLoggedIn() {
        if (!isset($_SESSION['user_id']) || !isset($_SESSION['session_token'])) {
            return false;
        }

        // Check if session expired
        if (isset($_SESSION['expires_at']) && $_SESSION['expires_at'] < time()) {
            $this->logout();
            return false;
        }

        // Verify session in database
        $session = $this->db->getSessionByToken($_SESSION['session_token']);
        if (!$session) {
            $this->logout();
            return false;
        }

        return true;
    }

    /**
     * Logout user
     */
    public function logout() {
        if (isset($_SESSION['session_token'])) {
            $this->db->deleteSession($_SESSION['session_token']);
        }
        session_destroy();
    }

    /**
     * Get current session token
     */
    public function getSessionToken() {
        return $_SESSION['session_token'] ?? null;
    }

    /**
     * Get current user ID
     */
    public function getUserId() {
        return $_SESSION['user_id'] ?? null;
    }

    /**
     * Get current user email
     */
    public function getUserEmail() {
        return $_SESSION['user_email'] ?? null;
    }
}

