"""
Unit tests for pattern templates library.
"""

import pytest
from core.pattern_templates import TemplateLibrary, TemplateCategory, PatternTemplate
from core.pattern import Pattern


class TestTemplateLibrary:
    """Test TemplateLibrary functionality."""
    
    def test_library_initialization(self):
        """Test that library initializes with templates."""
        library = TemplateLibrary()
        assert len(library.templates) > 0
    
    def test_list_templates_all(self):
        """Test listing all templates."""
        library = TemplateLibrary()
        templates = library.list_templates()
        assert len(templates) > 0
        assert all(isinstance(t, PatternTemplate) for t in templates)
    
    def test_list_templates_by_category(self):
        """Test filtering templates by category."""
        library = TemplateLibrary()
        animation_templates = library.list_templates(TemplateCategory.ANIMATION)
        effect_templates = library.list_templates(TemplateCategory.EFFECT)
        text_templates = library.list_templates(TemplateCategory.TEXT)
        
        assert all(t.category == TemplateCategory.ANIMATION for t in animation_templates)
        assert all(t.category == TemplateCategory.EFFECT for t in effect_templates)
        assert all(t.category == TemplateCategory.TEXT for t in text_templates)
    
    def test_get_template(self):
        """Test getting a template by name."""
        library = TemplateLibrary()
        template = library.get_template("Bouncing Ball")
        assert template is not None
        assert template.name == "Bouncing Ball"
        assert template.category == TemplateCategory.ANIMATION
    
    def test_get_template_not_found(self):
        """Test getting non-existent template."""
        library = TemplateLibrary()
        template = library.get_template("NonExistent Template")
        assert template is None
    
    def test_generate_bouncing_ball(self):
        """Test generating bouncing ball pattern."""
        library = TemplateLibrary()
        pattern = library.generate_pattern("Bouncing Ball", width=16, height=16, frames=10)
        
        assert isinstance(pattern, Pattern)
        assert pattern.metadata.width == 16
        assert pattern.metadata.height == 16
        assert len(pattern.frames) == 10
    
    def test_generate_fire_effect(self):
        """Test generating fire effect pattern."""
        library = TemplateLibrary()
        pattern = library.generate_pattern("Fire Effect", width=32, height=16, frames=15)
        
        assert isinstance(pattern, Pattern)
        assert pattern.metadata.width == 32
        assert pattern.metadata.height == 16
        assert len(pattern.frames) == 15
    
    def test_generate_scrolling_text(self):
        """Test generating scrolling text pattern."""
        library = TemplateLibrary()
        pattern = library.generate_pattern(
            "Scrolling Text",
            width=64,
            height=8,
            text="Hello",
            color=(255, 255, 0),
            direction="left"
        )
        
        assert isinstance(pattern, Pattern)
        assert pattern.metadata.width == 64
        assert pattern.metadata.height == 8
        assert len(pattern.frames) > 0
    
    def test_generate_color_cycle(self):
        """Test generating color cycle pattern."""
        library = TemplateLibrary()
        pattern = library.generate_pattern(
            "Color Cycle",
            width=16,
            height=16,
            frames=20,
            speed=1.0
        )
        
        assert isinstance(pattern, Pattern)
        assert len(pattern.frames) == 20
    
    def test_generate_wave(self):
        """Test generating wave pattern."""
        library = TemplateLibrary()
        pattern = library.generate_pattern(
            "Wave",
            width=32,
            height=16,
            frames=30,
            color=(0, 150, 255)
        )
        
        assert isinstance(pattern, Pattern)
        assert len(pattern.frames) == 30
    
    def test_generate_spiral(self):
        """Test generating spiral pattern."""
        library = TemplateLibrary()
        pattern = library.generate_pattern(
            "Spiral",
            width=24,
            height=24,
            frames=20
        )
        
        assert isinstance(pattern, Pattern)
        assert len(pattern.frames) == 20
    
    def test_generate_pulse(self):
        """Test generating pulse pattern."""
        library = TemplateLibrary()
        pattern = library.generate_pattern(
            "Pulse",
            width=16,
            height=16,
            frames=15
        )
        
        assert isinstance(pattern, Pattern)
        assert len(pattern.frames) == 15
    
    def test_generate_fade(self):
        """Test generating fade pattern."""
        library = TemplateLibrary()
        pattern = library.generate_pattern(
            "Fade",
            width=16,
            height=16,
            frames=20,
            fade_type="in_out"
        )
        
        assert isinstance(pattern, Pattern)
        assert len(pattern.frames) == 20
    
    def test_generate_random(self):
        """Test generating random pixel pattern."""
        library = TemplateLibrary()
        pattern = library.generate_pattern(
            "Random Pixels",
            width=16,
            height=16,
            frames=10,
            density=0.1
        )
        
        assert isinstance(pattern, Pattern)
        assert len(pattern.frames) == 10
    
    def test_generate_with_custom_parameters(self):
        """Test generating pattern with custom parameters."""
        library = TemplateLibrary()
        pattern = library.generate_pattern(
            "Bouncing Ball",
            width=20,
            height=20,
            color=(255, 0, 0),
            frames=25,
            speed=2.0
        )
        
        assert isinstance(pattern, Pattern)
        assert pattern.metadata.width == 20
        assert pattern.metadata.height == 20
        assert len(pattern.frames) == 25
    
    def test_generate_invalid_template(self):
        """Test generating pattern with invalid template name."""
        library = TemplateLibrary()
        with pytest.raises(ValueError, match="Template not found"):
            library.generate_pattern("Invalid Template", width=16, height=16)

