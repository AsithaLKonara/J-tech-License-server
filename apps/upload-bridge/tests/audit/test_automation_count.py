"""
Tests for automation action fixes
Verifies automation action count (should be 8+)
"""

import pytest
from pathlib import Path
from core.automation.instructions import KNOWN_LMS_ACTIONS


class TestAutomationCount:
    """Test automation actions count"""
    
    def test_automation_actions_defined(self):
        """Test automation actions are defined"""
        assert KNOWN_LMS_ACTIONS is not None, "KNOWN_LMS_ACTIONS should be defined"
        assert len(KNOWN_LMS_ACTIONS) > 0, "Should have automation actions"
    
    def test_automation_actions_count(self):
        """Test automation actions count is 8+"""
        action_count = len(KNOWN_LMS_ACTIONS)
        assert action_count >= 8, \
            f"Should have at least 8 automation actions, found {action_count}"
    
    def test_automation_actions_list(self):
        """Test specific automation actions exist"""
        expected_actions = [
            'moveLeft1', 'moveRight1', 'moveUp1', 'moveDown1',
            'scrollText', 'rotate90', 'mirrorH', 'mirrorV',
            'invert'
        ]
        
        for action in expected_actions:
            assert action in KNOWN_LMS_ACTIONS, \
                f"Action '{action}' should be in KNOWN_LMS_ACTIONS"
    
    def test_automation_instruction_classes(self):
        """Test automation instruction classes exist"""
        from core.automation.instructions import (
            LMSInstruction, PatternInstruction, PatternInstructionSequence
        )
        
        assert LMSInstruction is not None, "LMSInstruction should exist"
        assert PatternInstruction is not None, "PatternInstruction should exist"
        assert PatternInstructionSequence is not None, \
            "PatternInstructionSequence should exist"
    
    def test_automation_engine_exists(self):
        """Test automation engine is implemented"""
        engine_file = Path("core/automation/engine.py")
        assert engine_file.exists(), "Automation engine should exist"
        
        from core.automation.engine import AutomationEngine
        assert AutomationEngine is not None, "AutomationEngine should exist"

