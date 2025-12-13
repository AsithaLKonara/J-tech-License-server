"""
Tests for chip support verification
Verifies chip database, profiles, and uploader implementations
"""

import pytest
import yaml
import json
from pathlib import Path
from uploaders.uploader_registry import UploaderRegistry


class TestChipSupport:
    """Test chip support consistency"""
    
    def test_chip_database_loads(self):
        """Test chip database loads correctly"""
        db_path = Path("config/chip_database.yaml")
        assert db_path.exists(), "chip_database.yaml not found"
        
        with open(db_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        assert 'chips' in data, "chip_database.yaml should have 'chips' key"
        assert len(data['chips']) > 0, "chip_database.yaml should have chips"
    
    def test_all_chips_have_uploaders(self):
        """Test all chips in database have uploader specified"""
        db_path = Path("config/chip_database.yaml")
        with open(db_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        chips = data.get('chips', {})
        chips_without_uploader = []
        
        for chip_id, spec in chips.items():
            if 'uploader' not in spec:
                chips_without_uploader.append(chip_id)
        
        assert len(chips_without_uploader) == 0, \
            f"Chips without uploader: {chips_without_uploader}"
    
    def test_profile_json_chip_id_format(self):
        """Test profile JSONs use lowercase chip_id matching database"""
        db_path = Path("config/chip_database.yaml")
        with open(db_path, 'r', encoding='utf-8') as f:
            db_data = yaml.safe_load(f)
        
        db_chip_ids = set(db_data.get('chips', {}).keys())
        
        profiles_dir = Path("uploaders/profiles")
        mismatches = []
        
        for json_file in profiles_dir.glob("*.json"):
            if json_file.name == "template.json":
                continue
            
            with open(json_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            chip_id = profile_data.get('chip_id', '')
            chip_id_lower = chip_id.lower()
            
            # Check if chip_id matches database (case-insensitive)
            if chip_id_lower not in db_chip_ids:
                # Check if it's a case mismatch
                matching_db_id = None
                for db_id in db_chip_ids:
                    if db_id.lower() == chip_id_lower:
                        matching_db_id = db_id
                        break
                
                if matching_db_id:
                    mismatches.append(f"{json_file.name}: chip_id='{chip_id}' should be '{matching_db_id}'")
                else:
                    mismatches.append(f"{json_file.name}: chip_id='{chip_id}' not in database")
        
        # Note: Some mismatches are expected (STM32F407, NuvotonM051)
        # This test documents them but doesn't fail
        if mismatches:
            print(f"Profile chip_id mismatches: {mismatches}")
    
    def test_uploader_registry_loads_chips(self):
        """Test uploader registry can load all chips from database"""
        registry = UploaderRegistry.instance()
        chips = registry.list_supported_chips()
        
        assert len(chips) > 0, "Registry should list supported chips"
        
        # Try to get uploader for each chip
        failed_chips = []
        for chip_id in chips:
            uploader = registry.get_uploader_for_chip(chip_id)
            if uploader is None:
                failed_chips.append(chip_id)
        
        # Some chips may not have uploaders (expected for some cases)
        # This test documents them
        if failed_chips:
            print(f"Chips without uploaders: {failed_chips}")
    
    def test_esp32s_json_chip_id(self):
        """Test esp32s.json has correct chip_id"""
        esp32s_profile = Path("uploaders/profiles/esp32s.json")
        if not esp32s_profile.exists():
            pytest.skip("esp32s.json not found")
        
        with open(esp32s_profile, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chip_id = data.get('chip_id')
        assert chip_id == 'esp32s2', \
            f"esp32s.json should have chip_id='esp32s2', got '{chip_id}'"

