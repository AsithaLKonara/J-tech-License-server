/* Placeholder linker script for STM32F030F4P6. Update with accurate memory map before production use. */
MEMORY
{
  FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 16K
  RAM (xrw) : ORIGIN = 0x20000000, LENGTH = 4K
}
SECTIONS
{
  .text : { *(.text*) *(.rodata*) } > FLASH
  .data : { *(.data*) } > RAM AT > FLASH
  .bss  : { *(.bss*) *(COMMON) } > RAM
}
