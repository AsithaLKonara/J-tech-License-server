# UI / UX & Flow Matrix – Upload Bridge

This matrix tracks user-facing surfaces (GUIs and CLIs), their navigation, and their linkage to backend logic.

## Columns

- **ID**: UI/flow identifier (e.g., FLOW-Design-1).
- **Surface Type**: `GUI`, `CLI`, `Dialog`, etc.
- **Entry Points**: How the user gets here.
- **Exit Targets**: Where they can go next or what is triggered.
- **Related Features**: UB-* IDs tied to this surface.
- **Backend Modules**: Scripts or modules invoked.
- **Validation & Errors**: How input is validated and errors surfaced.
- **Security / Permissions**: Any access restrictions.
- **Logging / Monitoring**: Observability details.
- **Issues / Notes**: Observed or suspected UX issues.

## Seed UI/Flow Rows

| ID | Surface Type | Entry Points | Exit Targets | Related Features | Backend Modules | Validation & Errors | Security / Permissions | Logging / Monitoring | Issues / Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FLOW-Design-1 | GUI (Main design tools tab) | Launch app → Design Tools tab | Other tabs (Preview, Flash, Wi-Fi Upload, etc.), file export | UB-1, UB-2, UB-3, UB-6, UB-15, UB-17 | `ui/tabs/design_tools_tab.py`, `ui/widgets/*`, `domain/*`, `core/*` | Unknown | Unknown | Unknown | To be filled after detailed flow tracing. |
| FLOW-Import-1 | GUI (Pattern import flow) | Design Tools tab → Import | Canvas display, timeline populated | UB-17, UB-18, UB-19 | `ui/tabs/design_tools_tab.py`, `core/io/lms_formats.py`, `core/file_format_detector.py`, `core/dimension_scorer.py` | Unknown | Unknown | Unknown | Focus for IO and metadata guard verification. |
| FLOW-Export-1 | GUI (Pattern export flow) | Design Tools tab → Export | Files on disk, possibly firmware templates | UB-14, UB-18, UB-25 | `ui/tabs/design_tools_tab.py`, `core/pattern_exporter.py`, `core/io/lms_formats.py` | Unknown | Unknown | Unknown | Will be used to confirm alignment with LMS and MCU expectations. |
| FLOW-Automation-1 | GUI (Automation queue) | Design Tools tab → Automation panel | Updated frames or LMS instructions | UB-9, UB-10, UB-11 | `ui/tabs/design_tools_tab.py`, `core/automation/preview_simulator.py` | Unknown | Unknown | Unknown | Target for checking preview vs finalize differences. |
| FLOW-LMS-1 | GUI (LMS automation) | Design Tools tab → LMS Automation | LMS instructions persisted and exported | UB-12, UB-13, UB-14 | `ui/tabs/design_tools_tab.py`, `core/io/lms_formats.py`, `core/automation/*` | Unknown | Unknown | Unknown | Critical for runtime instruction correctness. |
| FLOW-Package-1 | CLI (Package creation) | Run packaging scripts | Generated ZIPs/installer artifacts | UB-25, UB-26 | `create_complete_package.py`, `create_deployment_package.py`, `create_final_package.py`, `build_package.py` | Unknown | Unknown | Prints to console | Verify included vs missing assets; check docs alignment. |


