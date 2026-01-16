"""
Unit tests for Project File Format (.ledproj)

Tests project file save/load, atomic writes, and version migration.
"""

import pytest
import json
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime

from core.pattern import Pattern, Frame, PatternMetadata
from core.project.project_file import (
    ProjectFile,
    save_project,
    load_project,
    ProjectFileError,
)
from core.project.project_metadata import ProjectMetadata, ProjectSettings
from core.project.versioning import (
    ProjectVersion,
    migrate_project,
    get_project_version,
    needs_migration,
)


class TestProjectFile:
    """Test ProjectFile class"""
    
    def test_project_file_creation(self):
        """Test creating a ProjectFile"""
        pattern = Pattern(
            metadata=PatternMetadata(width=8, height=8),
            frames=[Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)]
        )
        metadata = ProjectMetadata(name="Test Project")
        
        project = ProjectFile(pattern=pattern, metadata=metadata)
        
        assert project.pattern == pattern
        assert project.metadata.name == "Test Project"
    
    def test_project_file_to_dict(self):
        """Test converting project to dictionary"""
        pattern = Pattern(
            id="test-id",
            name="Test Pattern",
            metadata=PatternMetadata(width=4, height=4),
            frames=[Frame(pixels=[(255, 0, 0)] * 16, duration_ms=100)]
        )
        metadata = ProjectMetadata(name="Test Project", author="Test Author")
        
        project = ProjectFile(pattern=pattern, metadata=metadata)
        project_dict = project.to_dict()
        
        assert project_dict["project_version"] == "1.1"
        assert project_dict["schema_version"] == "1.0"
        assert project_dict["metadata"]["name"] == "Test Project"
        assert project_dict["metadata"]["author"] == "Test Author"
        assert "pattern" in project_dict
    
    def test_project_file_from_dict(self):
        """Test creating project from dictionary"""
        project_dict = {
            "project_version": "1.1",
            "schema_version": "1.0",
            "metadata": {
                "project_version": "1.1",
                "name": "Test Project",
                "author": "Test Author",
                "tags": ["test"],
                "settings": {}
            },
            "pattern": {
                "schema_version": "1.0",
                "id": str(uuid.uuid4()),
                "name": "Test Pattern",
                "description": "",
                "tags": [],
                "created_at": datetime.utcnow().isoformat() + 'Z',
                "modified_at": datetime.utcnow().isoformat() + 'Z',
                "matrix": {
                    "width": 8,
                    "height": 8,
                    "layout": "row_major",
                    "wiring": "linear",
                    "default_color_order": "RGB"
                },
                "frames": [
                    {
                        "index": 0,
                        "duration_ms": 100,
                        "layers": [
                            {
                                "id": str(uuid.uuid4()),
                                "name": "base",
                                "opacity": 1.0,
                                "blend_mode": "normal",
                                "visible": True,
                                "pixels": [[255, 0, 0]] * 64,
                                "encoding": "raw+rgb8"
                            }
                        ]
                    }
                ],
                "effects": [],
                "metadata": {}
            }
        }
        
        project = ProjectFile.from_dict(project_dict)
        
        assert project.metadata.name == "Test Project"
        assert project.metadata.author == "Test Author"
        assert project.pattern.metadata.width == 8
    
    def test_project_file_save_load(self, tmp_path):
        """Test saving and loading project file"""
        pattern = Pattern(
            id="save-test-id",
            name="Save Test Pattern",
            metadata=PatternMetadata(width=8, height=8),
            frames=[
                Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100),
                Frame(pixels=[(0, 255, 0)] * 64, duration_ms=150)
            ]
        )
        metadata = ProjectMetadata(
            name="Save Test Project",
            author="Test Author",
            tags=["test", "save"]
        )
        
        project = ProjectFile(pattern=pattern, metadata=metadata)
        file_path = tmp_path / "test_project.ledproj"
        
        # Save
        project.save(file_path)
        assert file_path.exists()
        
        # Load
        loaded_project = ProjectFile.load(file_path)
        
        assert loaded_project.metadata.name == "Save Test Project"
        assert loaded_project.metadata.author == "Test Author"
        assert "test" in loaded_project.metadata.tags
        assert loaded_project.pattern.id == "save-test-id"
        assert len(loaded_project.pattern.frames) == 2
    
    def test_atomic_save(self, tmp_path):
        """Test that atomic save prevents corruption"""
        pattern = Pattern(
            metadata=PatternMetadata(width=4, height=4),
            frames=[Frame(pixels=[(255, 0, 0)] * 16, duration_ms=100)]
        )
        
        project = ProjectFile(pattern=pattern)
        file_path = tmp_path / "atomic_test.ledproj"
        
        # Save (atomic)
        project.save(file_path)
        
        # Verify no temp file remains
        temp_file = file_path.with_suffix('.ledproj.tmp')
        assert not temp_file.exists()
        
        # Verify file is valid JSON
        with open(file_path, 'r') as f:
            data = json.load(f)
            assert "project_version" in data
            assert "pattern" in data
    
    def test_save_load_round_trip(self, tmp_path):
        """Test round-trip save/load preserves data"""
        original_pattern = Pattern(
            id="round-trip-id",
            name="Round Trip Pattern",
            metadata=PatternMetadata(width=16, height=16, color_order="GRB"),
            frames=[
                Frame(pixels=[(255, 0, 0), (0, 255, 0), (0, 0, 255)] * 85 + [(255, 255, 0)], duration_ms=150),
                Frame(pixels=[(0, 255, 255), (255, 0, 255)] * 128, duration_ms=200)
            ]
        )
        original_metadata = ProjectMetadata(
            name="Round Trip Project",
            author="Test Author",
            description="Round trip test",
            tags=["test", "round-trip"]
        )
        
        project = ProjectFile(pattern=original_pattern, metadata=original_metadata)
        file_path = tmp_path / "round_trip.ledproj"
        
        # Save
        project.save(file_path)
        
        # Load
        loaded_project = ProjectFile.load(file_path)
        
        # Verify round-trip
        assert loaded_project.pattern.id == original_pattern.id
        assert loaded_project.pattern.name == original_pattern.name
        assert loaded_project.pattern.metadata.width == original_pattern.metadata.width
        assert loaded_project.pattern.metadata.color_order == original_pattern.metadata.color_order
        assert len(loaded_project.pattern.frames) == len(original_pattern.frames)
        
        for orig_frame, loaded_frame in zip(original_pattern.frames, loaded_project.pattern.frames):
            assert loaded_frame.duration_ms == orig_frame.duration_ms
            assert loaded_frame.pixels == orig_frame.pixels
        
        assert loaded_project.metadata.name == original_metadata.name
        assert loaded_project.metadata.author == original_metadata.author
        assert loaded_project.metadata.tags == original_metadata.tags


