#!/usr/bin/env python3
"""
Fix Missing Config - Add missing configuration files to installer
"""

import os
import shutil
import zipfile
from pathlib import Path

def fix_missing_config():
    """Fix the installer by adding missing config files"""
    
    print("🔧 Fixing Missing Configuration Files")
    print("=" * 50)
    
    # Create config directory
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Create chip database YAML file
    print("📝 Creating chip database...")
    
    chip_database_content = '''# Upload Bridge - Chip Database
# Configuration for all supported microcontrollers

chips:
  # ESP Family
  esp8266:
    name: "ESP8266"
    family: "ESP"
    flash_size: "4MB"
    ram_size: "80KB"
    uploader: "esp_uploader"
    requirements: ["python -m esptool", "arduino-cli"]
    bootloader_instructions: "Hold GPIO0 LOW, press RESET, release GPIO0"
    default_gpio: 2
    max_leds: 1000
    
  esp32:
    name: "ESP32"
    family: "ESP"
    flash_size: "4MB"
    ram_size: "520KB"
    uploader: "esp_uploader"
    requirements: ["python -m esptool", "arduino-cli"]
    bootloader_instructions: "Hold BOOT button, press RESET, release BOOT"
    default_gpio: 2
    max_leds: 2000
    
  esp32s2:
    name: "ESP32-S2"
    family: "ESP"
    flash_size: "4MB"
    ram_size: "320KB"
    uploader: "esp_uploader"
    requirements: ["python -m esptool", "arduino-cli"]
    bootloader_instructions: "Hold BOOT button, press RESET, release BOOT"
    default_gpio: 2
    max_leds: 1500
    
  esp32s3:
    name: "ESP32-S3"
    family: "ESP"
    flash_size: "4MB"
    ram_size: "512KB"
    uploader: "esp_uploader"
    requirements: ["python -m esptool", "arduino-cli"]
    bootloader_instructions: "Hold BOOT button, press RESET, release BOOT"
    default_gpio: 2
    max_leds: 2000
    
  esp32c3:
    name: "ESP32-C3"
    family: "ESP"
    flash_size: "4MB"
    ram_size: "400KB"
    uploader: "esp_uploader"
    requirements: ["python -m esptool", "arduino-cli"]
    bootloader_instructions: "Hold BOOT button, press RESET, release BOOT"
    default_gpio: 2
    max_leds: 1500

  # AVR Family
  atmega328p:
    name: "ATmega328P"
    family: "AVR"
    flash_size: "32KB"
    ram_size: "2KB"
    uploader: "avr_uploader"
    requirements: ["avrdude", "avr-gcc"]
    bootloader_instructions: "Connect programmer to ICSP header"
    default_gpio: 2
    max_leds: 100
    
  atmega2560:
    name: "ATmega2560"
    family: "AVR"
    flash_size: "256KB"
    ram_size: "8KB"
    uploader: "avr_uploader"
    requirements: ["avrdude", "avr-gcc"]
    bootloader_instructions: "Connect programmer to ICSP header"
    default_gpio: 2
    max_leds: 200
    
  attiny85:
    name: "ATtiny85"
    family: "AVR"
    flash_size: "8KB"
    ram_size: "512B"
    uploader: "avr_uploader"
    requirements: ["avrdude", "avr-gcc"]
    bootloader_instructions: "Connect programmer to ICSP header"
    default_gpio: 0
    max_leds: 50

  # STM32 Family
  stm32f103c8:
    name: "STM32F103C8"
    family: "STM32"
    flash_size: "64KB"
    ram_size: "20KB"
    uploader: "stm32_uploader"
    requirements: ["stm32flash", "arm-none-eabi-gcc"]
    bootloader_instructions: "Connect ST-Link debugger"
    default_gpio: "PA0"
    max_leds: 300
    
  stm32f401re:
    name: "STM32F401RE"
    family: "STM32"
    flash_size: "512KB"
    ram_size: "96KB"
    uploader: "stm32_uploader"
    requirements: ["stm32flash", "arm-none-eabi-gcc"]
    bootloader_instructions: "Connect ST-Link debugger"
    default_gpio: "PA0"
    max_leds: 500

  # PIC Family
  pic16f876a:
    name: "PIC16F876A"
    family: "PIC"
    flash_size: "8KB"
    ram_size: "368B"
    uploader: "pic_uploader"
    requirements: ["mplab", "xc8"]
    bootloader_instructions: "Connect PIC programmer"
    default_gpio: 0
    max_leds: 50
    
  pic18f4550:
    name: "PIC18F4550"
    family: "PIC"
    flash_size: "32KB"
    ram_size: "2KB"
    uploader: "pic_uploader"
    requirements: ["mplab", "xc8"]
    bootloader_instructions: "Connect PIC programmer"
    default_gpio: 0
    max_leds: 100

  # Nuvoton Family
  nuc123:
    name: "NUC123"
    family: "Nuvoton"
    flash_size: "64KB"
    ram_size: "20KB"
    uploader: "numicro_uploader"
    requirements: ["nu-link"]
    bootloader_instructions: "Connect Nu-Link debugger"
    default_gpio: 0
    max_leds: 200
    
  nuc505:
    name: "NUC505"
    family: "Nuvoton"
    flash_size: "128KB"
    ram_size: "32KB"
    uploader: "numicro_uploader"
    requirements: ["nu-link"]
    bootloader_instructions: "Connect Nu-Link debugger"
    default_gpio: 0
    max_leds: 300

# Uploader configurations
uploaders:
  esp_uploader:
    class: "EspUploader"
    module: "uploaders.esp_uploader"
    
  avr_uploader:
    class: "AvrUploader"
    module: "uploaders.avr_uploader"
    
  stm32_uploader:
    class: "Stm32Uploader"
    module: "uploaders.stm32_uploader"
    
  pic_uploader:
    class: "PicUploader"
    module: "uploaders.pic_uploader"
    
  numicro_uploader:
    class: "NuMicroUploader"
    module: "uploaders.numicro_uploader"

# Default settings
defaults:
  brightness: 1.0
  frame_duration: 100
  color_order: "RGB"
  led_type: "ws2812"
'''
    
    with open(config_dir / "chip_database.yaml", "w", encoding="utf-8") as f:
        f.write(chip_database_content)
    
    print("   ✅ Created chip_database.yaml")
    
    # Create app config
    print("📝 Creating app configuration...")
    
    app_config_content = '''# Upload Bridge - Application Configuration

# UI Settings
ui:
  theme: "dark"
  window_width: 1200
  window_height: 800
  auto_save: true
  preview_fps: 30

# Build Settings
build:
  default_output_dir: "build"
  clean_before_build: true
  verbose_output: false

# Upload Settings
upload:
  verify_after_upload: true
  auto_reset: true
  timeout: 30

# Pattern Settings
pattern:
  default_brightness: 1.0
  default_speed: 1.0
  max_leds: 2000
  max_frames: 10000

# Logging
logging:
  level: "INFO"
  file: "upload_bridge.log"
  max_size: "10MB"
  backup_count: 5
'''
    
    with open(config_dir / "app_config.yaml", "w", encoding="utf-8") as f:
        f.write(app_config_content)
    
    print("   ✅ Created app_config.yaml")
    
    # Now update the working installer
    print("📦 Updating working installer...")
    
    installer_dir = Path("dist/upload_bridge_working")
    
    # Copy config directory to installer
    if installer_dir.exists():
        config_dest = installer_dir / "config"
        shutil.copytree(config_dir, config_dest, dirs_exist_ok=True)
        print("   ✅ Added config/ to installer")
    
    # Create updated ZIP
    print("📦 Creating updated ZIP package...")
    zip_path = "dist/upload_bridge_working_fixed.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(installer_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(installer_dir)
                zipf.write(file_path, arc_path)
    
    print(f"   ✅ Created: {zip_path}")
    
    # Create final summary
    print("\\n🎉 Fixed Installer Package Created Successfully!")
    print("=" * 50)
    print(f"📁 Package location: {installer_dir}")
    print(f"📦 ZIP file: {zip_path}")
    print()
    print("📋 Fixed issues:")
    print("   ✅ Added missing config/ directory")
    print("   ✅ Created chip_database.yaml")
    print("   ✅ Created app_config.yaml")
    print("   ✅ All configuration files included")
    print()
    print("🚀 Use the FIXED ZIP file for distribution!")
    print("   File: upload_bridge_working_fixed.zip")

if __name__ == "__main__":
    fix_missing_config()












