# Requirements & Success Criteria

## Functional Requirements

1. Frame-by-frame timeline with scrubbing, thumbnails, keyboard nav.  
2. Layer inspector with visibility, lock, opacity, reorder.  
3. Playback controls (play/pause, step, loop, speed, FPS).  
4. Automation queue management with presets and preview.  
5. Theme support (dark default, light optional).  
6. Export workflow for presets/templates/hardware.

## Non-functional Requirements

| Category | Goal |
| -------- | ---- |
| Performance | ≥30 FPS playback up to 256 frames. |
| Latency | Scrubbing latency <50 ms; canvas redraw <33 ms. |
| Responsiveness | Usable ≥1200 px width; panels adapt. |
| Accessibility | WCAG AA contrast; keyboard-friendly. |
| Localisation | Strings structured for translation. |

## Acceptance Criteria Highlights

- Frame operations achievable within 3 interactions.  
- Visual feedback appears within 200 ms.  
- Keyboard shortcuts cover playback and frame stepping.  
- Undo/redo displays toast with action summary.

## Accessibility Checklist (excerpt)

- Tab order covers all controls.  
- Focus indicator 3:1 contrast.  
- Timeline handles ≥44 px hit area.  
- Offer colour-blind friendly palette.

## Performance KPIs

- Time to interactive <2 s for default project.  
- Memory <500 MB for 256 frames at 32x32.  
- Automation preview <200 ms for standard presets.

## Constraints & Assumptions

- Desktop-first (Windows/macOS), tablet secondary.  
- Playback accuracy prioritised over eye candy.  
- Hardware preview handled by existing communication stack.

