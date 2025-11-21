"""
Uploader Adapter Initialization - Auto-register all adapters

This module imports all uploader adapters to trigger their registration.
"""

# Import all adapters to trigger registration
try:
    from uploaders.esp32_uploader import ESP32Uploader
    from uploaders.esp32s_uploader import ESP32SUploader
    from uploaders.esp32c3_uploader import ESP32C3Uploader
    from uploaders.esp32s3_uploader import ESP32S3Uploader
    from uploaders.atmega2560_uploader import ATmega2560Uploader
    from uploaders.attiny85_uploader import ATtiny85Uploader
    from uploaders.stm32f407_uploader import STM32F407Uploader
    from uploaders.pic18f4550_uploader import PIC18F4550Uploader
    from uploaders.nuvoton_m051_uploader import NuvotonM051Uploader
except ImportError as e:
    # Some adapters might not be available in all environments
    pass

