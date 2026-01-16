"""
Power Calculator - Calculate power consumption and voltage drop for LED displays.

This module provides tools for planning power supplies and analyzing voltage drop
for Budurasmala and other LED matrix displays.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum


class LEDType(Enum):
    """LED chip types with power characteristics."""
    WS2812B = "WS2812B"  # 60mA max per LED (20mA per channel)
    WS2811 = "WS2811"    # 60mA max per LED
    SK6812 = "SK6812"    # 60mA max per LED
    APA102 = "APA102"    # 60mA max per LED
    CUSTOM = "CUSTOM"    # User-defined


@dataclass
class PowerCalculation:
    """Result of power calculation."""
    total_leds: int
    max_power_watts: float
    max_current_amps: float
    typical_power_watts: float
    typical_current_amps: float
    voltage: float
    recommended_psu_watts: float
    recommended_psu_amps: float
    warnings: List[str]
    recommendations: List[str]


@dataclass
class VoltageDropResult:
    """Result of voltage drop calculation."""
    led_count: int
    wire_length_meters: float
    wire_gauge_awg: float
    voltage_at_end: float
    voltage_drop: float
    voltage_drop_percent: float
    current_amps: float
    warnings: List[str]
    recommendations: List[str]


class PowerCalculator:
    """Calculate power consumption and voltage drop for LED displays."""
    
    # LED power characteristics (max current per LED in amps)
    LED_CURRENT_MAX = {
        LEDType.WS2812B: 0.060,  # 60mA max
        LEDType.WS2811: 0.060,
        LEDType.SK6812: 0.060,
        LEDType.APA102: 0.060,
    }
    
    # Typical current (at 50% brightness, white)
    LED_CURRENT_TYPICAL = {
        LEDType.WS2812B: 0.030,  # 30mA typical
        LEDType.WS2811: 0.030,
        LEDType.SK6812: 0.030,
        LEDType.APA102: 0.030,
    }
    
    # Standard voltage
    STANDARD_VOLTAGE = 5.0  # 5V for most addressable LEDs
    
    # Wire resistance per meter (ohms/meter) by AWG gauge
    WIRE_RESISTANCE = {
        18: 0.021,  # AWG 18
        20: 0.033,  # AWG 20
        22: 0.052,  # AWG 22
        24: 0.084,  # AWG 24
        26: 0.134,  # AWG 26
        28: 0.213,  # AWG 28
    }
    
    @staticmethod
    def calculate_power(
        led_count: int,
        led_type: LEDType = LEDType.WS2812B,
        voltage: float = 5.0,
        brightness_percent: float = 100.0,
        custom_current_amps: Optional[float] = None
    ) -> PowerCalculation:
        """
        Calculate power consumption for LED display.
        
        Args:
            led_count: Number of LEDs
            led_type: LED chip type
            voltage: Supply voltage (typically 5V)
            brightness_percent: Brightness percentage (0-100)
            custom_current_amps: Custom current per LED (for CUSTOM type)
            
        Returns:
            PowerCalculation with results and recommendations
        """
        warnings = []
        recommendations = []
        
        # Get current per LED
        if led_type == LEDType.CUSTOM:
            if custom_current_amps is None:
                raise ValueError("custom_current_amps required for CUSTOM LED type")
            max_current_per_led = custom_current_amps
            typical_current_per_led = custom_current_amps * 0.5
        else:
            max_current_per_led = PowerCalculator.LED_CURRENT_MAX.get(led_type, 0.060)
            typical_current_per_led = PowerCalculator.LED_CURRENT_TYPICAL.get(led_type, 0.030)
        
        # Adjust for brightness
        brightness_factor = brightness_percent / 100.0
        max_current_per_led *= brightness_factor
        typical_current_per_led *= brightness_factor
        
        # Calculate total current
        max_current_total = led_count * max_current_per_led
        typical_current_total = led_count * typical_current_per_led
        
        # Calculate power (P = V * I)
        max_power = voltage * max_current_total
        typical_power = voltage * typical_current_total
        
        # Recommend PSU with 20% headroom
        recommended_psu_watts = max_power * 1.2
        recommended_psu_amps = max_current_total * 1.2
        
        # Generate warnings
        if led_count > 100:
            warnings.append(f"Large display ({led_count} LEDs) - consider power injection")
        
        if max_current_total > 10.0:
            warnings.append(f"High current ({max_current_total:.2f}A) - use thick wires (18AWG or larger)")
        
        if max_power > 50.0:
            warnings.append(f"High power consumption ({max_power:.1f}W) - ensure adequate cooling")
        
        # Generate recommendations
        if led_count > 50:
            recommendations.append("Consider power injection at multiple points")
        
        if max_current_total > 5.0:
            recommendations.append("Use 18AWG or larger wire for power distribution")
        
        if max_power > 30.0:
            recommendations.append("Use a switching power supply (not linear)")
        
        recommendations.append(f"Recommended PSU: {recommended_psu_watts:.1f}W ({recommended_psu_amps:.2f}A) @ {voltage}V")
        
        return PowerCalculation(
            total_leds=led_count,
            max_power_watts=max_power,
            max_current_amps=max_current_total,
            typical_power_watts=typical_power,
            typical_current_amps=typical_current_total,
            voltage=voltage,
            recommended_psu_watts=recommended_psu_watts,
            recommended_psu_amps=recommended_psu_amps,
            warnings=warnings,
            recommendations=recommendations
        )
    
    @staticmethod
    def calculate_voltage_drop(
        led_count: int,
        wire_length_meters: float,
        wire_gauge_awg: float = 22.0,
        led_type: LEDType = LEDType.WS2812B,
        voltage: float = 5.0,
        brightness_percent: float = 100.0,
        custom_current_amps: Optional[float] = None
    ) -> VoltageDropResult:
        """
        Calculate voltage drop along LED strip.
        
        Args:
            led_count: Number of LEDs
            wire_length_meters: Length of wire from power supply to end of strip
            wire_gauge_awg: Wire gauge (AWG)
            led_type: LED chip type
            voltage: Supply voltage
            brightness_percent: Brightness percentage
            custom_current_amps: Custom current per LED
            
        Returns:
            VoltageDropResult with voltage drop analysis
        """
        warnings = []
        recommendations = []
        
        # Get current per LED
        if led_type == LEDType.CUSTOM:
            if custom_current_amps is None:
                raise ValueError("custom_current_amps required for CUSTOM LED type")
            current_per_led = custom_current_amps
        else:
            current_per_led = PowerCalculator.LED_CURRENT_MAX.get(led_type, 0.060)
        
        # Adjust for brightness
        brightness_factor = brightness_percent / 100.0
        current_per_led *= brightness_factor
        
        # Total current
        total_current = led_count * current_per_led
        
        # Get wire resistance
        # Find closest AWG gauge
        available_gauges = sorted(PowerCalculator.WIRE_RESISTANCE.keys())
        closest_gauge = min(available_gauges, key=lambda x: abs(x - wire_gauge_awg))
        resistance_per_meter = PowerCalculator.WIRE_RESISTANCE[closest_gauge]
        
        # Calculate voltage drop (V = I * R)
        # For round trip (power and ground), multiply by 2
        total_resistance = resistance_per_meter * wire_length_meters * 2
        voltage_drop = total_current * total_resistance
        voltage_at_end = voltage - voltage_drop
        voltage_drop_percent = (voltage_drop / voltage) * 100.0
        
        # Generate warnings
        if voltage_drop_percent > 10.0:
            warnings.append(f"High voltage drop ({voltage_drop_percent:.1f}%) - LEDs may dim or flicker")
        
        if voltage_at_end < 4.0:
            warnings.append(f"Voltage at end ({voltage_at_end:.2f}V) is too low - LEDs may not work properly")
        
        if wire_length_meters > 5.0:
            warnings.append(f"Long wire run ({wire_length_meters:.1f}m) - consider power injection")
        
        # Generate recommendations
        if voltage_drop_percent > 5.0:
            recommendations.append("Use thicker wire (lower AWG number)")
            recommendations.append("Add power injection at multiple points")
        
        if voltage_drop_percent > 10.0:
            recommendations.append("Consider using 12V LEDs with step-down converters")
        
        if wire_gauge_awg > 20:
            recommendations.append(f"Upgrade to {closest_gauge}AWG or thicker wire")
        
        return VoltageDropResult(
            led_count=led_count,
            wire_length_meters=wire_length_meters,
            wire_gauge_awg=wire_gauge_awg,
            voltage_at_end=voltage_at_end,
            voltage_drop=voltage_drop,
            voltage_drop_percent=voltage_drop_percent,
            current_amps=total_current,
            warnings=warnings,
            recommendations=recommendations
        )
    
    @staticmethod
    def calculate_led_density(
        display_area_m2: float,
        led_count: int
    ) -> Tuple[float, str]:
        """
        Calculate LED density and provide recommendations.
        
        Args:
            display_area_m2: Display area in square meters
            led_count: Number of LEDs
            
        Returns:
            Tuple of (LEDs per m², recommendation string)
        """
        if display_area_m2 <= 0:
            return 0.0, "Invalid area"
        
        density = led_count / display_area_m2
        
        if density < 100:
            recommendation = "Low density - good for large displays, may appear sparse"
        elif density < 500:
            recommendation = "Medium density - good balance for most displays"
        elif density < 1000:
            recommendation = "High density - good for detailed patterns, requires more power"
        else:
            recommendation = "Very high density - excellent detail, high power consumption"
        
        return density, recommendation

