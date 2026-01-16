"""
Testing utilities for comprehensive test coverage.

Provides helpers for:
- Exception path testing
- File cleanup testing
- Concurrent operation testing
- Input validation testing
- Edge case handling
"""

import pytest
import tempfile
from pathlib import Path
from typing import Optional, Callable, Any
import threading
import time


class ExceptionTestHelper:
    """Helper for testing exception paths"""
    
    @staticmethod
    def assert_exception_logged(caplog, exception_type: type, message_part: str = ""):
        """
        Assert that an exception was logged.
        
        Args:
            caplog: pytest caplog fixture
            exception_type: Expected exception type
            message_part: Optional part of message to search for
        """
        assert any(
            exception_type.__name__ in record.message or message_part in record.message
            for record in caplog.records
            if record.levelname == 'ERROR'
        ), f"Expected exception {exception_type.__name__} not found in logs"
    
    @staticmethod
    def assert_cleanup_on_exception(func: Callable, cleanup_check: Callable, *args, **kwargs):
        """
        Assert that cleanup occurs even on exception.
        
        Args:
            func: Function that should raise exception
            cleanup_check: Function to check cleanup occurred
            *args: Arguments for func
            **kwargs: Keyword arguments for func
        """
        try:
            func(*args, **kwargs)
        except Exception:
            pass  # Expected
        
        assert cleanup_check(), "Cleanup did not occur on exception"


class FileTestHelper:
    """Helper for file-based tests"""
    
    @staticmethod
    def create_test_file(size_bytes: int = 1024) -> Path:
        """
        Create a test file.
        
        Args:
            size_bytes: Size of file to create
        
        Returns:
            Path to created file
        """
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'x' * size_bytes)
            return Path(f.name)
    
    @staticmethod
    def assert_file_cleanup(file_path: Path):
        """
        Assert that a file was cleaned up.
        
        Args:
            file_path: Path to file that should be deleted
        """
        assert not file_path.exists(), f"File was not cleaned up: {file_path}"
    
    @staticmethod
    def assert_temp_files_cleaned(before_count: int, after_cleanup_check: Callable) -> bool:
        """
        Assert that temp files were cleaned up.
        
        Args:
            before_count: Number of temp files before operation
            after_cleanup_check: Function to check temp files after
        
        Returns:
            True if cleaned up properly
        """
        after_count = after_cleanup_check()
        return after_count <= before_count


class ConcurrencyTestHelper:
    """Helper for testing concurrent operations"""
    
    @staticmethod
    def run_concurrent(func: Callable, args_list: list, num_threads: Optional[int] = None):
        """
        Run function concurrently in multiple threads.
        
        Args:
            func: Function to run
            args_list: List of argument tuples
            num_threads: Number of threads (defaults to len(args_list))
        
        Returns:
            List of results
        """
        if num_threads is None:
            num_threads = len(args_list)
        
        results = [None] * len(args_list)
        errors = [None] * len(args_list)
        threads = []
        
        def worker(index: int, args):
            try:
                results[index] = func(*args)
            except Exception as e:
                errors[index] = e
        
        for index, args in enumerate(args_list):
            thread = threading.Thread(target=worker, args=(index, args))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Check for errors
        for error in errors:
            if error:
                raise error
        
        return results
    
    @staticmethod
    def assert_thread_safe(func: Callable, args_list: list, iterations: int = 10):
        """
        Assert that a function is thread-safe.
        
        Args:
            func: Function to test
            args_list: List of argument tuples
            iterations: Number of iterations to test
        """
        for _ in range(iterations):
            results = ConcurrencyTestHelper.run_concurrent(func, args_list)
            assert all(r is not None for r in results), "Some concurrent operations failed"


