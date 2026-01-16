"""
API Client Helper for E2E Tests
Provides a wrapper around API requests with retry logic, logging, and error handling
"""

import requests
import time
import logging
from typing import Optional, Dict, Any, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from tests.e2e.test_config import (
    API_BASE_URL,
    API_RETRY_ATTEMPTS,
    API_RETRY_DELAY,
    TEST_TIMEOUT,
    LOG_LEVEL
)

logger = logging.getLogger(__name__)


class APIClient:
    """API client with retry logic and error handling"""
    
    def __init__(self, base_url: str = API_BASE_URL, timeout: int = TEST_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.token: Optional[str] = None
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=API_RETRY_ATTEMPTS,
            backoff_factor=API_RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def set_token(self, token: str):
        """Set authentication token"""
        self.token = token
        self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def clear_token(self):
        """Clear authentication token"""
        self.token = None
        self.session.headers.pop('Authorization', None)
    
    def _log_request(self, method: str, url: str, **kwargs):
        """Log API request"""
        if LOG_LEVEL == 'DEBUG':
            logger.debug(f"{method} {url}")
            if 'json' in kwargs:
                logger.debug(f"Request body: {kwargs['json']}")
    
    def _log_response(self, response: requests.Response):
        """Log API response"""
        if LOG_LEVEL == 'DEBUG':
            logger.debug(f"Response: {response.status_code}")
            try:
                logger.debug(f"Response body: {response.json()}")
            except:
                logger.debug(f"Response body: {response.text[:200]}")
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """GET request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self._log_request('GET', url, **kwargs)
        response = self.session.get(url, timeout=self.timeout, **kwargs)
        self._log_response(response)
        return response
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """POST request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self._log_request('POST', url, **kwargs)
        response = self.session.post(url, timeout=self.timeout, **kwargs)
        self._log_response(response)
        return response
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """PUT request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self._log_request('PUT', url, **kwargs)
        response = self.session.put(url, timeout=self.timeout, **kwargs)
        self._log_response(response)
        return response
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """DELETE request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self._log_request('DELETE', url, **kwargs)
        response = self.session.delete(url, timeout=self.timeout, **kwargs)
        self._log_response(response)
        return response
    
    def health_check(self) -> Tuple[bool, Optional[str]]:
        """Check API health"""
        try:
            response = self.get('/health')
            if response.status_code == 200:
                return True, None
            return False, f"Health check failed: {response.status_code}"
        except Exception as e:
            return False, f"Health check error: {str(e)}"
    
    def login(self, email: str, password: str, device_name: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Login and get session token
        
        Returns:
            (success, response_data, error_message)
        """
        try:
            payload = {
                'email': email,
                'password': password
            }
            if device_name:
                payload['device_name'] = device_name
            
            response = self.post('/auth/login', json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if 'session_token' in data:
                    self.set_token(data['session_token'])
                return True, data, None
            else:
                error_msg = response.json().get('message', f"Login failed: {response.status_code}")
                return False, None, error_msg
        except Exception as e:
            return False, None, f"Login error: {str(e)}"
    
    def refresh_token(self, refresh_token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Refresh session token"""
        try:
            response = self.post('/auth/refresh', json={'refresh_token': refresh_token})
            
            if response.status_code == 200:
                data = response.json()
                if 'session_token' in data:
                    self.set_token(data['session_token'])
                return True, data, None
            else:
                error_msg = response.json().get('message', f"Token refresh failed: {response.status_code}")
                return False, None, error_msg
        except Exception as e:
            return False, None, f"Token refresh error: {str(e)}"
    
    def logout(self) -> Tuple[bool, Optional[str]]:
        """Logout"""
        try:
            response = self.post('/auth/logout')
            self.clear_token()
            
            if response.status_code == 200:
                return True, None
            else:
                return False, f"Logout failed: {response.status_code}"
        except Exception as e:
            return False, f"Logout error: {str(e)}"
    
    def request_magic_link(self, email: str) -> Tuple[bool, Optional[str]]:
        """Request magic link"""
        try:
            response = self.post('/auth/magic-link/request', json={'email': email})
            
            if response.status_code == 200:
                return True, None
            else:
                error_msg = response.json().get('message', f"Magic link request failed: {response.status_code}")
                return False, error_msg
        except Exception as e:
            return False, f"Magic link request error: {str(e)}"
    
    def verify_magic_link(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Verify magic link token"""
        try:
            response = self.post('/auth/magic-link/verify', json={'token': token})
            
            if response.status_code == 200:
                data = response.json()
                if 'session_token' in data:
                    self.set_token(data['session_token'])
                return True, data, None
            else:
                error_msg = response.json().get('message', f"Magic link verification failed: {response.status_code}")
                return False, None, error_msg
        except Exception as e:
            return False, None, f"Magic link verification error: {str(e)}"
    
    def validate_license(self) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Validate license"""
        try:
            response = self.get('/license/validate')
            
            if response.status_code == 200:
                return True, response.json(), None
            else:
                error_msg = response.json().get('message', f"License validation failed: {response.status_code}")
                return False, None, error_msg
        except Exception as e:
            return False, None, f"License validation error: {str(e)}"
    
    def get_license_info(self) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Get license information"""
        try:
            response = self.get('/license/info')
            
            if response.status_code == 200:
                return True, response.json(), None
            else:
                error_msg = response.json().get('message', f"License info failed: {response.status_code}")
                return False, None, error_msg
        except Exception as e:
            return False, None, f"License info error: {str(e)}"
    
    def register_device(self, device_name: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Register device"""
        try:
            response = self.post('/devices/register', json={'device_name': device_name})
            
            if response.status_code == 200 or response.status_code == 201:
                return True, response.json(), None
            else:
                error_msg = response.json().get('message', f"Device registration failed: {response.status_code}")
                return False, None, error_msg
        except Exception as e:
            return False, None, f"Device registration error: {str(e)}"
    
    def list_devices(self) -> Tuple[bool, Optional[list], Optional[str]]:
        """List devices"""
        try:
            response = self.get('/devices')
            
            if response.status_code == 200:
                return True, response.json(), None
            else:
                error_msg = response.json().get('message', f"Device list failed: {response.status_code}")
                return False, None, error_msg
        except Exception as e:
            return False, None, f"Device list error: {str(e)}"
    
    def delete_device(self, device_id: int) -> Tuple[bool, Optional[str]]:
        """Delete device"""
        try:
            response = self.delete(f'/devices/{device_id}')
            
            if response.status_code == 200 or response.status_code == 204:
                return True, None
            else:
                error_msg = response.json().get('message', f"Device deletion failed: {response.status_code}")
                return False, error_msg
        except Exception as e:
            return False, f"Device deletion error: {str(e)}"
