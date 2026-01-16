"""
Connection Pooling for WiFi Upload
Provides efficient HTTP session management with connection reuse
"""

import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WiFiSessionPool:
    """
    Manages persistent HTTP sessions for WiFi uploads.
    
    Features:
    - Connection reuse (reduces TCP overhead)
    - Automatic session cleanup on timeout
    - Per-device session isolation
    - Connection pool limits
    """
    
    def __init__(self, max_sessions: int = 10, session_timeout_minutes: int = 30):
        """
        Initialize session pool.
        
        Args:
            max_sessions: Maximum number of concurrent sessions
            session_timeout_minutes: Session idle timeout in minutes
        """
        self.max_sessions = max_sessions
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info(
            f"WiFi session pool initialized: "
            f"max {max_sessions} sessions, "
            f"timeout {session_timeout_minutes}min"
        )
    
    def _cleanup_session(self, device_id: str) -> None:
        """
        Clean up a session.
        
        Args:
            device_id: Device identifier
        """
        if device_id in self.sessions:
            session_info = self.sessions[device_id]
            try:
                session_info['session'].close()
                logger.debug(f"Closed session for device {device_id}")
            except Exception as e:
                logger.warning(f"Error closing session for {device_id}: {e}")
            
            del self.sessions[device_id]
    
    def _cleanup_expired(self) -> None:
        """Remove expired sessions"""
        now = datetime.now()
        expired = [
            device_id for device_id, info in self.sessions.items()
            if now - info['last_used'] > self.session_timeout
        ]
        
        for device_id in expired:
            logger.info(f"Removing expired session for {device_id}")
            self._cleanup_session(device_id)
    
    def get_session(self, device_id: str) -> requests.Session:
        """
        Get or create a session for a device.
        
        Args:
            device_id: Device identifier (IP:port or hostname)
        
        Returns:
            requests.Session instance for the device
        """
        # Cleanup expired sessions
        self._cleanup_expired()
        
        # Check if session exists
        if device_id in self.sessions:
            session_info = self.sessions[device_id]
            session_info['last_used'] = datetime.now()
            logger.debug(f"Reusing session for device {device_id}")
            return session_info['session']
        
        # Check if we can create new session
        if len(self.sessions) >= self.max_sessions:
            logger.warning(
                f"Session pool at capacity ({len(self.sessions)}/{self.max_sessions}). "
                f"Removing least recently used session."
            )
            # Remove least recently used session
            lru_device = min(
                self.sessions.keys(),
                key=lambda d: self.sessions[d]['last_used']
            )
            self._cleanup_session(lru_device)
        
        # Create new session
        logger.info(f"Creating new session for device {device_id}")
        session = requests.Session()
        
        # Configure session
        session.headers.update({
            'User-Agent': 'UploadBridge/3.0',
            'Connection': 'keep-alive'
        })
        
        # Store session info
        self.sessions[device_id] = {
            'session': session,
            'created': datetime.now(),
            'last_used': datetime.now(),
            'request_count': 0
        }
        
        return session
    
    def record_request(self, device_id: str) -> None:
        """
        Record a request for statistics.
        
        Args:
            device_id: Device identifier
        """
        if device_id in self.sessions:
            self.sessions[device_id]['request_count'] += 1
    
    def close_session(self, device_id: str) -> None:
        """
        Explicitly close a session.
        
        Args:
            device_id: Device identifier
        """
        if device_id in self.sessions:
            logger.info(f"Explicitly closing session for {device_id}")
            self._cleanup_session(device_id)
    
    def close_all(self) -> None:
        """Close all sessions"""
        logger.info(f"Closing all {len(self.sessions)} sessions")
        for device_id in list(self.sessions.keys()):
            self._cleanup_session(device_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get session pool statistics.
        
        Returns:
            Dictionary with pool statistics
        """
        stats = {
            'active_sessions': len(self.sessions),
            'max_sessions': self.max_sessions,
            'devices': {}
        }
        
        for device_id, info in self.sessions.items():
            elapsed = (datetime.now() - info['created']).total_seconds()
            stats['devices'][device_id] = {
                'requests': info['request_count'],
                'age_seconds': int(elapsed),
                'idle_seconds': int((datetime.now() - info['last_used']).total_seconds())
            }
        
        return stats


class PooledWiFiClient:
    """
    WiFi client using connection pooling for efficient requests.
    """
    
    def __init__(self, device_id: str, session_pool: Optional[WiFiSessionPool] = None):
        """
        Initialize pooled WiFi client.
        
        Args:
            device_id: Device identifier (IP:port format)
            session_pool: Optional session pool to use
        """
        self.device_id = device_id
        self.session_pool = session_pool or WiFiSessionPool()
    
    def get(self, endpoint: str, timeout: float = 10.0, **kwargs) -> Optional[requests.Response]:
        """
        Perform GET request using pooled session.
        
        Args:
            endpoint: API endpoint (e.g., '/api/status')
            timeout: Request timeout in seconds
            **kwargs: Additional arguments for requests
        
        Returns:
            Response object or None on error
        """
        try:
            session = self.session_pool.get_session(self.device_id)
            url = f"http://{self.device_id}{endpoint}"
            
            response = session.get(url, timeout=timeout, **kwargs)
            self.session_pool.record_request(self.device_id)
            
            logger.debug(f"GET {endpoint} -> {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"GET {endpoint} failed: {e}")
            return None
    
    def post(self, endpoint: str, timeout: float = 10.0, **kwargs) -> Optional[requests.Response]:
        """
        Perform POST request using pooled session.
        
        Args:
            endpoint: API endpoint (e.g., '/api/upload')
            timeout: Request timeout in seconds
            **kwargs: Additional arguments for requests
        
        Returns:
            Response object or None on error
        """
        try:
            session = self.session_pool.get_session(self.device_id)
            url = f"http://{self.device_id}{endpoint}"
            
            response = session.post(url, timeout=timeout, **kwargs)
            self.session_pool.record_request(self.device_id)
            
            logger.debug(f"POST {endpoint} -> {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"POST {endpoint} failed: {e}")
            return None
    
    def close(self) -> None:
        """Close this client's session"""
        self.session_pool.close_session(self.device_id)
