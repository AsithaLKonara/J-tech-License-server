"""
Socket and connection cleanup utilities.

Ensures proper cleanup of network sockets and connections
to prevent resource leaks.
"""

import socket
import logging
from typing import Optional, List
import weakref
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class SocketManager:
    """Manages socket lifecycle and cleanup"""
    
    # Global registry of active sockets
    _sockets: List[weakref.ref] = []
    
    @classmethod
    def register_socket(cls, sock: socket.socket) -> None:
        """
        Register a socket for tracking.
        
        Args:
            sock: Socket to register
        """
        # Use weak reference to avoid keeping sockets alive
        cls._sockets.append(weakref.ref(sock))
        logger.debug(f"Registered socket: {sock.getpeername() if sock.getpeername() else 'unknown'}")
    
    @classmethod
    def unregister_socket(cls, sock: socket.socket) -> None:
        """
        Unregister a socket.
        
        Args:
            sock: Socket to unregister
        """
        cls._sockets = [ref for ref in cls._sockets if ref() is not None and ref() != sock]
        logger.debug("Unregistered socket")
    
    @classmethod
    def cleanup_all(cls) -> int:
        """
        Clean up all tracked sockets.
        
        Returns:
            Number of sockets cleaned up
        """
        cleaned = 0
        
        for socket_ref in cls._sockets:
            sock = socket_ref()
            if sock is not None:
                try:
                    sock.close()
                    cleaned += 1
                    logger.debug("Cleaned up socket")
                except Exception as e:
                    logger.warning(f"Error closing socket: {e}")
        
        cls._sockets.clear()
        return cleaned


class ConnectionPool:
    """Manages a pool of connections with proper cleanup"""
    
    def __init__(self, max_size: int = 10):
        """
        Initialize connection pool.
        
        Args:
            max_size: Maximum number of connections
        """
        self.max_size = max_size
        self.connections: List[socket.socket] = []
        self.active_connections: List[socket.socket] = []
    
    def get_connection(self, host: str, port: int, timeout: float = 5.0) -> Optional[socket.socket]:
        """
        Get a connection from the pool or create new.
        
        Args:
            host: Host address
            port: Port number
            timeout: Connection timeout
        
        Returns:
            Socket connection or None on failure
        """
        # Try to reuse existing connection
        if self.connections:
            try:
                sock = self.connections.pop(0)
                # Verify connection is still alive
                sock.send(b'')
                self.active_connections.append(sock)
                return sock
            except (socket.error, OSError):
                # Connection is dead, close it
                try:
                    sock.close()
                except:
                    pass
        
        # Create new connection
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            
            SocketManager.register_socket(sock)
            self.active_connections.append(sock)
            
            logger.debug(f"Created new connection to {host}:{port}")
            return sock
        
        except (socket.error, OSError) as e:
            logger.error(f"Failed to connect to {host}:{port}: {e}")
            return None
    
    def return_connection(self, sock: socket.socket) -> None:
        """
        Return a connection to the pool.
        
        Args:
            sock: Socket to return
        """
        try:
            if sock in self.active_connections:
                self.active_connections.remove(sock)
            
            if len(self.connections) < self.max_size:
                self.connections.append(sock)
                logger.debug("Returned connection to pool")
            else:
                sock.close()
                SocketManager.unregister_socket(sock)
                logger.debug("Closed excess connection")
        
        except Exception as e:
            logger.error(f"Error returning connection: {e}")
            try:
                sock.close()
            except:
                pass
    
    def cleanup(self) -> int:
        """
        Clean up all connections in pool.
        
        Returns:
            Number of connections closed
        """
        closed = 0
        
        # Close pooled connections
        for sock in self.connections:
            try:
                sock.close()
                SocketManager.unregister_socket(sock)
                closed += 1
            except Exception as e:
                logger.warning(f"Error closing pooled connection: {e}")
        
        self.connections.clear()
        
        # Close active connections
        for sock in self.active_connections:
            try:
                sock.close()
                SocketManager.unregister_socket(sock)
                closed += 1
            except Exception as e:
                logger.warning(f"Error closing active connection: {e}")
        
        self.active_connections.clear()
        
        return closed


@contextmanager
def managed_socket(host: str, port: int, timeout: float = 5.0):
    """
    Context manager for socket connections.
    
    Ensures socket is properly closed even on exception.
    
    Args:
        host: Host address
        port: Port number
        timeout: Connection timeout
    
    Yields:
        Socket connection
    """
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        
        SocketManager.register_socket(sock)
        
        logger.debug(f"Connected to {host}:{port}")
        yield sock
    
    except (socket.error, OSError) as e:
        logger.error(f"Socket connection error: {e}")
        raise
    
    finally:
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except (socket.error, OSError):
                pass
            
            try:
                sock.close()
                SocketManager.unregister_socket(sock)
                logger.debug("Socket closed and cleaned up")
            except (socket.error, OSError) as e:
                logger.warning(f"Error closing socket: {e}")


class SafeSocketOperation:
    """Wrapper for safe socket operations with cleanup"""
    
    @staticmethod
    def send_data(sock: socket.socket, data: bytes, timeout: float = 5.0) -> bool:
        """
        Safely send data over socket.
        
        Args:
            sock: Socket to send on
            data: Data to send
            timeout: Operation timeout
        
        Returns:
            True if successful
        """
        try:
            sock.settimeout(timeout)
            sock.sendall(data)
            logger.debug(f"Sent {len(data)} bytes")
            return True
        
        except socket.timeout:
            logger.error("Send operation timed out")
            return False
        
        except (socket.error, OSError) as e:
            logger.error(f"Send error: {e}")
            return False
    
    @staticmethod
    def receive_data(sock: socket.socket, buffer_size: int = 4096, 
                    timeout: float = 5.0) -> Optional[bytes]:
        """
        Safely receive data from socket.
        
        Args:
            sock: Socket to receive from
            buffer_size: Size of receive buffer
            timeout: Operation timeout
        
        Returns:
            Received data or None on error
        """
        try:
            sock.settimeout(timeout)
            data = sock.recv(buffer_size)
            
            if not data:
                logger.debug("Connection closed by peer")
                return None
            
            logger.debug(f"Received {len(data)} bytes")
            return data
        
        except socket.timeout:
            logger.error("Receive operation timed out")
            return None
        
        except (socket.error, OSError) as e:
            logger.error(f"Receive error: {e}")
            return None


class ConnectionCleanupHandler:
    """Handles cleanup of connections on shutdown"""
    
    _pools: List[ConnectionPool] = []
    
    @classmethod
    def register_pool(cls, pool: ConnectionPool) -> None:
        """Register a connection pool for cleanup"""
        cls._pools.append(pool)
    
    @classmethod
    def cleanup_all_pools(cls) -> int:
        """
        Clean up all registered pools.
        
        Returns:
            Total connections closed
        """
        total_closed = 0
        
        for pool in cls._pools:
            closed = pool.cleanup()
            total_closed += closed
        
        cls._pools.clear()
        
        logger.info(f"Cleaned up {total_closed} connections from pools")
        return total_closed
    
    @classmethod
    def cleanup_all(cls) -> int:
        """
        Clean up all sockets and pools.
        
        Returns:
            Total connections closed
        """
        # Cleanup pools first
        total_closed = cls.cleanup_all_pools()
        
        # Then cleanup any remaining sockets
        socket_closed = SocketManager.cleanup_all()
        total_closed += socket_closed
        
        logger.info(f"Total cleanup: {total_closed} connections closed")
        return total_closed
