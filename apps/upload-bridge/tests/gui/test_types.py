"""
Test Types - Shared data structures for test results.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class TestStatus(Enum):
    """Test execution status."""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    PASS = "Pass"
    FAIL = "Fail"
    SKIP = "Skip"


@dataclass
class TestResult:
    """Individual test result."""
    category: str
    feature: str
    status: TestStatus = TestStatus.PENDING
    message: str = ""
    error: Optional[str] = None
    duration: float = 0.0

