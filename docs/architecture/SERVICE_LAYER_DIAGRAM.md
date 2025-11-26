# Service Layer Architecture Diagram

**Last Updated**: 2024  
**Status**: Complete

---

## Overview

This document provides visual diagrams of the service layer architecture, showing how components interact through the service layer and repository.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         UI LAYER                                   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ MainWindow   │  │ DesignTools  │  │ PreviewTab   │            │
│  │              │  │ Tab          │   │              │            │
│  │ - Tabs       │  │ - Canvas     │   │ - Simulator  │            │
│  │ - Menus      │  │ - Timeline   │   │ - Playback   │            │
│  │ - Toolbars   │  │ - Layers     │   │ - Controls   │            │
│  └──────┬───────┘  └──────┬───────┘   └──────┬───────┘            │
│         │                 │                   │                    │
│         └─────────────────┼───────────────────┘                    │
│                           │                                        │
│                    Uses Services                                   │
└───────────────────────────┼────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                                  │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Pattern      │  │ Export       │  │ Flash        │            │
│  │ Service      │  │ Service      │  │ Service      │            │
│  │              │  │              │  │              │            │
│  │ - Load       │  │ - Export     │  │ - Build      │            │
│  │ - Save       │  │ - Validate   │  │ - Upload     │            │
│  │ - Create     │  │ - Preview    │  │ - Verify     │            │
│  │ - Duplicate  │  │ - Formats    │  │ - Chips      │            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
│         │                 │                  │                    │
│         └─────────────────┼──────────────────┘                    │
│                           │                                        │
│                    Uses Repository                                 │
└───────────────────────────┼────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    REPOSITORY LAYER                                 │
│                                                                     │
│                    ┌──────────────┐                               │
│                    │ Pattern       │                               │
│                    │ Repository    │                               │
│                    │               │                               │
│                    │ - Pattern     │                               │
│                    │ - File Path   │                               │
│                    │ - Dirty State │                               │
│                    │ - Signals     │                               │
│                    └──────┬───────┘                               │
│                           │                                        │
│                    Manages State                                   │
└───────────────────────────┼────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                                   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Pattern      │  │ Frame        │  │ PatternMeta  │            │
│  │              │  │              │  │              │            │
│  │ - ID         │  │ - Pixels     │  │ - Dimensions │            │
│  │ - Name       │  │ - Duration   │  │ - Config     │            │
│  │ - Frames[]   │  │ - RGB        │  │ - Wiring     │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Event Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EVENT-DRIVEN COMMUNICATION                       │
│                                                                     │
│  Service Operations                                                 │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────┐                                                  │
│  │ Pattern      │                                                  │
│  │ Service      │                                                  │
│  │              │                                                  │
│  │ load_pattern()                                                  │
│  │ save_pattern()                                                  │
│  │ create_pattern()                                                │
│  └──────┬───────┘                                                  │
│         │                                                           │
│         │ Publishes                                                 │
│         ▼                                                           │
│  ┌──────────────┐                                                  │
│  │ EventBus     │                                                  │
│  │              │                                                  │
│  │ - Subscribe  │                                                  │
│  │ - Publish    │                                                  │
│  │ - History    │                                                  │
│  └──────┬───────┘                                                  │
│         │                                                           │
│         │ Dispatches                                                │
│         ▼                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ UI Component │  │ UI Component  │  │ UI Component  │            │
│  │ (Tab 1)     │  │ (Tab 2)       │  │ (Tab 3)      │            │
│  │             │  │               │  │              │            │
│  │ Listens to  │  │ Listens to    │  │ Listens to   │            │
│  │ Events      │  │ Events        │  │ Events       │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING FLOW                              │
│                                                                     │
│  Operation                                                          │
│      │                                                              │
│      ▼                                                              │
│  ┌──────────────┐                                                  │
│  │ Service      │                                                  │
│  │ Method       │                                                  │
│  └──────┬───────┘                                                  │
│         │                                                           │
│         │ Exception Raised                                          │
│         ▼                                                           │
│  ┌──────────────┐                                                  │
│  │ Custom      │                                                   │
│  │ Exception   │                                                   │
│  │             │                                                   │
│  │ - Pattern   │                                                   │
│  │   LoadError │                                                   │
│  │ - Export    │                                                   │
│  │   Error     │                                                   │
│  │ - Flash     │                                                   │
│  │   Error     │                                                   │
│  └──────┬───────┘                                                  │
│         │                                                           │
│         │ Handled By                                                │
│         ▼                                                           │
│  ┌──────────────┐                                                  │
│  │ Error       │                                                   │
│  │ Handler     │                                                   │
│  │             │                                                   │
│  │ - Logs      │                                                   │
│  │ - Notifies │                                                   │
│  │ - Recovers  │                                                   │
│  └──────┬───────┘                                                  │
│         │                                                           │
│         │ Notifies                                                  │
│         ▼                                                           │
│  ┌──────────────┐                                                  │
│  │ User        │                                                   │
│  │ (via UI)    │                                                   │
│  └──────────────┘                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Interaction Sequence

