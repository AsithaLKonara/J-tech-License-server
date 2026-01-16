#!/usr/bin/env python3
"""
Update Vercel License Server URL
Updates the auth_config.yaml with the Vercel deployment URL
"""

import sys
import yaml
from pathlib import Path

def update_vercel_url(vercel_url: str):
    """Update auth_config.yaml with Vercel URL"""
    config_file = Path(__file__).parent.parent.parent / "config" / "auth_config.yaml"
    
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        return False
    
    try:
        # Read current config
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        # Update server URL
        config['auth_server_url'] = vercel_url
        
        # Write back
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Updated auth_server_url to: {vercel_url}")
        print(f"   Config file: {config_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python update_vercel_url.py <vercel-url>")
        print("Example: python update_vercel_url.py https://your-project.vercel.app")
        sys.exit(1)
    
    vercel_url = sys.argv[1].rstrip('/')  # Remove trailing slash
    
    if not vercel_url.startswith('http'):
        print("❌ URL must start with http:// or https://")
        sys.exit(1)
    
    if update_vercel_url(vercel_url):
        print("\n✅ Configuration updated successfully!")
        print("\nNext steps:")
        print("  1. Restart Upload Bridge application")
        print("  2. Test login with: test@example.com / testpassword123")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

