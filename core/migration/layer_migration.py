"""
Layer Migration - Convert old per-frame layer structure to new LayerTrack structure.

This module handles migration from the old layer architecture (per-frame layers)
to the new architecture (layer tracks spanning frames).
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from domain.layers import Layer, LayerTrack, LayerFrame, LayerGroup, LayerManager
from domain.pattern_state import PatternState

Color = Tuple[int, int, int]


def detect_old_layer_structure(layer_manager: LayerManager) -> bool:
    """
    Detect if layer manager is using old per-frame structure.
    
    Returns True if old structure detected, False otherwise.
    """
    # Check if legacy layers exist
    if hasattr(layer_manager, '_legacy_layers') and layer_manager._legacy_layers:
        return True
    
    # Check if using legacy mode
    if hasattr(layer_manager, '_use_legacy_mode') and layer_manager._use_legacy_mode:
        return True
    
    # Check if layer tracks are empty but pattern has frames
    if not layer_manager._layer_tracks:
        pattern = layer_manager._state.pattern()
        if pattern and pattern.frames:
            # Might be old structure - check if we need to migrate
            return True
    
    return False


def migrate_layers_to_tracks(
    layer_manager: LayerManager,
    old_layers: Dict[int, List[Layer]],
    old_groups: Optional[Dict[int, Dict[str, LayerGroup]]] = None
) -> None:
    """
    Migrate old per-frame layer structure to new LayerTrack structure.
    
    Args:
        layer_manager: LayerManager instance to migrate
        old_layers: Old structure: {frame_index: [Layer, ...]}
        old_groups: Old groups: {frame_index: {group_id: LayerGroup}}
    """
    if not old_layers:
        return
    
    # Collect all unique layer names across frames
    layer_names: Dict[str, List[Tuple[int, int, Layer]]] = {}  # name -> [(frame_idx, layer_idx, layer), ...]
    
    for frame_idx, layers in old_layers.items():
        for layer_idx, layer in enumerate(layers):
            layer_name = layer.name
            if layer_name not in layer_names:
                layer_names[layer_name] = []
            layer_names[layer_name].append((frame_idx, layer_idx, layer))
    
    # Create LayerTracks from grouped layers
    layer_manager._layer_tracks = []
    z_index = 0
    
    # Process layers in order of first appearance
    processed_names = set()
    for frame_idx in sorted(old_layers.keys()):
        for layer_idx, layer in enumerate(old_layers[frame_idx]):
            if layer.name in processed_names:
                continue
            
            # Create new LayerTrack
            track = LayerTrack(
                name=layer.name,
                visible=layer.visible,
                opacity=layer.opacity,
                blend_mode=layer.blend_mode,
                group_id=layer.group_id,
                locked=layer.locked,
                z_index=z_index
            )
            z_index += 1
            
            # Add all frames for this layer
            for f_idx, l_idx, l in layer_names[layer.name]:
                # Create LayerFrame from Layer
                layer_frame = LayerFrame(
                    pixels=list(l.pixels),
                    visible=None if l.visible == layer.visible else l.visible,
                    opacity=None if abs(l.opacity - layer.opacity) < 0.001 else l.opacity,
                    mask=l.mask.copy() if l.mask else None
                )
                track.set_frame(f_idx, layer_frame)
            
            layer_manager._layer_tracks.append(track)
            processed_names.add(layer.name)
    
    # Migrate groups (groups now span frames)
    if old_groups:
        layer_manager._groups = {}
        # Collect all unique groups across frames
        all_groups: Dict[str, LayerGroup] = {}
        
        for frame_idx, groups in old_groups.items():
            for group_id, group in groups.items():
                if group_id not in all_groups:
                    all_groups[group_id] = group
        
        layer_manager._groups = all_groups
    
    # Clear legacy data
    layer_manager._legacy_layers = None
    layer_manager._legacy_groups = None
    layer_manager._use_legacy_mode = False
    
    # Emit signals for all frames
    layer_manager.layers_changed.emit(-1)  # -1 = all frames


def auto_migrate_on_load(layer_manager: LayerManager) -> bool:
    """
    Automatically migrate old layer structure if detected.
    
    This should be called when loading a pattern to ensure backward compatibility.
    
    Returns:
        True if migration was performed, False otherwise
    """
    # Check if we have legacy data to migrate
    if hasattr(layer_manager, '_legacy_layers') and layer_manager._legacy_layers:
        old_layers = layer_manager._legacy_layers
        old_groups = getattr(layer_manager, '_legacy_groups', None)
        
        migrate_layers_to_tracks(layer_manager, old_layers, old_groups)
        return True
    
    # Check if layer tracks are empty but we should have layers
    pattern = layer_manager._state.pattern()
    if pattern and pattern.frames and not layer_manager._layer_tracks:
        # Initialize with default layer track (already done in set_pattern)
        # But check if we need to migrate from frame pixels
        return False
    
    return False


def create_migration_backup(layer_manager: LayerManager) -> Dict:
    """
    Create a backup of current layer state before migration.
    
    Returns:
        Dictionary with backup data
    """
    backup = {
        'layer_tracks': [track.copy() for track in layer_manager._layer_tracks],
        'groups': {gid: LayerGroup(g.group_id, g.name, g.visible, g.opacity) 
                  for gid, g in layer_manager._groups.items()},
    }
    
    if hasattr(layer_manager, '_legacy_layers') and layer_manager._legacy_layers:
        backup['legacy_layers'] = {
            frame_idx: [layer.copy() for layer in layers]
            for frame_idx, layers in layer_manager._legacy_layers.items()
        }
    
    return backup


def restore_from_backup(layer_manager: LayerManager, backup: Dict) -> None:
    """
    Restore layer state from backup.
    
    Args:
        layer_manager: LayerManager instance
        backup: Backup data from create_migration_backup
    """
    if 'layer_tracks' in backup:
        layer_manager._layer_tracks = [track.copy() for track in backup['layer_tracks']]
    
    if 'groups' in backup:
        layer_manager._groups = {
            gid: LayerGroup(g.group_id, g.name, g.visible, g.opacity)
            for gid, g in backup['groups'].items()
        }
    
    if 'legacy_layers' in backup:
        layer_manager._legacy_layers = {
            frame_idx: [layer.copy() for layer in layers]
            for frame_idx, layers in backup['legacy_layers'].items()
        }
