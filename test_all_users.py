"""
Test admin login and verify all users
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.e2e.helpers.api_client import APIClient

def test_all_users():
    """Test login for all seeded users"""
    api_client = APIClient(base_url="http://localhost:8000/api/v2")
    
    users = [
        ("admin@example.com", "admin123", "Admin"),
        ("trial@example.com", "password123", "Trial User"),
        ("monthly@example.com", "password123", "Monthly Subscriber"),
        ("yearly@example.com", "password123", "Yearly Subscriber"),
        ("perpetual@example.com", "password123", "Perpetual License Holder"),
        ("test@example.com", "testpassword123", "Test User"),
    ]
    
    print("Testing all seeded users...\n")
    print("=" * 70)
    
    for email, password, name in users:
        print(f"\nTesting: {name} ({email})")
        success, data, error = api_client.login(email, password)
        
        if success:
            print(f"  ✓ Login successful!")
            print(f"  User ID: {data['user']['id']}")
            print(f"  User Name: {data['user']['name']}")
            
            # Get license info
            success_info, license_data, error_info = api_client.get_license_info()
            if success_info:
                print(f"  ✓ License info retrieved")
                if 'entitlement' in license_data:
                    ent = license_data['entitlement']
                    print(f"    Plan: {ent.get('plan', 'N/A')}")
                    print(f"    Status: {ent.get('status', 'N/A')}")
                    print(f"    Max Devices: {ent.get('max_devices', 'N/A')}")
                    print(f"    Features: {', '.join(ent.get('features', []))}")
            
            # Clear token for next user
            api_client.clear_token()
        else:
            print(f"  ✗ Login failed: {error}")
    
    print("\n" + "=" * 70)
    print("All user tests completed!")

if __name__ == "__main__":
    test_all_users()
