#!/usr/bin/env python3
"""
Test Auth0 API Configuration

The error "Service not found" means the audience URL needs to be
configured as an API in Auth0.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config

def check_api_config():
    """Check API configuration"""
    print("=" * 70)
    print("Auth0 API Configuration Check")
    print("=" * 70)
    print()
    
    config = get_config()
    audience = config.get("auth0_audience") or config.get("auth_audience")
    
    print("📋 Current Configuration:")
    print(f"   Audience: {audience}")
    print()
    
    print("❌ Error: 'Service not found: {audience}'")
    print()
    print("💡 This means the audience URL needs to be configured as an API in Auth0")
    print()
    print("🔧 How to Fix:")
    print()
    print("Step 1: Create API in Auth0")
    print("   1. Go to: https://manage.auth0.com/")
    print("   2. Select tenant: dev-oczlciw58f2a4oei")
    print("   3. Click 'Applications' → 'APIs' (in left sidebar)")
    print("   4. Click 'Create API' button")
    print()
    print("Step 2: Configure API")
    print("   Name: J-Tech License Server (or any name)")
    print(f"   Identifier: {audience}")
    print("   Signing Algorithm: RS256")
    print("   Click 'Create'")
    print()
    print("Step 3: Authorize Application")
    print("   1. In the API you just created, go to 'Machine to Machine Applications' tab")
    print("   2. Find your application: AVLPE7EULVWdJV5NIzFI56EAeHmnt2Um")
    print("   3. Toggle it ON (authorize it)")
    print("   4. Select scopes if needed (or leave default)")
    print()
    print("Step 4: Alternative - Use Application Audience")
    print("   If you don't want to create an API, you can:")
    print("   1. Remove the 'audience' parameter from authorization URL")
    print("   2. Or set audience to the Auth0 domain")
    print()
    print("🔗 Direct Links:")
    print("   APIs: https://manage.auth0.com/dashboard/us/dev-oczlciw58f2a4oei/apis")
    print("   Create API: https://manage.auth0.com/dashboard/us/dev-oczlciw58f2a4oei/apis/create")
    print()

def check_alternative_solutions():
    """Check alternative solutions"""
    print("=" * 70)
    print("Alternative Solutions")
    print("=" * 70)
    print()
    
    print("Option 1: Create API in Auth0 (Recommended)")
    print("   → Follow steps above to create API with audience identifier")
    print()
    print("Option 2: Remove Audience Parameter")
    print("   → If you don't need a specific API audience, you can remove it")
    print("   → This will use Auth0's default token format")
    print()
    print("Option 3: Use Auth0 Domain as Audience")
    print("   → Set audience to: https://dev-oczlciw58f2a4oei.us.auth0.com/userinfo")
    print("   → This uses Auth0's userinfo endpoint")
    print()

def main():
    """Run check"""
    print()
    print("🔍 Auth0 API Configuration Check")
    print()
    
    check_api_config()
    check_alternative_solutions()
    
    print("=" * 70)
    print("✅ Check Complete")
    print("=" * 70)
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

