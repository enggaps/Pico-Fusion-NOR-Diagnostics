import sys
import unittest
import zlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'host'))
from nor_diag import dump, identify

class Port:
    def __init__(self, lines):
        self.lines = iter(x.encode() + b'\n' for x in lines)
        self.commands = []
    def write(self, value):
        self.commands.append(value)
    def readline(self):
        return next(self.lines, b'')

class ProtocolTests(unittest.TestCase):
    def test_id(self):
        port = Port(['ID EF4018'])
        self.assertEqual(identify(port), 'EF4018')
        self.assertEqual(port.commands, [b'ID\n'])
    def test_dump_crc(self):
        data = bytes(range(16))
        port = Port([f'DATA 32 {data.hex().upper()}', f'DONE {zlib.crc32(data):08X} 16'])
        self.assertEqual(dump(port, 32, 16), data)
        self.assertEqual(port.commands, [b'READ 32 16\n'])
    def test_bad_checksum(self):
        with self.assertRaises(ValueError):
            dump(Port(['DATA 0 AABB', 'DONE 00000000 2']), 0, 2)
    def test_reject_16mb_crossing(self):
        with self.assertRaises(ValueError):
            dump(Port([]), 0xFFFFFF, 2)
    def test_timeout(self):
        with self.assertRaises(TimeoutError):
            identify(Port([]))

if __name__ == '__main__':
    unittest.main()
