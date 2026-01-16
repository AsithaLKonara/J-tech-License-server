# Cursor AI Tasks

This directory contains YAML task definitions for Cursor AI to automate test generation, fixing, and maintenance.

## Available Tasks

### 1. Test Generation Task (`test_generation.yaml`)
Auto-generates or updates all tests for full coverage using the MASTER TESTING CHECKLIST.

**Usage**: Load this task in Cursor and let it analyze the codebase and generate missing tests.

### 2. Auto-Fix Task (`test_auto_fix.yaml`)
Fixes all failing tests by correcting implementation code or tests.

**Usage**: Run this when tests are failing to automatically fix issues.

### 3. Coverage Enforcement Task (`coverage_enforcement.yaml`)
Confirms >= 85% coverage and auto-writes missing tests.

**Usage**: Run this to ensure coverage threshold is met before merging.

### 4. Regression Sweep Task (`regression_sweep.yaml`)
Runs all workflows end-to-end and identifies breakpoints.

**Usage**: Run this to catch workflow regressions before release.

## How to Use

1. Open Cursor AI
2. Navigate to Tasks panel
3. Load the desired YAML task file
4. Let Cursor execute the task
5. Review and commit changes

## Task Structure

Each task YAML file contains:
- **name**: Task name
- **description**: What the task does
- **steps**: Sequential actions to perform
- **requirements/constraints**: Rules to follow

## Customization

You can modify these tasks to:
- Change coverage thresholds
- Add new test suites
- Modify test generation rules
- Add custom validation steps

