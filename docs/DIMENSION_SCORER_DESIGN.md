---
title: Dimension Scorer Design
status: Stable
updated: 2025-11-09
owner: core-team
---

# Dimension Scorer Design Note

**Audience:** parser authors and maintainers updating layout heuristics.  
**Scope:** documents the shared asymmetric dimension inference pipeline introduced in `core/dimension_scorer.py`.

```python
from core.dimension_scorer import pick_best_layout

width, height, confidence = pick_best_layout(led_count, first_frame=pixels)
print(f"{width}×{height} (confidence {confidence:.2f})")
```

| Function | Input | Output | Used by |
|----------|-------|--------|---------|
| `generate_layout_candidates()` | LED count, optional frame sample | `[(width, height, confidence)]` | Parsers, `MatrixDetector` |
| `pick_best_layout()` | LED count, optional frame sample | `(width, height, confidence)` | Parsers, `MatrixDetector` |
| `infer_leds_and_frames()` | Total pixels (+ optional bytes) | `DimensionResolution(leds, width, height, frames, confidence)` | Parsers with no explicit header |

---

## 1. Purpose & Scope {#purpose}

Historically each parser (`raw_rgb`, `standard`, `enhanced_binary`) bundled its own width/height heuristics. That led to square bias, inconsistent confidence scoring, and duplicated code. `core/dimension_scorer.py` replaces those ad‑hoc routines with a single module that:

- Factors LED counts into all `(width, height)` pairs (square and rectangular)
- Scores candidates with shared heuristics (layout tables, aspect ratios, pixel alignment)
- Infers frame counts from total pixel payload when headers are absent
- Emits a normalized confidence score so UI and exporters can flag uncertain guesses

Every consumer (parsers, `MatrixDetector`, future tools) now calls the same API to stay consistent.

---

## 2. Core Algorithm Summary {#algorithm-summary}

1. **Raw stats** – Compute total pixel count (`len(bytes) // bytes_per_pixel`). Current helpers support `bytes_per_pixel` of 1 (mono), 3 (RGB), and 4 (RGBW/RGBA). Extend as needed before invocation.
2. **Factorisation** – Enumerate every `(width, height)` divisor pair of the LED count (optionally including strips).
3. **Candidate scoring**
   - Boost layouts listed in `COMMON_LAYOUTS` and LED counts in `COMMON_LED_COUNTS`
   - Compare aspect ratios against `PREFERRED_ASPECT_RATIOS`
   - Apply pixel-alignment bonus by comparing row-wrap versus inline RGB diffs when frame data is available
4. **Frame count** – For each LED candidate, compute `frames = total_pixels // leds`; score via `_frame_score` (prefers 5–240).
5. **Confidence fusion** – Combine layout score (80%) and frame score (20%), clamp to `[0.0, 0.99]`.
6. **Selection** – Return the highest confidence candidate; fallback to `(led_count, 1)` strip when nothing qualifies.

---

## 3. API Contract {#api}

```python
generate_layout_candidates(led_count, first_frame=None, include_strips=False, limit=8)
pick_best_layout(led_count, first_frame=None, include_strips=False)
infer_leds_and_frames(total_pixels, include_strips=True, preferred_led_counts=None, pixel_bytes=None)
```

- `pick_best_layout` → `(width, height, confidence)` where `confidence ∈ [0.05, 0.99]`
- `infer_leds_and_frames` → `DimensionResolution(led_count, width, height, frames, confidence)` or `None`

Inputs accept optional RGB pixel samples (`first_frame` or `pixel_bytes`) to enable alignment scoring. `preferred_led_counts` can bias hardware-specific sizes.

---

## 4. Integration Pattern {#integration}

