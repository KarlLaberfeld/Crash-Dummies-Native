"""Static title asset decoding from synthetic layout/tile identifiers."""
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from extract_title_layout import title_layout,pack


class TitleLayoutAssets(unittest.TestCase):
    def fixture(self,width=2,height=2,x=3,y=4):
        rom=bytearray(0x20000);rom[:14]=bytes([0x82,1,0x81,x,y,0x83,width,height,7,0,0x40,0x80,0,0]);rom[0x1c000:0x1c004]=bytes([0,127,128,255]);return rom
    def test_identifiers_are_not_interpreted_as_glyphs(self):
        decoded=title_layout(self.fixture(),0);self.assertEqual(decoded,[(0,1,0,0,0,b''),(1,3,4,0,0,b''),(2,0,0,2,2,bytes([0,127,128,255])),(3,0,0,0,0,b'')])
        blob=pack(decoded);self.assertEqual(blob[:10],b'CDNTL001'+struct.pack('<H',4));self.assertIn(bytes([0,127,128,255]),blob)
    def test_empty_rectangle(self):
        with self.assertRaises(ValueError):title_layout(self.fixture(width=0),0)
    def test_rectangle_cannot_escape_map(self):
        with self.assertRaises(ValueError):title_layout(self.fixture(x=31),0)
    def test_unknown_operation(self):
        with self.assertRaises(ValueError):title_layout(bytes([0x88]),0)
    def test_truncated_anchor(self):
        with self.assertRaises(ValueError):title_layout(bytes([0x81,0]),0)
    def test_truncated_rectangle(self):
        with self.assertRaises(ValueError):title_layout(bytes([0x83,1,1]),0)
    def test_bank_cannot_escape_rom(self):
        rom=self.fixture();rom[8]=8
        with self.assertRaises(ValueError):title_layout(rom,0)
    def test_rectangle_cannot_cross_source_bank(self):
        rom=self.fixture();rom[9:11]=bytes([255,127])
        with self.assertRaises(ValueError):title_layout(rom,0)
    def test_layer_selector(self):
        with self.assertRaises(ValueError):title_layout(bytes([0x82,2,0x80]),0)
    def test_missing_end(self):
        with self.assertRaises(ValueError):title_layout(bytes([0x82,0]),0)


if __name__=='__main__':unittest.main()
