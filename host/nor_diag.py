#!/usr/bin/env python3
"""Read-only USB serial client for RP2040 SPI NOR diagnostics firmware."""
import argparse
import binascii
import pathlib
import re
import zlib

ID = re.compile(r"ID ([0-9A-F]{6})$")
DATA = re.compile(r"DATA ([0-9]+) ([0-9A-F]+)$")
DONE = re.compile(r"DONE ([0-9A-F]{8}) ([0-9]+)$")

def read_line(port):
    raw = port.readline()
    if not raw:
        raise TimeoutError("Serial timeout: check Pico USB connection and chip wiring")
    return raw.decode("ascii", errors="replace").strip()

def identify(port):
    port.write(b"ID\n")
    while True:
        line = read_line(port)
        if line.startswith("ERR "):
            raise RuntimeError(line)
        match = ID.fullmatch(line)
        if match:
            return match.group(1)

def dump(port, offset, length):
    if offset < 0 or length <= 0 or offset + length > 0x1000000:
        raise ValueError("Read must be within 24-bit address space (16 MiB maximum)")
    port.write(f"READ {offset} {length}\n".encode("ascii"))
    output = bytearray()
    while True:
        line = read_line(port)
        if line.startswith("ERR "):
            raise RuntimeError(line)
        match = DATA.fullmatch(line)
        if match:
            address = int(match.group(1))
            block = binascii.unhexlify(match.group(2))
            if address != offset + len(output) or not block or len(block) > 128:
                raise ValueError("Unexpected block offset/size")
            if len(output) + len(block) > length:
                raise ValueError("More bytes received than requested")
            output.extend(block)
            continue
        match = DONE.fullmatch(line)
        if match:
            expected_crc = int(match.group(1), 16)
            reported_length = int(match.group(2))
            actual_crc = zlib.crc32(output)
            if len(output) != length or reported_length != length or actual_crc != expected_crc:
                raise ValueError("Dump CRC32 or size mismatch; do not trust the result")
            return bytes(output)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="e.g. COM6 or /dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200, help="CDC virtual baud; ignored by USB")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("id", help="Read JEDEC manufacturer/device ID")
    command = sub.add_parser("dump", help="Dump selected range using standard 0x03 read")
    command.add_argument("--offset", type=lambda s: int(s, 0), default=0)
    command.add_argument("--length", type=lambda s: int(s, 0), required=True)
    command.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    import serial
    with serial.Serial(args.port, baudrate=args.baud, timeout=10, write_timeout=10) as port:
        if args.command == "id":
            print("JEDEC ID:", identify(port))
        else:
            data = dump(port, args.offset, args.length)
            args.out.write_bytes(data)
            print(f"Saved {len(data)} bytes to {args.out}; CRC32 {zlib.crc32(data):08X}")

if __name__ == "__main__":
    main()
