# Feature Linkage Diagrams

**Date**: 2025-01-27  
**Purpose**: Visual representation of all feature linkages and data flows

---

## Core Data Flow Architecture

```mermaid
graph TB
    PatternRepository[PatternRepository<br/>Single Source of Truth]
    MainWindow[MainWindow]
    DesignToolsTab[DesignToolsTab]
    PreviewTab[PreviewTab]
    FlashTab[FlashTab]
    BatchFlashTab[BatchFlashTab]
    WiFiUploadTab[WiFiUploadTab]
    
    PatternRepository -->|pattern_changed signal| MainWindow
    MainWindow -->|pattern_changed signal| DesignToolsTab
    MainWindow -->|pattern_changed signal| PreviewTab
    MainWindow -->|pattern_changed signal| FlashTab
    MainWindow -->|pattern_changed signal| BatchFlashTab
    MainWindow -->|pattern_changed signal| WiFiUploadTab
    
    DesignToolsTab -->|pattern_modified signal| MainWindow
    PreviewTab -->|pattern_modified signal| MainWindow
    MainWindow -->|pattern_changed signal| PatternRepository
```

---

## Drawing → Layer → Frame → Pattern Flow

```mermaid
sequenceDiagram
    participant User
    participant Canvas as MatrixDesignCanvas
    participant DesignTab as DesignToolsTab
    participant LayerMgr as LayerManager
    participant FrameMgr as FrameManager
    participant Pattern as Pattern
    participant Repo as PatternRepository
    participant Tabs as All Tabs
    
    User->>Canvas: Draw on canvas
    Canvas->>Canvas: pixel_updated.emit(x, y, color)
    Canvas->>DesignTab: _on_canvas_pixel_updated()
    DesignTab->>LayerMgr: apply_pixel(frame, x, y, color, layer)
    LayerMgr->>LayerMgr: Update layer pixels
    LayerMgr->>LayerMgr: sync_frame_from_layers()
    LayerMgr->>Pattern: Update frame pixels
    DesignTab->>DesignTab: pattern_modified.emit()
    DesignTab->>Repo: Notify pattern changed
    Repo->>Tabs: pattern_changed signal
    Tabs->>Tabs: Update UI
```

---

## Timeline → Frame → Animation Flow

```mermaid
graph LR
    Timeline[TimelineWidget]
    FrameMgr[FrameManager]
    Canvas[MatrixDesignCanvas]
    Pattern[Pattern]
    Preview[PreviewTab]
    
    Timeline -->|frameSelected signal| FrameMgr
    FrameMgr -->|select index| Pattern
    FrameMgr -->|frames_changed signal| Timeline
    FrameMgr -->|frame_index_changed signal| Canvas
    FrameMgr -->|frame_index_changed signal| Preview
    Canvas -->|Display frame| User
    Preview -->|Play animation| User
```

---

## Export Flow

```mermaid
flowchart TD
    Pattern[Pattern]
    ExportService[ExportService]
    Validator[ExportValidator]
    Preview[ExportPreview]
    Exporter[Exporter]
    File[File System]
    
    Pattern -->|export_pattern| ExportService
    ExportService -->|validate_export| Validator
    Validator -->|ExportPreview| Preview
    Preview -->|User confirms| ExportService
    ExportService -->|export| Exporter
    Exporter -->|write| File
```

---

## Flash Flow

```mermaid
flowchart TD
    Pattern[Pattern]
    FlashService[FlashService]
    FirmwareBuilder[Firmware Builder]
    Uploader[Uploader]
    Device[Hardware Device]
    
    Pattern -->|build_firmware| FlashService
    FlashService -->|generate| FirmwareBuilder
    FirmwareBuilder -->|firmware binary| FlashService
    FlashService -->|upload| Uploader
    Uploader -->|flash| Device
    Device -->|verify| Uploader
    Uploader -->|success| FlashService
```

---

## Import Flow

```mermaid
sequenceDiagram
    participant User
    participant FileSystem as File System
    participant ParserRegistry as ParserRegistry
    participant PatternService as PatternService
    participant PatternRepo as PatternRepository
    participant Tabs as All Tabs
    
    User->>FileSystem: Select file
    FileSystem->>ParserRegistry: parse_file(file_path)
    ParserRegistry->>ParserRegistry: Detect format
    ParserRegistry->>ParserRegistry: Parse file
    ParserRegistry->>PatternService: Pattern object
    PatternService->>PatternRepo: set_current_pattern()
    PatternRepo->>PatternRepo: pattern_changed.emit()
    PatternRepo->>Tabs: Notify all tabs
    Tabs->>Tabs: load_pattern() / update_pattern()
```

---

## Layer System Flow

```mermaid
graph TB
    LayerPanel[LayerPanelWidget]
    LayerMgr[LayerManager]
    FrameComposite[Frame Composite]
    Canvas[Canvas]
    Pattern[Pattern Frame]
    
    LayerPanel -->|set_layer_visible| LayerMgr
    LayerPanel -->|set_layer_opacity| LayerMgr
    LayerPanel -->|set_blend_mode| LayerMgr
    LayerPanel -->|move_layer| LayerMgr
    LayerMgr -->|get_composite_pixels| FrameComposite
    FrameComposite -->|blend layers| Pattern
    Pattern -->|display| Canvas
    Canvas -->|render| User
```

