"""
Design Tools Tab Components.

This package contains refactored components extracted from DesignToolsTab
to improve maintainability and testability.
"""

from ui.tabs.design_tools.components.pattern_operations import PatternOperationsComponent
from ui.tabs.design_tools.components.frame_management import FrameManagementComponent
from ui.tabs.design_tools.components.canvas_controller import CanvasControllerComponent

__all__ = [
    'PatternOperationsComponent',
    'FrameManagementComponent',
    'CanvasControllerComponent',
]

