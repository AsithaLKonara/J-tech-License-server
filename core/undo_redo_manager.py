"""
Shared Undo/Redo Manager - Cross-tab undo/redo coordination
"""

from PySide6.QtCore import QObject, Signal
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class UndoCommand:
    """Base class for undo/redo commands"""
    
    def __init__(self, description: str = ""):
        self.description = description
    
    def execute(self):
        """Execute the command (redo)"""
        raise NotImplementedError
    
    def undo(self):
        """Undo the command"""
        raise NotImplementedError


class SharedUndoRedoManager(QObject):
    """
    Shared undo/redo manager for coordinating undo/redo across tabs
    Maintains separate history stacks per tab
    """
    
    # Signals
    undo_available_changed = Signal(str, bool)  # tab_name, available
    redo_available_changed = Signal(str, bool)  # tab_name, available
    
    def __init__(self, max_history: int = 50):
        """
        Initialize undo/redo manager
        
        Args:
            max_history: Maximum number of commands to keep in history per tab
        """
        super().__init__()
        self.max_history = max_history
        # History stacks per tab: {tab_name: {'undo': [commands], 'redo': [commands]}}
        self._histories: Dict[str, Dict[str, List[UndoCommand]]] = {}
        # Current positions per tab: {tab_name: position}
        self._positions: Dict[str, int] = {}
    
    def push_command(self, tab_name: str, command: UndoCommand):
        """
        Push a command to the undo history for a tab
        
        Args:
            tab_name: Name of the tab
            command: Command to push
        """
        if tab_name not in self._histories:
            self._histories[tab_name] = {'undo': [], 'redo': []}
            self._positions[tab_name] = -1
        
        # Clear redo stack when new command is pushed
        self._histories[tab_name]['redo'] = []
        
        # Add command to undo stack
        self._histories[tab_name]['undo'].append(command)
        
        # Limit history size
        if len(self._histories[tab_name]['undo']) > self.max_history:
            self._histories[tab_name]['undo'].pop(0)
        else:
            self._positions[tab_name] += 1
        
        # Emit signals
        self.undo_available_changed.emit(tab_name, self.can_undo(tab_name))
        self.redo_available_changed.emit(tab_name, False)
        
        logger.debug(f"Pushed command to {tab_name}: {command.description}")
    
    def undo(self, tab_name: str) -> bool:
        """
        Undo last command for a tab
        
        Args:
            tab_name: Name of the tab
            
        Returns:
            True if undo was successful, False otherwise
        """
        if not self.can_undo(tab_name):
            return False
        
        try:
            history = self._histories[tab_name]
            if history['undo']:
                command = history['undo'].pop()
                command.undo()
                
                # Move to redo stack
                history['redo'].append(command)
                self._positions[tab_name] -= 1
                
                # Emit signals
                self.undo_available_changed.emit(tab_name, self.can_undo(tab_name))
                self.redo_available_changed.emit(tab_name, self.can_redo(tab_name))
                
                logger.debug(f"Undid command in {tab_name}: {command.description}")
                return True
        except Exception as e:
            logger.error(f"Failed to undo in {tab_name}: {e}", exc_info=True)
            return False
    
    def redo(self, tab_name: str) -> bool:
        """
        Redo last undone command for a tab
        
        Args:
            tab_name: Name of the tab
            
        Returns:
            True if redo was successful, False otherwise
        """
        if not self.can_redo(tab_name):
            return False
        
        try:
            history = self._histories[tab_name]
            if history['redo']:
                command = history['redo'].pop()
                command.execute()
                
                # Move back to undo stack
                history['undo'].append(command)
                self._positions[tab_name] += 1
                
                # Emit signals
                self.undo_available_changed.emit(tab_name, self.can_undo(tab_name))
                self.redo_available_changed.emit(tab_name, self.can_redo(tab_name))
                
                logger.debug(f"Redid command in {tab_name}: {command.description}")
                return True
        except Exception as e:
            logger.error(f"Failed to redo in {tab_name}: {e}", exc_info=True)
            return False
    
    def can_undo(self, tab_name: str) -> bool:
        """Check if undo is available for a tab"""
        if tab_name not in self._histories:
            return False
        return len(self._histories[tab_name]['undo']) > 0
    
    def can_redo(self, tab_name: str) -> bool:
        """Check if redo is available for a tab"""
        if tab_name not in self._histories:
            return False
        return len(self._histories[tab_name]['redo']) > 0
    
    def clear_history(self, tab_name: str):
        """Clear undo/redo history for a tab"""
        if tab_name in self._histories:
            self._histories[tab_name] = {'undo': [], 'redo': []}
            self._positions[tab_name] = -1
            self.undo_available_changed.emit(tab_name, False)
            self.redo_available_changed.emit(tab_name, False)
            logger.debug(f"Cleared history for {tab_name}")
    
    def get_history_info(self, tab_name: str) -> Dict[str, Any]:
        """Get history information for a tab"""
        if tab_name not in self._histories:
            return {'undo_count': 0, 'redo_count': 0}
        
        history = self._histories[tab_name]
        return {
            'undo_count': len(history['undo']),
            'redo_count': len(history['redo']),
            'can_undo': self.can_undo(tab_name),
            'can_redo': self.can_redo(tab_name)
        }

