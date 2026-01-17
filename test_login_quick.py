"""
Quick test script to verify login functionality
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.e2e.helpers.api_client import APIClient

def test_login():
    """Test login with test credentials"""
    print("Testing login endpoint...")
    
    api_client = APIClient(base_url="http://localhost:8000/api/v2")
    
    # Try to login with test credentials (matching DatabaseSeeder)
    email = "test@example.com"
    password = "testpassword123"  # Matches DatabaseSeeder
    
    print(f"Attempting login with {email}...")
    success, data, error = api_client.login(email, password)
    
    if success:
        print("✓ Login successful!")
        print(f"Response data: {data}")
        
        # Test that features are properly returned as array
        print("\nTesting license info endpoint...")
        success_info, license_data, error_info = api_client.get_license_info()
        if success_info:
            print("✓ License info retrieved successfully!")
            print(f"License data: {license_data}")
        else:
            print(f"✗ License info failed: {error_info}")
        
        return True
    else:
        print(f"✗ Login failed: {error}")
        return False

if __name__ == "__main__":
    success = test_login()
    sys.exit(0 if success else 1)
