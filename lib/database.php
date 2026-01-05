<?php
/**
 * Database Class
 * Handles database operations with SQLite/MySQL support
 */

require_once __DIR__ . '/../includes/config.php';

class Database {
    private $db;
    private $type;

    public function __construct() {
        $this->type = DB_TYPE;
        $this->connect();
        $this->initialize();
    }

    private function connect() {
        if ($this->type === 'sqlite') {
            // Create data directory if it doesn't exist
            $dataDir = dirname(DB_PATH);
            if (!is_dir($dataDir)) {
                mkdir($dataDir, 0755, true);
            }
            $this->db = new PDO('sqlite:' . DB_PATH);
            $this->db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        } else {
            // MySQL connection
            $dsn = "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4";
            $this->db = new PDO($dsn, DB_USER, DB_PASS);
            $this->db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        }
    }

    private function initialize() {
        // Create sessions table
        $this->db->exec("
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                created_at INTEGER NOT NULL
            )
        ");

        // Create index
        $this->db->exec("
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)
        ");
        $this->db->exec("
            CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)
        ");
    }

    /**
     * Create session
     */
    public function createSession($userId, $token, $expiresAt) {
        $id = uniqid('session_', true);
        $stmt = $this->db->prepare("
            INSERT INTO sessions (id, user_id, token, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
        ");
        $stmt->execute([$id, $userId, $token, $expiresAt, time()]);
        return $id;
    }

    /**
     * Get session by token
     */
    public function getSessionByToken($token) {
        $stmt = $this->db->prepare("
            SELECT * FROM sessions 
            WHERE token = ? AND expires_at > ?
        ");
        $stmt->execute([$token, time()]);
        return $stmt->fetch(PDO::FETCH_ASSOC);
    }

    /**
     * Delete session
     */
    public function deleteSession($token) {
        $stmt = $this->db->prepare("DELETE FROM sessions WHERE token = ?");
        return $stmt->execute([$token]);
    }

    /**
     * Clean expired sessions
     */
    public function cleanExpiredSessions() {
        $stmt = $this->db->prepare("DELETE FROM sessions WHERE expires_at < ?");
        return $stmt->execute([time()]);
    }

    /**
     * Get PDO instance
     */
    public function getPDO() {
        return $this->db;
    }
}

