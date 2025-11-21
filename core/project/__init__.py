"""
Project File Format (.ledproj) - Pattern project management

Provides utilities for saving and loading .ledproj files which contain
patterns with project metadata, versioning, and atomic save support.
"""

from .project_file import (
    ProjectFile,
    save_project,
    load_project,
    ProjectFileError,
)
from .project_metadata import (
    ProjectMetadata,
    ProjectSettings,
)
from .versioning import (
    ProjectVersion,
    migrate_project,
    get_project_version,
    needs_migration,
)

__all__ = [
    'ProjectFile',
    'save_project',
    'load_project',
    'ProjectFileError',
    'ProjectMetadata',
    'ProjectSettings',
    'ProjectVersion',
    'migrate_project',
    'get_project_version',
    'needs_migration',
]

