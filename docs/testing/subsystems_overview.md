# Subsystem Inventory and Testing Scope

This document captures the major functional areas exposed by `ui/tabs/design_tools_tab.py`
and the depth of testing that will be targeted for each area.

## Core State & Shared Utilities

| Component | Responsibilities | Testing Depth |
| --------- | ---------------- | ------------- |
| `Pattern`, `Frame`, `LayerData` wrappers | Persistence of pixel data, metadata (width, height, duration) and per-layer properties (visibility, lock, opacity). | **Unit** (data helpers), **Property-based** (roundtrip serialization / resizing). |
| History manager commands (`LayerFramesCommand`, `LayerPixelEditCommand`, etc.) | Undo/redo semantics for frame, layer, pixel operations. | **Unit** (command behaviour) and **Integration** (stack interactions). |

## Subsystems

| Subsystem | Responsibilities | Notes | Testing Depth |
| --------- | ---------------- | ----- | ------------- |
| **Frame Management** | Create/duplicate/delete/move frames, manage active index, duration, sync with history. | `_insert_frame_internal`, `_remove_frame_internal`, `_move_frame_internal`, `_on_duration_changed`. | **Unit**, **Integration**, **GUI**. |
| **Layer Management** | Maintain per-frame layer stacks, toggles for visibility/lock/opacity, pixel application. | `_ensure_frame_layers`, `_apply_layer_pixel_internal`, layer UI controls. | **Unit**, **Integration**, **Property-based**. |
| **Canvas & Pixel Editing** | Apply pixels directly, recompute composites, refresh canvas. | `_apply_pixel_direct`, `_refresh_canvas_from_layers`. | **Unit**, **Integration**, **GUI**. |
| **Palette & Colour Tools** | Colour selection, RGB sliders/spins, gradient generation. | `_sync_channel_controls`, `_generate_gradient_pixels`, `_apply_gradient_from_controls`. | **Unit**, **Property-based**, **GUI**. |
| **Matrix Configuration** | Width/height adjustments, canvas resizing, rotation helpers. | `_create_blank_frame`, `_create_default_pattern`. | **Unit**, **Integration**, **GUI**. |
| **Automation Queue** | Queue actions and apply across frames, handle easing/distance. | `_queue_action`, `_perform_action`, `_create_action_for_frame`. | **Unit**, **Integration**, **Property-based**. |
| **Automation Presets** | Save/load/delete presets, storage interaction, preview dialog. | `_on_save_preset`, `_on_apply_preset`, `_on_preview_preset`. | **Unit**, **Integration**, **GUI**. |
| **Pattern Export** | Emit pattern to other tabs, naming. | `_emit_pattern`. | **Unit**, **Integration**, **GUI**. |
| **History & Undo** | Coordinated undo stack across operations. | `history.push`, command usage. | **Integration**, **Regression**. |
| **Preset Preview Dialog** | Modal preview of automation presets. | `AutomationPresetPreviewDialog`. | **Unit**, **GUI**. |

## Testing Depth Legend

- **Unit**: logic-only tests, mocks/stubs, fast.
- **Integration**: multiple subsystems verifying consistency.
- **Property-based**: Hypothesis fuzzing to ensure invariants.
- **GUI**: event-driven tests via `pytest-qt`.
- **Regression**: snapshot/visual comparisons.

## Coverage Expectations

- Critical logic (frame/layer/automation) target ≥90% statement coverage.
- Canvas compositing requires property tests to avoid index errors.
- Automation presets need regression tests to catch storage format changes.

## Next Steps

1. Extract subsystem logic into dedicated managers.
2. Provide fixtures delivering isolated `PatternState` instances.
3. Prioritise coverage for frame, layer, automation subsystems.

