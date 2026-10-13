# Project scope

This independent educational project implements standard SPI NOR read commands on Raspberry Pi Pico RP2040, plus a host-side dump/CRC32 utility.

It does **not** include any proprietary Pico Fusion firmware, Syscon programming, console unlocking, security bypass, write/erase commands, proprietary dumps, or third-party credentials.

## Current limits
- 24-bit addressing, maximum 16 MiB addressable window; actual chip size must be checked independently
- Standard SPI commands only, no quad mode
- Reads supported; no writing or erasing
- No hardware compatibility test result is currently claimed
- Before using a physical part, validate the pinout, voltage, supply budget and read authorization
