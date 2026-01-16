"""
Enhanced monitoring and alerting for Upload Bridge.

Provides:
- Success/failure rate tracking
- Repeated failure detection and alerts
- Health score calculation
- Alert escalation
- Metric aggregation
"""

import logging
import threading
import time
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum


logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts"""
    REPEATED_FAILURE = "repeated_failure"
    HIGH_ERROR_RATE = "high_error_rate"
    TIMEOUT_EXCEEDED = "timeout_exceeded"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"


@dataclass
class Alert:
    """Represents an alert event"""
    
    type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict = field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation"""
        return f"[{self.severity.value.upper()}] {self.type.value}: {self.message} ({self.timestamp})"


@dataclass
class OperationMetric:
    """Tracks metrics for an operation"""
    
    name: str
    success_count: int = 0
    failure_count: int = 0
    total_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    last_failure_time: Optional[datetime] = None
    last_failure_reason: Optional[str] = None
    consecutive_failures: int = 0
    
    @property
    def total_count(self) -> int:
        """Total operations"""
        return self.success_count + self.failure_count
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage"""
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100.0
    
    @property
    def average_duration(self) -> float:
        """Average operation duration"""
        if self.success_count == 0:
            return 0.0
        return self.total_duration / self.success_count
    
    def record_success(self, duration: float):
        """Record successful operation"""
        self.success_count += 1
        self.total_duration += duration
        self.min_duration = min(self.min_duration, duration)
        self.max_duration = max(self.max_duration, duration)
        self.consecutive_failures = 0
    
    def record_failure(self, reason: str):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.last_failure_reason = reason
        self.consecutive_failures += 1


class OperationMonitor:
    """Monitors individual operations"""
    
    def __init__(self, name: str, failure_threshold: int = 3):
        """
        Initialize operation monitor.
        
        Args:
            name: Operation name
            failure_threshold: Threshold for alerts
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.metric = OperationMetric(name)
        self._lock = threading.Lock()
    
    def record_success(self, duration: float):
        """Record successful operation"""
        with self._lock:
            self.metric.record_success(duration)
            logger.info(f"Operation '{self.name}' succeeded ({duration:.3f}s)")
    
    def record_failure(self, reason: str):
        """Record failed operation"""
        with self._lock:
            self.metric.record_failure(reason)
            logger.warning(f"Operation '{self.name}' failed: {reason}")
            
            # Check for repeated failures
            if self.metric.consecutive_failures >= self.failure_threshold:
                logger.error(
                    f"Operation '{self.name}' has failed {self.metric.consecutive_failures} "
                    f"consecutive times. Last failure: {reason}"
                )
    
    def get_metrics(self) -> OperationMetric:
        """Get current metrics"""
        with self._lock:
            return self.metric
    
    def reset(self):
        """Reset metrics"""
        with self._lock:
            self.metric = OperationMetric(self.name)


class HealthScoreCalculator:
    """Calculates overall health score"""
    
    # Weight for different aspects
    SUCCESS_RATE_WEIGHT = 0.4
    PERFORMANCE_WEIGHT = 0.3
    STABILITY_WEIGHT = 0.3
    
    # Performance baselines (in seconds)
    GOOD_PERFORMANCE = 1.0
    ACCEPTABLE_PERFORMANCE = 2.0
    
    @staticmethod
    def calculate_health_score(metrics: List[OperationMetric]) -> float:
        """
        Calculate health score (0-100).
        
        Args:
            metrics: List of operation metrics
        
        Returns:
            Health score
        """
        if not metrics:
            return 100.0
        
        # Success rate component (0-40 points)
        avg_success_rate = sum(m.success_rate for m in metrics) / len(metrics)
        success_score = (avg_success_rate / 100.0) * HealthScoreCalculator.SUCCESS_RATE_WEIGHT * 100
        
        # Performance component (0-30 points)
        valid_durations = [m.average_duration for m in metrics if m.average_duration > 0]
        if valid_durations:
            avg_duration = sum(valid_durations) / len(valid_durations)
            if avg_duration <= HealthScoreCalculator.GOOD_PERFORMANCE:
                perf_score = HealthScoreCalculator.PERFORMANCE_WEIGHT * 100
            elif avg_duration <= HealthScoreCalculator.ACCEPTABLE_PERFORMANCE:
                perf_score = (HealthScoreCalculator.PERFORMANCE_WEIGHT * 100) * 0.75
            else:
                perf_score = (HealthScoreCalculator.PERFORMANCE_WEIGHT * 100) * 0.5
        else:
            perf_score = 0
        
        # Stability component (0-30 points)
        # Based on consecutive failures ratio
        total_failures = sum(m.consecutive_failures for m in metrics)
        if total_failures == 0:
            stability_score = HealthScoreCalculator.STABILITY_WEIGHT * 100
        else:
            stability_ratio = min(total_failures / 10, 1.0)  # Max 10 failures = 0 points
            stability_score = (1.0 - stability_ratio) * HealthScoreCalculator.STABILITY_WEIGHT * 100
        
        total_score = success_score + perf_score + stability_score
        return min(100.0, max(0.0, total_score))


