# Integration & Contract Matrix – Upload Bridge

This matrix tracks how modules, scripts, and external systems interact and whether their data contracts are aligned.

## Columns

- **ID**: Integration identifier (e.g., INT-LMS-Import-1).
- **Source Module**: Producer of data (script, UI tab, core module).
- **Target Module / Service**: Consumer of data.
- **Interface Type**: `Function call`, `Module import`, `File IO`, `CLI`, `Network`, etc.
- **Endpoint / Channel**: Function names, file paths, network endpoints, etc.
- **Request / Input Contract (Expected)**: Fields, types, constraints.
- **Request / Input Contract (Actual)**: As implemented/observed.
- **Response / Output Contract (Expected)**: Expected results.
- **Response / Output Contract (Actual)**: Actual implementation behavior.
- **Validation & Error Handling**: How bad inputs and failures are handled.
- **Versioning / Compatibility**: Backwards compatibility, breaking changes.
- **Logging & Monitoring**: How the integration is observed and logged.
- **Issues / Mismatches**: Known discrepancies.
- **Severity / Risk**: `Low`, `Medium`, `High`, `Critical`.
- **Next Actions**: Follow-up investigation or fixes.

## Seed Integrations (High-Level)

| ID | Source Module | Target Module / Service | Interface Type | Endpoint / Channel | Notes / Expected Contract |
| --- | --- | --- | --- | --- | --- |
| INT-LMS-Import-1 | `ui/tabs/design_tools_tab.py` | `core/io/lms_formats.py` | File IO / Function call | `parse_leds_file`, `parse_dat_file`, `parse_hex_file`, `parse_bin_stream` | UI requests parsing of DAT/HEX/BIN/LEDS files and expects dimension/metadata inference plus validation errors. |
| INT-LMS-Export-1 | `ui/tabs/design_tools_tab.py` | `core/io/lms_formats.py`, `core/pattern_exporter.py` | File IO / Function call | `write_leds_file`, export helpers | UI exports patterns/instructions to disk with correct metadata and format. |
| INT-Automation-1 | `ui/tabs/design_tools_tab.py` | `core/automation/preview_simulator.py` | Function call | `PreviewSimulator` | Automation and LMS preview flows rely on preview simulator to generate frames from instructions/actions. |
| INT-Diagnostics-1 | Diagnostic scripts (e.g., `verify_speed_brightness_pixel_order.py`) | `core/io/lms_formats.py`, `parsers/*.py`, `patterns/*` | File IO / Script | Uses pattern files and parsers | Scripts validate patterns, wiring, and brightness by consuming pattern files and parser output. |
| INT-WiFi-1 | `ui/tabs/wifi_upload_tab.py`, `wifi_upload/wifi_uploader.py` | ESP devices / firmware | Network / HTTP | `/api/status`, `/api/upload` endpoints on device | Wi-Fi upload UI/scripts communicate with devices using HTTP APIs for status and pattern upload. |
| INT-Packaging-1 | `create_complete_package.py`, `create_deployment_package.py` | Entire repo (docs, firmware, wifi_upload, patterns, etc.) | File IO | Filesystem paths | Packaging scripts gather assets from multiple modules and must track required vs optional resources. |

## Integration Analysis (Expected vs Actual)

### INT-LMS-Import-1 – LMS file analysis & import

- **Request / input contract (expected)**:
  - `parse_dat_file(path)`: DAT files with header lines for `width height` and `frame_count`, followed by hex rows.
  - `parse_hex_file(path)`: Intel HEX records with valid checksums; optional `guess_bytes_per_pixel`.
  - `parse_bin_stream(data)`: Raw BIN payload with optional `width`, `height`, `bytes_per_pixel`.
  - `parse_leds_file(path)`: LEDS files with comment metadata, `PatternN:` instruction lines, and an optional `Data:` section.
- **Request / input contract (actual)** (from `core/io/lms_formats.py` and `ui/tabs/design_tools_tab.py`):
  - DAT/HEX/BIN helpers accept only a `Path` or `bytes` payload and infer most metadata; serpentine and orientation are hard-coded.
  - LEDS parser uses regex-based metadata extraction and constructs `PatternInstructionSequence` with `LayerBinding`/`LMSInstruction` instances.
- **Response / output contract (expected)**:
  - Return structured metadata (dimensions, color information, frame counts) plus raw rows/payload or instruction sequences for further processing.
- **Response / output contract (actual)**:
  - DAT: returns dict with `format`, `width`, `height`, `frame_count`, `color_space="RGB32"`, `color_order="RGB"`, `bit_packing="8-bit"`, `serpentine=False`, `orientation="RowLeftToRight"`, and `rows`.
  - HEX: returns dict with inferred `bytes_per_pixel`, `width`, `frame_count`, `color_space`, `color_order="RGB"`, `serpentine=False`, `orientation="RowLeftToRight"`.
  - BIN: returns dict with inferred or provided dimensions and similar metadata, plus `payload`.
  - LEDS: returns `metadata` dict, `PatternInstructionSequence` under `sequence`, and `data` lines list.
