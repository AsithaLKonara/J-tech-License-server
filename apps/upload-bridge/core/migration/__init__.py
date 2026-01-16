"""
Migration module for converting between different data structure versions.
"""

from .layer_migration import (
    auto_migrate_on_load,
    detect_old_layer_structure,
    migrate_layers_to_tracks,
    create_migration_backup,
    restore_from_backup,
)

__all__ = [
    'auto_migrate_on_load',
    'detect_old_layer_structure',
    'migrate_layers_to_tracks',
    'create_migration_backup',
    'restore_from_backup',
]