class TestProjectVersioning:
    """Test project version migration"""
    
    def test_get_project_version(self):
        """Test getting project version"""
        data_v1 = {
            "project_version": "1.1",
            "metadata": {"project_version": "1.1"}
        }
        assert get_project_version(data_v1) == "1.1"
        
        data_no_version = {"name": "Test"}
        assert get_project_version(data_no_version) is None
    
    def test_needs_migration(self):
        """Test migration detection"""
        data_v1 = {"project_version": "1.1", "metadata": {"project_version": "1.1"}}
        assert needs_migration(data_v1) is False
        
        data_old = {"metadata": {"project_version": "1.0"}}
        assert needs_migration(data_old) is True
    
    def test_migrate_v1_0_to_1_1(self):
        """Test migration from v1.0 to v1.1"""
        data_v1_0 = {
            "project_version": "1.0",
            "metadata": {"project_version": "1.0", "name": "Test"},
            "pattern": {}
        }
        
        migrated = migrate_project(data_v1_0, target_version="1.1")
        
        assert migrated["project_version"] == "1.1"
        assert migrated["metadata"]["project_version"] == "1.1"
        assert "settings" in migrated["metadata"]


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_save_project_function(self, tmp_path):
        """Test save_project convenience function"""
        pattern = Pattern(
            metadata=PatternMetadata(width=8, height=8),
            frames=[Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)]
        )
        metadata = ProjectMetadata(name="Convenience Test")
        
        file_path = tmp_path / "convenience_test.ledproj"
        save_project(pattern, file_path, metadata=metadata)
        
        assert file_path.exists()
    
    def test_load_project_function(self, tmp_path):
        """Test load_project convenience function"""
        pattern = Pattern(
            metadata=PatternMetadata(width=8, height=8),
            frames=[Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)]
        )
        metadata = ProjectMetadata(name="Load Test")
        
        file_path = tmp_path / "load_test.ledproj"
        save_project(pattern, file_path, metadata=metadata)
        
        loaded_pattern, loaded_metadata = load_project(file_path)
        
        assert loaded_pattern.metadata.width == 8
        assert loaded_metadata.name == "Load Test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

