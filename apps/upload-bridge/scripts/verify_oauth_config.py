"""
Verify OAuth Configuration - Check that Railway URL is being used
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config
from core.oauth_handler import build_auth_url, generate_pkce_pair, OAuthConfig

def verify_oauth_config():
    """Verify OAuth configuration uses Railway URLs."""
    
    print("=" * 60)
    print("OAuth Configuration Verification")
    print("=" * 60)
    print()
    
    # Load configuration
    config = get_config()
    
    # Check server URL
    auth_server_url = config.get("auth_server_url", "NOT SET")
    print(f"📡 License Server URL: {auth_server_url}")
    
    if "railway.app" in auth_server_url:
        print("   ✅ Using Railway server")
    elif "vercel.app" in auth_server_url:
        print("   ⚠️  Still using Vercel server")
    else:
        print("   ⚠️  Unknown server")
    print()
    
    # Check Auth0 configuration
    auth0_domain = config.get("auth0_domain") or config.get("auth_domain")
    auth0_client_id = config.get("auth0_client_id") or config.get("auth_client_id")
    auth0_audience = config.get("auth0_audience") or config.get("auth_audience")
    
    print(f"🔐 Auth0 Configuration:")
    print(f"   Domain: {auth0_domain or 'NOT SET'}")
    print(f"   Client ID: {auth0_client_id or 'NOT SET'}")
    print(f"   Audience: {auth0_audience or 'NOT SET'}")
    print()
    
    if not auth0_domain or not auth0_client_id:
        print("❌ Auth0 not fully configured!")
        return False
    
    # Check audience
    if auth0_audience:
        if "railway.app" in auth0_audience:
            print("   ✅ Audience uses Railway URL")
        elif "vercel.app" in auth0_audience:
            print("   ⚠️  Audience still uses Vercel URL")
        else:
            print("   ℹ️  Audience uses custom URL")
    else:
        print("   ℹ️  No audience set (optional)")
    print()
    
    # Build sample authorization URL
    print("🔗 Sample Authorization URL:")
    print("-" * 60)
    
    try:
        code_verifier, code_challenge = generate_pkce_pair()
        state = "test_state_12345"
        redirect_uri = "http://127.0.0.1:5000/callback"
        
        oauth_config = OAuthConfig(
            auth_domain=auth0_domain,
            client_id=auth0_client_id,
            audience=auth0_audience,
            scope="openid profile email offline_access"
        )
        
        auth_url = build_auth_url(oauth_config, redirect_uri, state, code_challenge)
        
        print(auth_url)
        print()
        
        # Check URL components
        if "railway.app" in auth_url:
            print("✅ Authorization URL contains Railway URL")
        elif "vercel.app" in auth_url:
            print("⚠️  Authorization URL still contains Vercel URL")
        
        # Check audience parameter
        if auth0_audience and "audience=" in auth_url:
            if "railway.app" in auth_url:
                print("✅ Audience parameter uses Railway URL")
            elif "vercel.app" in auth_url:
                print("⚠️  Audience parameter still uses Vercel URL")
        
    except Exception as e:
        print(f"❌ Error building URL: {e}")
        return False
    
    print()
    print("=" * 60)
    print("✅ Configuration Verification Complete")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = verify_oauth_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

