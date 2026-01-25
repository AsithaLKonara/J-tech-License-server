<?php
/**
 * Helper Functions
 * Common utility functions used across the application
 */

/**
 * Escape HTML output to prevent XSS
 */
function escape($string) {
    return htmlspecialchars($string, ENT_QUOTES, 'UTF-8');
}

/**
 * Generate CSRF token
 */
function generateCSRFToken() {
    if (!isset($_SESSION[CSRF_TOKEN_NAME])) {
        $_SESSION[CSRF_TOKEN_NAME] = bin2hex(random_bytes(32));
    }
    return $_SESSION[CSRF_TOKEN_NAME];
}

/**
 * Verify CSRF token
 */
function verifyCSRFToken($token) {
    return isset($_SESSION[CSRF_TOKEN_NAME]) && hash_equals($_SESSION[CSRF_TOKEN_NAME], $token);
}

/**
 * Check if user is logged in
 */
function isLoggedIn() {
    return isset($_SESSION['user_id']) && isset($_SESSION['session_token']);
}

/**
 * Require login - redirect if not logged in
 */
function requireLogin() {
    if (!isLoggedIn()) {
        header('Location: /login');
        exit;
    }
}

/**
 * Get current user ID
 */
function getCurrentUserId() {
    return $_SESSION['user_id'] ?? null;
}

/**
 * Get current user email
 */
function getCurrentUserEmail() {
    return $_SESSION['user_email'] ?? null;
}

/**
 * Format date
 */
function formatDate($timestamp, $format = 'Y-m-d H:i:s') {
    return date($format, $timestamp);
}

/**
 * Format currency
 */
function formatCurrency($amount, $currency = 'USD') {
    return '$' . number_format($amount, 2);
}

/**
 * Redirect with message
 */
function redirect($url, $message = null) {
    if ($message) {
        $_SESSION['flash_message'] = $message;
    }
    header("Location: $url");
    exit;
}

/**
 * Get and clear flash message
 */
function getFlashMessage() {
    if (isset($_SESSION['flash_message'])) {
        $message = $_SESSION['flash_message'];
        unset($_SESSION['flash_message']);
        return $message;
    }
    return null;
}

/**
 * JSON response
 */
function jsonResponse($data, $statusCode = 200) {
    http_response_code($statusCode);
    header('Content-Type: application/json');
    echo json_encode($data);
    exit;
}

/**
 * Error response
 */
function errorResponse($message, $statusCode = 400) {
    jsonResponse(['error' => $message], $statusCode);
}

/**
 * Success response
 */
function successResponse($data = [], $message = null) {
    $response = ['success' => true];
    if ($message) {
        $response['message'] = $message;
    }
    if ($data) {
        $response['data'] = $data;
    }
    jsonResponse($response);
}

