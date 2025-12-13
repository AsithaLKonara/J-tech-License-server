# Refactor PR Plan

**Date**: 2025-01-27  
**Purpose**: Detailed steps for 8 refactor PRs based on audit findings

---

## PR 1: Version & Python Version Consistency

**Branch**: `fix/version-consistency`  
**Priority**: Critical  
**Status**: ⚠️ **AUDIT SHOWS ALREADY FIXED** - Verify and document

### Files to Update

**Note**: Audit shows these are already correct, but verify:

- ✅ `setup.py` - Already has version="3.0.0" and python_requires=">=3.10"
- ✅ `core/config/config_manager.py` - Already has app_version='3.0.0'
- ✅ `tests/test_installation.py` - Already checks for Python 3.10+
- ✅ `docs/operations/DEPLOYMENT.md` - Already says Python 3.10+
- ✅ All docs/*.md - Already reference version 3.0.0

### Actions

1. **Verify Current State**: Run audit tests to confirm all files are correct
2. **Update QA_MISMATCH_REPORT.md**: Add note that version issues have been resolved
3. **Document**: Create note in changelog if needed

### Tests

- Run `tests/audit/test_version_consistency.py`
- Verify no version 1.0.0 references in code

---

## PR 2: Chip Database & Profile Alignment

**Branch**: `fix/chip-database-alignment`  
**Priority**: High  
**Status**: ⚠️ **ISSUES FOUND** - Needs fixing

### Files to Update

1. **`uploaders/profiles/atmega2560.json`**:
   - Change `chip_id: "ATmega2560"` → `chip_id: "atmega2560"`

2. **`uploaders/profiles/attiny85.json`**:
   - Change `chip_id: "ATtiny85"` → `chip_id: "attiny85"`

3. **`uploaders/profiles/pic18f4550.json`**:
   - Change `chip_id: "PIC18F4550"` → `chip_id: "pic18f4550"`

4. **`uploaders/profiles/esp32s3.json`**:
   - Change `chip_id: "ESP32"` → `chip_id: "esp32s3"`

5. **`config/chip_database.yaml`**:
   - Add `stm32f407` chip definition (if profile should exist)
   - OR remove `uploaders/profiles/stm32f407.json` if not needed
   - Add `nuvoton_m051` chip definition (if profile should exist)
   - OR remove `uploaders/profiles/nuvoton_m051.json` if not needed

6. **`docs/FEATURE_INVENTORY.md`**:
   - Update feature 9.3: Change file reference to `uploaders/avr_uploader.py`
   - Update feature 9.5: Change file reference to `uploaders/esp_uploader.py`
   - Update feature 9.8: Change file reference to `uploaders/avr_uploader.py`
   - Update feature 9.9: Change file reference to `uploaders/numicro_uploader.py`
   - Add notes about generic uploader usage

7. **`README.md`**:
   - Update chip count section to clarify "9 fully supported" vs "29 total chips"
   - Or list all 29 chips from database

### Tests

- Run `tests/audit/test_chip_support_verification.py`
- Verify all profile JSONs have correct chip_id
- Verify all chips in database can be loaded

---

## PR 3: Config System Consolidation

**Branch**: `fix/config-system-consolidation`  
**Priority**: Medium  
**Status**: ✅ **SYSTEM WORKING** - Optional cleanup

### Files to Update

**Option A: Remove Empty Modules** (Recommended)
- Delete `config/app_config.py` (empty, just imports)
- Delete `config/chip_database.py` (empty, just imports)

**Option B: Populate Modules** (Alternative)
- Move loading functions from `config/__init__.py` into respective modules

### Documentation

- Document when to use `core.config.ConfigManager` vs `config.load_*`
- Add examples to `docs/CONFIGURATION_GUIDE.md`

### Tests

- Run `tests/audit/test_config_system.py`
- Verify config loading still works after changes

---

## PR 4: Requirements File Documentation

**Branch**: `fix/requirements-documentation`  
**Priority**: Low  
**Status**: ✅ **ALREADY DOCUMENTED** - Verify completeness

### Files to Update

1. **`requirements_simple.txt`**:
   - ✅ Already has comments explaining minimal install
   - Verify comments are clear and complete

2. **`docs/INSTALLATION.md`**:
   - Add section: "Minimal vs Full Installation"
   - Document which features require which dependencies

3. **Create `docs/DEPENDENCY_MATRIX.md`** (optional):
   - Feature → Dependency mapping table
   - Installation guide for different use cases

### Tests

- Manual verification: Install from requirements_simple.txt
- Verify missing features are documented

---

## PR 5: Feature Count Verification & Documentation

**Branch**: `fix/feature-count-verification`  
**Priority**: Medium  
**Status**: ⚠️ **COUNTS VERIFIED** - Update README

### Files to Update

1. **`README.md`**:
   - Update automation actions: "8 parametric automation actions" → "12 automation actions"
   - Verify effects count: "92+ effects" (already correct - 92 verified)
   - Verify import formats: "17 import formats" (already correct)
   - Verify export formats: "12 export formats" (already correct)

### Verification Results

- ✅ Effects: 92 (verified)
- ✅ Automation Actions: 12 (exceeds "8+" claim)
- ✅ Import Formats: 17 (verified)
- ✅ Export Formats: 12 (verified)

### Tests

- Run `tests/audit/test_effects_count.py`
- Run `tests/audit/test_automation_count.py`
- Run `tests/audit/test_format_counts.py`

---

## PR 6: Code Quality Improvements

**Branch**: `refactor/code-quality`  
**Priority**: Medium  
**Status**: ⚠️ **ISSUES FOUND** - Needs review

### Issues Found

- **90 code quality issues** (TODO/FIXME/XXX/HACK/BUG comments)
- Many are in documentation files
- Some are in code files

### Actions

1. **Review All TODOs**:
   - Prioritize critical TODOs
   - Implement or document planned features
   - Remove obsolete TODOs

2. **Address FIXME Comments**:
   - Fix known bugs
   - Or document why they can't be fixed yet

3. **Remove HACK Comments**:
   - Replace temporary workarounds
   - Or document why hack is necessary

4. **Add Type Hints** (where missing):
   - Improve code maintainability
   - Better IDE support

5. **Improve Error Handling**:
   - Consistent error handling patterns
   - Proper exception types

### Tests

- Run existing test suite
- Verify no regressions
- Run code quality checks (flake8, mypy if configured)

---

## PR 7: Feature Status Documentation

**Branch**: `docs/feature-status-matrix`  
**Priority**: Low  
**Status**: ✅ **COMPLETED** - Documentation created

### Files Created

- ✅ `docs/FEATURE_STATUS_MATRIX.md` - Complete feature status
- ✅ `docs/IMPLEMENTATION_GAPS.md` - Gaps documented

### Actions

1. **Review Documentation**:
   - Verify accuracy of feature status
   - Update if needed based on testing

2. **Update FEATURE_INVENTORY.md** (if needed):
   - Mark actual status based on audit results
   - Fix file references (see PR 2)

### Tests

- Verification tests for each status category
- Manual review of documentation

---

## PR 8: Test Coverage for Audit Findings

**Branch**: `test/audit-coverage`  
**Priority**: High  
**Status**: ✅ **COMPLETED** - Tests created

### Files Created

- ✅ `tests/audit/test_version_consistency.py`
- ✅ `tests/audit/test_chip_support_verification.py`
- ✅ `tests/audit/test_config_system.py`
- ✅ `tests/audit/test_feature_verification.py`
- ✅ `tests/audit/test_drawing_tools_verification.py`
- ✅ `tests/audit/test_effects_count.py`
- ✅ `tests/audit/test_format_counts.py`
- ✅ `tests/audit/test_automation_count.py`

### Actions

1. **Run All Audit Tests**:
   - Verify all tests pass
   - Fix any test failures

2. **Integrate with Test Suite**:
   - Add to pytest configuration
   - Include in CI/CD if applicable

3. **Generate Coverage Report**:
   - Run coverage for audited areas
   - Document coverage metrics

### Tests

- Run full test suite including audit tests
- Verify coverage for audited areas

---

## PR Execution Order

### Recommended Order

1. **PR 7** (Documentation) - No code changes, can be merged immediately
2. **PR 8** (Tests) - Provides test coverage for other PRs
3. **PR 1** (Version) - Verify current state (may be no-op)
4. **PR 2** (Chips) - Critical fixes for chip support
5. **PR 5** (Feature Counts) - Update documentation
6. **PR 4** (Requirements) - Documentation improvements
7. **PR 3** (Config) - Optional cleanup
8. **PR 6** (Quality) - Ongoing improvement

---

## Summary

### PRs Ready to Merge

- ✅ **PR 7**: Feature Status Documentation (completed)
- ✅ **PR 8**: Test Coverage (completed)

### PRs Needing Implementation

- ⚠️ **PR 1**: Version Consistency (verify - may already be fixed)
- ⚠️ **PR 2**: Chip Database Alignment (needs fixes)
- ⚠️ **PR 3**: Config System (optional cleanup)
- ⚠️ **PR 4**: Requirements Documentation (verify completeness)
- ⚠️ **PR 5**: Feature Counts (update README)
- ⚠️ **PR 6**: Code Quality (review and fix issues)

---

**Plan Created**: 2025-01-27  
**Based On**: Comprehensive codebase audit results

