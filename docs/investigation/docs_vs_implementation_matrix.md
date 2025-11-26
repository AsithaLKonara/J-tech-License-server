# Docs vs Implementation Matrix – Upload Bridge

This matrix compares key documented features/flows against their observed implementations and notes mismatches or uncertainties.

## Columns

- **ID**: UB-* feature ID or FLOW-* flow ID.
- **Name**: Doc-level feature/flow name.
- **Doc Source**: Where the behavior is described.
- **Implementation Reference**: Where it appears in code.
- **Alignment Status**: `Aligned`, `Partial`, `Impl Ahead`, `Docs Ahead`, `Unknown`.
- **Notes / Mismatches**: Important details and gaps.

## Feature-Level Comparison

| ID | Name | Doc Source | Implementation Reference | Alignment Status | Notes / Mismatches |
| --- | --- | --- | --- | --- | --- |
| UB-1–5 | Canvas authoring toolbox (canvas, tools, undo/redo, palette) | `docs/FEATURE_OVERVIEW.txt` §1 | `ui/widgets/matrix_design_canvas.py`, `ui/tabs/design_tools_tab.py`, `domain/frames.py`, `domain/layers.py`, `domain.canvas` | Aligned | Code structure (MatrixDesignCanvas, CanvasController, HistoryManager, PatternState palette) matches described architecture and behaviors. |
| UB-6–8 | Frame & layer management | `docs/FEATURE_OVERVIEW.txt` §2 | `ui/widgets/timeline_widget.py`, `ui/widgets/layer_panel.py`, `domain/frames.py`, `domain/layers.py` | Aligned | Timeline and layer panel widgets, plus dimension warning logic via metadata snapshots, are present and consistent with docs. |
| UB-9–11 | Automation queue (legacy frame baking) | `docs/FEATURE_OVERVIEW.txt` §3 | `ui/tabs/design_tools_tab.py`, `core/automation/preview_simulator.py`, `domain/automation/*` | Partial | Core behaviors (DesignAction, ACTION_PARAM_CONFIG, preview vs finalize flows) are implemented; long-term intent is to favor LMS automation, and some edge behaviors may differ from historical LMS automation semantics. |
| UB-12–14 | LMS automation suite (instruction builder, queue, import/export/analyze) | `docs/FEATURE_OVERVIEW.txt` §4, `docs/automation/lms_automation.md` | `ui/tabs/design_tools_tab.py`, `core/io/lms_formats.py`, `core/automation/*`, `tests/unit/test_lms_formats.py` | Partial | Instruction builder and LEDS import/export are implemented; however LEDS export omits instruction parameters beyond code/repeat, and DAT/HEX/BIN analysis does not capture serpentine/color-order metadata fully. |
| UB-15–16 | Custom effects engine | `docs/FEATURE_OVERVIEW.txt` §5 | `ui/widgets/effects_library_widget.py`, `domain/effects.py`, `ui/tabs/design_tools_tab.py` | Aligned | Effects library and application paths exist and match described preview/apply semantics; detailed per-effect intensity curves are implementation-specific but reasonable. |
| UB-17–19 | File importers/exporters & metadata guards | `docs/FEATURE_OVERVIEW.txt` §6, IO-related docs | `core/io/lms_formats.py`, `core/file_format_detector.py`, `core/dimension_scorer.py`, `core/pattern_exporter.py`, `ui/tabs/design_tools_tab.py` | Partial | Import/export functionality and metadata snapshots are implemented; guards exist, but some LMS export options (wiring, color order) are not fully reconstructed on analysis, leading to potential mismatch with OEM LMS outputs. |
| UB-20–21 | Diagnostics & hardware support | `docs/FEATURE_OVERVIEW.txt` §7, `DIAGNOSTIC_TOOLS_README.md` | `verify_speed_brightness_pixel_order.py`, `verify_all_16_wiring_combinations.py`, `create_diagnostic_pattern.py`, `firmware/*`, `wifi_upload/*` | Aligned | Diagnostic scripts and sample patterns match described behaviors; tests like `verify_speed_brightness_pixel_order` enforce invariants (e.g., speed/brightness not affecting pixel order). |
| UB-22–24 | Theme & UX facilities | `docs/FEATURE_OVERVIEW.txt` §8, `UI_IMPROVEMENTS_SUMMARY.md` | `ui/tabs/design_tools_tab.py`, `ui/widgets/*`, `ui/main_window.py` | Aligned | THEME_DEFINITIONS, playback controls, and inline warnings exist; UX polish appears slightly ahead of high-level docs. |
| UB-25–26 | Package creation & distribution scripts | `docs/FEATURE_OVERVIEW.txt` §9, `PACKAGE_DISTRIBUTION_GUIDE.md` | `create_complete_package.py`, `create_deployment_package.py`, `build_package.py` | Partial | Packaging scripts match overall description but currently include license keys and broad config/docs; docs do not explicitly call out this potential exposure. |
| UB-27–28 | Documentation set & LMS parity research | `docs/*.md`, `docs/automation/*.md`, `final fixing and upgrade plan resources` | Docs themselves | Aligned | Documentation coverage is extensive and mostly matches implementation; LMS parity research is reflected in automation and IO modules. |
| UB-29–30 | Testing & validation | `docs/FEATURE_OVERVIEW.txt` §11, `FINAL_VERIFICATION_CHECKLIST.md`, `tests/*.py` | `tests/unit/*`, `tests/integration/*`, `tests/automation/*` | Aligned | Tests exist for filename hints, LMS formats, preview simulator, and more; some newer flows (Wi-Fi UI, license flows) could benefit from additional automated coverage. |
| UB-31–34 | Safety, scratchpads & template tooling | `docs/FEATURE_OVERVIEW.txt` §12 | `domain/scratchpads.py`, `ui/dialogs/font_designer_dialog.py`, `domain/text/bitmap_font.py`, `core/export_templates.py`, autosave logic in `design_tools_tab` | Aligned | Scratchpad manager, font designer, export templates, and autosave/memory warnings are present and behave as described; minor details (e.g., autosave intervals) are implementation-specific rather than fully documented. |

