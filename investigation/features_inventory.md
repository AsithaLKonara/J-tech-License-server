# Upload Bridge – Preliminary Feature Inventory

This file structures the major features and behaviors described in `docs/FEATURE_OVERVIEW.txt` and `docs/LED_MATRIX_STUDIO_FEATURES.txt`. It will be refined as we map features to concrete implementations and flows.

## Columns

- **ID**: Stable identifier for cross-referencing in other matrices.
- **Source**: `UPLOAD_BRIDGE` or `LED_MATRIX_STUDIO`.
- **Section**: High-level section in the source document.
- **Name**: Short feature name.
- **Category**: Rough grouping (Canvas, Animation, Automation, IO, Packaging, Docs, Testing, etc.).
- **Description**: Concise summary of what the feature does.

## Feature List

| ID | Source | Section | Name | Category | Description |
| --- | --- | --- | --- | --- | --- |
| UB-1 | UPLOAD_BRIDGE | 1. Canvas Authoring Toolbox | High-resolution LED matrix canvas | Canvas | Interactive matrix canvas with point-and-click painting tools. |
| UB-2 | UPLOAD_BRIDGE | 1. Canvas Authoring Toolbox | Pixel/shape/gradient/fill tools | Canvas | Tools for pixels, rectangles, circles, lines, fill, gradients with palette-backed colors. |
| UB-3 | UPLOAD_BRIDGE | 1. Canvas Authoring Toolbox | Undo/redo & layer-aware editing | Canvas | History-backed editing with layer awareness for scoped undo/redo. |
| UB-4 | UPLOAD_BRIDGE | 1. Canvas Authoring Toolbox | Random spray & gradient broadcast | Canvas/Automation | Random Spray and Gradient brushes with multi-frame broadcast toggle. |
| UB-5 | UPLOAD_BRIDGE | 1. Canvas Authoring Toolbox | Palette & color management | Canvas | Palette stored on `PatternState` and bound to UI controls. |
| UB-6 | UPLOAD_BRIDGE | 2. Frame & Layer Management | Multi-frame animations | Animation | Frame list with per-frame duration, ordering, and playback controls. |
| UB-7 | UPLOAD_BRIDGE | 2. Frame & Layer Management | Per-frame, per-layer editing | Layers | Layer panel with visibility/lock and composite sync to frames. |
| UB-8 | UPLOAD_BRIDGE | 2. Frame & Layer Management | Dimension mismatch warnings | Validation | UI warnings when frame sizes diverge from pattern metadata/imported dimensions. |
| UB-9 | UPLOAD_BRIDGE | 3. Automation Queue | Scripted transformations | Automation | Legacy frame-baking automation (scroll, wipe, mirror, rotate, color cycle, etc.). |
| UB-10 | UPLOAD_BRIDGE | 3. Automation Queue | Automation wizard | Automation | Wizard for stacking actions with shared repeats/gaps and fade hooks. |
| UB-11 | UPLOAD_BRIDGE | 3. Automation Queue | Preview vs finalize automation | Automation | Non-destructive preview vs baking LMS instructions into pattern state. |
| UB-12 | UPLOAD_BRIDGE | 4. LMS Automation Suite | LMS instruction builder | LMS/Automation | UI for building raw MCU runtime instructions (Layer1/2/Mask, repeats, gaps, brightness, JSON params). |
| UB-13 | UPLOAD_BRIDGE | 4. LMS Automation Suite | LMS queue & preview | LMS/Automation | Playlist management and preview of instruction sequences via `PreviewSimulator`. |
| UB-14 | UPLOAD_BRIDGE | 4. LMS Automation Suite | Import/export/analyze DAT/HEX/BIN/LEDS | IO | Import/export LEDS and analyze DAT/HEX/BIN files, surfacing metadata before flashing. |
| UB-15 | UPLOAD_BRIDGE | 5. Custom Effects Engine | CPU-side image effects | Effects | Fade, blur, sharpen, brightness, contrast, color shift, noise, pixelate with intensity control. |
| UB-16 | UPLOAD_BRIDGE | 5. Custom Effects Engine | Effect preview & range apply | Effects | Preview on single frame and apply across frame ranges with history updates. |
| UB-17 | UPLOAD_BRIDGE | 6. File Import/Export & Metadata Guards | Multi-format import | IO | Import patterns from BIN, DAT, HEX, LEDS with auto-detected dimensions and wiring hints. |
| UB-18 | UPLOAD_BRIDGE | 6. File Import/Export & Metadata Guards | Multi-format export & MCU templates | IO | Exporters for raw binary, Intel HEX, LEDS, MCU templates with metadata annotation. |
| UB-19 | UPLOAD_BRIDGE | 6. File Import/Export & Metadata Guards | Dimension provenance & warnings | Validation | Tracking dimension origin and surfacing divergence warnings in UI. |
| UB-20 | UPLOAD_BRIDGE | 7. Diagnostics & Hardware Support | Diagnostic scripts & patterns | Diagnostics | Scripts and assets to validate speed, brightness, pixel order, wiring combinations. |
| UB-21 | UPLOAD_BRIDGE | 7. Diagnostics & Hardware Support | Wi-Fi upload & firmware templates | Firmware | Wi-Fi upload helpers and firmware templates for reference MCU builds. |
| UB-22 | UPLOAD_BRIDGE | 8. Theme & UX Facilities | Theming & appearance | UX | Dark/light themes and consistent styling across UI components. |
| UB-23 | UPLOAD_BRIDGE | 8. Theme & UX Facilities | Playback & preview UX | UX | Timeline zoom, FPS controls, loop toggles, and status overlays. |
| UB-24 | UPLOAD_BRIDGE | 8. Theme & UX Facilities | Inline warnings & autosync preview | UX/Validation | Inline warnings for dimension/import/export issues and preview sync with canvas. |
| UB-25 | UPLOAD_BRIDGE | 9. Package Creation & Distribution | Complete package builder | Packaging | `create_complete_package.py` bundling core app, docs, diagnostics, firmware, Wi-Fi upload. |
| UB-26 | UPLOAD_BRIDGE | 9. Package Creation & Distribution | Deployment-specific packages | Packaging | Deployment package scripts for targeted MCU/customer releases. |
| UB-27 | UPLOAD_BRIDGE | 10. Documentation Set | Narrative docs set | Docs | README, PACKAGE_README, auto-detect summaries, troubleshooting guides, LMS automation docs. |
| UB-28 | UPLOAD_BRIDGE | 10. Documentation Set | LED Matrix Studio parity research | Docs | `final fixing and upgrade plan resources` capturing OEM workflows for parity. |
| UB-29 | UPLOAD_BRIDGE | 11. Testing & Validation | Automated tests | Testing | PyTest suites for filename hints, LMS formats, automation simulator, instruction serialization, etc. |
| UB-30 | UPLOAD_BRIDGE | 11. Testing & Validation | Lint & manual regression | Testing | Lint checks and manual regression checklists derived from docs. |
| UB-31 | UPLOAD_BRIDGE | 12. Safety, Scratchpads & Template Tooling | Scratchpad manager | Workflow | Ten-slot scratchpad manager for copying frames/motifs across projects. |
| UB-32 | UPLOAD_BRIDGE | 12. Safety, Scratchpads & Template Tooling | Bitmap font designer & repository | Fonts | Bitmap Font Designer, font repository, and MCU code template exports. |
| UB-33 | UPLOAD_BRIDGE | 12. Safety, Scratchpads & Template Tooling | Autosave & memory warnings | Safety | Configurable autosave and live memory usage warnings for oversize animations. |
| UB-34 | UPLOAD_BRIDGE | 12. Safety, Scratchpads & Template Tooling | Font backup tooling | Safety | One-click backup/zip of custom fonts under `Res/fonts`. |


