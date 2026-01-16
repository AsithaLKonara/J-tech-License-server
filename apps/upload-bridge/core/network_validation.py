"""
Network Validation Utilities
Validates IP addresses, ports, and other network configuration
"""

import logging
import ipaddress
import socket
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def validate_ip_address(ip: str) -> Tuple[bool, str]:
    """
    Validate IPv4 or IPv6 address format.
    
    Args:
        ip: IP address string
    
    Returns:
        (is_valid: bool, error_message: str)
    """
    if not ip or not isinstance(ip, str):
        return False, "IP address must be a non-empty string"
    
    try:
        ipaddress.ip_address(ip)
        return True, ""
    except ValueError:
        return False, f"Invalid IP address format: '{ip}'"


def validate_port(port: int) -> Tuple[bool, str]:
    """
    Validate port number (1-65535).
    
    Args:
        port: Port number
    
    Returns:
        (is_valid: bool, error_message: str)
    """
    if not isinstance(port, int):
        return False, "Port must be an integer"
    
    if not (1 <= port <= 65535):
        return False, f"Port must be between 1 and 65535, got {port}"
    
    return True, ""


def validate_esp_config(ip: str, port: int = 80) -> Tuple[bool, str]:
    """
    Validate complete ESP8266 network configuration.
    
    Args:
        ip: ESP8266 IP address
        port: ESP8266 port (default: 80)
    
    Returns:
        (is_valid: bool, error_message: str)
    """
    # Validate IP
    ip_valid, ip_error = validate_ip_address(ip)
    if not ip_valid:
        return False, ip_error
    
    # Validate port
    port_valid, port_error = validate_port(port)
    if not port_valid:
        return False, port_error
    
    return True, ""


def check_ip_reachable(ip: str, port: int = 80, timeout: float = 5.0) -> Tuple[bool, str]:
    """
    Check if IP address is reachable.
    
    Args:
        ip: IP address to check
        port: Port to check
        timeout: Timeout in seconds
    
    Returns:
        (is_reachable: bool, error_message: str)
    """
    # First validate
    valid, error = validate_esp_config(ip, port)
    if not valid:
        return False, error
    
    try:
        socket.create_connection((ip, port), timeout=timeout)
        logger.debug(f"IP {ip}:{port} is reachable")
        return True, ""
    except socket.timeout:
        return False, f"Connection to {ip}:{port} timed out (>{timeout}s)"
    except socket.error as e:
        return False, f"Cannot reach {ip}:{port}: {e}"
    except Exception as e:
        logger.error(f"Unexpected error checking {ip}:{port}: {e}", exc_info=True)
        return False, f"Unexpected error: {e}"


def validate_hostname(hostname: str) -> Tuple[bool, str]:
    """
    Validate hostname format.
    
    Args:
        hostname: Hostname string
    
    Returns:
        (is_valid: bool, error_message: str)
    """
    if not hostname or not isinstance(hostname, str):
        return False, "Hostname must be a non-empty string"
    
    if len(hostname) > 253:
        return False, f"Hostname too long (max 253 chars): {len(hostname)}"
    
    # Check each label
    labels = hostname.split('.')
    for label in labels:
        if not label or len(label) > 63:
            return False, f"Invalid hostname label: '{label}'"
        if not all(c.isalnum() or c in '-' for c in label):
            return False, f"Hostname contains invalid characters: '{label}'"
        if label.startswith('-') or label.endswith('-'):
            return False, f"Hostname label cannot start/end with dash: '{label}'"
    
    return True, ""


def get_network_diagnostics(ip: str, port: int = 80) -> dict:
    """
    Get detailed network diagnostics for debugging.
    
    Args:
        ip: IP address to diagnose
        port: Port to check
    
    Returns:
        Dictionary with diagnostic information
    """
    diagnostics = {
        'ip': ip,
        'port': port,
        'ip_valid': False,
        'port_valid': False,
        'reachable': False,
        'errors': []
    }
    
    # Check IP validity
    ip_valid, ip_error = validate_ip_address(ip)
    diagnostics['ip_valid'] = ip_valid
    if not ip_valid:
        diagnostics['errors'].append(ip_error)
    
    # Check port validity
    port_valid, port_error = validate_port(port)
    diagnostics['port_valid'] = port_valid
    if not port_valid:
        diagnostics['errors'].append(port_error)
    
    # Check reachability
    if ip_valid and port_valid:
        reachable, reach_error = check_ip_reachable(ip, port)
        diagnostics['reachable'] = reachable
        if not reachable:
            diagnostics['errors'].append(reach_error)
    
    return diagnostics
