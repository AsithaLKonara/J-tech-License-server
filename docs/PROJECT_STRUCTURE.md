# Upload Bridge - Project Structure

**Last Updated**: 2025-01-XX  
**Status**: ✅ Organized

---

## 📁 Complete Directory Structure

```
upload_bridge/
│
├── 📄 main.py                    # Application entry point
├── 📄 setup.py                   # Package setup script
├── 📄 pytest.ini                 # Pytest configuration
├── 📄 requirements.txt           # Python dependencies
├── 📄 requirements_simple.txt    # Simplified dependencies
├── 📄 README.md                  # Main project README
├── 📄 LICENSE                    # License file
├── 📄 .gitignore                 # Git ignore rules
├── 📄 .pre-commit-config.yaml    # Pre-commit hooks
├── 📄 .ruff.toml                 # Ruff linter config
│
├── 📂 core/                      # Core services and business logic
│   ├── services/                 # Service layer (PatternService, ExportService, etc.)
│   ├── repositories/             # Data repositories
│   ├── events/                   # Event system
│   ├── errors/                   # Error handling
│   ├── export/                   # Export functionality
│   ├── config/                   # Configuration management
│   ├── logging/                  # Logging system
│   ├── health/                   # Health checks
│   ├── performance/              # Performance utilities
│   ├── security/                 # Security features
│   ├── schemas/                  # Data schemas
│   ├── metadata/                 # Metadata management
│   ├── project/                  # Project file handling
│   └── [core modules].py
│
├── 📂 domain/                     # Domain models and business logic
│   ├── animation/                # Animation system
│   ├── automation/               # Automation engine
│   ├── canvas/                   # Canvas rendering
│   ├── drawing/                  # Drawing tools
│   ├── effects/                  # Visual effects
│   ├── history/                  # Undo/redo system
│   ├── layer_blending/           # Layer blending modes
│   ├── performance/              # Performance domain logic
│   ├── text/                     # Text rendering
│   └── [domain models].py
│
├── 📂 ui/                         # User interface
│   ├── tabs/                     # Application tabs
│   │   ├── design_tools_tab.py
│   │   ├── preview_tab.py
│   │   ├── flash_tab.py
│   │   └── [other tabs].py
│   ├── widgets/                  # UI widgets
│   ├── dialogs/                  # Dialog windows
│   ├── icons/                    # Icon resources
│   ├── i18n/                     # Internationalization
│   ├── accessibility/            # Accessibility features
│   └── utils/                    # UI utilities
│
├── 📂 uploaders/                  # Hardware uploaders
│   ├── profiles/                 # Chip profiles (JSON)
│   ├── verification/             # Firmware verification
│   └── [chip uploaders].py
│
├── 📂 firmware/                   # Firmware templates
│   ├── templates/                # Firmware templates for all chips
│   └── [firmware generators].py
│
├── 📂 parsers/                    # File format parsers
│   └── [parser modules].py
│
├── 📂 wifi_upload/                # WiFi upload functionality
│   └── [wifi upload modules].py
│
├── 📂 license_server/             # License server
│   └── [license server files]
│
├── 📂 config/                     # Application configuration
│   ├── app_config.py
│   ├── app_config.yaml
│   ├── chip_database.py
│   ├── chip_database.yaml
│   ├── license_keys.yaml
│   └── LICENSE_KEYS.txt
│
├── 📂 scripts/                    # Utility scripts
│   ├── build/                     # Build and package scripts
│   │   ├── build_package.py
│   │   ├── create_*.py
│   │   └── CREATE_PACKAGE.bat
│   ├── install/                   # Installation scripts
│   │   ├── install_*.py
│   │   ├── install_*.bat
│   │   ├── install_*.sh
│   │   └── fix_*.py
│   ├── development/               # Development tools
│   │   ├── build_firmware.py
│   │   ├── flash_firmware.py
│   │   ├── debug_*.py
│   │   └── inspect_*.py
│   ├── testing/                   # Testing utilities
│   │   ├── coverage_gate.py
│   │   ├── generate_test_*.py
│   │   └── run_all_tests_*.py
│   ├── security/                  # Security tools
│   │   └── security_audit.py
│   ├── tools/                     # General tools
│   │   ├── detect_toolchains.py
│   │   ├── flash_cli.py
│   │   └── [other tools].py
│   ├── demos/                     # Demo scripts
│   │   ├── demo_*.py
│   │   └── upload_sample_pattern.py
│   ├── launch.py                  # Launch scripts
│   ├── launch_safe.py
│   ├── RUN.py
│   ├── RUN.sh
│   └── LaunchUploadBridge.vbs
│
├── 📂 tests/                      # Test suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   ├── e2e/                       # End-to-end tests
│   ├── comprehensive/             # Comprehensive test suites
│   ├── performance/               # Performance tests
│   ├── gui/                       # GUI tests
│   ├── ux/                        # UX tests
│   ├── edge_cases/                # Edge case tests
│   ├── regression/                # Regression tests
│   ├── meta/                       # Meta tests
│   ├── scripts/                   # Test runner scripts
│   ├── verification/              # Verification scripts
│   ├── data/                      # Test data files
│   └── [test files].py
│
├── 📂 docs/                       # Documentation
│   ├── architecture/              # Architecture documentation
│   ├── enterprise/                # Enterprise documentation
│   ├── operations/                # Operations guides
│   ├── testing/                   # Testing documentation
│   ├── ux/                        # UX documentation
│   ├── automation/                # Automation docs
│   ├── investigation/             # Investigation reports
│   ├── archive/                   # Archived documents
│   └── [documentation files].md
│
├── 📂 resources/                  # Static resources
│   ├── icons/                     # Application icons
│   ├── binaries/                  # Binary files
│   └── archives/                  # Archive files
│
├── 📂 data/                       # Runtime data
│   ├── cache/                     # Cache files
│   └── logs/                      # Log files
│
├── 📂 installer/                  # Installer scripts
│   ├── windows/                   # Windows installers
│   ├── macos/                     # macOS installers
│   ├── linux/                     # Linux installers
│   └── installer.py
│
├── 📂 docker/                     # Docker configurations
│   └── [chip dockerfiles]/
│
├── 📂 patterns/                   # Sample patterns
│   └── [pattern files]
│
├── 📂 Res/                        # Application resources
│   ├── effects/                   # Effect files
│   ├── fonts/                     # Font files
│   └── [other resources]
│
├── 📂 windows/                    # Windows-specific scripts
│   └── [windows scripts]
│
└── 📂 installers/                 # Legacy installers
    └── [installer files]
```