class ValidationTestHelper:
    """Helper for testing input validation"""
    
    @staticmethod
    def assert_validation_error(func: Callable, invalid_input: Any, 
                               expected_exception: type = ValueError):
        """
        Assert that invalid input raises exception.
        
        Args:
            func: Function to test
            invalid_input: Invalid input to pass
            expected_exception: Expected exception type
        """
        with pytest.raises(expected_exception):
            func(invalid_input)
    
    @staticmethod
    def assert_edge_cases(func: Callable, test_cases: dict):
        """
        Assert that function handles edge cases.
        
        Args:
            func: Function to test
            test_cases: Dict of {input: expected_output}
        """
        for input_val, expected in test_cases.items():
            result = func(input_val)
            assert result == expected, f"Failed for input {input_val}: got {result}, expected {expected}"


class TimeoutTestHelper:
    """Helper for testing timeout behavior"""
    
    @staticmethod
    def assert_timeout(func: Callable, timeout_seconds: float, *args, **kwargs):
        """
        Assert that function respects timeout.
        
        Args:
            func: Function to test
            timeout_seconds: Timeout duration
            *args: Function arguments
            **kwargs: Function keyword arguments
        """
        start = time.time()
        
        try:
            func(*args, timeout=timeout_seconds, **kwargs)
        except TimeoutError:
            pass  # Expected
        
        elapsed = time.time() - start
        
        # Should not take much longer than timeout
        assert elapsed <= timeout_seconds * 1.5, \
            f"Operation took {elapsed}s, timeout was {timeout_seconds}s"


class MockDeviceHelper:
    """Helper for mocking device operations"""
    
    @staticmethod
    def create_mock_device_response(status: str = "ok", data: Optional[dict] = None) -> dict:
        """
        Create a mock device response.
        
        Args:
            status: Response status
            data: Additional data
        
        Returns:
            Mock response dictionary
        """
        response = {
            'status': status,
            'timestamp': time.time(),
        }
        
        if data:
            response.update(data)
        
        return response
    
    @staticmethod
    def simulate_device_delay(delay_seconds: float = 0.1):
        """
        Simulate device response delay.
        
        Args:
            delay_seconds: Delay duration
        """
        time.sleep(delay_seconds)


# Test fixtures

@pytest.fixture
def temp_file():
    """Fixture for temporary test file"""
    file_path = FileTestHelper.create_test_file()
    yield file_path
    if file_path.exists():
        file_path.unlink()


@pytest.fixture
def temp_dir():
    """Fixture for temporary directory"""
    dir_path = Path(tempfile.mkdtemp())
    yield dir_path
    import shutil
    shutil.rmtree(dir_path, ignore_errors=True)


@pytest.fixture
def caplog_at_level(caplog):
    """Fixture to capture logs at all levels"""
    caplog.set_level(logging.DEBUG)
    return caplog


# Example test patterns

def example_exception_test():
    """Example of testing exception handling"""
    def func_with_exception():
        raise ValueError("Test error")
    
    # Test that exception is raised and logged
    with pytest.raises(ValueError):
        func_with_exception()


def example_file_cleanup_test(temp_file):
    """Example of testing file cleanup"""
    def func_with_cleanup(file_path):
        try:
            with open(file_path, 'w') as f:
                f.write('test')
        finally:
            file_path.unlink()
    
    # Test that cleanup happens
    func_with_cleanup(temp_file)
    FileTestHelper.assert_file_cleanup(temp_file)


def example_concurrent_test():
    """Example of testing concurrent operations"""
    def func(x):
        return x * 2
    
    results = ConcurrencyTestHelper.run_concurrent(
        func,
        [(1,), (2,), (3,), (4,), (5,)]
    )
    
    assert results == [2, 4, 6, 8, 10]


def example_validation_test():
    """Example of testing input validation"""
    def validate_port(port):
        if not isinstance(port, int) or not (1 <= port <= 65535):
            raise ValueError("Invalid port")
        return port
    
    # Test valid input
    assert validate_port(8080) == 8080
    
    # Test invalid input
    ValidationTestHelper.assert_validation_error(validate_port, 99999)


if __name__ == '__main__':
    # Run examples
    print("Testing utilities defined successfully")
