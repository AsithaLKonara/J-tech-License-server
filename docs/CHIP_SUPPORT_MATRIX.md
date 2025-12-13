# Chip Support Matrix

**Last Updated**: 2025-01-XX  
**Version**: 3.0.0

This document details the support level for each microcontroller chip in Upload Bridge.

---

## Support Levels

- **✅ Fully Supported**: Has dedicated uploader adapter class and profile JSON
- **⚠️ Partially Supported**: Uses generic uploader (may work but not fully tested)
- **❌ Not Supported**: Listed in database but not implemented/tested

---

## Fully Supported Chips (9)

These chips have dedicated uploader implementations and profile JSONs:

| Chip ID | Name | Family | Uploader | Profile JSON | Status |
|---------|------|--------|----------|--------------|--------|
| esp32 | ESP32 | ESP | ESP32Uploader | ✅ esp32.json | ✅ Fully Supported |
| esp32c3 | ESP32-C3 | ESP | ESP32C3Uploader | ✅ esp32c3.json | ✅ Fully Supported |
| esp32s | ESP32-S | ESP | ESP32SUploader | ✅ esp32s.json | ✅ Fully Supported |
| esp32s3 | ESP32-S3 | ESP | ESP32S3Uploader | ✅ esp32s3.json | ✅ Fully Supported |
| atmega2560 | ATmega2560 | AVR | ATmega2560Uploader | ✅ atmega2560.json | ✅ Fully Supported |
| attiny85 | ATtiny85 | AVR | ATtiny85Uploader | ✅ attiny85.json | ✅ Fully Supported |
| stm32f407 | STM32F407 | STM32 | STM32F407Uploader | ✅ stm32f407.json | ✅ Fully Supported |
| pic18f4550 | PIC18F4550 | PIC | PIC18F4550Uploader | ✅ pic18f4550.json | ✅ Fully Supported |
| nuvoton_m051 | Nuvoton M051 | Nuvoton | NuvotonM051Uploader | ✅ nuvoton_m051.json | ✅ Fully Supported |

---

## Partially Supported Chips (19)

These chips are in the database and may work with generic uploaders, but don't have dedicated implementations:

### ESP Family (1)
- **esp8266**: Uses EspUploader (generic ESP uploader)

### AVR Family (2)
- **atmega328p**: Uses AvrUploader (generic AVR uploader)
- Other AVR chips may work via AvrUploader

### STM32 Family (2)
- **stm32f103c8**: Uses Stm32Uploader (generic STM32 uploader)
- **stm32f401re**: Uses Stm32Uploader
- **stm32f030f4p6**: Uses Stm32Uploader

### PIC Family (14)
All use PicUploader (generic PIC uploader):
- pic16f876a
- pic12f508, pic12f629, pic12f675, pic12f683
- pic16f877a, pic16f628a, pic16f84a, pic16f676, pic16f690, pic16f54a
- pic18f2520, pic18f2550, pic18f4520

### Nuvoton Family (2)
- **nuc123**: Uses NuMicroUploader (generic Nuvoton uploader)
- **nuc505**: Uses NuMicroUploader
- **n76e003at20**: Uses NuMicroUploader

---

## Notes

1. **Generic Uploaders**: Chips using generic uploaders may work but haven't been fully tested. Use at your own risk.

2. **Profile JSONs**: Only fully supported chips have profile JSONs. Generic uploaders use database defaults.

3. **Adding Support**: To add full support for a chip:
   - Create dedicated uploader adapter class
   - Create profile JSON in `uploaders/profiles/`
   - Test upload functionality
   - Update this matrix

4. **Database vs Implementation**: The chip database (`config/chip_database.yaml`) contains 28 chips, but only 9 are fully supported. The others rely on generic uploaders.

---

## Recommendations

- **For Production**: Use only fully supported chips
- **For Development**: Partially supported chips may work but require testing
- **For New Projects**: Check this matrix before selecting a chip

---

**Total Chips in Database**: 28  
**Fully Supported**: 9  
**Partially Supported**: 19  
**Not Supported**: 0

