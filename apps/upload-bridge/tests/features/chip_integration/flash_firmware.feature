Feature: Chip Firmware Flashing
  As a developer
  I want to flash firmware to chips
  So that I can upload LED patterns to hardware

  Background:
    Given I have a connected chip
    And I have built firmware for the chip
    And I have the firmware binary file

  Scenario: Flash firmware to ESP32
    Given I have selected ESP32 chip
    And device is detected on port "/dev/ttyUSB0"
    When I flash firmware "firmware.bin" to the device
    Then firmware should be flashed successfully
    And verification should pass

  Scenario: Flash firmware to ATmega2560
    Given I have selected ATmega2560 chip
    And device is detected on port "/dev/ttyACM0"
    When I flash firmware "firmware.hex" to the device
    Then firmware should be flashed successfully
    And verification should pass

  Scenario: Flash firmware to STM32F407
    Given I have selected STM32F407 chip
    And device is detected on port "/dev/ttyACM0"
    When I flash firmware "firmware.bin" to the device
    Then firmware should be flashed successfully
    And verification should pass

  Scenario: Verify firmware hash
    Given firmware has been flashed
    When I verify firmware with expected hash "abc123..."
    Then verification should succeed
    And hash should match expected value