| LMS-1 | LED_MATRIX_STUDIO | 1. Matrix Configuration & Display Modes | Matrix size & color depth | Canvas | Project-level width/height and color depth configuration (mono, bi-color, RGB). |
| LMS-2 | LED_MATRIX_STUDIO | 1. Matrix Configuration & Display Modes | Special geometries | Canvas | Rectangular, circular, hollow square, radial, semi-circle matrix previews. |
| LMS-3 | LED_MATRIX_STUDIO | 2. Drawing & Editing Tools | Core drawing tools | Canvas | Pixel toggle, freehand, rectangles, circles, line tool, text insertion. |
| LMS-4 | LED_MATRIX_STUDIO | 2. Drawing & Editing Tools | Multi-draw & transformations | Canvas/Automation | Multi-draw edits all frames; flip, mirror, invert, rotate, scroll transformations. |
| LMS-5 | LED_MATRIX_STUDIO | 3. Frame & Animation Management | Frame management & GIF IO | Animation/IO | Unlimited frames, GIF import/export, frame duplication and reordering. |
| LMS-6 | LED_MATRIX_STUDIO | 4. Layers, Buffers & Presets | Layers & scratchpads | Layers/Workflow | Unlimited layers and ten scratchpads for reusable content. |
| LMS-7 | LED_MATRIX_STUDIO | 4. Layers, Buffers & Presets | Hardware presets | Workflow | Presets for common resolutions/color modes to speed new project setup. |
| LMS-8 | LED_MATRIX_STUDIO | 5. Text & Font Designer | Text tool | Fonts | Built-in text insertion with 5×7/3×5 fonts. |
| LMS-9 | LED_MATRIX_STUDIO | 5. Text & Font Designer | Font designer mode | Fonts | Mode for designing and storing custom single-color or RGB fonts. |
| LMS-10 | LED_MATRIX_STUDIO | 6. Automatic Animation Creation | Automate wizard | Automation | Wizard that generates animations by scripted actions (scrolls, wipes, bounces, color cycles, etc.). |
| LMS-11 | LED_MATRIX_STUDIO | 7. Preview Modes | Zoom & mapping previews | UX | Zoom controls and alternate mapping previews (radial, detached window, etc.). |
| LMS-12 | LED_MATRIX_STUDIO | 8. Import/Export & Code Templates | Export engine | IO | Binary/decimal/hex export with wiring/scan order, color order, brightness scaling. |
| LMS-13 | LED_MATRIX_STUDIO | 8. Import/Export & Code Templates | MCU code templates | IO/Firmware | `codeTemplates` system for Arduino, PIC, PICAXE, Parallax code generation. |
| LMS-14 | LED_MATRIX_STUDIO | 9. Randomization & Gradient | Random & gradient brushes | Canvas | Random color tool and gradient brush with palette endpoints and brush sizes. |
| LMS-15 | LED_MATRIX_STUDIO | 10. Undo/Redo & Auto-save | Undo/redo & autosave | Safety | Per-frame undo/redo stacks and periodic autosave of project files. |
| LMS-16 | LED_MATRIX_STUDIO | 11. Workflow Summary & Tips | End-to-end workflow | Workflow | Recommended sequence from matrix setup to MCU export and hardware validation. |
| LMS-17 | LED_MATRIX_STUDIO | 12–13. Tips & Limitations | Limits & best practices | Constraints | Known limitations (max sizes, automation assumptions) and best practices. |

