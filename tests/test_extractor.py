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
import extract_air
import extract_ski
import extract_bomb
import extract_cruise
import extract_ui
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
        for name in ('input.gb','crash.dat','manifest.json','air.dat','air-manifest.json','ski.dat','ski-manifest.json','bomb.dat','bomb-manifest.json','cruise.dat','cruise-manifest.json','ui.dat','ui-manifest.json'):
            (path/name).unlink(missing_ok=True)
        path.rmdir()

class BinaryFormats(unittest.TestCase):
    def test_air_map_rotates_each_template_row(self):
        data=bytearray(131072)
        struct.pack_into('<H',data,0x1d78,0x7000)
        source=extract.address(4,0x7000)
        data[source:source+64]=bytes(range(64))
        start=extract.address(4,0x7acc)
        data[start:start+5]=bytes([3,0,15,0,255])
        cells,rows=extract_air.air_map(data,0x7acc)
        self.assertEqual(rows,8)
        self.assertEqual(list(cells[:16]),list(range(13,16))+list(range(13)))
        self.assertEqual(list(cells[16:32]),list(range(29,32))+list(range(16,29)))
        self.assertEqual(list(cells[64:80]),list(range(1,16))+[0])
        self.assertEqual(cells[128:],bytes(4096-128))

    def test_air_map_rejects_excess_bands(self):
        data=bytearray(131072)
        struct.pack_into('<H',data,0x1d78,0x7000)
        with self.assertRaisesRegex(ValueError,'exceeds'):extract_air.air_map(data,0x7acc)

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
            self.assertEqual(pack[:8],b'TICDNAT4')
            self.assertNotIn(self.rom,pack)
            first=pack
            extract.extract(self.rom,directory)
            self.assertEqual(first,(Path(directory)/'crash.dat').read_bytes())

    def test_air_pack_and_graph(self):
        with scratch_directory() as directory:
            result=extract_air.extract_air(self.rom,directory)
            levels=result['difficulties']
            self.assertEqual([x['rows'] for x in levels],[184,236,256,256])
            self.assertEqual([x['objects'] for x in levels],[78,131,143,143])
            self.assertEqual([x['seconds'] for x in levels],[40,60,70,70])
            self.assertEqual([x['quota'] for x in levels],[14,15,24,16])
            pack=(Path(directory)/'air.dat').read_bytes()
            self.assertEqual(pack[:8],b'TICDAIR3')
            extract_air.extract_air(self.rom,directory)
            self.assertEqual(pack,(Path(directory)/'air.dat').read_bytes())
        roots,commands=extract.animation_records(self.rom,extract_air.ANIMATIONS,extract_air.HANDLERS)
        self.assertEqual(len(roots),13)
        for op,a,b,c,nxt in commands:
            self.assertLessEqual(nxt,len(commands))
            if op==10:self.assertTrue(1<=a<=len(commands))
            if op==11:self.assertIn(a,extract_air.HANDLERS.values())
            if op==16:self.assertTrue(17<=c<=34)
        frames=extract.sprite_frames(self.rom,59,0xe0bf,0xe08f,12,extract.address(5,0x4000))
        for _,pixels in frames:self.assertTrue(set(pixels)<={0,1,2,3,255})

    def test_ski_pack_and_declared_playable_height(self):
        with scratch_directory() as directory:
            result=extract_ski.extract_ski(self.rom,directory)
            levels=result['difficulties']
            self.assertEqual([x['rows'] for x in levels],[120,108,152,200])
            self.assertEqual([x['objects'] for x in levels],[52,58,77,124])
            self.assertEqual([x['flags'] for x in levels],[30,22,41,31])
            self.assertEqual([x['seconds'] for x in levels],[80,80,90,90])
            self.assertTrue(all(x['rows']==x['expanded_rows'] for x in levels))
            pack=(Path(directory)/'ski.dat').read_bytes()
            self.assertEqual(pack[:8],b'TICDSKI1')
            extract_ski.extract_ski(self.rom,directory)
            self.assertEqual(pack,(Path(directory)/'ski.dat').read_bytes())
        roots,commands=extract.animation_records(self.rom,extract_ski.ANIMATIONS,extract_ski.HANDLERS)
        self.assertEqual(len(roots),11)
        for op,a,b,c,nxt in commands:
            self.assertLessEqual(nxt,len(commands))
            if op==10:self.assertTrue(1<=a<=len(commands))
            if op==4:self.assertTrue(0<=a<39)

    def test_bomb_pack_and_explicit_animation_callbacks(self):
        with scratch_directory() as directory:
            result=extract_bomb.extract_bomb(self.rom,directory)
            self.assertEqual([x['quota'] for x in result['levels']],[40,50,60,70])
            self.assertEqual([x['speeds'] for x in result['levels']],[[3,3,3],[3,4,3],[5,4,3],[5,3,5]])
            pack=(Path(directory)/'bomb.dat').read_bytes()
            self.assertEqual(pack[:8],b'TICDBOM1')
            extract_bomb.extract_bomb(self.rom,directory)
            self.assertEqual(pack,(Path(directory)/'bomb.dat').read_bytes())
        with self.assertRaisesRegex(ValueError,'Unported native animation callback'):
            extract.animation_records(self.rom,extract_bomb.ANIMATIONS,extract_bomb.HANDLERS)
        roots,commands=extract.animation_records(self.rom,extract_bomb.ANIMATIONS,extract_bomb.HANDLERS,{0x1747:0})
        self.assertEqual(len(roots),6)
        callbacks=[a for op,a,b,c,nxt in commands if op==20]
        self.assertEqual(callbacks,[0]*6)

    def test_cruise_pack_column_major_map_and_graphs(self):
        with scratch_directory() as directory:
            result=extract_cruise.extract_cruise(self.rom,directory)
            self.assertEqual([x['objects'] for x in result['levels']],[13,27,34,38])
            self.assertEqual([x['seconds'] for x in result['levels']],[60]*4)
            pack=(Path(directory)/'cruise.dat').read_bytes()
            self.assertEqual(pack[:8],b'TICDCRU1')
            start=8+82*64
            self.assertEqual(pack[start:start+2048],self.rom[0x1c180:0x1c980])
            extract_cruise.extract_cruise(self.rom,directory)
            self.assertEqual(pack,(Path(directory)/'cruise.dat').read_bytes())
        roots,commands=extract.animation_records(self.rom,extract_cruise.ANIMATIONS,extract_cruise.HANDLERS)
        self.assertEqual(len(roots),10)
        for op,a,b,c,nxt in commands:
            self.assertLessEqual(nxt,len(commands))
            if op==11:self.assertIn(a,extract_cruise.HANDLERS.values())
            if op==4:self.assertTrue(0<=a<42)

    def test_original_title_menu_maps(self):
        with scratch_directory() as directory:
            extract_ui.extract_ui(self.rom,directory)
            pack=(Path(directory)/'ui.dat').read_bytes()
            self.assertEqual(pack[:8],b'TICDUI01')
            self.assertEqual(len(pack),8+16384+23040+6144+48)
            maps=pack[39432:45576]
            self.assertEqual(maps[14*32:14*32+20],self.rom[0x1db0e:0x1db0e+20])
            self.assertEqual(pack[-48:],self.rom[0xa3:0xd3])
            options=maps[5*1024:6*1024]
            self.assertEqual(options[18*32+3:18*32+6],bytes([25,24,15])) # ONE
            extract_ui.extract_ui(self.rom,directory)
            self.assertEqual(pack,(Path(directory)/'ui.dat').read_bytes())
        with self.assertRaisesRegex(ValueError,'Unported menu operation'):
            extract_ui.menu_map(bytes([0x94,0x80]),0)

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
