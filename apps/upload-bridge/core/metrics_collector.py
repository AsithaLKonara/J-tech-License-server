"""
Metrics collection and performance monitoring for Upload Bridge.

This module provides metrics collection for:
- Upload performance (speed, duration, success rate)
- Network health (latency, connection reliability)
- System performance (CPU, memory usage)
- Error rates and types
"""

import logging
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class UploadMetrics:
    """Metrics for a single upload operation"""
    timestamp: datetime = field(default_factory=datetime.now)
    file_size: int = 0
    duration_seconds: float = 0.0
    success: bool = False
    error_type: Optional[str] = None
    speed_mbps: float = 0.0
    retry_count: int = 0
    device_ip: Optional[str] = None
    
    def calculate_speed(self) -> float:
        """Calculate transfer speed in Mbps"""
        if self.duration_seconds <= 0:
            return 0.0
        
        bytes_per_second = self.file_size / self.duration_seconds
        mbps = (bytes_per_second * 8) / (1000 * 1000)
        self.speed_mbps = mbps
        return mbps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'file_size': self.file_size,
            'duration_seconds': self.duration_seconds,
            'success': self.success,
            'error_type': self.error_type,
            'speed_mbps': self.speed_mbps,
            'retry_count': self.retry_count,
            'device_ip': self.device_ip,
        }


@dataclass
class NetworkMetrics:
    """Metrics for network health monitoring"""
    timestamp: datetime = field(default_factory=datetime.now)
    device_ip: str = ""
    latency_ms: float = 0.0
    connection_success: bool = False
    packet_loss: float = 0.0  # Percentage
    bandwidth_available_mbps: float = 0.0
    dns_lookup_time_ms: float = 0.0