> This inventory is intentionally high-level. During mapping and deep dives, we will refine IDs, add sub-feature rows (e.g., per effect, per import format), and attach implementation and test coverage details via the master investigation matrix.

## Feature → Implementation Mapping (Initial Pass)

This section records likely implementation locations for each Upload Bridge feature, to be expanded into the full master matrix.

| ID | Primary Modules / Files | Notes |
| --- | --- | --- |
| UB-1–5 (Canvas & tools) | `ui/widgets/matrix_design_canvas.py`, `ui/tabs/design_tools_tab.py`, `domain/frames.py`, `domain/layers.py` | Canvas widget, design tools tab wiring, and frame/layer domain models. |
| UB-6–8 (Frames & layers) | `ui/widgets/timeline_widget.py`, `ui/widgets/layer_panel.py`, `domain/frames.py`, `domain/layers.py` | Timeline and layer panel widgets plus backing domain logic. |
| UB-9–11 (Automation queue) | `ui/tabs/design_tools_tab.py`, `core/automation/preview_simulator.py`, `core/automation/__init__.py`, `docs/automation/*.md` | Legacy frame-baking automation and preview simulator. |
| UB-12–14 (LMS automation suite) | `ui/tabs/design_tools_tab.py`, `core/io/lms_formats.py`, `parsers/*.py`, `tests/unit/test_lms_formats.py` | LMS instruction builder UI plus format parsing/serialization. |
| UB-15–16 (Custom effects engine) | `ui/widgets/effects_library_widget.py`, `domain/effects.py` (or similar effect helpers), `ui/tabs/design_tools_tab.py` | Effects widget and effect application logic referenced in design tools tab. |
| UB-17–19 (Import/export & metadata) | `core/io/lms_formats.py`, `core/file_format_detector.py`, `core/dimension_scorer.py`, `core/pattern_exporter.py`, `ui/tabs/design_tools_tab.py` | File IO, detection, scoring, and exporter modules plus tab integration. |
| UB-20–21 (Diagnostics & hardware support) | `verify_speed_brightness_pixel_order.py`, `verify_all_16_wiring_combinations.py`, `create_diagnostic_pattern.py`, `wifi_upload/*.py`, `firmware/*` | Diagnostic scripts and firmware/Wi-Fi upload helpers. |
| UB-22–24 (Theme & UX facilities) | `ui/main_window.py`, `ui/tabs/design_tools_tab.py`, `ui/widgets/*`, `config/theme_config.py` (if present) | Theme application and UX wiring across main window and tabs. |
| UB-25–26 (Package creation & distribution) | `create_complete_package.py`, `create_deployment_package.py`, `create_final_package.py`, `build_package.py`, `PACKAGE_DISTRIBUTION_GUIDE.md` | Packaging scripts and distribution docs. |
| UB-27–28 (Documentation set & LMS parity) | `docs/*.md`, `docs/automation/*.md`, `final fixing and upgrade plan resources`, `PROJECT_OVERVIEW.md` | Narrative documentation and OEM parity research. |
| UB-29–30 (Testing & validation) | `tests/unit/*.py`, `tests/integration/*.py`, `tests/automation/*.py`, `pytest.ini`, `FINAL_VERIFICATION_CHECKLIST.md` | Automated test suites and manual verification checklists. |
| UB-31–34 (Scratchpads, fonts, autosave, safety) | `domain/scratchpads.py`, `ui/tabs/design_tools_tab.py`, `ui/dialogs/font_designer_dialog.py`, `domain/text/bitmap_font.py`, `core/export_templates.py`, `build/autosaves` (runtime), `Res/fonts/*` | Scratchpad domain logic, font designer dialog, bitmap font repo, export templates, autosave paths, and font backup behavior. |

> LED Matrix Studio features (LMS-*) are external reference points and are not mapped to code here, but will be used in the feature-comparison and compatibility matrices.