class AlertManager:
    """Manages alert generation and notification"""
    
    def __init__(self):
        """Initialize alert manager"""
        self._alerts: deque = deque(maxlen=1000)  # Keep last 1000 alerts
        self._handlers: Dict[AlertType, List[Callable]] = {}
        self._lock = threading.Lock()
    
    def register_handler(self, alert_type: AlertType, handler: Callable):
        """
        Register alert handler.
        
        Args:
            alert_type: Type of alert
            handler: Function to call on alert
        """
        if alert_type not in self._handlers:
            self._handlers[alert_type] = []
        self._handlers[alert_type].append(handler)
    
    def trigger_alert(self, alert: Alert):
        """
        Trigger an alert.
        
        Args:
            alert: Alert to trigger
        """
        with self._lock:
            self._alerts.append(alert)
            logger.log(
                logging.ERROR if alert.severity == AlertSeverity.CRITICAL else logging.WARNING,
                str(alert)
            )
        
        # Call handlers
        if alert.type in self._handlers:
            for handler in self._handlers[alert.type]:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Error in alert handler: {e}")
    
    def get_alerts(self, since: Optional[datetime] = None) -> List[Alert]:
        """
        Get alerts since timestamp.
        
        Args:
            since: Optional datetime to filter from
        
        Returns:
            List of alerts
        """
        with self._lock:
            if since is None:
                return list(self._alerts)
            
            return [a for a in self._alerts if a.timestamp >= since]
    
    def clear_alerts(self):
        """Clear all alerts"""
        with self._lock:
            self._alerts.clear()


class MonitoringService:
    """Central monitoring service"""
    
    def __init__(self):
        """Initialize monitoring service"""
        self._monitors: Dict[str, OperationMonitor] = {}
        self._alert_manager = AlertManager()
        self._lock = threading.Lock()
        self._last_health_check = datetime.now()
    
    def get_monitor(self, operation_name: str) -> OperationMonitor:
        """
        Get or create monitor for operation.
        
        Args:
            operation_name: Name of operation
        
        Returns:
            Operation monitor
        """
        with self._lock:
            if operation_name not in self._monitors:
                self._monitors[operation_name] = OperationMonitor(operation_name)
            return self._monitors[operation_name]
    
    def calculate_health_score(self) -> float:
        """
        Calculate overall health score.
        
        Returns:
            Health score (0-100)
        """
        with self._lock:
            metrics = [m.get_metrics() for m in self._monitors.values()]
        
        return HealthScoreCalculator.calculate_health_score(metrics)
    
    def get_metrics_summary(self) -> Dict:
        """
        Get summary of all metrics.
        
        Returns:
            Metrics summary
        """
        with self._lock:
            metrics = {
                name: {
                    'success_count': m.get_metrics().success_count,
                    'failure_count': m.get_metrics().failure_count,
                    'success_rate': m.get_metrics().success_rate,
                    'average_duration': m.get_metrics().average_duration,
                    'consecutive_failures': m.get_metrics().consecutive_failures,
                }
                for name, m in self._monitors.items()
            }
        
        return {
            'health_score': self.calculate_health_score(),
            'operations': metrics,
            'timestamp': datetime.now().isoformat(),
        }
    
    def check_repeated_failures(self, operation_name: str, threshold: int = 3):
        """
        Check for repeated failures.
        
        Args:
            operation_name: Name of operation to check
            threshold: Failure threshold
        """
        monitor = self.get_monitor(operation_name)
        metric = monitor.get_metrics()
        
        if metric.consecutive_failures >= threshold:
            alert = Alert(
                type=AlertType.REPEATED_FAILURE,
                severity=AlertSeverity.CRITICAL,
                message=f"{operation_name} has failed {metric.consecutive_failures} consecutive times",
                context={
                    'operation': operation_name,
                    'consecutive_failures': metric.consecutive_failures,
                    'last_failure': metric.last_failure_reason,
                }
            )
            self._alert_manager.trigger_alert(alert)
    
    def check_error_rate(self, operation_name: str, threshold: float = 0.2):
        """
        Check error rate.
        
        Args:
            operation_name: Name of operation
            threshold: Error rate threshold (0-1)
        """
        monitor = self.get_monitor(operation_name)
        metric = monitor.get_metrics()
        
        error_rate = 1.0 - (metric.success_rate / 100.0)
        
        if error_rate >= threshold:
            alert = Alert(
                type=AlertType.HIGH_ERROR_RATE,
                severity=AlertSeverity.WARNING,
                message=f"{operation_name} error rate is {error_rate:.1%}",
                context={
                    'operation': operation_name,
                    'error_rate': error_rate,
                    'total_operations': metric.total_count,
                }
            )
            self._alert_manager.trigger_alert(alert)
    
    def register_alert_handler(self, alert_type: AlertType, handler: Callable):
        """
        Register alert handler.
        
        Args:
            alert_type: Type of alert
            handler: Handler function
        """
        self._alert_manager.register_handler(alert_type, handler)
    
    def get_alerts(self, since: Optional[timedelta] = None) -> List[Alert]:
        """
        Get recent alerts.
        
        Args:
            since: Optional timedelta to look back
        
        Returns:
            List of alerts
        """
        since_time = None
        if since:
            since_time = datetime.now() - since
        
        return self._alert_manager.get_alerts(since_time)


# Global monitoring service instance
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get global monitoring service instance"""
    global _monitoring_service
    
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    
    return _monitoring_service


def record_operation_success(operation_name: str, duration: float):
    """
    Record successful operation.
    
    Args:
        operation_name: Name of operation
        duration: Operation duration in seconds
    """
    service = get_monitoring_service()
    monitor = service.get_monitor(operation_name)
    monitor.record_success(duration)
    service.check_error_rate(operation_name)


def record_operation_failure(operation_name: str, reason: str):
    """
    Record failed operation.
    
    Args:
        operation_name: Name of operation
        reason: Failure reason
    """
    service = get_monitoring_service()
    monitor = service.get_monitor(operation_name)
    monitor.record_failure(reason)
    service.check_repeated_failures(operation_name)
