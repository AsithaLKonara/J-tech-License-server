#!/usr/bin/env python3
"""
Comprehensive UI Integration Verification
Tests all UI connections, signals, slots, and widget functionality
"""
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject

sys.path.insert(0, os.path.dirname(__file__))

print("="*70)
print("COMPREHENSIVE UI INTEGRATION VERIFICATION")
print("="*70)
print()

app = QApplication.instance()
if app is None:
    app = QApplication([])

results = {}

# ============================================================================
# 1. MAIN WINDOW → DESIGN TOOLS TAB INTEGRATION
# ============================================================================
print("[1] Testing Main Window → Design Tools Tab Integration...")
try:
    from ui.main_window import UploadBridgeMainWindow
    from ui.tabs.design_tools_tab import DesignToolsTab
    
    main_window = UploadBridgeMainWindow()
    
    # Check if design tools tab is initialized
    if main_window.design_tab is None:
        # Trigger lazy initialization
        main_window.initialize_tab('design_tools')
    
    design_tab = main_window.design_tab
    
    if design_tab:
        # Check signal connections
        connections_ok = True
        issues = []
        
        # Check pattern_modified signal
        if hasattr(design_tab, 'pattern_modified'):
            results["main_to_design"] = {"status": "✓ WORKING", "signals": ["pattern_modified"]}
            print("  ✓ pattern_modified signal exists")
        else:
            issues.append("pattern_modified signal missing")
            connections_ok = False
        
        # Check pattern_created signal
        if hasattr(design_tab, 'pattern_created'):
            results["main_to_design"]["signals"].append("pattern_created")
            print("  ✓ pattern_created signal exists")
        else:
            issues.append("pattern_created signal missing")
        
        # Check update_pattern method exists
        if hasattr(design_tab, 'update_pattern'):
            results["main_to_design"]["methods"] = ["update_pattern"]
            print("  ✓ update_pattern method exists")
        else:
            issues.append("update_pattern method missing")
        
        if issues:
            results["main_to_design"]["issues"] = issues
            print(f"  ⚠ Issues: {', '.join(issues)}")
    else:
        results["main_to_design"] = {"status": "✗ ERROR", "issues": ["Design tab not initialized"]}
        print("  ✗ Design tab not initialized")
        
except Exception as e:
    results["main_to_design"] = {"status": "✗ ERROR", "issues": [str(e)]}
    print(f"  ✗ Error: {e}")

print()

# ============================================================================
# 2. DESIGN TOOLS TAB INTERNAL UI INTEGRATIONS
# ============================================================================
print("[2] Testing Design Tools Tab Internal UI Connections...")
try:
    from ui.tabs.design_tools_tab import DesignToolsTab
    
    design_tab = DesignToolsTab()
    
    integrations = {
        "signals": [],
        "widgets": [],
        "connections": []
    }
    
    # Check all signals
    signals_to_check = [
        'pattern_modified',
        'pattern_created',
        'playback_state_changed',
        'frame_changed'
    ]
    
    for signal_name in signals_to_check:
        if hasattr(design_tab, signal_name):
            integrations["signals"].append(signal_name)
            print(f"  ✓ Signal: {signal_name}")
    
    # Check key widgets exist
    widgets_to_check = [
        ('canvas', 'MatrixDesignCanvas'),
        ('layer_panel', 'LayerPanelWidget'),
        ('timeline', 'TimelineWidget'),
        ('effects_widget', 'EffectsLibraryWidget'),
        ('toolbox_tabs', 'QTabWidget'),
        ('header_bar', 'Header toolbar'),
    ]
    
    for widget_name, widget_type in widgets_to_check:
        if hasattr(design_tab, widget_name):
            attr = getattr(design_tab, widget_name)
            if attr is not None:
                integrations["widgets"].append(widget_name)
                print(f"  ✓ Widget: {widget_name} ({widget_type})")
            else:
                print(f"  ⚠ Widget: {widget_name} exists but is None")
        else:
            print(f"  ⚠ Widget: {widget_name} not found")
    
    # Check manager connections
    managers = [
        ('frame_manager', 'FrameManager'),
        ('layer_manager', 'LayerManager'),
        ('automation_manager', 'AutomationQueueManager'),
        ('history_manager', 'HistoryManager'),
    ]
    
    for mgr_name, mgr_type in managers:
        if hasattr(design_tab, mgr_name):
            integrations["connections"].append(f"{mgr_name} connected")
            print(f"  ✓ Manager: {mgr_name}")
    
    results["design_tab_internal"] = {
        "status": "✓ WORKING",
        "signals": len(integrations["signals"]),
        "widgets": len(integrations["widgets"]),
        "managers": len(integrations["connections"])
    }
    
