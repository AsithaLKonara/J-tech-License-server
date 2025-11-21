# Changelog

All notable changes to Upload Bridge will be documented in this file.

## [Unreleased] - 2025-01-XX

### Added
- **Deep System Investigation & Audit**: Comprehensive investigation matrices tracking features, integrations, data flows, security, and documentation alignment
- **IO Metadata Fidelity Improvements**: DAT/HEX/BIN parsers now correctly mark wiring/orientation as unknown instead of hard-coding defaults
- **LEDS Round-Tripping**: Full preservation of LMS instruction parameters (gap, JSON params) through import/export cycles
- **Enhanced LMS Preview Coverage**: Implemented `fade` and `randomize` actions, improved `brightness` handling, proper `scrollText` no-op behavior
- **WiFi Security Documentation**: Added explicit security notes in documentation and UI warning users about trusted network requirements
- **Packaging Flexibility**: Added `include_license_keys` parameter to deployment package script for hardened production builds
- **License Cache Tests**: Comprehensive test coverage for encrypted license precedence, cache-valid offline behavior, and stale cache handling
- **UX Improvements**: Added tooltips to Analyze dialogs and "Open Docs" buttons in LMS Automation and WiFi Upload tabs

### Changed
- **BIN Layout Inference**: Now uses shared `score_dimensions` helper for consistent layout detection with confidence scores
- **LMS Format Documentation**: Updated to clarify that DAT/HEX/BIN don't encode wiring/orientation, and LEDS exports include Upload Bridge extensions
- **Test Infrastructure**: Fixed pytest module name conflicts, added timeout protection and test markers (gui, network, slow)

### Fixed
- **Module Name Conflict**: Resolved pytest import collision between `tests/unit/test_presets.py` and `tests/integration/test_presets.py`
- **Metadata Ambiguity**: IO parsers now explicitly communicate when wiring/orientation are unknown vs inferred

### Security
- **WiFi Upload Warnings**: Added UI-level security notices about trusted network requirements
- **Packaging Security**: Deployment script now supports excluding offline license keys from production packages

---

## Previous Releases

[Previous changelog entries would go here]

