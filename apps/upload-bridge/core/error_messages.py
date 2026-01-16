"""
User-friendly error messages with troubleshooting guidance.

This module provides standardized error messages for common issues,
including recovery steps and diagnostic information.
"""

import logging
from typing import Dict, Tuple, Optional


# Error message templates with troubleshooting steps
ERROR_MESSAGES: Dict[str, Dict[str, str]] = {
    "connection_timeout": {
        "title": "Connection Timeout",
        "message": "Could not connect to device within the time limit",
        "steps": [
            "1. Check that the device is powered on and connected to the network",
            "2. Verify the IP address or hostname is correct",
            "3. Ensure the device is within WiFi range",
            "4. Check if your firewall is blocking the connection",
            "5. Try reconnecting the device to the network",
        ],
        "docs_link": "https://docs.uploadbridge.local/troubleshooting#timeout",
    },
    "connection_refused": {
        "title": "Connection Refused",
        "message": "Device rejected the connection",
        "steps": [
            "1. Verify the device is running and ready to accept connections",
            "2. Check if the correct port is specified in configuration",
            "3. Ensure the device firmware supports this feature",
            "4. Try restarting the device",
            "5. Check device logs for error details",
        ],
        "docs_link": "https://docs.uploadbridge.local/troubleshooting#refused",
    },
    "device_not_found": {
        "title": "Device Not Found",
        "message": "Could not locate device on the network",
        "steps": [
            "1. Verify the device hostname or IP address is correct",
            "2. Check that the device is connected to the network",
            "3. Ensure the device is powered on",
            "4. Try using the device's IP address instead of hostname",
            "5. Check your network for connectivity issues",
        ],
        "docs_link": "https://docs.uploadbridge.local/troubleshooting#not_found",
    },
    "invalid_credentials": {
        "title": "Authentication Failed",
        "message": "Invalid username or password",
        "steps": [
            "1. Verify your username and password are correct",
            "2. Check Caps Lock is off",
            "3. Reset your password if you forgot it",
            "4. Ensure your account is active",
            "5. Contact support if the issue persists",
        ],
        "docs_link": "https://docs.uploadbridge.local/troubleshooting#auth",
    },
    "insufficient_storage": {
        "title": "Insufficient Storage",
        "message": "Device does not have enough space for the upload",
        "steps": [
            "1. Check available storage on the device",
            "2. Delete unnecessary files from the device",
            "3. Try uploading a smaller file first",
            "4. Format the device storage if needed",
            "5. Contact support for storage expansion options",
        ],
        "docs_link": "https://docs.uploadbridge.local/troubleshooting#storage",
    },
    "invalid_file_format": {
        "title": "Invalid File Format",
        "message": "The file format is not supported or the file is corrupted",
        "steps": [
            "1. Verify the file extension is correct",
            "2. Check if the file is corrupted by opening it",
            "3. Try converting the file to a supported format",
            "4. Ensure the file content matches the expected structure",
            "5. Check the documentation for supported formats",
        ],
        "docs_link": "https://docs.uploadbridge.local/troubleshooting#format",
    },
    "network_error": {
        "title": "Network Error",
        "message": "An unexpected network error occurred",
        "steps": [
            "1. Check your internet connection",
            "2. Verify network connectivity to the device",
            "3. Check if DNS resolution is working",
            "4. Try using a different network",
            "5. Restart your router and try again",
        ],
        "docs_link": "https://docs.uploadbridge.local/troubleshooting#network",
    },
    "invalid_json": {
        "title": "Invalid JSON File",
        "message": "The JSON file is malformed or corrupted",
        "steps": [
            "1. Validate the JSON syntax using an online validator",
            "2. Check for unmatched braces or quotes",
            "3. Ensure the file encoding is UTF-8",
            "4. Try opening the file in a text editor",
            "5. Regenerate the file if it's corrupted",
        ],
        "docs_link": "https://docs.uploadbridge.local/troubleshooting#json",
    },
    "permission_denied": {
        "title": "Permission Denied",
        "message": "You do not have permission to perform this operation",
        "steps": [
            "1. Check your user account permissions",
            "2. Verify your license allows this operation",
            "3. Try using an administrator account",
            "4. Contact support to request elevated permissions",
            "5. Check the documentation for permission requirements",
        ],
        "docs_link": "https://docs.uploadbridge.local/troubleshooting#permissions",
    },
    "device_busy": {
        "title": "Device Busy",
        "message": "Device is currently processing another operation",
        "steps": [
            "1. Wait for the current operation to complete",
            "2. Check the device status or progress indicator",
            "3. Try the operation again after a few moments",
            "4. Restart the device if it's unresponsive",
            "5. Check device logs for ongoing processes",
        ],
        "docs_link": "https://docs.uploadbridge.local/troubleshooting#busy",
    },
}


def get_error_message(error_type: str, custom_message: Optional[str] = None) -> Tuple[str, str, list, str]:
    """
    Get a formatted error message with troubleshooting steps.
    
    Args:
        error_type: The type of error (key in ERROR_MESSAGES)
        custom_message: Optional custom message to append
    
    Returns:
        Tuple of (title, message, troubleshooting_steps, docs_link)
    """
    if error_type not in ERROR_MESSAGES:
        logging.warning(f"Unknown error type: {error_type}")
        error_type = "network_error"
    
    error_info = ERROR_MESSAGES[error_type]
    
    # Append custom message if provided
    message = error_info["message"]
    if custom_message:
        message = f"{message}\n\nDetails: {custom_message}"
    
    return (
        error_info["title"],
        message,
        error_info["steps"],
        error_info["docs_link"],
    )


def format_error_dialog(error_type: str, custom_message: Optional[str] = None) -> str:
    """
    Format a complete error message for display in a dialog box.
    
    Args:
        error_type: The type of error
        custom_message: Optional custom message to append
    
    Returns:
        Formatted error message as string
    """
    title, message, steps, docs_link = get_error_message(error_type, custom_message)
    
    # Build formatted message
    formatted = f"{title}\n\n{message}\n\n"
    formatted += "Troubleshooting steps:\n"
    for step in steps:
        formatted += f"  {step}\n"
    formatted += f"\nFor more help, visit: {docs_link}"
    
    return formatted


def format_error_log(error_type: str, exception: Exception, context: Optional[str] = None) -> str:
    """
    Format an error message for logging with full details.
    
    Args:
        error_type: The type of error
        exception: The exception that occurred
        context: Optional context information
    
    Returns:
        Formatted error message for logging
    """
    title, message, _, docs_link = get_error_message(error_type)
    
    log_message = f"[{title}] {message}\n"
    log_message += f"Exception: {exception.__class__.__name__}: {str(exception)}\n"
    
    if context:
        log_message += f"Context: {context}\n"
    
    log_message += f"Documentation: {docs_link}"
    
    return log_message


def get_recovery_suggestion(error_type: str) -> str:
    """
    Get a brief recovery suggestion for an error.
    
    Args:
        error_type: The type of error
    
    Returns:
        Brief recovery suggestion
    """
    if error_type not in ERROR_MESSAGES:
        return "Please check the documentation or contact support."
    
    steps = ERROR_MESSAGES[error_type]["steps"]
    # Return the first step as a quick suggestion
    return steps[0].split(". ", 1)[1] if steps else "Please try again."
