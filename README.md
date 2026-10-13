# Pico Fusion NOR Diagnostics — RP2040 (Read-only)

An independent, open-source SPI NOR diagnostic example for Raspberry Pi Pico (RP2040). **This is not the proprietary Pico Fusion firmware.** It includes no Syscon code, proprietary protocols, bypass logic, flash writes or erase operations.

## Features
- JEDEC ID via SPI command `0x9F`
- Standard SPI NOR reads via `0x03` with 24-bit addressing (up to 16 MiB address range)
- USB CDC serial protocol and Python PC client
- CRC32 validation and automated host protocol tests

**Status:** Host protocol tests are provided. RP2040 UF2 compilation and real-chip reading have not been independently validated. Supports only compatible SPI NOR chips and read ranges; it does not identify chip capacity automatically.

## Wiring — isolated standalone SPI NOR only

| Pico RP2040 | SPI NOR |
| --- | --- |
| GP16 (SPI0 RX) | DO / MISO |
| GP17 (GPIO) | /CS |
| GP18 (SPI0 SCK) | CLK |
| GP19 (SPI0 TX) | DI / MOSI |
| GND | GND |
| 3V3 OUT | VCC **only if 3.3 V compatibility and current draw are confirmed** |

Check the specific chip datasheet, including /WP and /HOLD pullups and supply decoupling. **Do not attach to an energized motherboard.** RP2040 GPIO is not 5 V tolerant. For 1.8 V devices use appropriate level shifting and power.

## Compile firmware

Install the [Raspberry Pi Pico SDK](https://github.com/raspberrypi/pico-sdk), ARM toolchain and CMake. In PowerShell:

```powershell
$env:PICO_SDK_PATH = 'C:\path\to\pico-sdk'
Copy-Item "$env:PICO_SDK_PATH\external\pico_sdk_import.cmake" firmware\pico_sdk_import.cmake
cmake -S firmware -B build -DPICO_BOARD=pico
cmake --build build
```

Hold BOOTSEL while plugging in the Pico and copy `build/nor_diag.uf2` to its boot drive.

## PC client

```powershell
python -m pip install -r requirements.txt
python host/nor_diag.py --port COM6 id
python host/nor_diag.py --port COM6 dump --offset 0 --length 0x10000 --out nor_64k.bin
python -m unittest discover -s tests -v
```

Replace COM6 with your detected serial port. Confirm JEDEC ID against the datasheet, then compare two reads before relying on a dump.

## USB serial protocol
- `ID` => `ID EF4018` (example only)
- `READ 0 4` => `DATA 0 00112233` and `DONE <CRC32_hex> 4`
- `HELP` => available commands

Wire addresses and lengths are decimal. CRC32 is compatible with Python's `zlib.crc32`. The firmware sends up to 128 bytes per data line.

## Security and research scope
Read only hardware you own or are authorized to inspect. Do not publish copyrighted flash contents, private data, keys or customer firmware. Repository ownership alone does not establish the adoption or security-maintainer evidence needed for Anthropic CVP.

MIT licensed. Contributions and hardware test reports are welcome.