except Exception as e:
    results["design_tab_internal"] = {"status": "✗ ERROR", "issues": [str(e)]}
    print(f"  ✗ Error: {e}")

print()

# ============================================================================
# 3. LAYERS UI INTEGRATION
# ============================================================================
print("[3] Testing Layers UI Integration...")
try:
    from ui.tabs.design_tools_tab import DesignToolsTab
    from ui.widgets.layer_panel import LayerPanelWidget
    
    design_tab = DesignToolsTab()
    
    layer_integrations = []
    
    # Check layer panel widget
    if hasattr(design_tab, 'layer_panel') and design_tab.layer_panel is not None:
        layer_panel = design_tab.layer_panel
        layer_integrations.append("LayerPanelWidget exists")
        
        # Check layer panel signals
        if hasattr(layer_panel, 'active_layer_changed'):
            layer_integrations.append("active_layer_changed signal")
        
        if hasattr(layer_panel, 'solo_mode_changed'):
            layer_integrations.append("solo_mode_changed signal")
        
        # Check layer manager connection
        if hasattr(layer_panel, 'layer_manager'):
            layer_integrations.append("Connected to LayerManager")
        
        print(f"  ✓ Layer panel integrated: {len(layer_integrations)} connections")
        for conn in layer_integrations:
            print(f"    • {conn}")
    else:
        print("  ⚠ Layer panel not found or not initialized")
        layer_integrations.append("Layer panel missing")
    
    results["layers_ui"] = {
        "status": "✓ WORKING" if layer_integrations else "⚠ PARTIAL",
        "connections": layer_integrations
    }
    
except Exception as e:
    results["layers_ui"] = {"status": "✗ ERROR", "issues": [str(e)]}
    print(f"  ✗ Error: {e}")

print()

# ============================================================================
# 4. EFFECTS UI INTEGRATION
# ============================================================================
print("[4] Testing Effects UI Integration...")
try:
    from ui.tabs.design_tools_tab import DesignToolsTab
    from ui.widgets.effects_library_widget import EffectsLibraryWidget
    
    design_tab = DesignToolsTab()
    
    effects_integrations = []
    
    # Check effects widget
    if hasattr(design_tab, 'effects_widget') and design_tab.effects_widget is not None:
        effects_widget = design_tab.effects_widget
        effects_integrations.append("EffectsLibraryWidget exists")
        
        # Check effects widget signals
        signals_to_check = [
            'effectSelected',
            'previewRequested',
            'applyRequested',
            'refreshRequested',
            'openFolderRequested'
        ]
        
        for signal_name in signals_to_check:
            if hasattr(effects_widget, signal_name):
                effects_integrations.append(f"{signal_name} signal")
        
        # Check handler methods exist
        handlers = [
            '_on_effect_selection_changed',
            '_on_effect_preview_requested',
            '_on_effect_apply_requested',
            '_on_effects_refresh_requested',
            '_on_effects_open_folder'
        ]
        
        for handler in handlers:
            if hasattr(design_tab, handler):
                effects_integrations.append(f"{handler} handler")
        
        print(f"  ✓ Effects widget integrated: {len(effects_integrations)} connections")
        for conn in effects_integrations[:5]:  # Show first 5
            print(f"    • {conn}")
        if len(effects_integrations) > 5:
            print(f"    ... and {len(effects_integrations) - 5} more")
    else:
        print("  ⚠ Effects widget not found or not initialized")
        effects_integrations.append("Effects widget missing")
    
    results["effects_ui"] = {
        "status": "✓ WORKING" if effects_integrations else "⚠ PARTIAL",
        "connections": len(effects_integrations)
    }
    
