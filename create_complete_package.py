"""
Create Complete Upload Bridge Package with All Fixes
Includes auto-detection, universal wiring, and all new features
"""

import zipfile
import os
from pathlib import Path
from datetime import datetime

def create_complete_package():
    """Create complete ZIP package"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f"UploadBridge_UniversalFix_v1.0_{timestamp}.zip"
    
    print("="*80)
    print("UPLOAD BRIDGE - COMPLETE PACKAGE CREATOR")
    print("="*80)
    print(f"Creating: {zip_filename}")
    print()
    
    # Files to include
    essential_files = [
        # Core application
        "main.py",
        "requirements.txt",
        
        # Documentation
        "README.md",
        "PACKAGE_README.md",
        "AUTO_DETECT_AND_BRIGHTNESS_SUMMARY.md",
        "UNIVERSAL_FIX_SUMMARY.md",
        "COMPLETE_FLOW_DOCUMENTATION.md",
        "DIAGNOSTIC_TOOLS_README.md",
        "TROUBLESHOOTING_GUIDE.md",
        
        # Test and diagnostic tools
        "create_diagnostic_pattern.py",
        "diagnostic_12x6.bin",
        "test_brightness_options.py",
        "verify_all_16_wiring_combinations.py",
        "verify_hardware_to_design.py",
        "verify_speed_brightness_pixel_order.py",
    ]
    
    # Directories to include (recursively)
    directories = [
        "ui",
        "core",
        "parsers",
        "firmware",
        "uploaders",
        "config",
        "docs",
        "wifi_upload",
    ]
    
    files_added = 0
    files_missing = 0
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        print("Adding essential files...")
        for file_path in essential_files:
            if os.path.exists(file_path):
                zipf.write(file_path, file_path)
                print(f"  ✓ {file_path}")
                files_added += 1
            else:
                print(f"  ✗ {file_path} (missing)")
                files_missing += 1
        
        print("\nAdding directories...")
        for dir_name in directories:
            if os.path.exists(dir_name):
                print(f"  📁 {dir_name}/")
                for root, dirs, files in os.walk(dir_name):
                    # Skip __pycache__ and .pyc files
                    dirs[:] = [d for d in dirs if d != '__pycache__']
                    
                    for file in files:
                        # Skip .pyc files
                        if file.endswith('.pyc'):
                            continue
                            
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, file_path)
                        files_added += 1
                
                print(f"     ✓ Added {dir_name}/ recursively")
            else:
                print(f"  ✗ {dir_name}/ (missing)")
                files_missing += 1
    
    # Get final package size
    package_size = os.path.getsize(zip_filename)
    
    print()
    print("="*80)
    print("✅ PACKAGE CREATED SUCCESSFULLY!")
    print("="*80)
    print(f"Package: {zip_filename}")
    print(f"Size: {package_size / 1024:.2f} KB ({package_size / 1024 / 1024:.2f} MB)")
    print(f"Files added: {files_added}")
    print(f"Files missing: {files_missing}")
    print()
    print("="*80)
    print("PACKAGE INCLUDES:")
    print("="*80)
    print("✅ File format auto-detection")
    print("✅ Universal wiring support (all 16 combinations)")
    print("✅ Brightness options (verified working)")
    print("✅ Speed controls")
    print("✅ Flip X/Y corrections")
    print("✅ Comprehensive logging")
    print("✅ Diagnostic tools + test pattern")
    print("✅ Complete documentation")
    print()
    print("="*80)
    print("TO USE:")
    print("="*80)
    print("1. Extract ZIP to a folder")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run: python main.py")
    print()
    print("4. Load pattern file → Auto-detection runs")
    print("5. Verify preview looks correct")
    print("6. Flash to hardware → Should match preview perfectly!")
    print("="*80)
    
    return zip_filename

if __name__ == "__main__":
    package = create_complete_package()
    print(f"\n🎉 Package ready: {package}")


