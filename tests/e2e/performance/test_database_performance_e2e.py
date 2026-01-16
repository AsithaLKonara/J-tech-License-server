"""
Database Performance E2E Tests
Tests for database query performance
"""

import pytest
import time

from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.test_config import DB_QUERY_TIME_THRESHOLD
from tests.e2e.setup.test_fixtures import TestDataFactory


@pytest.mark.performance
@pytest.mark.requires_database
class TestDatabasePerformanceE2E:
    """E2E tests for database performance"""
    
    def test_database_query_performance(self, db_client: DatabaseClient):
        """Test database query performance"""
        # Create test user
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Measure query time
        start_time = time.time()
        user = db_client.get_user(user_data['email'])
        query_time = time.time() - start_time
        
        assert user is not None
        assert query_time < DB_QUERY_TIME_THRESHOLD * 2, \
            f"Query time {query_time}s exceeds threshold"
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_database_connection_pooling(self, db_client: DatabaseClient):
        """Test database connection pooling"""
        # Make multiple queries (should use connection pool)
        start_time = time.time()
        for _ in range(10):
            with db_client.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
        total_time = time.time() - start_time
        
        # Should be fast with connection pooling
        assert total_time < 1, f"Connection pooling test took {total_time}s"
    
    def test_database_transaction_performance(self, db_client: DatabaseClient):
        """Test database transaction performance"""
        # Create user in transaction
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        
        start_time = time.time()
        success = db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        transaction_time = time.time() - start_time
        
        assert success
        assert transaction_time < DB_QUERY_TIME_THRESHOLD * 3, \
            f"Transaction time {transaction_time}s exceeds threshold"
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
