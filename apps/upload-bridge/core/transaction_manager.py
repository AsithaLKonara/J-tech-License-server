"""
Transaction management utilities for safe database operations.

This module provides context managers and helpers for handling
database transactions with proper rollback on errors.
"""

import logging
from contextlib import contextmanager
from typing import Any, Callable, Optional, TypeVar, Generic
import threading


T = TypeVar('T')
logger = logging.getLogger(__name__)


class TransactionError(Exception):
    """Raised when a transaction operation fails"""
    pass


class DatabaseConnection:
    """Mock database connection interface for type hints"""
    
    def begin(self) -> None:
        """Begin a transaction"""
        raise NotImplementedError
    
    def commit(self) -> None:
        """Commit the transaction"""
        raise NotImplementedError
    
    def rollback(self) -> None:
        """Rollback the transaction"""
        raise NotImplementedError
    
    def close(self) -> None:
        """Close the connection"""
        raise NotImplementedError


class TransactionManager:
    """Manages database transactions with automatic rollback"""
    
    def __init__(self, connection: DatabaseConnection):
        """
        Initialize transaction manager.
        
        Args:
            connection: Database connection object
        """
        self.connection = connection
        self._lock = threading.Lock()
        self._transaction_depth = 0
    
    @contextmanager
    def transaction(self, name: str = "transaction"):
        """
        Context manager for database transactions.
        
        Automatically commits on success, rolls back on exception.
        
        Example:
            with manager.transaction("create_user"):
                user_id = insert_user({"name": "John"})
                insert_profile(user_id, {"bio": "..."})
        
        Args:
            name: Optional name for the transaction (for logging)
        
        Yields:
            Database connection object
        
        Raises:
            TransactionError: If transaction fails
        """
        with self._lock:
            self._transaction_depth += 1
            is_root_transaction = self._transaction_depth == 1
        
        if is_root_transaction:
            try:
                logger.debug(f"Starting transaction: {name}")
                self.connection.begin()
            except Exception as e:
                logger.error(f"Failed to begin transaction {name}: {e}", exc_info=True)
                raise TransactionError(f"Could not start transaction: {e}") from e
        
        try:
            yield self.connection
            
            if is_root_transaction:
                logger.debug(f"Committing transaction: {name}")
                self.connection.commit()
                logger.info(f"Transaction committed: {name}")
        
        except Exception as e:
            if is_root_transaction:
                try:
                    logger.warning(f"Rolling back transaction {name}: {e}")
                    self.connection.rollback()
                    logger.info(f"Transaction rolled back: {name}")
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback transaction {name}: {rollback_error}", exc_info=True)
                    raise TransactionError(f"Failed to rollback transaction: {rollback_error}") from rollback_error
            
            raise TransactionError(f"Transaction {name} failed: {e}") from e
        
        finally:
            with self._lock:
                self._transaction_depth -= 1


@contextmanager
def safe_transaction(connection: DatabaseConnection, name: str = "transaction"):
    """
    Simplified context manager for transactions.
    
    Args:
        connection: Database connection object
        name: Optional name for the transaction (for logging)
    
    Yields:
        Database connection object
    """
    manager = TransactionManager(connection)
    with manager.transaction(name):
        yield connection


class BatchTransactionManager:
    """Manages multiple transactions with batching and error handling"""
    
    def __init__(self, connection: DatabaseConnection, batch_size: int = 100):
        """
        Initialize batch transaction manager.
        
        Args:
            connection: Database connection object
            batch_size: Number of operations per batch
        """
        self.connection = connection
        self.batch_size = batch_size
        self._operations = []
        self._lock = threading.Lock()
    
    def add_operation(self, operation: Callable[[], Any]) -> None:
        """
        Add an operation to the batch.
        
        Args:
            operation: Callable that performs the operation
        """
        with self._lock:
            self._operations.append(operation)
    
    def execute_batch(self, name: str = "batch_transaction") -> int:
        """
        Execute all batched operations in transactions.
        
        Args:
            name: Name for the transaction
        
        Returns:
            Number of operations successfully executed
        
        Raises:
            TransactionError: If batch execution fails
        """
        manager = TransactionManager(self.connection)
        executed = 0
        
        with self._lock:
            operations = self._operations.copy()
            self._operations.clear()
        
        # Execute in batches
        for i in range(0, len(operations), self.batch_size):
            batch = operations[i:i + self.batch_size]
            batch_name = f"{name}_batch_{i // self.batch_size + 1}"
            
            try:
                with manager.transaction(batch_name):
                    for operation in batch:
                        operation()
                        executed += 1
            except TransactionError as e:
                logger.error(f"Batch transaction failed: {batch_name}")
                # Attempt to continue with remaining batches
                continue
        
        logger.info(f"Batch execution completed: {executed}/{len(operations)} operations")
        return executed


def validate_transaction_state(connection: DatabaseConnection) -> bool:
    """
    Validate that the connection is in a valid transaction state.
    
    Args:
        connection: Database connection to validate
    
    Returns:
        True if connection is valid, False otherwise
    """
    try:
        if not connection:
            logger.warning("Connection is None")
            return False
        
        # Check if connection has required methods
        required_methods = ['begin', 'commit', 'rollback']
        for method in required_methods:
            if not hasattr(connection, method):
                logger.warning(f"Connection missing required method: {method}")
                return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error validating transaction state: {e}")
        return False
