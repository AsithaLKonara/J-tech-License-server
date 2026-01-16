"""GPIO Pin Selector Widget for ESP32 Configuration"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QSpinBox,
    QPushButton, QMessageBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, List


class GPIOSelectorWidget(QWidget):
    """Widget for selecting and validating GPIO pins"""
    
    # Signals
    config_changed = Signal(dict)  # Emitted when config changes
    validation_error = Signal(str)  # Emitted on validation error
    
    # Reserved pins for ESP32
    RESERVED_PINS = {6, 7, 8, 9, 10, 11, 20, 24, 28, 29, 30, 31}
    VALID_PIN_RANGE = (0, 39)
    
    # Default pins
    DEFAULT_CONFIG = {
        'sd_clk_pin': 18,
        'sd_mosi_pin': 23,
        'sd_miso_pin': 19,
        'sd_cs_pin': 5,
        'led_data_pin': 2,
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = self.DEFAULT_CONFIG.copy()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # SD Card GPIO Group
        sd_group = self._create_sd_group()
        layout.addWidget(sd_group)
        
        # LED GPIO Group
        led_group = self._create_led_group()
        layout.addWidget(led_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_validate = QPushButton("✓ Validate")
        btn_validate.clicked.connect(self._on_validate)
        btn_layout.addWidget(btn_validate)
        
        btn_reset = QPushButton("↻ Reset to Defaults")
        btn_reset.clicked.connect(self._on_reset)
        btn_layout.addWidget(btn_reset)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def _create_sd_group(self):
        """Create SD card GPIO configuration group"""
        group = QGroupBox("SD Card GPIO Configuration (SPI Mode)")
        layout = QFormLayout()
        
        # SD CLK Pin
        self.spin_sd_clk = QSpinBox()
        self.spin_sd_clk.setRange(*self.VALID_PIN_RANGE)
        self.spin_sd_clk.setValue(self.DEFAULT_CONFIG['sd_clk_pin'])
        self.spin_sd_clk.valueChanged.connect(self._on_pin_changed)
        layout.addRow("CLK (Clock) Pin:", self.spin_sd_clk)
        
        # SD MOSI Pin
        self.spin_sd_mosi = QSpinBox()
        self.spin_sd_mosi.setRange(*self.VALID_PIN_RANGE)
        self.spin_sd_mosi.setValue(self.DEFAULT_CONFIG['sd_mosi_pin'])
        self.spin_sd_mosi.valueChanged.connect(self._on_pin_changed)
        layout.addRow("MOSI (Data Out) Pin:", self.spin_sd_mosi)
        
        # SD MISO Pin
        self.spin_sd_miso = QSpinBox()
        self.spin_sd_miso.setRange(*self.VALID_PIN_RANGE)
        self.spin_sd_miso.setValue(self.DEFAULT_CONFIG['sd_miso_pin'])
        self.spin_sd_miso.valueChanged.connect(self._on_pin_changed)
        layout.addRow("MISO (Data In) Pin:", self.spin_sd_miso)
        
        # SD CS Pin
        self.spin_sd_cs = QSpinBox()
        self.spin_sd_cs.setRange(*self.VALID_PIN_RANGE)
        self.spin_sd_cs.setValue(self.DEFAULT_CONFIG['sd_cs_pin'])
        self.spin_sd_cs.valueChanged.connect(self._on_pin_changed)
        layout.addRow("CS (Chip Select) Pin:", self.spin_sd_cs)
        
        # Info label
        info = QLabel("ℹ Configure SD card SPI pins. Default: GPIO18(CLK), GPIO23(MOSI), GPIO19(MISO), GPIO5(CS)")
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; font-size: 10px;")
        layout.addRow("", info)
        
        group.setLayout(layout)
        return group
    
    def _create_led_group(self):
        """Create LED GPIO configuration group"""
        group = QGroupBox("LED Control GPIO Configuration")
        layout = QFormLayout()
        
        # LED Data Pin
        self.spin_led_pin = QSpinBox()
        self.spin_led_pin.setRange(*self.VALID_PIN_RANGE)
        self.spin_led_pin.setValue(self.DEFAULT_CONFIG['led_data_pin'])
        self.spin_led_pin.valueChanged.connect(self._on_pin_changed)
        layout.addRow("Data (DIN) Pin:", self.spin_led_pin)
        
        # Info label
        info = QLabel("ℹ GPIO pin for WS2812B/SK6812 LED data signal. Default: GPIO2")
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; font-size: 10px;")
        layout.addRow("", info)
        
        group.setLayout(layout)
        return group
    
    def _on_pin_changed(self):
        """Handle pin value changes"""
        self.config = {
            'sd_clk_pin': self.spin_sd_clk.value(),
            'sd_mosi_pin': self.spin_sd_mosi.value(),
            'sd_miso_pin': self.spin_sd_miso.value(),
            'sd_cs_pin': self.spin_sd_cs.value(),
            'led_data_pin': self.spin_led_pin.value(),
        }
        self.config_changed.emit(self.config)
    
    def _on_validate(self):
        """Validate GPIO configuration"""
        errors = self.validate_config(self.config)
        if errors:
            error_msg = "Configuration Errors:\n\n" + "\n".join(f"• {e}" for e in errors)
            self.validation_error.emit(error_msg)
            QMessageBox.warning(self, "GPIO Validation Failed", error_msg)
        else:
            QMessageBox.information(self, "GPIO Validation", "✓ All GPIO pins are valid!")
    
    def _on_reset(self):
        """Reset to default configuration"""
        self.set_config(self.DEFAULT_CONFIG)
        QMessageBox.information(self, "Reset", "GPIO configuration reset to defaults")
    
    def validate_config(self, config: Dict) -> List[str]:
        """Validate GPIO configuration"""
        errors = []
        
        pins = {
            'SD CLK': config.get('sd_clk_pin'),
            'SD MOSI': config.get('sd_mosi_pin'),
            'SD MISO': config.get('sd_miso_pin'),
            'SD CS': config.get('sd_cs_pin'),
            'LED Data': config.get('led_data_pin'),
        }
        
        # Check for uniqueness
        pin_values = list(pins.values())
        if len(pin_values) != len(set(pin_values)):
            errors.append("GPIO pins must be unique (no duplicates)")
        
        # Check each pin
        for name, pin in pins.items():
            if pin in self.RESERVED_PINS:
                errors.append(f"{name} (GPIO{pin}) is reserved")
            elif pin < self.VALID_PIN_RANGE[0] or pin > self.VALID_PIN_RANGE[1]:
                errors.append(f"{name} (GPIO{pin}) is out of valid range (0-39)")
        
        return errors
    
    def get_config(self) -> Dict:
        """Get current GPIO configuration"""
        return self.config.copy()
    
    def set_config(self, config: Dict):
        """Set GPIO configuration"""
        self.spin_sd_clk.setValue(config.get('sd_clk_pin', 18))
        self.spin_sd_mosi.setValue(config.get('sd_mosi_pin', 23))
        self.spin_sd_miso.setValue(config.get('sd_miso_pin', 19))
        self.spin_sd_cs.setValue(config.get('sd_cs_pin', 5))
        self.spin_led_pin.setValue(config.get('led_data_pin', 2))