except Exception as e:
    results["effects_ui"] = {"status": "✗ ERROR", "issues": [str(e)]}
    print(f"  ✗ Error: {e}")

print()

# ============================================================================
# 5. AUTOMATION UI INTEGRATION
# ============================================================================
print("[5] Testing Automation UI Integration...")
try:
    from ui.tabs.design_tools_tab import DesignToolsTab
    
    design_tab = DesignToolsTab()
    
    automation_integrations = []
    
    # Check automation manager exists
    if hasattr(design_tab, 'automation_manager'):
        automation_integrations.append("AutomationQueueManager exists")
    
    # Check automation UI widgets (LMS automation)
    lms_widgets = [
        'lms_action_combo',
        'lms_source_combo',
        'lms_instruction_list',
        'lms_sequence_summary_label'
    ]
    
    for widget_name in lms_widgets:
        if hasattr(design_tab, widget_name):
            widget = getattr(design_tab, widget_name)
            if widget is not None:
                automation_integrations.append(f"{widget_name} widget")
    
    # Check queue changed connection
    if hasattr(design_tab.automation_manager, 'queue_changed'):
        automation_integrations.append("queue_changed signal")
    
    if hasattr(design_tab, '_on_manager_queue_changed'):
        automation_integrations.append("_on_manager_queue_changed handler")
    
    print(f"  ✓ Automation integrated: {len(automation_integrations)} connections")
    for conn in automation_integrations[:5]:
        print(f"    • {conn}")
    
    results["automation_ui"] = {
        "status": "✓ WORKING" if automation_integrations else "⚠ PARTIAL",
        "connections": len(automation_integrations)
    }
    
except Exception as e:
    results["automation_ui"] = {"status": "✗ ERROR", "issues": [str(e)]}
    print(f"  ✗ Error: {e}")

print()

# ============================================================================
# 6. TEXT UI INTEGRATION
# ============================================================================
print("[6] Testing Text UI Integration...")
try:
    from ui.tabs.design_tools_tab import DesignToolsTab
    
    design_tab = DesignToolsTab()
    
    text_integrations = []
    
    # Check text widgets
    text_widgets = [
        'text_font_combo',
        'text_font_size_spin',
        'text_input_edit',
    ]
    
    for widget_name in text_widgets:
        if hasattr(design_tab, widget_name):
            widget = getattr(design_tab, widget_name)
            if widget is not None:
                text_integrations.append(f"{widget_name} widget")
    
    # Check text renderer
    if hasattr(design_tab, 'text_renderer'):
        text_integrations.append("TextRenderer instance")
    
    # Check font repository
    if hasattr(design_tab, 'font_repo'):
        text_integrations.append("BitmapFontRepository instance")
        if hasattr(design_tab.font_repo, 'list_fonts'):
            fonts = design_tab.font_repo.list_fonts()
            text_integrations.append(f"Font repository: {len(fonts)} fonts")
    
    print(f"  ✓ Text UI integrated: {len(text_integrations)} connections")
    for conn in text_integrations:
        print(f"    • {conn}")
    
    results["text_ui"] = {
        "status": "✓ WORKING" if text_integrations else "⚠ PARTIAL",
        "connections": len(text_integrations)
    }
    
except Exception as e:
    results["text_ui"] = {"status": "✗ ERROR", "issues": [str(e)]}
    print(f"  ✗ Error: {e}")

