# Design Tools Tab Overview

The Design Tools tab provides an in-application environment for creating and
editing LED matrix animations without relying on third-party editors. This
document outlines the primary sections and workflows.

## Layout

- **Matrix Designer:** Interactive grid backed by `MatrixDesignCanvas` that
  supports painting, erasing (right-click), and hover feedback.
- **Frames Panel:** Manage timeline (add, duplicate, delete, reorder) and adjust
  per-frame duration.
- **Automation Actions:** Queue transformations—scroll, rotate, mirror, flip,
  invert, wipe, and reveal—across configurable frame ranges.
- **Palette & Gradient Tools:** Choose colours, fine-tune RGB sliders, or apply
  generated gradients (horizontal, vertical, radial) with customizable steps.
- **Live Preview:** Uses `EnhancedLEDSimulatorWidget` to play the current
  pattern.
- **Export Controls:** Save the design back into the application, propagating to
  other tabs (Preview, Flash, WiFi Upload).

## Typical Workflow

1. **Set Matrix Dimensions** via the Matrix Configuration panel.
2. **Draw or import base content** on the Matrix Designer canvas.
3. **Manage frames:** Add or duplicate frames to build sequences.
4. **Queue automation actions** for movement or transformations.
5. **Tune colours** using the palette, sliders, or gradients.
6. **Preview the animation** and iterate.
7. **Save to Pattern** to propagate changes throughout the application.

## Notes

- Wipe and reveal actions currently apply intensity masks to simulate transitions.
- Gradient application overwrites the active frame's pixel data.
- Canvas selections default to the first pixel's colour when switching frames.

For further integration details, inspect `ui/tabs/design_tools_tab.py` and
`ui/widgets/matrix_design_canvas.py`.

