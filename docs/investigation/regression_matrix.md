# Regression & Change Impact Matrix – Upload Bridge

This matrix tracks significant changes, their affected areas, and required regression coverage.

## Columns

- **ID**: Change identifier (e.g., CHG-2025-11-Release-1).
- **Change Type**: `New feature`, `Refactor`, `Bugfix`, `Config`, etc.
- **Summary**: Short description of the change.
- **Source**: Where the change is documented (release notes, docs, git history).
- **Affected Features**: UB-* IDs impacted.
- **Affected Flows**: FLOW-* IDs impacted.
- **Affected Integrations**: INT-* IDs impacted.
- **Risk Level**: `Low`, `Medium`, `High`, `Critical`.
- **Regression Tests Needed**: Manual/automated tests to run.
- **Regression Tests Run**: Status and references.
- **Issues Found**: Bugs or regressions discovered.
- **Next Actions**: Follow-up work.

## Seed Change Rows

| ID | Change Type | Summary | Source | Affected Features | Affected Flows | Affected Integrations | Risk Level | Regression Tests Needed | Regression Tests Run | Issues Found | Next Actions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CHG-UniversalFix-1 | Release | Universal Fix package and LMS alignment updates | `UNIVERSAL_FIX_SUMMARY.md`, `UploadBridge_UniversalFix_v1.0_*.zip` | UB-12, UB-17, UB-20, UB-25, UB-31 | FLOW-Import-1, FLOW-Export-1, FLOW-Design-1 | INT-LMS-Import-1, INT-LMS-Export-1, INT-Diagnostics-1 | High | Full LMS import/export + diagnostics suite + Wi-Fi upload smoke tests | Unknown | Unknown | Populate after examining summary docs and running tests. |


