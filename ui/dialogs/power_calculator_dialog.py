"""
Power Calculator Dialog - UI for calculating power consumption and voltage drop.
"""

from __future__ import annotations

import os
import sys
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QDoubleSpinBox, QComboBox, QGroupBox, QFormLayout,
    QTextEdit, QTabWidget, QWidget, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.power_calculator import PowerCalculator, LEDType, PowerCalculation, VoltageDropResult
from core.pattern import PatternMetadata


class PowerCalculatorDialog(QDialog):
    """Dialog for calculating power consumption and voltage drop."""
    
    def __init__(self, parent=None, pattern_metadata: Optional[PatternMetadata] = None):
        super().__init__(parent)
        self.setWindowTitle("Power Calculator")
        self.setModal(True)
        self.resize(700, 600)
        
        self.pattern_metadata = pattern_metadata
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Tabs for different calculations
        self.tabs = QTabWidget()
        
        # Power Calculation tab
        power_tab = self._create_power_tab()
        self.tabs.addTab(power_tab, "Power Consumption")
        
        # Voltage Drop tab
        voltage_tab = self._create_voltage_drop_tab()
        self.tabs.addTab(voltage_tab, "Voltage Drop")
        
        # LED Density tab
        density_tab = self._create_density_tab()
        self.tabs.addTab(density_tab, "LED Density")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Initialize with pattern data if available
        if pattern_metadata:
            self._load_pattern_data()
    
    def _create_power_tab(self) -> QWidget:
        """Create power consumption calculation tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Input group
        input_group = QGroupBox("Input Parameters")
        input_layout = QFormLayout()
        
        # LED count
        self.led_count_spin = QSpinBox()
        self.led_count_spin.setRange(1, 10000)
        self.led_count_spin.setValue(60)
        input_layout.addRow("LED Count:", self.led_count_spin)
        
        # LED type
        self.led_type_combo = QComboBox()
        for led_type in LEDType:
            self.led_type_combo.addItem(led_type.value, led_type)
        self.led_type_combo.setCurrentText("WS2812B")
        input_layout.addRow("LED Type:", self.led_type_combo)
        
        # Voltage
        self.voltage_spin = QDoubleSpinBox()
        self.voltage_spin.setRange(3.0, 24.0)
        self.voltage_spin.setValue(5.0)
        self.voltage_spin.setDecimals(1)
        self.voltage_spin.setSuffix(" V")
        input_layout.addRow("Voltage:", self.voltage_spin)
        
        # Brightness
        self.brightness_spin = QSpinBox()
        self.brightness_spin.setRange(0, 100)
        self.brightness_spin.setValue(100)
        self.brightness_spin.setSuffix("%")
        input_layout.addRow("Brightness:", self.brightness_spin)
        
        # Custom current (for CUSTOM type)
        self.custom_current_spin = QDoubleSpinBox()
        self.custom_current_spin.setRange(0.001, 1.0)
        self.custom_current_spin.setValue(0.060)
        self.custom_current_spin.setDecimals(3)
        self.custom_current_spin.setSuffix(" A")
        self.custom_current_spin.setEnabled(False)
        input_layout.addRow("Custom Current (per LED):", self.custom_current_spin)
        
        self.led_type_combo.currentTextChanged.connect(self._on_led_type_changed)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Calculate button
        calc_btn = QPushButton("Calculate")
        calc_btn.clicked.connect(self._calculate_power)
        layout.addWidget(calc_btn)
        
        # Results group
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        
        self.power_results_text = QTextEdit()
        self.power_results_text.setReadOnly(True)
        self.power_results_text.setMaximumHeight(200)
        results_layout.addWidget(self.power_results_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_voltage_drop_tab(self) -> QWidget:
        """Create voltage drop calculation tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Input group
        input_group = QGroupBox("Input Parameters")
        input_layout = QFormLayout()
        
        # LED count
        self.vd_led_count_spin = QSpinBox()
        self.vd_led_count_spin.setRange(1, 10000)
        self.vd_led_count_spin.setValue(60)
        input_layout.addRow("LED Count:", self.vd_led_count_spin)
        
        # Wire length
        self.wire_length_spin = QDoubleSpinBox()
        self.wire_length_spin.setRange(0.1, 100.0)
        self.wire_length_spin.setValue(5.0)
        self.wire_length_spin.setDecimals(1)
        self.wire_length_spin.setSuffix(" m")
        input_layout.addRow("Wire Length:", self.wire_length_spin)
        
        # Wire gauge
        self.wire_gauge_spin = QDoubleSpinBox()
        self.wire_gauge_spin.setRange(18, 28)
        self.wire_gauge_spin.setValue(22.0)
        self.wire_gauge_spin.setDecimals(0)
        self.wire_gauge_spin.setSuffix(" AWG")
        input_layout.addRow("Wire Gauge:", self.wire_gauge_spin)
        
        # LED type
        self.vd_led_type_combo = QComboBox()
        for led_type in LEDType:
            self.vd_led_type_combo.addItem(led_type.value, led_type)
        self.vd_led_type_combo.setCurrentText("WS2812B")
        input_layout.addRow("LED Type:", self.vd_led_type_combo)
        
        # Voltage
        self.vd_voltage_spin = QDoubleSpinBox()
        self.vd_voltage_spin.setRange(3.0, 24.0)
        self.vd_voltage_spin.setValue(5.0)
        self.vd_voltage_spin.setDecimals(1)
        self.vd_voltage_spin.setSuffix(" V")
        input_layout.addRow("Voltage:", self.vd_voltage_spin)
        
        # Brightness
        self.vd_brightness_spin = QSpinBox()
        self.vd_brightness_spin.setRange(0, 100)
        self.vd_brightness_spin.setValue(100)
        self.vd_brightness_spin.setSuffix("%")
        input_layout.addRow("Brightness:", self.vd_brightness_spin)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Calculate button
        calc_btn = QPushButton("Calculate")
        calc_btn.clicked.connect(self._calculate_voltage_drop)
        layout.addWidget(calc_btn)
        
        # Results group
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        
        self.voltage_drop_results_text = QTextEdit()
        self.voltage_drop_results_text.setReadOnly(True)
        self.voltage_drop_results_text.setMaximumHeight(200)
        results_layout.addWidget(self.voltage_drop_results_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_density_tab(self) -> QWidget:
        """Create LED density calculation tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Input group
        input_group = QGroupBox("Input Parameters")
        input_layout = QFormLayout()
        
        # Display area
        self.area_spin = QDoubleSpinBox()
        self.area_spin.setRange(0.01, 100.0)
        self.area_spin.setValue(1.0)
        self.area_spin.setDecimals(2)
        self.area_spin.setSuffix(" m²")
        input_layout.addRow("Display Area:", self.area_spin)
        
        # LED count
        self.density_led_count_spin = QSpinBox()
        self.density_led_count_spin.setRange(1, 10000)
        self.density_led_count_spin.setValue(100)
        input_layout.addRow("LED Count:", self.density_led_count_spin)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Calculate button
        calc_btn = QPushButton("Calculate")
        calc_btn.clicked.connect(self._calculate_density)
        layout.addWidget(calc_btn)
        
        # Results group
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        
        self.density_results_text = QTextEdit()
        self.density_results_text.setReadOnly(True)
        self.density_results_text.setMaximumHeight(200)
        results_layout.addWidget(self.density_results_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
        
        return widget
    
    def _on_led_type_changed(self, text: str):
        """Enable/disable custom current field based on LED type."""
        is_custom = (text == "CUSTOM")
        self.custom_current_spin.setEnabled(is_custom)
    
    def _calculate_power(self):
        """Calculate power consumption."""
        try:
            led_count = self.led_count_spin.value()
            led_type = self.led_type_combo.currentData()
            voltage = self.voltage_spin.value()
            brightness = self.brightness_spin.value()
            custom_current = self.custom_current_spin.value() if led_type == LEDType.CUSTOM else None
            
            result = PowerCalculator.calculate_power(
                led_count=led_count,
                led_type=led_type,
                voltage=voltage,
                brightness_percent=brightness,
                custom_current_amps=custom_current
            )
            
            # Format results
            text = f"<b>Power Consumption Analysis</b><br><br>"
            text += f"Total LEDs: {result.total_leds}<br>"
            text += f"Max Power: {result.max_power_watts:.2f} W<br>"
            text += f"Max Current: {result.max_current_amps:.2f} A<br>"
            text += f"Typical Power: {result.typical_power_watts:.2f} W<br>"
            text += f"Typical Current: {result.typical_current_amps:.2f} A<br>"
            text += f"Voltage: {result.voltage:.1f} V<br><br>"
            
            text += f"<b>Recommended PSU:</b><br>"
            text += f"{result.recommended_psu_watts:.1f} W ({result.recommended_psu_amps:.2f} A) @ {result.voltage:.1f}V<br><br>"
            
            if result.warnings:
                text += f"<b style='color: orange;'>Warnings:</b><br>"
                for warning in result.warnings:
                    text += f"• {warning}<br>"
                text += "<br>"
            
            if result.recommendations:
                text += f"<b style='color: green;'>Recommendations:</b><br>"
                for rec in result.recommendations:
                    text += f"• {rec}<br>"
            
            self.power_results_text.setHtml(text)
            
        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", f"Failed to calculate power: {e}")
    
    def _calculate_voltage_drop(self):
        """Calculate voltage drop."""
        try:
            led_count = self.vd_led_count_spin.value()
            wire_length = self.wire_length_spin.value()
            wire_gauge = self.wire_gauge_spin.value()
            led_type = self.vd_led_type_combo.currentData()
            voltage = self.vd_voltage_spin.value()
            brightness = self.vd_brightness_spin.value()
            
            result = PowerCalculator.calculate_voltage_drop(
                led_count=led_count,
                wire_length_meters=wire_length,
                wire_gauge_awg=wire_gauge,
                led_type=led_type,
                voltage=voltage,
                brightness_percent=brightness
            )
            
            # Format results
            text = f"<b>Voltage Drop Analysis</b><br><br>"
            text += f"LED Count: {result.led_count}<br>"
            text += f"Wire Length: {result.wire_length_meters:.1f} m<br>"
            text += f"Wire Gauge: {result.wire_gauge_awg:.0f} AWG<br>"
            text += f"Current: {result.current_amps:.2f} A<br>"
            text += f"Voltage at End: {result.voltage_at_end:.2f} V<br>"
            text += f"Voltage Drop: {result.voltage_drop:.2f} V ({result.voltage_drop_percent:.1f}%)<br><br>"
            
            if result.warnings:
                text += f"<b style='color: orange;'>Warnings:</b><br>"
                for warning in result.warnings:
                    text += f"• {warning}<br>"
                text += "<br>"
            
            if result.recommendations:
                text += f"<b style='color: green;'>Recommendations:</b><br>"
                for rec in result.recommendations:
                    text += f"• {rec}<br>"
            
            self.voltage_drop_results_text.setHtml(text)
            
        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", f"Failed to calculate voltage drop: {e}")
    
    def _calculate_density(self):
        """Calculate LED density."""
        try:
            area = self.area_spin.value()
            led_count = self.density_led_count_spin.value()
            
            density, recommendation = PowerCalculator.calculate_led_density(area, led_count)
            
            # Format results
            text = f"<b>LED Density Analysis</b><br><br>"
            text += f"Display Area: {area:.2f} m²<br>"
            text += f"LED Count: {led_count}<br>"
            text += f"LED Density: {density:.1f} LEDs/m²<br><br>"
            text += f"<b>Recommendation:</b><br>{recommendation}"
            
            self.density_results_text.setHtml(text)
            
        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", f"Failed to calculate density: {e}")
    
    def _load_pattern_data(self):
        """Load data from pattern metadata if available."""
        if not self.pattern_metadata:
            return
        
        # Get LED count
        if hasattr(self.pattern_metadata, 'circular_led_count') and self.pattern_metadata.circular_led_count:
            led_count = self.pattern_metadata.circular_led_count
        else:
            led_count = self.pattern_metadata.width * self.pattern_metadata.height
        
        self.led_count_spin.setValue(led_count)
        self.vd_led_count_spin.setValue(led_count)
        self.density_led_count_spin.setValue(led_count)
        
        # Get LED type from metadata if available
        if hasattr(self.pattern_metadata, 'led_type'):
            led_type_str = self.pattern_metadata.led_type.upper()
            for led_type in LEDType:
                if led_type.value == led_type_str:
                    index = self.led_type_combo.findText(led_type.value)
                    if index >= 0:
                        self.led_type_combo.setCurrentIndex(index)
                        self.vd_led_type_combo.setCurrentIndex(index)
                    break

