"""
Test Fixtures and Factories
Provides test data factories and fixtures for E2E tests
"""

import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def generate_email(prefix: str = "test") -> str:
        """Generate unique test email"""
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}_{unique_id}@test.example.com"
    
    @staticmethod
    def generate_password() -> str:
        """Generate test password"""
        return "testpassword123"
    
    @staticmethod
    def generate_user_id() -> str:
        """Generate unique user ID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_entitlement_id() -> str:
        """Generate unique entitlement ID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_device_id() -> str:
        """Generate unique device ID"""
        return f"DEVICE_{uuid.uuid4().hex[:16].upper()}"
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password (simple hash for testing)"""
        # In production, use proper password hashing (bcrypt, etc.)
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def create_user_data(email: Optional[str] = None, password: Optional[str] = None,
                        name: Optional[str] = None, is_admin: bool = False) -> Dict[str, Any]:
        """Create user data dictionary"""
        return {
            'id': TestDataFactory.generate_user_id(),
            'email': email or TestDataFactory.generate_email(),
            'password': password or TestDataFactory.generate_password(),
            'name': name or "Test User",
            'is_admin': is_admin,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    @staticmethod
    def create_entitlement_data(user_id: str, plan: str = 'trial', 
                                status: str = 'active', max_devices: int = 1,
                                expires_in_days: Optional[int] = None) -> Dict[str, Any]:
        """Create entitlement data dictionary"""
        expires_at = None
        if expires_in_days is not None:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        elif plan == 'trial':
            expires_at = datetime.now() + timedelta(days=30)
        elif plan in ['monthly', 'yearly']:
            days = 30 if plan == 'monthly' else 365
            expires_at = datetime.now() + timedelta(days=days)
        
        return {
            'id': TestDataFactory.generate_entitlement_id(),
            'user_id': user_id,
            'product_id': 'upload-bridge',
            'plan': plan,
            'status': status,
            'features': '[]',
            'max_devices': max_devices,
            'expires_at': expires_at,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    @staticmethod
    def create_device_data(user_id: str, device_name: Optional[str] = None,
                          entitlement_id: Optional[str] = None) -> Dict[str, Any]:
        """Create device data dictionary"""
        return {
            'user_id': user_id,
            'device_id': TestDataFactory.generate_device_id(),
            'device_name': device_name or "Test Device",
            'entitlement_id': entitlement_id,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    @staticmethod
    def create_expired_entitlement_data(user_id: str, plan: str = 'trial') -> Dict[str, Any]:
        """Create expired entitlement data"""
        return TestDataFactory.create_entitlement_data(
            user_id=user_id,
            plan=plan,
            status='expired',
            expires_in_days=-1  # Expired yesterday
        )
    
    @staticmethod
    def create_expiring_soon_entitlement_data(user_id: str, plan: str = 'monthly',
                                             days_until_expiry: int = 3) -> Dict[str, Any]:
        """Create entitlement expiring soon"""
        return TestDataFactory.create_entitlement_data(
            user_id=user_id,
            plan=plan,
            status='active',
            expires_in_days=days_until_expiry
        )


class TestPatternFactory:
    """Factory for creating test patterns"""
    
    @staticmethod
    def create_pattern_data(name: str = "Test Pattern", width: int = 72, 
                           height: int = 1, frame_count: int = 1) -> Dict[str, Any]:
        """Create pattern data dictionary"""
        return {
            'name': name,
            'width': width,
            'height': height,
            'frame_count': frame_count,
            'fps': 30,
            'created_at': datetime.now()
        }
    
    @staticmethod
    def create_large_pattern_data(name: str = "Large Test Pattern") -> Dict[str, Any]:
        """Create large pattern data for performance testing"""
        return TestPatternFactory.create_pattern_data(
            name=name,
            width=64,
            height=64,
            frame_count=100
        )


class TestLicenseFactory:
    """Factory for creating test licenses"""
    
    @staticmethod
    def create_trial_license_data(user_id: str) -> Dict[str, Any]:
        """Create trial license data"""
        return TestDataFactory.create_entitlement_data(
            user_id=user_id,
            plan='trial',
            status='active',
            max_devices=1
        )
    
    @staticmethod
    def create_monthly_license_data(user_id: str) -> Dict[str, Any]:
        """Create monthly license data"""
        return TestDataFactory.create_entitlement_data(
            user_id=user_id,
            plan='monthly',
            status='active',
            max_devices=5
        )
    
    @staticmethod
    def create_yearly_license_data(user_id: str) -> Dict[str, Any]:
        """Create yearly license data"""
        return TestDataFactory.create_entitlement_data(
            user_id=user_id,
            plan='yearly',
            status='active',
            max_devices=10
        )
    
    @staticmethod
    def create_perpetual_license_data(user_id: str) -> Dict[str, Any]:
        """Create perpetual license data"""
        return TestDataFactory.create_entitlement_data(
            user_id=user_id,
            plan='perpetual',
            status='active',
            max_devices=999,
            expires_in_days=None  # No expiration
        )
