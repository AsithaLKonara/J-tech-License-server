"""
Quality of Service (QoS) Manager - Control CPU usage and performance

Provides QoS controls for limiting CPU usage during heavy operations.
"""

from typing import Optional
from PySide6.QtCore import QObject, QTimer, Signal, Qt


class QoSManager(QObject):
    """
    Quality of Service manager for controlling CPU usage.
    
    Provides CPU limiting and performance throttling for heavy operations.
    """
    
    cpu_limit_changed = Signal(float)  # New CPU limit (0.0-1.0)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cpu_limit = 1.0  # 0.0-1.0 (1.0 = 100%, 0.5 = 50%)
        self._throttle_timer = QTimer(self)
        self._throttle_timer.setSingleShot(True)
    
    def set_cpu_limit(self, limit: float):
        """
        Set CPU usage limit.
        
        Args:
            limit: CPU limit (0.0-1.0, where 1.0 = 100%)
        """
        self._cpu_limit = max(0.0, min(1.0, limit))
        self.cpu_limit_changed.emit(self._cpu_limit)
    
    def get_cpu_limit(self) -> float:
        """Get current CPU limit"""
        return self._cpu_limit
    
    def throttle(self, operation):
        """
        Throttle an operation based on CPU limit.
        
        Args:
            operation: Callable to throttle
        """
        if self._cpu_limit >= 1.0:
            # No throttling
            operation()
        else:
            # Schedule with delay based on CPU limit
            delay_ms = int((1.0 - self._cpu_limit) * 100)  # 0-100ms delay
            self._throttle_timer.timeout.connect(operation, Qt.QueuedConnection)
            self._throttle_timer.start(delay_ms)
    
    def should_throttle(self) -> bool:
        """Check if operations should be throttled"""
        return self._cpu_limit < 1.0

