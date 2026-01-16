"""
Health Checker - System health monitoring.

Provides health check capabilities for production monitoring.
"""

import psutil
import sys
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheck:
    """Result of a health check."""
    
    def __init__(self, name: str, status: HealthStatus, message: str = "", details: Optional[Dict[str, Any]] = None):
        """
        Initialize health check result.
        
        Args:
            name: Check name
            status: Health status
            message: Status message
            details: Additional details
        """
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()


class HealthChecker:
    """
    System health checker.
    
    Provides health check capabilities for monitoring system status,
    resource usage, and application health.
    """
    
    _instance: Optional['HealthChecker'] = None
    
    def __init__(self):
        """Initialize health checker."""
        if HealthChecker._instance is not None:
            raise RuntimeError("HealthChecker is a singleton. Use get_health_checker() instead.")
        
        HealthChecker._instance = self
    
    @classmethod
    def instance(cls) -> 'HealthChecker':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def check_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Health check results dictionary
        """
        checks = {
            'application': self.check_application(),
            'memory': self.check_memory(),
            'disk': self.check_disk(),
            'cpu': self.check_cpu(),
        }
        
        # Determine overall status
        statuses = [check.status for check in checks.values()]
        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return {
            'status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'checks': {name: {
                'status': check.status.value,
                'message': check.message,
                'details': check.details,
                'timestamp': check.timestamp
            } for name, check in checks.items()}
        }
    
    def check_application(self) -> HealthCheck:
        """
        Check application health.
        
        Returns:
            HealthCheck result
        """
        try:
            # Basic application health check
            # Can be extended to check database connections, external services, etc.
            return HealthCheck(
                name="application",
                status=HealthStatus.HEALTHY,
                message="Application is running",
                details={'version': sys.version}
            )
        except Exception as e:
            return HealthCheck(
                name="application",
                status=HealthStatus.UNHEALTHY,
                message=f"Application check failed: {str(e)}"
            )
    
    def check_memory(self) -> HealthCheck:
        """
        Check memory usage.
        
        Returns:
            HealthCheck result
        """
        try:
            memory = psutil.virtual_memory()
            percent_used = memory.percent
            
            if percent_used > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Memory usage critical: {percent_used:.1f}%"
            elif percent_used > 75:
                status = HealthStatus.DEGRADED
                message = f"Memory usage high: {percent_used:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {percent_used:.1f}%"
            
            return HealthCheck(
                name="memory",
                status=status,
                message=message,
                details={
                    'percent_used': percent_used,
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3)
                }
            )
        except Exception as e:
            return HealthCheck(
                name="memory",
                status=HealthStatus.DEGRADED,
                message=f"Memory check failed: {str(e)}"
            )
    
    def check_disk(self) -> HealthCheck:
        """
        Check disk usage.
        
        Returns:
            HealthCheck result
        """
        try:
            disk = psutil.disk_usage('/')
            percent_used = disk.percent
            
            if percent_used > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Disk usage critical: {percent_used:.1f}%"
            elif percent_used > 80:
                status = HealthStatus.DEGRADED
                message = f"Disk usage high: {percent_used:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {percent_used:.1f}%"
            
            return HealthCheck(
                name="disk",
                status=status,
                message=message,
                details={
                    'percent_used': percent_used,
                    'total_gb': disk.total / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'used_gb': disk.used / (1024**3)
                }
            )
        except Exception as e:
            return HealthCheck(
                name="disk",
                status=HealthStatus.DEGRADED,
                message=f"Disk check failed: {str(e)}"
            )
    
    def check_cpu(self) -> HealthCheck:
        """
        Check CPU usage.
        
        Returns:
            HealthCheck result
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            if cpu_percent > 90:
                status = HealthStatus.DEGRADED
                message = f"CPU usage high: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage normal: {cpu_percent:.1f}%"
            
            return HealthCheck(
                name="cpu",
                status=status,
                message=message,
                details={
                    'percent_used': cpu_percent,
                    'cpu_count': cpu_count
                }
            )
        except Exception as e:
            return HealthCheck(
                name="cpu",
                status=HealthStatus.DEGRADED,
                message=f"CPU check failed: {str(e)}"
            )


def get_health_checker() -> HealthChecker:
    """
    Get the health checker instance.
    
    Returns:
        HealthChecker instance
    """
    return HealthChecker.instance()