### Pattern Loading Sequence

```
User Action: Open File
    │
    ▼
MainWindow.open_pattern()
    │
    ▼
PatternService.load_pattern(file_path)
    │
    ├─→ ParserRegistry.parse_file()
    │   └─→ Returns Pattern
    │
    ├─→ PatternRepository.set_current_pattern()
    │   └─→ Emits pattern_changed signal
    │
    └─→ EventBus.publish(PatternLoadedEvent)
        │
        ├─→ UI Component 1 receives event
        ├─→ UI Component 2 receives event
        └─→ UI Component 3 receives event
```

### Pattern Export Sequence

```
User Action: Export Pattern
    │
    ▼
PreviewTab.on_export_pattern()
    │
    ▼
ExportService.validate_export(pattern, format)
    │
    ├─→ Validates pattern
    └─→ Returns (is_valid, error, preview)
    │
    ▼
ExportService.export_pattern(pattern, file_path, format)
    │
    ├─→ PatternExporter.export_binary()
    │   └─→ Writes file
    │
    └─→ Returns output_path
```

### Firmware Flash Sequence

```
User Action: Build & Flash
    │
    ▼
FlashTab.on_flash()
    │
    ▼
FlashService.build_firmware(pattern, chip_id, config)
    │
    ├─→ UploaderRegistry.get_uploader(chip_id)
    │
    ├─→ Uploader.build_firmware(pattern, config)
    │   └─→ Returns BuildResult
    │
    └─→ Returns BuildResult
    │
    ▼
FlashService.upload_firmware(firmware_path, chip_id, port)
    │
    ├─→ Uploader.upload(firmware_path, config)
    │   └─→ Returns UploadResult
    │
    └─→ Returns UploadResult
```

---

## Repository State Management

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REPOSITORY STATE                                 │
│                                                                     │
│  PatternRepository (Singleton)                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ State:                                                       │  │
│  │   - _current_pattern: Pattern | None                        │  │
│  │   - _current_file: str | None                               │  │
│  │   - _is_dirty: bool                                         │  │
│  │                                                              │  │
│  │ Signals:                                                     │  │
│  │   - pattern_changed(Pattern)                                │  │
│  │   - pattern_cleared()                                       │  │
│  │                                                              │  │
│  │ Methods:                                                     │  │
│  │   - get_current_pattern() → Pattern | None                  │  │
│  │   - set_current_pattern(pattern, file_path)                 │  │
│  │   - clear_pattern()                                         │  │
│  │   - is_dirty() → bool                                       │  │
│  │   - set_dirty(dirty)                                        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  All Services and UI Components access through Repository           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Service Dependencies

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SERVICE DEPENDENCIES                             │
│                                                                     │
│  PatternService                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Dependencies:                                               │  │
│  │   - ParserRegistry (for loading)                            │  │
│  │   - PatternRepository (for state)                          │  │
│  │   - EventBus (for events)                                  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ExportService                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Dependencies:                                               │  │
│  │   - PatternExporter (for export)                           │  │
│  │   - ExportOptions (for configuration)                      │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  FlashService                                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Dependencies:                                               │  │
│  │   - UploaderRegistry (for uploaders)                        │  │
│  │   - FirmwareBuilder (for building)                          │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture (Refactored)

```
┌─────────────────────────────────────────────────────────────────────┐
│              DESIGNTOOLSTAB COMPONENT ARCHITECTURE                  │
│                                                                     │
│  DesignToolsTab (Main Container)                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │  ┌──────────────────┐  ┌──────────────────┐               │  │
│  │  │ Pattern          │  │ Frame             │               │  │
│  │  │ Operations       │  │ Management       │               │  │
│  │  │ Component        │  │ Component        │               │  │
│  │  │                  │  │                  │               │  │
│  │  │ - Create         │  │ - Add            │               │  │
│  │  │ - Load           │  │ - Delete         │               │  │
│  │  │ - Save           │  │ - Duplicate      │               │  │
│  │  │ - Duplicate      │  │ - Move           │               │  │
│  │  │ - Validate       │  │ - Select         │               │  │
│  │  └──────────────────┘  └──────────────────┘               │  │
│  │                                                              │  │
│  │  ┌──────────────────┐                                      │  │
│  │  │ Canvas           │                                       │  │
│  │  │ Controller       │                                       │  │
│  │  │ Component        │                                       │  │
│  │  │                  │                                       │  │
│  │  │ - Render         │                                       │  │
│  │  │ - Pixel Apply    │                                       │  │
│  │  │ - Matrix Size    │                                       │  │
│  │  │ - Color          │                                       │  │
│  │  └──────────────────┘                                      │  │
│  │                                                              │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

*Service Layer Architecture Diagram - Updated: 2024*

