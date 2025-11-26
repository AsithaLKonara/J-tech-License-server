# 🎨 Upload Bridge - Visual Design Matrix

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                              │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐   ┌──────────────┐  ┌────────────┐  │
│  │ MainWindow   │  │ DesignTools  │   │ PreviewTab   │  │ FlashTab   │  │
│  │              │  │ Tab          │   │              │  │            │  │
│  │ - Pattern    │  │ - Canvas     │   │ - Simulator  │  │ - Builder  │  │
│  │ - Workspace  │  │ - Timeline   │   │ - Playback   │  │ - Uploader │  │
│  │ - Tabs       │  │ - Layers     │   │ - Controls   │  │ - Config   │  │
│  └──────┬───────┘  └──────┬───────┘   └──────┬───────┘  └──────┬─────┘  │
│         │                 │                  │                 │        │
│         └─────────────────┼──────────────────┼─────────────────┘        │
│                           │                  │                          │
│                    Signals/Slots Communication                          │
└───────────────────────────┼──────────────────┼──────────────────────────┘
                            │                  │
                            ▼                  ▼
┌───────────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                                     │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │ Pattern      │  │ Export       │  │ Flash        │                │
│  │ Service      │  │ Service      │  │ Service      │                │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                │
│         │                 │                  │                        │
│         └─────────────────┼──────────────────┘                        │
│                           │                                            │
│                    Uses Repository                                     │
└───────────────────────────┼────────────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────────┐
│                    REPOSITORY LAYER                                   │
│                                                                       │
│                    ┌──────────────┐                                  │
│                    │ Pattern       │                                  │
│                    │ Repository    │                                  │
│                    │ (Singleton)   │                                  │
│                    └──────┬───────┘                                  │
│                           │                                            │
│                    Manages State                                      │
└───────────────────────────┼────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────── ──┐
│                         DOMAIN LAYER                                     │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                    │
│  │ PatternState │  │ FrameManager │  │ LayerManager │                    │
│  │              │  │              │  │              │                    │
│  │ - Pattern    │  │ - CRUD       │  │ - Composition│                    │
│  │ - Metadata   │  │ - Selection  │  │ - Blend      │                    │
│  │ - State      │  │ - Duration   │  │ - Visibility │                    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                    │
│         │                 │                 │                            │
│         └─────────────────┼─────────────────┘                            │
│                           │                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                    │
│  │ HistoryMgr   │  │ AutomationQ  │  │ EffectsLib   │                    │
│  │              │  │              │  │              │                    │
│  │ - Undo/Redo  │  │ - Queue      │  │ - Effects    │                    │
│  │ - Commands   │  │ - Actions    │  │ - Library    │                    │
│  └──────────────┘  └──────────────┘  └──────────────┘                    │
└───────────────────────────┬──────────────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         CORE LAYER                                    │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │ Pattern      │  │ PatternMeta  │  │ Frame        │                 │
│  │              │  │              │  │              │                 │
│  │ - ID         │  │ - Dimensions │  │ - Pixels     │                 │
│  │ - Name       │  │ - Config     │  │ - Duration   │                 │
│  │ - Frames[]   │  │ - Wiring     │  │ - RGB        │                 │
│  └──────┬───────┘  └──────────────┘  └──────────────┘                 │
│         │                                                             │
│  ┌──────▼──────────────────────────────────────────────────┐          │
│  │ Export/Import Services                                  │          │
│  │ - Exporters (BIN, HEX, DAT, LEDS, JSON)                 │          │
│  │ - Validators                                            │          │
│  │ - Templates                                             │          │
│  └─────────────────────────────────────────────────────────┘          │
└───────────────────────────┬───────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         DATA ACCESS LAYER                            │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │ ParserReg    │  │ FileIO       │  │ Converters   │                │
│  │              │  │              │  │              │                │
│  │ - Auto-detect│  │ - Read/Write │  │ - Format     │                │
│  │ - Parsers[]  │  │ - Serialize  │  │ - Transform  │                │
│  │ - Registry   │  │ - Validate   │  │ - Migrate    │                │
│  └──────────────┘  └──────────────┘  └──────────────┘                │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         INFRASTRUCTURE LAYER                         │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │ UploaderReg  │  │ FirmwareBldr │  │ Toolchains   │                │
│  │              │  │              │  │              │                │
│  │ - ESP8266    │  │ - Templates  │  │ - Arduino    │                │
│  │ - ESP32      │  │ - Compile    │  │ - AVR-GCC    │                │
│  │ - AVR        │  │ - Link       │  │ - ARM-GCC    │                │
│  │ - STM32      │  │ - Binary     │  │ - esptool    │                │
│  └──────────────┘  └──────────────┘  └──────────────┘                │
└──────────────────────────────────────────────────────────────────────┘
```

## Data Flow Matrix

### Pattern Creation Flow

```
User Action
    │
    ▼
DesignToolsTab
    │
    ├─► Canvas Drawing ──► FrameManager.add_frame()
    │                        │
    ├─► Layer Painting ──► LayerManager.update_layer()
    │                        │
    └─► Timeline Edit ──► FrameManager.duplicate()
                            │
                            ▼
                    PatternState.update()
                            │
                            ▼
                    Pattern.frames[] updated
                            │
                            ▼
                    Signals emitted ──► All tabs notified
```

### Pattern Loading Flow (New Architecture)

```
File Selection
    │
    ▼
MainWindow.open_pattern()
    │
    ▼
