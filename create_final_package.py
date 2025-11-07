#!/usr/bin/env python3
"""
Create Final Package - Upload Bridge
Creates a complete ZIP package with all fixed components
"""

import os
import zipfile
import shutil
from datetime import datetime

def create_package():
    """Create the final package ZIP file"""
    
    # Package info
    package_name = "UploadBridge_Fixed_v1.0"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"{package_name}_{timestamp}.zip"
    
    print("=" * 60)
    print("Upload Bridge - Final Package Creator")
    print("=" * 60)
    print(f"Creating package: {zip_filename}")
    print()
    
    # Files to include in the package
    essential_files = [
        # Core application files
        "main.py",
        "launch_safe.py",
        "test_installation.py",
        "test_directory.py",
        
        # Requirements and setup
        "requirements_simple.txt",
        "setup.py",
        
        # Batch files (fixed versions)
        "LAUNCH_SAFE.bat",
        "RUN_SIMPLE.bat", 
        "install_simple.bat",
        "TEST_DIRECTORY.bat",
        
        # Documentation
        "QUICK_START_FIXED.md",
        "TROUBLESHOOTING_GUIDE.md",
        "FIX_DIRECTORY_ISSUE.md",
        "README.md",
        "AUTO_DETECT_AND_BRIGHTNESS_SUMMARY.md",
        "UNIVERSAL_FIX_SUMMARY.md",
        "COMPLETE_FLOW_DOCUMENTATION.md",
        "DIAGNOSTIC_TOOLS_README.md",
        
        # Test and diagnostic files
        "create_diagnostic_pattern.py",
        "diagnostic_12x6.bin",
        "test_brightness_options.py",
        "verify_all_16_wiring_combinations.py",
        "verify_hardware_to_design.py",
        "verify_speed_brightness_pixel_order.py",
        
        # UI files
        "ui/__init__.py",
        "ui/main_window.py",
        "ui/tabs/__init__.py",
        "ui/tabs/preview_tab.py",
        "ui/tabs/flash_tab.py",
        "ui/widgets/__init__.py",
        "ui/widgets/advanced_brightness_controller.py",
        "ui/widgets/advanced_speed_controller.py",
        "ui/widgets/enhanced_led_simulator.py",
        "ui/widgets/fps_controller.py",
        "ui/widgets/led_simulator.py",
        
        # Core modules
        "core/__init__.py",
        "core/pattern.py",
        "core/batch_flasher.py",
        "core/file_format_detector.py",
        "core/pattern_converter.py",
        "core/wiring_mapper.py",
        
        # Parsers
        "parsers/__init__.py",
        "parsers/base_parser.py",
        "parsers/enhanced_binary_parser.py",
        "parsers/intel_hex_parser.py",
        "parsers/parser_registry.py",
        "parsers/raw_rgb_parser.py",
        "parsers/standard_format_parser.py",
    ]
    
    # Create ZIP file
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        print("Adding files to package...")
        
        for file_path in essential_files:
            if os.path.exists(file_path):
                # Add file to ZIP
                zipf.write(file_path, file_path)
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ Missing: {file_path}")
        
        # Add any additional files that might exist
        additional_files = [
            "firmware/",
            "config/",
            "uploaders/",
            "docs/",
        ]
        
        for item in additional_files:
            if os.path.exists(item):
                if os.path.isdir(item):
                    # Add directory recursively
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, file_path)
                            print(f"  ✅ {file_path}")
                else:
                    zipf.write(item, item)
                    print(f"  ✅ {item}")
    
    print()
    print("=" * 60)
    print("Package Created Successfully!")
    print("=" * 60)
    print(f"Package: {zip_filename}")
    print(f"Size: {os.path.getsize(zip_filename) / 1024 / 1024:.2f} MB")
    print()
    print("Package Contents:")
    print("- Fixed Upload Bridge application")
    print("- Simple installer (install_simple.bat)")
    print("- Safe launcher (LAUNCH_SAFE.bat)")
    print("- Installation test (test_installation.py)")
    print("- Complete documentation")
    print("- All UI and core modules")
    print()
    print("To use on another PC:")
    print("1. Extract the ZIP file")
    print("2. Run install_simple.bat")
    print("3. Run LAUNCH_SAFE.bat")
    print("=" * 60)
    
    return zip_filename

if __name__ == "__main__":
    create_package()










