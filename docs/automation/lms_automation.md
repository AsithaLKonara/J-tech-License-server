## LMS Automation Behavior

LMS automation is fundamentally different from the legacy "frame baking" workflow. Instead of generating new frames, automation creates **MCU runtime instructions** that are executed on the hardware during playback. Each instruction describes how to transform existing frames (scroll, rotate, mirror, etc.) and optionally how often to repeat the action.

### Core concepts

- **Automation actions become MCU instructions** such as `moveLeft1`, `rotate90`, `mirrorH`, `mirrorV`, `scrollText`, `invert`, and `brightness`.
- **Pattern instructions** reference existing frame slots (Layer 1 / Layer 2 / Mask) along with the action code, repeat count, and gap.
- **No intermediate frames** are generated. The MCU applies the instructions at runtime, which keeps exports small and perfectly aligned with LMS firmware expectations.
- **Gap vs Repeat**
  - *Repeat* is the number of times the microcontroller executes the instruction.
  - *Gap* is **not a delay in milliseconds**. It represents frame spacing (skip/duplicate) to slow down animations on hardware.
- **Apply vs Finalize**
  - *Apply* uses the preview simulator to show the effect on screen without modifying the pattern.
  - *Finalize* converts the instruction queue into `PatternInstructionSequence` data and stores it in the pattern (`pattern.lms_pattern_instructions`) for export.

### Data structures

- `LayerBinding` – References a frame slot (e.g. `Frame1`) plus optional alias/index.
- `LMSInstruction` – Stores action code, parameters, repeat count, gap, and optional brightness delta.
- `PatternInstruction` – Combines Layer 1 / Layer 2 / Mask bindings with an instruction.
- `PatternInstructionSequence` – Ordered collection of instructions used by apply/finalize workflow and LEDS exports.

### Preview Simulator

The preview simulator (`core/automation/preview_simulator.py`) interprets pattern instructions against the current pattern to visualize the automation queue without baking frames. It supports the direction-sensitive LMS actions (moveLeft1, moveRight1, moveUp1, moveDown1, rotate90, mirrorH, mirrorV, invert, brightness adjustments, etc.). Repeats generate multiple preview frames, respecting gap spacing for playback timing.

### Import/Export

`core/io/lms_formats.py` handles LMS-specific formats:

- **DAT** – Simple text export with width/height/frame count headers.
- **HEX** – Intel HEX with metadata inferred from record lengths and byte packing.
- **BIN** – Raw binary payloads with inferred dimensions.
- **LEDS** – Full-featured export containing metadata, pattern instructions, and frame data.

All formats expose common metadata such as width, height, frame count, color order, and bit packing. For DAT/HEX/BIN imports, wiring mode and orientation are **not** explicitly encoded by LMS, so Upload Bridge marks `serpentine`/`orientation` as unknown and relies on the shared file-format detector and presets to infer them. LEDS exports store additional Upload Bridge–specific comments (e.g. per-instruction gap and JSON parameters) so complex LMS sequences can be round-tripped without breaking compatibility with legacy tools.