---

## 📋 Directory Descriptions

### Core Directories

#### `core/`
Core business logic, services, and infrastructure.
- **services/**: Service layer (PatternService, ExportService, FlashService)
- **repositories/**: Data access layer
- **events/**: Event bus and domain events
- **errors/**: Error handling system
- **export/**: Export functionality
- **config/**: Configuration management
- **logging/**: Logging infrastructure
- **health/**: Health check system
- **performance/**: Performance utilities
- **security/**: Security features
- **schemas/**: Data schemas and validation

#### `domain/`
Domain models and business logic.
- **animation/**: Animation system
- **automation/**: Automation engine
- **canvas/**: Canvas rendering
- **drawing/**: Drawing tools
- **effects/**: Visual effects library
- **history/**: Undo/redo system
- **layer_blending/**: Layer blending modes
- **text/**: Text rendering system

#### `ui/`
User interface components.
- **tabs/**: Main application tabs
- **widgets/**: Reusable UI widgets
- **dialogs/**: Dialog windows
- **icons/**: Icon resources
- **i18n/**: Internationalization
- **accessibility/**: Accessibility features

#### `uploaders/`
Hardware-specific uploaders.
- **profiles/**: Chip configuration profiles (JSON)
- **verification/**: Firmware verification utilities

#### `firmware/`
Firmware generation and templates.
- **templates/**: Firmware templates for all supported chips

### Supporting Directories

#### `scripts/`
Utility and helper scripts organized by purpose:
- **build/**: Build and packaging scripts
- **install/**: Installation scripts
- **development/**: Development tools
- **testing/**: Testing utilities
- **security/**: Security audit tools
- **tools/**: General utility tools
- **demos/**: Demo scripts

#### `tests/`
Complete test suite organized by test type.

#### `docs/`
All project documentation.

#### `resources/`
Static application resources (icons, binaries, archives).

#### `data/`
Runtime data (cache, logs).

#### `config/`
Application configuration files.

#### `installer/`
Platform-specific installer scripts.

---

## 📊 File Organization Rules

### Root Directory
Only essential files:
- `main.py` - Entry point
- `setup.py` - Package setup
- `README.md` - Main documentation
- `requirements.txt` - Dependencies
- Configuration files (`.gitignore`, `.ruff.toml`, etc.)

### Scripts Organization
- **Build scripts** → `scripts/build/`
- **Install scripts** → `scripts/install/`
- **Development tools** → `scripts/development/`
- **Testing tools** → `scripts/testing/`
- **Security tools** → `scripts/security/`
- **General tools** → `scripts/tools/`
- **Demos** → `scripts/demos/`
- **Launch scripts** → `scripts/` (root)

### Resources Organization
- **Icons** → `resources/icons/`
- **Binaries** → `resources/binaries/`
- **Archives** → `resources/archives/`

### Data Organization
- **Cache files** → `data/cache/`
- **Log files** → `data/logs/` (or `logs/`)

### Documentation Organization
- **All .md files** → `docs/` (except README.md)
- **Investigation docs** → `docs/investigation/`
- **Archived docs** → `docs/archive/`

---

## 🔄 Migration Notes

### Files Moved
- ✅ All build/package scripts → `scripts/build/`
- ✅ All install scripts → `scripts/install/`
- ✅ All demo scripts → `scripts/demos/`
- ✅ Development tools → `scripts/development/`
- ✅ Testing tools → `scripts/testing/`
- ✅ Security tools → `scripts/security/`
- ✅ General tools → `scripts/tools/`
- ✅ Resources → `resources/`
- ✅ Data files → `data/cache/`
- ✅ Investigation docs → `docs/investigation/`
- ✅ All .md files → `docs/` (except README.md)
- ✅ All test files → `tests/`

### Import Paths
Most imports should continue to work as package structure remains the same. Only script paths may need updates.

---

## 📝 Maintenance

### Adding New Files
1. **Scripts**: Place in appropriate `scripts/` subdirectory
2. **Tests**: Place in appropriate `tests/` subdirectory
3. **Documentation**: Place in `docs/` with appropriate subdirectory
4. **Resources**: Place in `resources/` with appropriate subdirectory
5. **Data**: Place in `data/` with appropriate subdirectory

### Naming Conventions
- **Scripts**: Use descriptive names, group by purpose
- **Tests**: Follow `test_*.py` convention
- **Documentation**: Use descriptive names with `.md` extension
- **Resources**: Use descriptive names, group by type

---

**Last Updated**: 2025-01-XX  
**Status**: ✅ Complete

