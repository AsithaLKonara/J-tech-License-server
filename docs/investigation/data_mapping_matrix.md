# Data Mapping Matrix – Upload Bridge

This matrix tracks key data concepts and how they are represented and validated across UI, domain, core logic, file formats, and tests.

## Columns

- **ID**: Data identifier (e.g., DATA-Project-1).
- **Concept / Field**: Business-level concept or field.
- **Source of Truth**: Documentation or spec describing the field.
- **UI Representation**: Widgets, dialogs, or tabs where it appears.
- **Domain / Core Representation**: Domain models and core modules.
- **Storage Representation**: Files, DB (if any), or in-memory formats.
- **Transformations**: Known conversions or derived values.
- **Validation Points**: Where and how validation is enforced.
- **Issues / Inconsistencies**: Any mismatches or gaps.
- **Severity / Risk**: `Low`, `Medium`, `High`, `Critical`.
- **Next Actions**: Follow-up investigation or fixes.

## Seed Data Concepts

| ID | Concept / Field | Source of Truth | UI Representation | Domain / Core Representation | Storage Representation | Validation Points | Issues / Inconsistencies | Severity / Risk | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DATA-Project-1 | Project / Pattern metadata (width, height, frames, color mode) | `docs/FEATURE_OVERVIEW.txt`, `docs/LED_MATRIX_STUDIO_FEATURES.txt` | `ui/dialogs/new_pattern_dialog.py`, `ui/tabs/design_tools_tab.py` | `core.pattern.PatternMetadata`, `domain/frames.py`, `domain/layers.py`, `core/dimension_scorer.py`, `core/file_format_detector.py` | Pattern files (BIN, DAT, HEX, LEDS), autosaves, project configs | New pattern dialogs and import flows enforce positive dimensions; DAT/HEX parsers raise on non-positive width/height/frame_count; dimension scorer compares candidates to heuristics. | Wiring mode (`serpentine`) and orientation are not fully preserved from DAT/HEX/BIN analysis (defaulted to non-serpentine row-major), even though LMS exports can encode alternates. | Medium | Core entity defining matrix shape and animation length; mismatches can cause previews to differ from hardware. |
| DATA-Frame-1 | Frame pixels and duration | `FEATURE_OVERVIEW`, LMS docs | `matrix_design_canvas`, `timeline_widget` | `core.pattern.Frame`, `domain/frames.py`, `core/automation/preview_simulator.py` | Pattern files, LEDS instructions (indirect) | Frame durations validated implicitly via FPS controls and pattern metadata; `PreviewSimulator` expects consistent `width × height` pixel counts and non-empty frame lists. | No explicit cross-check that all frames share the same dimensions; malformed patterns could slip in via external file manipulation. | Low–Medium | Per-frame pixel grids plus per-frame timing; robustness relies on upstream file IO and pattern creation paths. |
| DATA-LMS-1 | LMS instructions and sequences | `docs/automation/lms_automation.md`, `FEATURE_OVERVIEW` | LMS Automation UI in `design_tools_tab` | `core/io/lms_formats.py`, `core/automation/*` | LEDS files, MCU templates | UI validates instruction fields before constructing `PatternInstruction`; LEDS parser enforces required fields and integer repeat counts; invalid lines raise `LMSFormatError`. | Instruction parameters beyond `code` and `repeat` (e.g., gaps, JSON params) are not serialized to LEDS, so they cannot be round-tripped through files. | Medium | Runtime instruction sequences consumed by firmware; parameter loss mainly affects advanced behaviors. |
| DATA-IO-1 | File import metadata (detected geometry, wiring hints) | IO sections in docs | Import/analysis dialogs in design tools tab | `core/io/lms_formats.py`, `core/file_format_detector.py`, `core/dimension_scorer.py` | Pattern files and temp structures | DAT header, HEX record, and BIN payload parsing all validate basic structure; dimension scorer and file-format detector attempt to infer plausible geometries. | Heuristics do not incorporate all of LED Matrix Studio’s export options (serpentine, color order), and may mis-detect ambiguous BIN layouts without guidance from presets or filenames. | Medium | Auto-detected vs manual dimension sources and wiring hints; critical for avoiding rotated/mirrored outputs on hardware. |
| DATA-Scratchpad-1 | Scratchpad slots and content | `FEATURE_OVERVIEW` Section 12 | Scratchpad UI in design tools tab | `domain/scratchpads.py`, `domain.pattern_state.PatternState` | Project state and autosaves | `ScratchpadManager` constrains slots to `[1..max_slots]` and ensures per-pattern `scratchpads` dict exists; `is_slot_filled` checks for non-empty pixel lists. | No obvious issues; behavior depends on `PatternState.pattern()` being available, with a safe fallback while UI is initializing. | Low | Reusable frame/motif storage across projects; main risk is UX (discoverability) rather than data corruption. |


