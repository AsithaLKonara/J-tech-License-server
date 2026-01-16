"""
Environment Detection - Detect and manage application environment.
"""

import os
from enum import Enum


class Environment(Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


def get_environment() -> Environment:
    """
    Detect current environment from environment variable.
    
    Returns:
        Environment enum value
    
    Defaults to DEVELOPMENT if not set.
    """
    env_str = os.getenv('ENVIRONMENT', 'development').lower()
    
    try:
        return Environment(env_str)
    except ValueError:
        # Invalid environment, default to development
        return Environment.DEVELOPMENT

