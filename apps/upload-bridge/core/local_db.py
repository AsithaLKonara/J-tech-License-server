"""
Local SQLite Database for Desktop App
Stores session management and login details locally on the device
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class LocalDatabase:
    """
    Local SQLite database for storing:
    - User sessions
    - Login credentials (encrypted)
    - License cache
    - Device info
    - Offline license validation cache
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize local database
        
        Args:
            db_path: Path to SQLite database file
                    Default: ~/.upload_bridge/local.db
        """
        if db_path is None:
            db_dir = Path.home() / ".upload_bridge"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = db_dir / "local.db"
        
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Sessions table - stores active user sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    session_token TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    expires_at INTEGER,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            # Users table - stores user login information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    encrypted_credentials TEXT,
                    last_login INTEGER,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
            """)
            
            # License cache - stores license information for offline validation
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS license_cache (
                    id TEXT PRIMARY KEY,
                    license_jwt TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    device_fingerprint TEXT NOT NULL,
                    issued_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    cached_at INTEGER NOT NULL,
                    is_valid INTEGER DEFAULT 1,
                    last_validated INTEGER
                )
            """)
            
            # Device info - stores device information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS device_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_fingerprint TEXT UNIQUE NOT NULL,
                    device_name TEXT,
                    registered_at INTEGER NOT NULL,
                    last_seen INTEGER NOT NULL
                )
            """)
            
            # Offline validation log - tracks offline license validations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS validation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_id TEXT NOT NULL,
                    validated_at INTEGER NOT NULL,
                    was_valid INTEGER NOT NULL,
                    reason TEXT
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_is_active ON sessions(is_active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_license_cache_user_id ON license_cache(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_license_cache_expires_at ON license_cache(expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_validation_log_license_id ON validation_log(license_id)")
            
            conn.commit()
            logger.info(f"Local database initialized at {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
        try:
            yield conn
        finally:
            conn.close()
    
    # Session Management Methods
    
    def save_session(self, user_id: str, email: str, session_token: str = None,
                     access_token: str = None, refresh_token: str = None,
                     expires_at: Optional[int] = None):
        """Save or update user session"""
        now = int(datetime.now().timestamp())
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Deactivate old sessions for this user
            cursor.execute("""
                UPDATE sessions 
                SET is_active = 0, updated_at = ?
                WHERE user_id = ? AND is_active = 1
            """, (now, user_id))
            
            # Insert new session
            cursor.execute("""
                INSERT INTO sessions 
                (user_id, email, session_token, access_token, refresh_token, 
                 expires_at, created_at, updated_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (user_id, email, session_token, access_token, refresh_token,
                  expires_at, now, now))
            
            conn.commit()
            logger.debug(f"Session saved for user {user_id}")
    
    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """Get the most recent active session"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions 
                WHERE is_active = 1 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_session_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get active session for a specific user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions 
                WHERE user_id = ? AND is_active = 1 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def invalidate_session(self, user_id: Optional[str] = None):
        """Invalidate session(s)"""
        now = int(datetime.now().timestamp())
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("""
                    UPDATE sessions 
                    SET is_active = 0, updated_at = ?
                    WHERE user_id = ? AND is_active = 1
                """, (now, user_id))
            else:
                cursor.execute("""
                    UPDATE sessions 
                    SET is_active = 0, updated_at = ?
                    WHERE is_active = 1
                """, (now,))
            
            conn.commit()
            logger.debug(f"Sessions invalidated for user: {user_id or 'all'}")
    
    # User Management Methods
    
    def save_user(self, user_id: str, email: str, encrypted_credentials: Optional[str] = None):
        """Save or update user information"""
        now = int(datetime.now().timestamp())
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (id, email, encrypted_credentials, last_login, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    email = excluded.email,
                    encrypted_credentials = excluded.encrypted_credentials,
                    last_login = excluded.last_login,
                    updated_at = excluded.updated_at
            """, (user_id, email, encrypted_credentials, now, now, now))
            
            conn.commit()
            logger.debug(f"User saved: {user_id}")
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def update_last_login(self, user_id: str):
        """Update last login timestamp"""
        now = int(datetime.now().timestamp())
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET last_login = ?, updated_at = ?
                WHERE id = ?
            """, (now, now, user_id))
            
            conn.commit()
    
    # License Cache Methods
    
    def cache_license(self, license_id: str, license_jwt: str, user_id: str,
                     device_fingerprint: str, issued_at: int, expires_at: int):
        """Cache license for offline validation"""
        now = int(datetime.now().timestamp())
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO license_cache 
                (id, license_jwt, user_id, device_fingerprint, issued_at, expires_at, cached_at, is_valid, last_validated)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(id) DO UPDATE SET
                    license_jwt = excluded.license_jwt,
                    last_validated = excluded.last_validated,
                    is_valid = 1
            """, (license_id, license_jwt, user_id, device_fingerprint, 
                  issued_at, expires_at, now, now))
            
            conn.commit()
            logger.debug(f"License cached: {license_id}")
    
    def get_cached_license(self, license_id: str) -> Optional[Dict[str, Any]]:
        """Get cached license"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM license_cache 
                WHERE id = ? AND is_valid = 1
            """, (license_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_user_licenses(self, user_id: str) -> list:
        """Get all cached licenses for a user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM license_cache 
                WHERE user_id = ? AND is_valid = 1
                ORDER BY cached_at DESC
            """, (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def invalidate_license_cache(self, license_id: str):
        """Mark cached license as invalid"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE license_cache 
                SET is_valid = 0
                WHERE id = ?
            """, (license_id,))
            
            conn.commit()
    
    # Device Info Methods
    
    def save_device_info(self, device_fingerprint: str, device_name: Optional[str] = None):
        """Save or update device information"""
        now = int(datetime.now().timestamp())
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO device_info (device_fingerprint, device_name, registered_at, last_seen)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(device_fingerprint) DO UPDATE SET
                    device_name = excluded.device_name,
                    last_seen = excluded.last_seen
            """, (device_fingerprint, device_name, now, now))
            
            conn.commit()
    
    def get_device_info(self, device_fingerprint: str) -> Optional[Dict[str, Any]]:
        """Get device information"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM device_info WHERE device_fingerprint = ?", 
                         (device_fingerprint,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    # Validation Log Methods
    
    def log_validation(self, license_id: str, was_valid: bool, reason: Optional[str] = None):
        """Log license validation attempt"""
        now = int(datetime.now().timestamp())
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO validation_log (license_id, validated_at, was_valid, reason)
                VALUES (?, ?, ?, ?)
            """, (license_id, now, 1 if was_valid else 0, reason))
            
            conn.commit()
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data"""
        cutoff = int((datetime.now() - timedelta(days=days_to_keep)).timestamp())
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Clean old inactive sessions
            cursor.execute("DELETE FROM sessions WHERE is_active = 0 AND updated_at < ?", (cutoff,))
            
            # Clean old validation logs
            cursor.execute("DELETE FROM validation_log WHERE validated_at < ?", (cutoff,))
            
            # Clean expired license cache
            cursor.execute("DELETE FROM license_cache WHERE expires_at < ?", (cutoff,))
            
            conn.commit()
            logger.info(f"Cleaned up data older than {days_to_keep} days")
