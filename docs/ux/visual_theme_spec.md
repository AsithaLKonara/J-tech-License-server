# Visual System, Themes & Accessibility

## Palette

| Role | Dark | Light |
| ---- | ---- | ----- |
| Background | `#121212` | `#F5F5F5` |
| Panel | `#1E1E1E` | `#FFFFFF` |
| Accent | `#4C8BF5` | `#1E63D4` |
| Secondary | `#7A7CFF` | `#5A5CFF` |
| Success | `#3FB983` | `#1F8C5E` |
| Warning | `#F3A533` | `#C47E16` |
| Error | `#E55B5B` | `#C04444` |

## Typography

- Font: `Inter`, fallback sans-serif.  
- H1 24px, H2 18px, body 14px, caption 12px uppercase.

## Spacing

- Base unit 8 px.  
- Panels padding 16 px.  
- Button group gap 8 px; timeline lane spacing 4 px.

## Component States

| Component | Default | Hover | Active | Disabled |
| --------- | ------- | ----- | ------ | -------- |
| Primary Button | `#4C8BF5` | `#5B99FF` | `#2F6CD1` inset shadow | `#2E2E2E` |
| Icon Button | `#1E1E1E` | `#2C2C2C` | `#4C8BF5` | `#1A1A1A` |
| Slider Track | `#3A3A3A` | same | accent | `#2A2A2A` |
| Timeline Clip | `#2A2D3A` | border accent | accent fill 40% | opacity 40% |

## Iconography

- 2 px stroke, 16×16 or 20×20 grid.  
- Custom icons: automation, presets, hardware sync.

## Accessibility

- 4.5:1 contrast for body text.  
- Focus ring using accent colour 2 px.  
- Timeline markers include pattern overlay for colour-blind users.  
- Provide “reduce animations” preference.

## Theme Toggle

- Persist user choice; default dark.  
- Smooth fade transition 200 ms.  
- Canvas grid colours adjust per theme.

## UI Kit Deliverables

- Buttons (primary/secondary/ghost).  
- Timeline pieces (clip, playhead, markers).  
- Layer controls (visibility, lock, opacity slider).  
- Dialogs, toast notifications with 6 px radius.

