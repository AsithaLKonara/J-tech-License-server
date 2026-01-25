<?php
/**
 * Configuration File
 * Database and application settings
 */

// Database Configuration
define('DB_TYPE', 'sqlite'); // 'sqlite' or 'mysql'
define('DB_PATH', __DIR__ . '/../data/dashboard.db'); // SQLite path
// For MySQL, uncomment and configure:
// define('DB_HOST', 'localhost');
// define('DB_NAME', 'dashboard');
// define('DB_USER', 'username');
// define('DB_PASS', 'password');

// License Server API
define('LICENSE_SERVER_URL', 'https://j-tech-license-server-production.up.railway.app');
// Or use Vercel URL if deployed there:
// define('LICENSE_SERVER_URL', 'https://your-project.vercel.app');

// Application Settings
define('APP_NAME', 'Upload Bridge');
define('APP_URL', 'https://your-domain.com'); // Update with your domain
define('SESSION_LIFETIME', 86400 * 7); // 7 days

// Security
define('CSRF_TOKEN_NAME', 'csrf_token');
define('SESSION_NAME', 'upload_bridge_session');

// Paths
define('BASE_PATH', dirname(__DIR__));
define('INCLUDES_PATH', __DIR__);
define('ASSETS_PATH', BASE_PATH . '/assets');

// Error Reporting (set to 0 in production)
error_reporting(E_ALL);
ini_set('display_errors', 0); // Set to 0 in production

// Timezone
date_default_timezone_set('UTC');