---

## Automation & Effects Flow

```mermaid
flowchart LR
    EffectsUI[EffectsLibraryWidget]
    AutomationQueue[AutomationQueue]
    AutomationEngine[AutomationEngine]
    FrameGen[Frame Generator]
    Pattern[Pattern]
    
    EffectsUI -->|add effect| AutomationQueue
    AutomationQueue -->|execute| AutomationEngine
    AutomationEngine -->|generate frames| FrameGen
    FrameGen -->|update| Pattern
    Pattern -->|notify| AllTabs[All Tabs]
```

---

## Cross-Tab Synchronization

```mermaid
graph TB
    Repo[PatternRepository]
    MainWin[MainWindow]
    DesignTab[DesignToolsTab]
    PreviewTab[PreviewTab]
    FlashTab[FlashTab]
    WiFiTab[WiFiUploadTab]
    BatchTab[BatchFlashTab]
    
    Repo -->|pattern_changed| MainWin
    MainWin -->|pattern_changed| DesignTab
    MainWin -->|pattern_changed| PreviewTab
    MainWin -->|pattern_changed| FlashTab
    MainWin -->|pattern_changed| WiFiTab
    MainWin -->|pattern_changed| BatchTab
    
    DesignTab -->|pattern_modified| MainWin
    PreviewTab -->|pattern_modified| MainWin
    MainWin -->|pattern_changed| Repo
```

---

## Complete Feature Integration Map

```mermaid
graph TB
    subgraph "Pattern Creation"
        NewPattern[New Pattern Dialog]
        Templates[Pattern Templates]
        MediaImport[Media Import]
    end
    
    subgraph "Design Tools"
        Canvas[MatrixDesignCanvas]
        DrawingTools[Drawing Tools]
        LayerPanel[Layer Panel]
        Timeline[Timeline Widget]
    end
    
    subgraph "Core Systems"
        PatternRepo[PatternRepository]
        LayerMgr[LayerManager]
        FrameMgr[FrameManager]
        AutomationEngine[Automation Engine]
    end
    
    subgraph "Preview & Export"
        PreviewTab[Preview Tab]
        ExportService[Export Service]
        FlashService[Flash Service]
    end
    
    subgraph "Hardware"
        Uploaders[Uploaders]
        FirmwareBuilder[Firmware Builder]
        Devices[Hardware Devices]
    end
    
    NewPattern --> PatternRepo
    Templates --> PatternRepo
    MediaImport --> PatternRepo
    
    PatternRepo --> Canvas
    PatternRepo --> PreviewTab
    
    Canvas --> DrawingTools
    DrawingTools --> LayerMgr
    LayerPanel --> LayerMgr
    Timeline --> FrameMgr
    
    LayerMgr --> PatternRepo
    FrameMgr --> PatternRepo
    AutomationEngine --> FrameMgr
    
    PatternRepo --> ExportService
    PatternRepo --> FlashService
    
    FlashService --> FirmwareBuilder
    FirmwareBuilder --> Uploaders
    Uploaders --> Devices
```

---

## Signal Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Canvas
    participant DesignTab
    participant LayerMgr
    participant FrameMgr
    participant PatternRepo
    participant MainWin
    participant PreviewTab
    participant FlashTab
    
    User->>Canvas: Draw pixel
    Canvas->>DesignTab: pixel_updated(x, y, color)
    DesignTab->>LayerMgr: apply_pixel()
    LayerMgr->>LayerMgr: sync_frame_from_layers()
    LayerMgr->>DesignTab: layers_changed()
    DesignTab->>DesignTab: pattern_modified.emit()
    DesignTab->>MainWin: pattern_modified signal
    MainWin->>PatternRepo: pattern_changed.emit()
    PatternRepo->>MainWin: pattern_changed signal
    MainWin->>PreviewTab: pattern_changed signal
    MainWin->>FlashTab: pattern_changed signal
    PreviewTab->>PreviewTab: update_pattern()
    FlashTab->>FlashTab: refresh_preview()
```

---

## Component Interaction Diagram

```mermaid
graph TB
    subgraph "UI Layer"
        MainWindow[MainWindow]
        DesignToolsTab[DesignToolsTab]
        PreviewTab[PreviewTab]
        FlashTab[FlashTab]
    end
    
    subgraph "Domain Layer"
        LayerManager[LayerManager]
        FrameManager[FrameManager]
        CanvasController[CanvasController]
    end
    
    subgraph "Core Layer"
        PatternRepository[PatternRepository]
        PatternService[PatternService]
        ExportService[ExportService]
        FlashService[FlashService]
    end
    
    subgraph "Data Layer"
        Pattern[Pattern]
        Frame[Frame]
        Layer[Layer]
    end
    
    MainWindow --> PatternRepository
    DesignToolsTab --> LayerManager
    DesignToolsTab --> FrameManager
    PreviewTab --> PatternRepository
    FlashTab --> FlashService
    
    LayerManager --> Pattern
    FrameManager --> Pattern
    CanvasController --> Frame
    
    PatternRepository --> Pattern
    PatternService --> PatternRepository
    ExportService --> PatternRepository
    FlashService --> PatternRepository
    
    Pattern --> Frame
    Frame --> Layer
```

---

**Note**: These diagrams show the complete feature linkage architecture. All connections have been verified in the codebase and are working correctly.