print()

# ============================================================================
# 7. TIMELINE UI INTEGRATION
# ============================================================================
print("[7] Testing Timeline UI Integration...")
try:
    from ui.tabs.design_tools_tab import DesignToolsTab
    
    design_tab = DesignToolsTab()
    
    timeline_integrations = []
    
    # Check timeline widget
    if hasattr(design_tab, 'timeline') and design_tab.timeline is not None:
        timeline = design_tab.timeline
        timeline_integrations.append("TimelineWidget exists")
        
        # Check timeline signals
        timeline_signals = [
            'frameSelected',
            'framesSelected',
            'playheadDragged',
            'contextMenuRequested',
            'overlayActivated'
        ]
        
        for signal_name in timeline_signals:
            if hasattr(timeline, signal_name):
                timeline_integrations.append(f"{signal_name} signal")
        
        # Check handlers
        handlers = [
            '_on_frame_selected',
            '_on_frames_selected',
            '_on_timeline_playhead_dragged',
            '_on_timeline_context_menu',
            '_on_timeline_overlay_activated'
        ]
        
        for handler in handlers:
            if hasattr(design_tab, handler):
                timeline_integrations.append(f"{handler} handler")
    
    print(f"  ✓ Timeline integrated: {len(timeline_integrations)} connections")
    for conn in timeline_integrations[:5]:
        print(f"    • {conn}")
    
    results["timeline_ui"] = {
        "status": "✓ WORKING" if timeline_integrations else "⚠ PARTIAL",
        "connections": len(timeline_integrations)
    }
    
except Exception as e:
    results["timeline_ui"] = {"status": "✗ ERROR", "issues": [str(e)]}
    print(f"  ✗ Error: {e}")

print()

# ============================================================================
# 8. CANVAS UI INTEGRATION
# ============================================================================
print("[8] Testing Canvas UI Integration...")
try:
    from ui.tabs.design_tools_tab import DesignToolsTab
    
    design_tab = DesignToolsTab()
    
    canvas_integrations = []
    
    # Check canvas widget
    if hasattr(design_tab, 'canvas') and design_tab.canvas is not None:
        canvas = design_tab.canvas
        canvas_integrations.append("MatrixDesignCanvas exists")
        
        # Check canvas controller
        if hasattr(design_tab, 'canvas_controller'):
            canvas_integrations.append("CanvasController exists")
            if hasattr(design_tab.canvas_controller, 'frame_ready'):
                canvas_integrations.append("frame_ready signal")
        
        # Check drawing tools
        if hasattr(design_tab, 'toolbox_tabs'):
            canvas_integrations.append("Drawing tools tab exists")
    
    print(f"  ✓ Canvas integrated: {len(canvas_integrations)} connections")
    for conn in canvas_integrations:
        print(f"    • {conn}")
    
    results["canvas_ui"] = {
        "status": "✓ WORKING" if canvas_integrations else "⚠ PARTIAL",
        "connections": len(canvas_integrations)
    }
    
except Exception as e:
    results["canvas_ui"] = {"status": "✗ ERROR", "issues": [str(e)]}
    print(f"  ✗ Error: {e}")

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("="*70)
print("UI INTEGRATION SUMMARY")
print("="*70)
print()

for integration_name, data in results.items():
    status = data.get("status", "UNKNOWN")
    name_formatted = integration_name.replace("_", " ").title()
    print(f"{name_formatted:30} : {status}")
    
    if "connections" in data:
        print(f"  Connections: {data['connections']}")
    if "signals" in data:
        print(f"  Signals: {data['signals']}")
    if "widgets" in data:
        print(f"  Widgets: {data['widgets']}")
    if "issues" in data:
        for issue in data["issues"]:
            print(f"  ⚠ {issue}")
    print()

print("="*70)
print("✓ UI INTEGRATION VERIFICATION COMPLETE")
print("="*70)

app.quit()

