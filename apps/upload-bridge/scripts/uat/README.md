# UAT Automation Scripts

This directory contains automated test runners for User Acceptance Testing (UAT) scenarios.

## Overview

The UAT automation scripts help:
- Automate repetitive testing tasks
- Collect test results in structured format
- Validate core functionality programmatically
- Generate test reports

## Scripts

### `run_scenario.py`

Main script for running UAT scenarios programmatically.

**Usage**:
```bash
# Run all scenarios
python scripts/uat/run_scenario.py

# Run specific scenarios
python scripts/uat/run_scenario.py --scenarios 1 2 3

# Specify output directory
python scripts/uat/run_scenario.py --output-dir ./my_results

# Specify output filename
python scripts/uat/run_scenario.py --output-file my_test_results.json
```

**Available Scenarios**:
- `1`: Create New Pattern
- `2`: Import and Edit
- `3`: Animation Creation
- `4`: Multi-Layer Editing
- `5`: Template Usage
- `6`: Firmware Upload
- `7`: Invalid File Import (Error Handling)
- `8`: Device Connection Failure
- `9`: Large Pattern Handling
- `10`: Feature Discovery (requires manual testing)
- `11`: Workflow Efficiency (requires manual testing)

**Output**:
- Results are saved as JSON files in the output directory
- Each scenario result includes:
  - Status (pass/fail/error)
  - Duration
  - Errors and warnings
  - Notes

## Limitations

Note that some scenarios require manual user interaction and cannot be fully automated:
- **Scenario 4**: Multi-Layer Editing (requires UI)
- **Scenario 5**: Template Usage (requires template files)
- **Scenario 6**: Firmware Upload (requires hardware)
- **Scenario 8**: Device Connection (requires hardware)
- **Scenario 10**: Feature Discovery (requires human observation)
- **Scenario 11**: Workflow Efficiency (requires human timing)

These scenarios will be marked with warnings in the results.

## Results Format

Results are saved as JSON with the following structure:

```json
{
  "start_time": "2024-01-01T12:00:00",
  "end_time": "2024-01-01T12:05:00",
  "scenarios": {
    "1: Create New Pattern": {
      "name": "1: Create New Pattern",
      "status": "pass",
      "start_time": "2024-01-01T12:00:00",
      "end_time": "2024-01-01T12:00:05",
      "duration_seconds": 5.2,
      "errors": [],
      "warnings": [],
      "notes": ["Pattern created successfully"]
    }
  },
  "summary": {
    "total": 11,
    "passed": 9,
    "failed": 0,
    "errors": 0,
    "pass_rate": 81.8
  }
}
```

## Integration with Manual Testing

These automated scripts complement manual UAT testing:
- Automated scripts validate core functionality
- Manual testing validates UI/UX and user workflows
- Both results should be combined for complete UAT assessment

## Requirements

- Python 3.10+
- PySide6 (for UI-related scenarios)
- Project dependencies (see `requirements.txt`)

## Notes

- Some scenarios are simplified versions of full UAT scenarios
- Manual testing is still required for complete UAT coverage
- Results should be reviewed and combined with manual test results