1. **Parser header path** – If a file provides explicit width/height/frame count, set `PatternMetadata.dimension_source = "header"` and confidence `1.0`.
2. **Parser fallback path**
   ```python
   resolution = infer_leds_and_frames(
       total_pixels,
       pixel_bytes=data,
       preferred_led_counts=COMMON_LED_COUNTS,
   )
   if resolution:
       width = resolution.width
       height = resolution.height
       frames = resolution.frames
       dimension_source = "detector"
       dimension_confidence = resolution.confidence
   else:
       width, height = led_count, 1
       dimension_source = "fallback"
       dimension_confidence = 0.2

   metadata = PatternMetadata(
       width=width,
       height=height,
       color_order="RGB",
       dimension_source=dimension_source,
       dimension_confidence=dimension_confidence,
   )
   ```
3. **MatrixDetector** – Delegates to `pick_best_layout`, preserving cache, string helpers, and suggested arrangements.

---

## 5. Confidence Semantics {#confidence}

| Confidence | Meaning                                   | Recommended Action           |
|------------|-------------------------------------------|------------------------------|
| `>= 0.90`  | Header-confirmed or near-perfect heuristic | Auto-accept (no warning)     |
| `0.50–0.89`| Heuristic, likely correct                 | Display “verify layout” badge|
| `< 0.50`   | Weak fallback or ambiguous factorization  | Prompt user for override     |

Always populate `PatternMetadata.dimension_source` as `header`, `detector`, or `fallback` so downstream tools know whether to re-run detection.

---

## 6. Extension Hooks {#extensions}

- **Layout tables** – Update `COMMON_LAYOUTS` / `COMMON_LED_COUNTS` when new hardware panel sizes appear.
- **Aspect tuning** – Adjust `PREFERRED_ASPECT_RATIOS` to include portrait or ultra-wide panels.
- **Alignment strategies** – Swap `_pixel_alignment_bonus` for HSV or temporal-based scoring when dealing with non-RGB payloads.
- **Frame scoring** – Modify `_frame_score` for domains with very long or very short animations.
- **Pluggable heuristics** – Add custom weightings (power-of-two preference, diagonal coherence, etc.) before the final `total_score`.

---

## 7. Examples {#examples}

### Raw RGB Parser (before → after)

- **Before (legacy snippet):**
  ```python
  num_leds, num_frames = self._auto_detect_dimensions(total_pixels)
  if not num_leds:
      metadata = PatternMetadata(width=total_pixels, height=1)
  ```
  (square-biased fallback, no confidence metadata)

- **After (current code):**
  ```python
  resolution = infer_leds_and_frames(total_pixels, pixel_bytes=data, preferred_led_counts=COMMON_LED_COUNTS)
  if resolution:
      width_guess, height_guess = resolution.width, resolution.height
      dimension_source = "detector"
      dimension_confidence = resolution.confidence
  else:
      width_guess, height_guess = num_leds, 1
      dimension_source = "fallback"
      dimension_confidence = 0.2
  ```

### Enhanced Binary Parser

- **Header present:** set `dimension_source="header"`, `dimension_confidence=1.0`.
- **Header absent:**
  ```python
  guess = pick_best_layout(led_count, frames[0].pixels, include_strips=True)
  if guess:
      width, height, score = guess
      dimension_source = "detector"
      dimension_confidence = score
  else:
      width, height = led_count, 1
      dimension_source = "fallback"
      dimension_confidence = 0.2
  ```

---

> ⚙️ **Maintainer Tip:** When altering heuristics in `dimension_scorer.py`, run `pytest -k scorer` and verify this document’s examples remain accurate.

**Reminder:** Surface low-confidence detections (`dimension_confidence < 0.5`) in the UI so users can override before flashing. This keeps hardware wiring safe while the heuristics continue to evolve.

See also: [PREVIEW_vs_FIRMWARE_WIRING.md](PREVIEW_vs_FIRMWARE_WIRING.md)

---

*Versioning note: Introduced in the 2025.11 refactor. Keep this document in sync with `core/dimension_scorer.py` whenever scoring or layout heuristics change.*

