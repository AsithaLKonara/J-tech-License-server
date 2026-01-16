"""
Tests for Budurasmala Animation Templates.
"""

import pytest
from core.pattern_templates import TemplateLibrary, TemplateCategory
from core.pattern import Pattern


class TestBudurasmalaAnimations:
    """Test Budurasmala animation templates."""
    
    def test_budurasmala_templates_registered(self):
        """Test that all Budurasmala templates are registered."""
        library = TemplateLibrary()
        budurasmala_templates = library.list_templates(TemplateCategory.BUDURASMALA)
        
        # Should have at least 8 templates (5 original + 3 cultural)
        assert len(budurasmala_templates) >= 8
        
        template_names = [t.name for t in budurasmala_templates]
        
        # Original templates
        assert "Ray Rotation" in template_names
        assert "Pulsing Halo" in template_names
        assert "Twinkling Stars" in template_names
        assert "Wave Propagation" in template_names
        assert "Color Gradient Rotation" in template_names
        
        # Cultural templates
        assert "Lotus Pattern" in template_names
        assert "Dharma Wheel" in template_names
        assert "Vesak Stars" in template_names
    
    def test_ray_rotation_template(self):
        """Test ray rotation animation generation."""
        library = TemplateLibrary()
        template = library.get_template("Ray Rotation")
        
        assert template is not None
        assert template.category == TemplateCategory.BUDURASMALA
        
        pattern = library.generate_pattern("Ray Rotation", width=32, height=32, frames=10)
        assert pattern is not None
        assert len(pattern.frames) == 10
        assert pattern.metadata.width == 32
        assert pattern.metadata.height == 32
    
    def test_pulsing_halo_template(self):
        """Test pulsing halo animation generation."""
        library = TemplateLibrary()
        pattern = library.generate_pattern(
            "Pulsing Halo",
            width=32,
            height=32,
            frames=20,
            ring_count=3
        )
        
        assert pattern is not None
        assert len(pattern.frames) == 20
    
    def test_twinkling_stars_template(self):
        """Test twinkling stars animation generation."""
        library = TemplateLibrary()
        pattern = library.generate_pattern(
            "Twinkling Stars",
            width=32,
            height=32,
            frames=30
        )
        
        assert pattern is not None
        assert len(pattern.frames) == 30
    
    def test_lotus_pattern_template(self):
        """Test lotus pattern generation."""
        library = TemplateLibrary()
        pattern = library.generate_pattern(
            "Lotus Pattern",
            width=32,
            height=32,
            frames=20
        )
        
        assert pattern is not None
        assert len(pattern.frames) == 20
    
    def test_dharma_wheel_template(self):
        """Test dharma wheel pattern generation."""
        library = TemplateLibrary()
        pattern = library.generate_pattern(
            "Dharma Wheel",
            width=32,
            height=32,
            frames=30
        )
        
        assert pattern is not None
        assert len(pattern.frames) == 30
    
    def test_vesak_stars_template(self):
        """Test Vesak stars pattern generation."""
        library = TemplateLibrary()
        pattern = library.generate_pattern(
            "Vesak Stars",
            width=32,
            height=32,
            frames=40
        )
        
        assert pattern is not None
        assert len(pattern.frames) == 40

