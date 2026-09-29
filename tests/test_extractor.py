from pathlib import Path
import struct
import sys
import unittest
from contextlib import contextmanager
from uuid import uuid4

PROJECT=Path(__file__).resolve().parents[1]
TEMP_ROOT=PROJECT/'build'/'test-temp'
TEMP_ROOT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(PROJECT/'tools'))
import extract
from disassemble import decode

@contextmanager
def scratch_directory():
    # tempfile's mode 0700 ACL can deny the restricted Windows build account.
    # Use inherited workspace permissions and only delete these test-owned files.
    path=(TEMP_ROOT/str(uuid4())).resolve()
    assert path.parent==TEMP_ROOT.resolve()
    path.mkdir()
    try:yield path
    finally:
        for name in ('input.gb','crash.dat','manifest.json'):
            (path/name).unlink(missing_ok=True)
        path.rmdir()

class BinaryFormats(unittest.TestCase):
    def test_planar_tile_bit_order(self):
        data=bytes([0b10100000,0b01100000]+[0]*14)
        self.assertEqual(extract.tile(data,0)[:8],bytes([1,2,3,0,0,0,0,0]))

    def test_tile_bounds(self):
        with self.assertRaises(ValueError):extract.tile(bytes(15),0)
        with self.assertRaises(ValueError):extract.tile(bytes(16),-1)

    def test_rejects_modified_or_wrong_rom(self):
        with scratch_directory() as directory:
            path=Path(directory)/'input.gb'
            for data in (b'',bytes(131072)):
                path.write_bytes(data)
                with self.assertRaises(ValueError):extract.read_rom(path)

    def test_bank_boundaries(self):
        self.assertEqual(extract.address(4,0x4610),0x10610)
        with self.assertRaises(ValueError):extract.address(8,0x4000)

    def test_relative_branch_and_prefix_disassembly(self):
        self.assertEqual(decode(bytes([0x20,0xfe]),0,0x4000),(2,'jr nz,$4000'))
        self.assertEqual(decode(bytes([0xcb,0x7e]),0,0x4000),(2,'bit 7,[hl]'))
        self.assertEqual(decode(bytes([0x21,0x34,0x12]),0,0),(3,'ld hl,$1234'))

    def test_all_opcode_lengths_are_legal(self):
        for opcode in range(256):
            length,_=decode(bytes([opcode,0,0]),0,0)
            self.assertIn(length,(1,2,3))

    def test_animation_jump_is_relocated(self):
        data=bytearray(0x8000)
        for entry in extract.ANIMATIONS:data[entry]=0x80
        start=extract.ANIMATIONS[0]
        data[start:start+3]=bytes([0x8a,0x00,0x70])
        data[0x7000:0x7003]=bytes([0x85,3,0x81])
        data[0x7003]=0x80
        starts,commands=extract.animation_records(data)
        jump=commands[starts[0]-1]
        self.assertEqual(jump[0],10)
        self.assertEqual(commands[jump[1]-1][:2],(5,3))

class LocalCartridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        files=list(Path(__file__).resolve().parents[1].glob('*.gb'))
        if not files:raise unittest.SkipTest('Local ROM not present; no copyrighted fixture in repository')
        cls.rom=extract.read_rom(files[0])

    def test_exact_extraction_structure(self):
        with scratch_directory() as directory:
            manifest=extract.extract(self.rom,directory)
            self.assertEqual([l['objects'] for l in manifest['roof_difficulties']],[36,39,49,46])
            self.assertEqual([l['height'] for l in manifest['roof_difficulties']],[1888,1696,1952,1952])
            pack=(Path(directory)/'crash.dat').read_bytes()
            self.assertEqual(pack[:8],b'TICDNAT3')
            self.assertNotIn(self.rom,pack)
            first=pack
            extract.extract(self.rom,directory)
            self.assertEqual(first,(Path(directory)/'crash.dat').read_bytes())

    def test_sprite_palette_and_transparency(self):
        frames=extract.roof_frames(self.rom)
        self.assertEqual(len(frames),69)
        for meta,pixels in frames:
            self.assertEqual(len(meta),8)
            self.assertEqual(len(pixels),96*96)
            self.assertTrue(set(pixels)<={0,1,2,3,255})

    def test_sprite_origin_against_oam_coordinates(self):
        # Independent direct piece projection from 00:1cdb-1d36, without the
        # extractor's composite-image offsets. Static target has flipped pieces.
        frame=62
        meta,pixels=extract.roof_frames(self.rom)[frame]
        ptr=extract.address(3,struct.unpack_from('<H',self.rom,0xd95c+frame*2)[0])+8
        expected={}
        while self.rom[ptr]!=255:
            y,x,tile,flags=self.rom[ptr:ptr+4];ptr+=4
            origin_x=extract.signed(meta[0])+meta[6]+8+extract.signed(x)
            origin_y=extract.signed(meta[1])+meta[7]+16+extract.signed(y)
            for row in range(16):
                sy=15-row if flags&64 else row
                base=extract.address(4,0x4610)+(tile&254)*16+sy*2
                low,high=self.rom[base:base+2]
                for col in range(8):
                    bit=col if flags&32 else 7-col
                    shade=((low>>bit)&1)+2*((high>>bit)&1)
                    if shade:expected[origin_x-8+col,origin_y-16+row]=shade
        actual={(x-48,y-48):pixels[y*96+x] for y in range(96) for x in range(96) if pixels[y*96+x]!=255}
        self.assertEqual(actual,expected)

    def test_roof_status_tiles(self):
        atlas,layout,columns=extract.roof_hud(self.rom)
        self.assertEqual(len(atlas),256*64)
        self.assertEqual(len(layout),20)
        self.assertEqual(list(columns),[1,3,4,6,7,10,11,14,15,16,17,18,19])
        self.assertEqual(atlas[0xf6*64:0xf7*64],extract.tile(self.rom,0xc010))
        self.assertEqual(atlas[0xf1*64:0xf2*64],extract.tile(self.rom,0xd800))
        self.assertTrue(set(atlas)<={0,1,2,3})

if __name__=='__main__':unittest.main()