@dataclass
class ErrorMetrics:
    """Metrics for error tracking"""
    timestamp: datetime = field(default_factory=datetime.now)
    error_type: str = ""
    error_message: str = ""
    severity: str = "ERROR"  # INFO, WARNING, ERROR, CRITICAL
    context: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collects and aggregates metrics for the application"""
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector.
        
        Args:
            max_history: Maximum number of metrics to keep in memory
        """
        self.max_history = max_history
        self.uploads: deque = deque(maxlen=max_history)
        self.network: deque = deque(maxlen=max_history)
        self.errors: deque = deque(maxlen=max_history)
        self._start_time = datetime.now()
    
    def record_upload(self, metrics: UploadMetrics) -> None:
        """
        Record an upload operation.
        
        Args:
            metrics: UploadMetrics instance
        """
        metrics.calculate_speed()
        self.uploads.append(metrics)
        
        status = "SUCCESS" if metrics.success else f"FAILED ({metrics.error_type})"
        logger.info(
            f"Upload recorded: {metrics.file_size / 1024:.1f} KB, "
            f"{metrics.duration_seconds:.2f}s, {metrics.speed_mbps:.2f} Mbps, {status}"
        )
    
    def record_network_metric(self, metrics: NetworkMetrics) -> None:
        """
        Record network health metric.
        
        Args:
            metrics: NetworkMetrics instance
        """
        self.network.append(metrics)
    
    def record_error(self, error_type: str, error_message: str, severity: str = "ERROR", 
                    context: Optional[Dict[str, Any]] = None) -> None:
        """
        Record an error occurrence.
        
        Args:
            error_type: Type of error
            error_message: Error message
            severity: Error severity level
            context: Additional context information
        """
        metrics = ErrorMetrics(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            context=context or {},
        )
        self.errors.append(metrics)
    
    def get_upload_stats(self, time_window_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Get upload statistics.
        
        Args:
            time_window_minutes: Only include metrics from last N minutes
        
        Returns:
            Dictionary with upload statistics
        """
        if not self.uploads:
            return {
                'total_uploads': 0,
                'successful_uploads': 0,
                'failed_uploads': 0,
                'success_rate': 0.0,
            }
        
        # Filter by time window
        uploads_to_analyze = list(self.uploads)
        if time_window_minutes:
            cutoff = datetime.now() - timedelta(minutes=time_window_minutes)
            uploads_to_analyze = [m for m in uploads_to_analyze if m.timestamp >= cutoff]
        
        if not uploads_to_analyze:
            return {
                'total_uploads': 0,
                'successful_uploads': 0,
                'failed_uploads': 0,
                'success_rate': 0.0,
            }
        
        successful = [m for m in uploads_to_analyze if m.success]
        failed = [m for m in uploads_to_analyze if not m.success]
        
        # Calculate statistics
        speeds = [m.speed_mbps for m in successful if m.speed_mbps > 0]
        durations = [m.duration_seconds for m in successful]
        file_sizes = [m.file_size for m in uploads_to_analyze]
        
        return {
            'total_uploads': len(uploads_to_analyze),
            'successful_uploads': len(successful),
            'failed_uploads': len(failed),
            'success_rate': len(successful) / len(uploads_to_analyze) if uploads_to_analyze else 0.0,
            'avg_speed_mbps': statistics.mean(speeds) if speeds else 0.0,
            'max_speed_mbps': max(speeds) if speeds else 0.0,
            'min_speed_mbps': min(speeds) if speeds else 0.0,
            'avg_duration_seconds': statistics.mean(durations) if durations else 0.0,
            'total_data_transferred_mb': sum(file_sizes) / (1024 * 1024),
            'avg_retry_count': statistics.mean([m.retry_count for m in successful]),
        }
    
    def get_network_stats(self, time_window_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Get network health statistics.
        
        Args:
            time_window_minutes: Only include metrics from last N minutes
        
        Returns:
            Dictionary with network statistics
        """
        if not self.network:
            return {
                'total_checks': 0,
                'avg_latency_ms': 0.0,
                'connection_success_rate': 0.0,
            }
        
        network_to_analyze = list(self.network)
        if time_window_minutes:
            cutoff = datetime.now() - timedelta(minutes=time_window_minutes)
            network_to_analyze = [m for m in network_to_analyze if m.timestamp >= cutoff]
        
        if not network_to_analyze:
            return {
                'total_checks': 0,
                'avg_latency_ms': 0.0,
                'connection_success_rate': 0.0,
            }
        
        successful = [m for m in network_to_analyze if m.connection_success]
        latencies = [m.latency_ms for m in network_to_analyze if m.latency_ms > 0]
        
        return {
            'total_checks': len(network_to_analyze),
            'successful_checks': len(successful),
            'connection_success_rate': len(successful) / len(network_to_analyze),
            'avg_latency_ms': statistics.mean(latencies) if latencies else 0.0,
            'max_latency_ms': max(latencies) if latencies else 0.0,
            'min_latency_ms': min(latencies) if latencies else 0.0,
            'avg_packet_loss_percent': statistics.mean([m.packet_loss for m in network_to_analyze]),
        }
    
    def get_error_stats(self, time_window_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Get error statistics.
        
        Args:
            time_window_minutes: Only include errors from last N minutes
        
        Returns:
            Dictionary with error statistics
        """
        if not self.errors:
            return {
                'total_errors': 0,
                'errors_by_type': {},
                'errors_by_severity': {},
            }
        
        errors_to_analyze = list(self.errors)
        if time_window_minutes:
            cutoff = datetime.now() - timedelta(minutes=time_window_minutes)
            errors_to_analyze = [m for m in errors_to_analyze if m.timestamp >= cutoff]
        
        # Group by type and severity
        errors_by_type = {}
        errors_by_severity = {}
        
        for error in errors_to_analyze:
            errors_by_type[error.error_type] = errors_by_type.get(error.error_type, 0) + 1
            errors_by_severity[error.severity] = errors_by_severity.get(error.severity, 0) + 1
        
        return {
            'total_errors': len(errors_to_analyze),
            'errors_by_type': errors_by_type,
            'errors_by_severity': errors_by_severity,
        }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """
        Get overall application health score.
        
        Returns:
            Dictionary with health metrics (0-100 scale)
        """
        # Calculate health from various metrics
        upload_stats = self.get_upload_stats(time_window_minutes=60)
        network_stats = self.get_network_stats(time_window_minutes=60)
        error_stats = self.get_error_stats(time_window_minutes=60)
        
        # Health score components (each 0-100)
        upload_health = upload_stats.get('success_rate', 0) * 100
        network_health = network_stats.get('connection_success_rate', 0) * 100
        error_health = 100 - min(error_stats.get('total_errors', 0) * 10, 100)
        
        # Overall health (weighted average)
        overall_health = (upload_health * 0.4 + network_health * 0.3 + error_health * 0.3)
        
        return {
            'overall_health_score': min(overall_health, 100),
            'upload_health': upload_health,
            'network_health': network_health,
            'error_health': error_health,
            'uptime_hours': (datetime.now() - self._start_time).total_seconds() / 3600,
        }
    
    def reset_all(self) -> None:
        """Reset all metrics"""
        self.uploads.clear()
        self.network.clear()
        self.errors.clear()
        self._start_time = datetime.now()
        logger.info("Metrics reset")
    
    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all metrics for storage or analysis.
        
        Returns:
            Dictionary with all collected metrics
        """
        return {
            'upload_stats': self.get_upload_stats(),
            'network_stats': self.get_network_stats(),
            'error_stats': self.get_error_stats(),
            'health': self.get_overall_health(),
            'recent_uploads': [m.to_dict() for m in list(self.uploads)[-10:]],
        }


# Global metrics instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get the global metrics collector instance.
    
    Returns:
        MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    
    return _metrics_collector


def record_upload(file_size: int, duration: float, success: bool, 
                 error_type: Optional[str] = None, device_ip: Optional[str] = None) -> None:
    """
    Convenience function to record upload metrics.
    
    Args:
        file_size: Size of uploaded file in bytes
        duration: Upload duration in seconds
        success: Whether upload was successful
        error_type: Type of error if unsuccessful
        device_ip: IP address of target device
    """
    metrics = UploadMetrics(
        file_size=file_size,
        duration_seconds=duration,
        success=success,
        error_type=error_type,
        device_ip=device_ip,
    )
    get_metrics_collector().record_upload(metrics)