PatternService.load_pattern(file_path)
    │
    ├─► ParserRegistry.parse_file()
    │   ├─► Auto-detect format
    │   ├─► Select parser
    │   └─► Parse bytes
    │       │
    │       ▼
    │   Create Pattern object
    │
    ├─► PatternRepository.set_current_pattern()
    │   └─► Emits pattern_changed signal
    │
    └─► EventBus.publish(PatternLoadedEvent)
        │
        ▼
    All subscribed components notified
        │
        ├─► DesignToolsTab (via signal)
        ├─► PreviewTab (via signal)
        └─► FlashTab (via signal)
```

### Firmware Generation Flow (New Architecture)

```
User clicks "Flash"
    │
    ▼
FlashTab.on_flash()
    │
    ▼
FlashService.build_firmware(pattern, chip_id, config)
    │
    ├─► UploaderRegistry.get_uploader(chip_id)
    │
    ├─► Uploader.build_firmware(pattern, config)
    │   ├─► Generate firmware code
    │   ├─► Embed pattern data
    │   └─► Compile with toolchain
    │       │
    │       ▼
    │   Returns BuildResult
    │
    ▼
FlashService.upload_firmware(firmware_path, chip_id, port)
    │
    ├─► Uploader.upload(firmware_path, config)
    │   ├─► Detect port
    │   ├─► Flash binary
    │   └─► Returns UploadResult
    │
    └─► FlashService.verify_upload() (optional)
        └─► Verify flash success
```

## Dependency Matrix

### Layer Dependencies (Allowed)

```
UI Layer
    │
    ▼ (allowed)
Domain Layer
    │
    ▼ (allowed)
Core Layer
    │
    ▼ (allowed)
Data Access Layer
    │
    ▼ (allowed)
Infrastructure Layer
```

### Cross-Layer Dependencies (Restricted)

```
❌ UI → Infrastructure (NOT ALLOWED)
❌ Domain → Infrastructure (NOT ALLOWED)
❌ Core → UI (NOT ALLOWED)

✅ All layers → Core (ALLOWED)
✅ UI → Domain (ALLOWED)
✅ Domain → Core (ALLOWED)
```

## Signal Flow Matrix

### Qt Signals/Slots Communication

```
DesignToolsTab
    │
    ├─► pattern_modified ──► MainWindow.on_pattern_modified()
    ├─► pattern_created ──► MainWindow._on_design_pattern_created()
    ├─► playback_state_changed ──► PreviewTab.sync_playback_state()
    └─► frame_changed ──► PreviewTab.sync_frame_selection()

MainWindow
    │
    ├─► pattern_changed ──► All tabs update_pattern()
    └─► save_state_changed ──► UI indicators update

FrameManager
    │
    ├─► frames_changed ──► TimelineWidget.refresh()
    └─► frame_index_changed ──► CanvasWidget.update_frame()

LayerManager
    │
    ├─► layers_changed ──► LayerPanelWidget.refresh()
    └─► pixel_changed ──► CanvasWidget.repaint()
```

## Extension Points Matrix

### Registry-Based Extensions

```
ParserRegistry
    │
    ├─► StandardFormatParser
    ├─► RawRGBParser
    ├─► IntelHexParser
    └─► [NEW] CustomParser ──► register_parser()

UploaderRegistry
    │
    ├─► ESPUploader
    ├─► AVRUploader
    ├─► STM32Uploader
    └─► [NEW] CustomUploader ──► register_uploader()
```

### Strategy-Based Extensions

```
BrightnessCurves
    │
    ├─► LinearCurve
    ├─► GammaCurve
    ├─► LogarithmicCurve
    └─► [NEW] CustomCurve ──► add_curve()

SpeedCurves
    │
    ├─► LinearSpeed
    ├─► EaseInOut
    └─► [NEW] CustomSpeed ──► add_speed_curve()
```

## State Management Matrix

### State Ownership (New Architecture)

```
PatternRepository (Singleton)
    │
    ├─► _current_pattern ──► Single source of truth
    ├─► _current_file ──► Current file path
    └─► _is_dirty ──► Unsaved changes flag
        │
        ├─► Emits pattern_changed signal
        └─► Emits pattern_cleared signal

MainWindow
    │
    ├─► Uses PatternRepository (via PatternService)
    ├─► WorkspaceManager ──► Multi-pattern workspace
    └─► TabStateManager ──► Tab persistence

DesignToolsTab
    │
    ├─► Uses PatternRepository (via PatternService)
    ├─► PatternState ──► References repository pattern
    ├─► FrameManager ──► Manages frames
    ├─► LayerManager ──► Manages layers
    └─► HistoryManager ──► Local undo/redo
```

### State Synchronization (New Architecture)

```
Pattern Modified
    │
    ├─► PatternRepository.set_dirty(True)
    │
    ├─► PatternRepository.pattern_changed signal
    │   └─► All subscribed components notified
    │
    ├─► EventBus.publish(PatternModifiedEvent)
    │   └─► All event subscribers notified
    │
    └─► All tabs automatically update
```

## Performance Optimization Matrix

### Caching Strategy

```
Frame Rendering
    │
    ├─► Cache rendered QPixmap
    ├─► Invalidate on pixel change
    └─► LRU cache (last 10 frames)

Layer Composition
    │
    ├─► Cache composed result
    ├─► Invalidate on layer change
    └─► Recompute on visibility change
```

### Lazy Loading

```
Pattern Loading
    │
    ├─► Load metadata first
    ├─► Load frames on-demand
    └─► Load layers on frame access

Tab Initialization
    │
    ├─► Placeholder tabs
    ├─► Initialize on first access
    └─► Keep initialized tabs in memory
```

---

*Visual Design Matrix - Upload Bridge Architecture*

