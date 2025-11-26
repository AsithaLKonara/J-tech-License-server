# Master Investigation Matrix – Upload Bridge

This file is the central index of features, flows, integrations, data entities, and other key items to be validated. Each row will be refined as we perform deeper analysis.

## Columns

- **ID**: Stable identifier (e.g., UB-1, FLOW-Upload-1, INT-LED-1, DATA-Project-1).
- **Item Type**: `Feature`, `Flow`, `Screen/Tool`, `API/Script`, `Integration`, `Data Entity`, `Business Rule`, `Test`, etc.
- **Name**: Short descriptive label.
- **Description**: What this item is and why it exists.
- **Source of Truth**: Docs/spec file or test that defines expected behavior.
- **Owner / Module**: Primary code modules or directories responsible.
- **Implementation Status**: `Unknown`, `Not Implemented`, `Partial`, `Full`.
- **Integration Status**: For items that interact with others: `Unknown`, `Aligned`, `Mismatched`, `Missing`.
- **Validation & Rules**: Summary of validation/business rules in play.
- **Error Handling**: Summary of how errors are surfaced or handled.
- **Security / Permissions**: Any access controls or safety constraints.
- **Logging / Monitoring**: Notes on logging, observability, or diagnostics.
- **Test Coverage**: `None`, `Manual only`, `Unit`, `Integration`, `E2E`, combinations.
- **Known Issues**: Short summary of gaps or problems discovered.
- **Severity / Risk**: `Low`, `Medium`, `High`, `Critical`.
- **Next Actions**: Concrete follow-ups (investigate, fix, clarify spec, etc.).

## Seed Rows (Features)

These are initial rows corresponding to the Upload Bridge feature inventory; they will be enriched as the investigation proceeds.

| ID | Item Type | Name | Description | Source of Truth | Owner / Module | Implementation Status | Integration Status | Validation & Rules | Error Handling | Security / Permissions | Logging / Monitoring | Test Coverage | Known Issues | Severity / Risk | Next Actions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UB-1 | Feature | Canvas authoring toolbox | High-resolution LED matrix canvas with interactive tools. | `docs/FEATURE_OVERVIEW.txt` (Section 1) | `ui/widgets/matrix_design_canvas.py`, `ui/tabs/design_tools_tab.py` | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |  |  | Map flows, validations, and tests for canvas interactions. |
| UB-6 | Feature | Frame & layer management | Multi-frame animations with per-frame duration and layer editing. | `docs/FEATURE_OVERVIEW.txt` (Section 2) | `ui/widgets/timeline_widget.py`, `ui/widgets/layer_panel.py`, `domain/frames.py`, `domain/layers.py` | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |  |  | Trace full file-open → frame-edit → export flow. |
| UB-9 | Feature | Automation queue (legacy) | Legacy frame-baking automation for scripted transformations. | `docs/FEATURE_OVERVIEW.txt` (Section 3) | `ui/tabs/design_tools_tab.py`, `core/automation/preview_simulator.py` | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |  |  | Compare automation behaviors vs LMS automation suite; verify preview vs finalize. |
| UB-12 | Feature | LMS automation suite | Runtime LMS instruction builder, queue, preview, and IO. | `docs/FEATURE_OVERVIEW.txt` (Section 4) | `ui/tabs/design_tools_tab.py`, `core/io/lms_formats.py`, `parsers/*.py` | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |  |  | Validate instruction mapping, import/export, and preview alignment. |
| UB-15 | Feature | Custom effects engine | CPU-side image effects with preview and range apply. | `docs/FEATURE_OVERVIEW.txt` (Section 5) | `ui/widgets/effects_library_widget.py`, `ui/tabs/design_tools_tab.py`, `domain/effects.py` (or similar) | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |  |  | Confirm available effects, parameter ranges, and performance. |
| UB-17 | Feature | File import/export & metadata guards | Multi-format IO with dimension provenance and warnings. | `docs/FEATURE_OVERVIEW.txt` (Section 6) | `core/io/lms_formats.py`, `core/file_format_detector.py`, `core/dimension_scorer.py`, `core/pattern_exporter.py`, `ui/tabs/design_tools_tab.py` | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |  |  | Verify all formats and their detection heuristics end-to-end. |
| UB-20 | Feature | Diagnostics & hardware support | Diagnostic scripts/assets and firmware templates. | `docs/FEATURE_OVERVIEW.txt` (Section 7) | `verify_*.py`, `create_diagnostic_pattern.py`, `firmware/*`, `wifi_upload/*` | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |  |  | Cross-check diagnostic flows with hardware docs and tests. |
| UB-22 | Feature | Theme & UX facilities | Theming, playback controls, status overlays, warnings. | `docs/FEATURE_OVERVIEW.txt` (Section 8) | `ui/main_window.py`, `ui/widgets/*`, `ui/tabs/design_tools_tab.py` | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |  |  | Validate navigation, warnings, and appearance consistency. |
| UB-25 | Feature | Package creation & distribution | Scripts to build complete and deployment packages. | `docs/FEATURE_OVERVIEW.txt` (Section 9) | `create_complete_package.py`, `create_deployment_package.py`, `create_final_package.py`, `build_package.py` | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |  |  | Confirm required assets/configs are included and verified. |
| UB-27 | Feature | Documentation set | Narrative docs and workflow descriptions. | `docs/*.md`, `PACKAGE_README.md`, `PROJECT_OVERVIEW.md` | `docs/*`, root `*.md` docs | Unknown | N/A | Unknown | N/A | N/A | N/A | Unknown |  |  | Align documentation with implementation across major flows. |
| UB-29 | Feature | Testing & validation | Automated tests and manual regression checklists. | `docs/FEATURE_OVERVIEW.txt` (Section 11), `tests/*.py` | `tests/*`, `pytest.ini`, test runner scripts | Unknown | N/A | N/A | N/A | N/A | N/A | Unknown |  |  | Map tests to features and critical flows; identify gaps. |
| UB-31 | Feature | Safety, scratchpads & template tooling | Scratchpads, font tools, autosave, memory warnings, backups. | `docs/FEATURE_OVERVIEW.txt` (Section 12) | `domain/scratchpads.py`, `ui/tabs/design_tools_tab.py`, `ui/dialogs/font_designer_dialog.py`, `domain/text/bitmap_font.py`, `core/export_templates.py` | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |  |  | Verify scratchpad persistence, autosave behavior, and backup tooling. |

> Additional rows for flows, integrations, data entities, and tests will be appended as we enumerate them during the deep-dive steps.


