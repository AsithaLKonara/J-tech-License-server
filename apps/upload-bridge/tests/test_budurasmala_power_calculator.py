"""
Tests for Budurasmala Power Calculator.
"""

import pytest
from core.power_calculator import (
    PowerCalculator,
    LEDType,
    PowerCalculation,
    VoltageDropResult
)


class TestPowerCalculator:
    """Test power calculation functionality."""
    
    def test_power_calculation_ws2812b(self):
        """Test power calculation for WS2812B LEDs."""
        result = PowerCalculator.calculate_power(
            led_count=60,
            led_type=LEDType.WS2812B,
            voltage=5.0,
            brightness_percent=100
        )
        
        assert isinstance(result, PowerCalculation)
        assert result.total_leds == 60
        assert result.max_power_watts > 0
        assert result.max_current_amps > 0
        assert result.voltage == 5.0
        assert result.recommended_psu_watts >= result.max_power_watts
    
    def test_power_calculation_brightness(self):
        """Test power calculation with brightness adjustment."""
        result_100 = PowerCalculator.calculate_power(
            led_count=60,
            led_type=LEDType.WS2812B,
            voltage=5.0,
            brightness_percent=100
        )
        
        result_50 = PowerCalculator.calculate_power(
            led_count=60,
            led_type=LEDType.WS2812B,
            voltage=5.0,
            brightness_percent=50
        )
        
        # 50% brightness should use less power
        assert result_50.max_power_watts < result_100.max_power_watts
        assert result_50.max_current_amps < result_100.max_current_amps
    
    
    def test_voltage_drop_calculation(self):
        """Test voltage drop calculation."""
        result = PowerCalculator.calculate_voltage_drop(
            led_count=60,
            wire_length_meters=5.0,
            wire_gauge_awg=22.0,
            led_type=LEDType.WS2812B,
            voltage=5.0,
            brightness_percent=100
        )
        
        assert isinstance(result, VoltageDropResult)
        assert result.led_count == 60
        assert result.wire_length_meters == 5.0
        assert result.voltage_drop >= 0
        assert result.voltage_at_end <= 5.0
        assert result.voltage_drop_percent >= 0
    
    def test_voltage_drop_warnings(self):
        """Test voltage drop warnings for long wires."""
        result = PowerCalculator.calculate_voltage_drop(
            led_count=100,
            wire_length_meters=10.0,
            wire_gauge_awg=28.0,  # Thin wire
            led_type=LEDType.WS2812B,
            voltage=5.0
        )
        
        # Should have warnings for long wire with thin gauge
        if result.voltage_drop_percent > 10.0:
            assert len(result.warnings) > 0
    
    def test_led_density_calculation(self):
        """Test LED density calculation."""
        density, recommendation = PowerCalculator.calculate_led_density(
            display_area_m2=1.0,
            led_count=100
        )
        
        assert density == 100.0
        assert isinstance(recommendation, str)
        assert len(recommendation) > 0

