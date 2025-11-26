# Folder Structure Reorganization Plan

## Current Issues
- Many loose files in root directory
- Build/package scripts scattered
- Demo scripts in root
- Launch scripts in root
- Data files in root
- Resources mixed with code

## Proposed Structure

```
upload_bridge/
├── upload_bridge/          # Main package (if needed)
├── core/                   # Core services and logic ✅
├── domain/                 # Domain models ✅
├── ui/                     # User interface ✅
├── uploaders/              # Chip-specific uploaders ✅
├── parsers/                # File parsers ✅
├── firmware/               # Firmware templates ✅
├── wifi_upload/            # WiFi upload functionality ✅
├── license_server/         # License server ✅
│
├── tests/                  # All tests ✅
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── scripts/
│   ├── verification/
│   └── data/
│
├── docs/                   # All documentation ✅
│
├── scripts/                # Utility scripts (expand)
│   ├── build/              # Build scripts
│   ├── install/            # Installation scripts
│   ├── tools/              # Development tools
│   └── deployment/         # Deployment scripts
│
├── tools/                  # Development tools (keep or merge)
│
├── resources/              # Static resources (NEW)
│   ├── icons/              # Icons
│   ├── binaries/           # Binary files
│   ├── patterns/           # Sample patterns
│   └── fonts/              # Fonts (if any)
│
├── data/                   # Runtime data (NEW)
│   ├── config/             # Configuration files
│   ├── cache/              # Cache files
│   └── logs/               # Log files (already exists)
│
├── installer/              # Installer scripts ✅
│
├── docker/                 # Docker configs ✅
│
├── config/                 # App config (already exists) ✅
│
├── patterns/               # Pattern files (keep or move to resources)
│
├── Res/                    # Resources (keep or reorganize)
│
├── investigation/          # Investigation docs (move to docs/)
│
├── windows/                # Windows-specific scripts ✅
│
├── .github/                # GitHub workflows (if exists)
│
├── main.py                 # Entry point ✅
├── setup.py                # Setup script ✅
├── pytest.ini              # Pytest config ✅
├── requirements.txt        # Dependencies ✅
├── requirements_simple.txt # Simple requirements ✅
├── README.md               # Main README ✅
└── LICENSE                 # License file
```

## Files to Move

### Build/Package Scripts → scripts/build/
- create_complete_installer.py
- create_complete_package.py
- create_deployment_package.py
- create_final_package.py
- create_gui_installer.py
- create_installer.py
- create_packages.py
- create_professional_installer.py
- create_working_installer.py
- build_package.py
- CREATE_PACKAGE.bat

### Installation Scripts → scripts/install/
- install_all_requirements.bat
- install_all_requirements.sh
- install_simple.bat
- install_tools.py
- INSTALL_UPLOAD_BRIDGE.bat
- fix_installer.py
- fix_missing_config.py

### Launch Scripts → scripts/
- launch.py
- launch_safe.py
- RUN.py
- RUN.sh
- LaunchUploadBridge.vbs

### Demo Scripts → scripts/demos/
- demo_advanced_controls.py
- demo_cli.py
- demo_media_conversion.py
- upload_sample_pattern.py

### Utility Scripts → scripts/tools/
- detect_toolchains.py
- flash_cli.py
- create_diagnostic_pattern.py

### Resources → resources/
- LEDMatrixStudio_Icon.ico → resources/icons/
- diagnostic_12x6.bin → resources/binaries/
- UploadBridge_UniversalFix_*.zip → resources/archives/ (or delete if not needed)

### Data Files → data/
- pattern_detection_results.json → data/cache/
- pattern_results.txt → data/cache/
- temp_output.txt → data/cache/ (or delete)
- verification_status.json → data/cache/
- checkup_report.json → data/cache/

### License Files → config/
- LICENSE_KEYS.txt → config/ (already in config/)

### Spec Files → installer/
- UploadBridge_Test.spec → installer/windows/
- UploadBridge.spec → installer/windows/
- UploadBridgeInstaller.spec → installer/windows/

### Investigation Docs → docs/investigation/
- investigation/* → docs/investigation/

### Misc
- "final fixing and upgrade plan resources" → docs/archive/ or delete
- patterns/ → resources/patterns/ (or keep as is)

