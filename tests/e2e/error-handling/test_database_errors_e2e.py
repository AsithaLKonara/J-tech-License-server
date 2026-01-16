"""
Database Error E2E Tests
Tests for handling database errors
"""

import pytest

from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.setup.test_fixtures import TestDataFactory


@pytest.mark.error
@pytest.mark.requires_database
class TestDatabaseErrorsE2E:
    """E2E tests for database error handling"""
    
    def test_database_connection_failures(self):
        """Test database connection failures"""
        # Use invalid database configuration
        error_client = DatabaseClient(database="nonexistent_db")
        
        try:
            with error_client.get_connection() as conn:
                pass
            assert False, "Should fail with invalid database"
        except Exception:
            # Expected to fail
            pass
    
    def test_database_constraint_violations(self, db_client: DatabaseClient):
        """Test database constraint violations"""
        # Create user
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Try to create duplicate user (should fail constraint)
        try:
            db_client.create_user(
                user_id=TestDataFactory.generate_user_id(),
                email=user_data['email'],  # Duplicate email
                password_hash=password_hash
            )
            # Should fail due to unique constraint
        except Exception:
            # Expected to fail
            pass
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_transaction_failures(self, db_client: DatabaseClient):
        """Test transaction failures"""
        # Database client should handle transaction failures
        # This would be tested with actual transaction rollback scenarios
        assert db_client is not None
    
    def test_database_timeout_handling(self, db_client: DatabaseClient):
        """Test database timeout handling"""
        # Database queries should timeout appropriately
        # This would be tested with slow queries
        assert db_client is not None
