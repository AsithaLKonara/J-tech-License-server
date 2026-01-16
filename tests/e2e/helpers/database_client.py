"""
Database Client Helper for E2E Tests
Provides database connection and query helpers for testing
"""

try:
    import mysql.connector
    from mysql.connector import Error, pooling
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    # Create dummy classes for when mysql-connector is not available
    class Error(Exception):
        pass
    class pooling:
        class MySQLConnectionPool:
            pass

from typing import Optional, Dict, Any, List, Tuple
import logging
from contextlib import contextmanager

from tests.e2e.test_config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    USE_TEST_DATABASE
)

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Database client for E2E tests"""
    
    _connection_pool: Optional[pooling.MySQLConnectionPool] = None
    
    def __init__(self, database: Optional[str] = None):
        self.database = database or DB_NAME
        self.host = DB_HOST
        self.port = DB_PORT
        self.user = DB_USER
        self.password = DB_PASSWORD
    
    @classmethod
    def get_connection_pool(cls) -> pooling.MySQLConnectionPool:
        """Get or create connection pool"""
        if not MYSQL_AVAILABLE:
            raise ImportError("mysql-connector-python is not installed. Install it with: pip install mysql-connector-python")
        
        if cls._connection_pool is None:
            try:
                cls._connection_pool = pooling.MySQLConnectionPool(
                    pool_name="e2e_test_pool",
                    pool_size=5,
                    pool_reset_session=True,
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME if USE_TEST_DATABASE else None,
                    autocommit=False
                )
                logger.info("Database connection pool created")
            except Error as e:
                logger.error(f"Error creating connection pool: {e}")
                raise
        return cls._connection_pool
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool"""
        pool = self.get_connection_pool()
        connection = pool.get_connection()
        try:
            yield connection
        finally:
            connection.close()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                return results
            finally:
                cursor.close()
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.rowcount
            except Error as e:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = %s"
        results = self.execute_query(query, (email,))
        return results[0] if results else None
    
    def create_user(self, user_id: str, email: str, password_hash: str, 
                   name: Optional[str] = None, is_admin: bool = False) -> bool:
        """Create test user"""
        try:
            query = """
                INSERT INTO users (id, email, password, name, is_admin, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """
            self.execute_update(query, (user_id, email, password_hash, name, is_admin))
            return True
        except Error as e:
            logger.error(f"Error creating user: {e}")
            return False
    
    def delete_user(self, email: str) -> bool:
        """Delete user by email"""
        try:
            query = "DELETE FROM users WHERE email = %s"
            self.execute_update(query, (email,))
            return True
        except Error as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    def get_entitlement(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get active entitlement for user"""
        query = """
            SELECT * FROM entitlements 
            WHERE user_id = %s AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        """
        results = self.execute_query(query, (user_id,))
        return results[0] if results else None
    
    def create_entitlement(self, entitlement_id: str, user_id: str, plan: str = 'trial',
                          status: str = 'active', max_devices: int = 1) -> bool:
        """Create test entitlement"""
        try:
            query = """
                INSERT INTO entitlements 
                (id, user_id, product_id, plan, status, features, max_devices, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            self.execute_update(query, (
                entitlement_id, user_id, 'upload-bridge', plan, status, '[]', max_devices
            ))
            return True
        except Error as e:
            logger.error(f"Error creating entitlement: {e}")
            return False
    
    def delete_entitlement(self, entitlement_id: str) -> bool:
        """Delete entitlement"""
        try:
            query = "DELETE FROM entitlements WHERE id = %s"
            self.execute_update(query, (entitlement_id,))
            return True
        except Error as e:
            logger.error(f"Error deleting entitlement: {e}")
            return False
    
    def get_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """Get devices for user"""
        query = "SELECT * FROM devices WHERE user_id = %s"
        return self.execute_query(query, (user_id,))
    
    def create_device(self, user_id: str, device_id: str, device_name: str,
                     entitlement_id: Optional[str] = None) -> bool:
        """Create test device"""
        try:
            query = """
                INSERT INTO devices (user_id, device_id, device_name, entitlement_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """
            self.execute_update(query, (user_id, device_id, device_name, entitlement_id))
            return True
        except Error as e:
            logger.error(f"Error creating device: {e}")
            return False
    
    def delete_device(self, device_id: str) -> bool:
        """Delete device"""
        try:
            query = "DELETE FROM devices WHERE device_id = %s"
            self.execute_update(query, (device_id,))
            return True
        except Error as e:
            logger.error(f"Error deleting device: {e}")
            return False
    
    def cleanup_test_data(self, email: str):
        """Cleanup all test data for a user"""
        user = self.get_user(email)
        if user:
            user_id = user['id']
            # Delete devices
            devices = self.get_devices(user_id)
            for device in devices:
                self.delete_device(device['device_id'])
            # Delete entitlements
            entitlements = self.execute_query(
                "SELECT id FROM entitlements WHERE user_id = %s", (user_id,)
            )
            for ent in entitlements:
                self.delete_entitlement(ent['id'])
            # Delete user
            self.delete_user(email)
            logger.info(f"Cleaned up test data for {email}")
    
    def verify_data_consistency(self, user_id: str) -> Tuple[bool, List[str]]:
        """Verify data consistency for a user"""
        issues = []
        
        # Check user exists
        user = self.execute_query("SELECT * FROM users WHERE id = %s", (user_id,))
        if not user:
            issues.append("User does not exist")
            return False, issues
        
        # Check entitlements
        entitlements = self.execute_query(
            "SELECT * FROM entitlements WHERE user_id = %s", (user_id,)
        )
        if not entitlements:
            issues.append("No entitlements found for user")
        
        # Check devices
        devices = self.get_devices(user_id)
        active_entitlement = self.get_entitlement(user_id)
        if active_entitlement:
            max_devices = active_entitlement.get('max_devices', 1)
            if len(devices) > max_devices:
                issues.append(f"Device count ({len(devices)}) exceeds max ({max_devices})")
        
        return len(issues) == 0, issues