## Flow-Level Comparison

| ID | Name | Doc Source | Implementation Reference | Alignment Status | Notes / Mismatches |
| --- | --- | --- | --- | --- | --- |
| FLOW-Design-1 | Main design/editing flow | `COMPLETE_FLOW_DOCUMENTATION.md`, `USER_FLOWS.md`, `FEATURE_OVERVIEW` §1–2 | `ui/main_window.py`, `ui/tabs/design_tools_tab.py`, `ui/widgets/*`, `domain/*` | Aligned | High-level user journey (open pattern → edit frames/layers → preview) matches the documented flows. |
| FLOW-Import-1 | File open / analyze / import flow | `FILE_OPEN_TO_EXPORT_FLOW.md`, `FEATURE_OVERVIEW` §6 | `ui/tabs/design_tools_tab.py`, `core/io/lms_formats.py`, `core/file_format_detector.py`, `core/dimension_scorer.py` | Partial | Import/analysis UX and metadata guards are implemented; some subtle LMS export flags (wiring, color order) are not fully reconstructed on analysis, which is not fully spelled out in docs. |
| FLOW-Export-1 | Export to LEDS/BIN/HEX and MCU templates | `AUTO_DETECT_AND_BRIGHTNESS_SUMMARY.md`, `UNIVERSAL_FIX_SUMMARY.md`, `FEATURE_OVERVIEW` §4 & §6 | `core/pattern_exporter.py`, `core/export_templates.py`, `ui/tabs/design_tools_tab.py` | Partial | Export flows work and align with docs at a high level; LEDS and template exports do not preserve all LMS parameters (gaps, custom JSON), which is not clearly documented. |
| FLOW-Automation-1 | Automation queue & preview | `FEATURE_OVERVIEW` §3, automation docs | `ui/tabs/design_tools_tab.py`, `core/automation/preview_simulator.py` | Partial | Queue construction and preview vs finalize behaviors match docs; coverage of all historical LMS automation actions is not complete in `PreviewSimulator._apply_action`. |
| FLOW-LMS-1 | LMS automation & sequence preview | `docs/automation/lms_automation.md`, `FEATURE_OVERVIEW` §4 | `ui/tabs/design_tools_tab.py`, `core/io/lms_formats.py`, `core/automation/*` | Partial | Overall behavior is aligned; parameter loss in LEDS export and partial action-code coverage create subtle deviations from the legacy LMS tool. |
| FLOW-Package-1 | Package build & distribution | `PACKAGE_DISTRIBUTION_GUIDE.md`, `UNIVERSAL_FIX_SUMMARY.md` | `create_complete_package.py`, `create_deployment_package.py`, `create_final_package.py` | Partial | Behavior of packaging scripts matches docs, but security/privacy implications of bundling all docs/configs/license keys are not discussed. |
| FLOW-WiFi-1 | Wi-Fi upload flow | `WIFI_INTEGRATION_COMPLETE.md`, `WIFI_UPLOAD_UI_ENHANCEMENTS.md` | `ui/tabs/wifi_upload_tab.py`, `wifi_upload/wifi_uploader.py` | Partial | UI and uploader implement the described Wi-Fi upload workflow; docs emphasize convenience but do not fully discuss the lack of authentication/TLS on `/api/*` endpoints. |


