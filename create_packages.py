"""
Helper script to create both development and production package variants.
"""

from create_deployment_package import create_deployment_package

def main():
    print("="*80)
    print("UPLOAD BRIDGE - PACKAGE CREATION HELPER")
    print("="*80)
    print()
    print("This script will create two package variants:")
    print("  1. Development/Internal (with LICENSE_KEYS.txt)")
    print("  2. Production/Hardened (without LICENSE_KEYS.txt)")
    print()
    
    response = input("Create both packages? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    print()
    print("Creating Development/Internal package...")
    print("-" * 80)
    dev_pkg = create_deployment_package(include_license_keys=True)
    if dev_pkg:
        print(f"✓ Development package: {dev_pkg}")
    
    print()
    print("Creating Production/Hardened package...")
    print("-" * 80)
    prod_pkg = create_deployment_package(include_license_keys=False)
    if prod_pkg:
        print(f"✓ Production package: {prod_pkg}")
    
    print()
    print("="*80)
    print("✅ PACKAGE CREATION COMPLETE")
    print("="*80)
    print()
    print("Next steps:")
    print("  1. Review package contents in dist/")
    print("  2. Test the packages before distribution")
    print("  3. Use production package for public releases")
    print("  4. Use development package for internal testing")

if __name__ == "__main__":
    main()