- **Validation & error handling**:
  - All helpers raise `LMSFormatError` for malformed headers, invalid checksums, zero dimensions, or invalid pattern lines; UI catches and shows message boxes on import/analysis (`_on_analyze_file`, `_on_lms_import_leds`).
- **Issues / mismatches**:
  - DAT/HEX/BIN analyses always set `serpentine=False` and a fixed orientation, even though legacy LED Matrix Studio exports can encode serpentine wiring and alternate scan orders; this loses wiring metadata unless re-specified elsewhere.
  - Color order is always reported as `"RGB"`, while hardware may use `GRB`/`BGR`; automatic mapping to hardware presets requires additional logic not encoded in these helpers.
  - BIN dimension inference uses a square-root heuristic and falls back to `width=total_pixels`, `height=1`, which can misrepresent multi-frame animations without guidance from project presets or filenames.
- **Versioning / compatibility**:
  - No explicit versioning for LEDS or other formats; future format changes could silently break parsing.
- **Logging & monitoring**:
  - Design tools tab logs summary dicts to the LMS message log; no structured logging beyond this.
- **Severity / risk**:
  - **Medium** for workflows that depend on accurate wiring/color metadata; **Low** for basic file inspection.
- **Next actions**:
  - Extend parsers to accept optional serpentine/orientation hints (from filenames or UI), propagate them into metadata, and expose ambiguous cases clearly.
  - Consider capturing more of LED Matrix Studio’s export options (wiring, color order) and surfacing them in the UI and pattern metadata.

### INT-LMS-Export-1 – LEDS export from UI to file

- **Request / input contract (expected)**:
  - Design tools tab passes a `PatternInstructionSequence` plus pattern metadata (`width`, `height`, `frames`, `format`, `serpentine`, `orientation`, `color_order`) to `write_leds_file`.
- **Request / input contract (actual)** (from `_on_lms_export_leds` in `design_tools_tab`):
  - Metadata is derived from `self._pattern.metadata` and `len(self._pattern.frames)` with sensible defaults when attributes are missing.
- **Response / output contract (expected)**:
  - LEDS output that can be re-imported by both Upload Bridge and original LED Matrix Studio, preserving dimensions and instruction behavior.
- **Response / output contract (actual)** (from `write_leds_file`):
  - Writes metadata as `# key: value` lines, then instruction lines `PatternN: source, code, layer2, mask, repeat`, then an optional `Data:` section.
  - Does not encode instruction parameters or brightness deltas beyond `code` and `repeat`.
- **Issues / mismatches**:
  - Extra LMS parameters (`gap`, custom JSON parameters) are not serialized, so they cannot be round-tripped through LEDS.
  - Data section defaults to a placeholder comment when `frame_data` is omitted, which is acceptable for instruction-only workflows but may surprise users expecting full frame exports.
- **Versioning / compatibility**:
  - No explicit LEDS version marker; relies on de-facto compatibility with legacy formats.
- **Logging & monitoring**:
  - Exports are logged in the LMS message log with dimensions and frame counts; no structured telemetry.
- **Severity / risk**:
  - **Medium** for advanced LMS parity (loss of parameters); **Low** for common scroll/rotate/mirror operations.
- **Next actions**:
  - Extend LEDS writing to optionally include serialized parameters and gap values, with backward-compatible defaults.
  - Document limitations in export dialogs so users understand which LMS features are fully preserved.

### INT-Automation-1 – Automation and LMS preview

- **Request / input contract (expected)**:
  - Design tools tab constructs `PatternInstructionSequence` objects from automation actions or LMS instructions and passes them, with the current `Pattern`, into `PreviewSimulator`.
- **Request / input contract (actual)**:
  - `PreviewSimulator` requires a `Pattern` with at least one frame and uses its metadata width/height for grid operations; sequences may reference `LayerBinding` slots like `"Frame1"` or explicit `frame_index` values.
- **Response / output contract (expected)**:
  - A sequence of preview `Frame` objects showing the visual effect of each instruction, bounded by `max_frames` if provided.
- **Response / output contract (actual)**:
  - `simulate_sequence` stops when `max_frames` is reached and falls back to frame 0 for unknown bindings; individual instructions map codes to transformations (`moveLeft1`, `rotate90`, `mirrorH`, `invert`, `brightness`, etc.).
- **Issues / mismatches**:
  - Unknown or unimplemented `code` values silently skip specialized behavior and may fall back to identity transforms, under-representing actual MCU behavior.
  - Some LMS actions described in docs may not have corresponding handlers in `_apply_action`, leading to previews that differ from firmware behavior.
- **Versioning / compatibility**:
  - No explicit mapping table version; adding new codes requires synchronized updates across UI, preview simulator, and firmware.
- **Logging & monitoring**:
  - No dedicated logging inside `PreviewSimulator`; issues are observable only via visual differences or tests.
- **Severity / risk**:
  - **Medium** for ensuring preview fidelity relative to runtime firmware.
- **Next actions**:
  - Enumerate all LMS action codes used in UI (`KNOWN_LMS_ACTIONS`) and ensure they have explicit implementations or documented limitations in `_apply_action`.
  - Strengthen tests (`tests/unit/automation/test_preview_simulator.py`) to cover representative instruction sequences and detect drift from MCU logic.
