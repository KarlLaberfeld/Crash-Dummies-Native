import struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from extract import address
from extract_following_setup import profiles,extract

def fixture():
    rom=bytearray(0x20000)
    for stage,table,bank,roots,object_pointer in ((1,0xc1f,4,0x608f,0x3500),(2,0xe9c,5,0x66bc,0x3600)):
        rom[address(3,roots)]=9 if stage==1 else 4
        for difficulty in range(4):struct.pack_into('<BBBBHH',rom,table+8*difficulty,1,174 if stage==1 else 30,0x40 if stage==1 else 0x80,14 if stage==1 else 4,0x7a00,object_pointer)
        rom[address(bank,0x7a00):address(bank,0x7a00)+3]=bytes([0,0,255])
        rom[object_pointer:object_pointer+6]=bytes([18 if stage==1 else 36,0,0,0,0,255])
    return rom

class FollowingMetadataExtraction(unittest.TestCase):
    def test_decoded_metadata_has_lengths_and_world_coordinates(self):
        values=profiles(fixture());self.assertEqual(len(values),8)
        self.assertEqual(values[0],(1,0,1,9,0x4400,0xae80));self.assertEqual(values[4],(1,0,1,4,0x3d00,0))
    def test_placement_count_uses_data_terminator(self):
        rom=fixture();rom[0x3505:0x350b]=bytes([18,0,0,0,0,255]);self.assertEqual(profiles(rom)[0][2],2)
    def test_ski_template_table_carry_is_metadata(self):
        rom=fixture();rom[address(5,0x7a00)+1]=12;self.assertEqual(profiles(rom)[4][1],1)
    def test_offscreen_ram_band_counts_work_without_fabricating_contents(self):
        rom=fixture();pos=address(5,0x7a00);rom[pos:pos+5]=bytes([0,0,128,31,255]);self.assertEqual(profiles(rom)[4][:2],(2,1))
    def test_ram_band_cannot_appear_before_more_rows(self):
        rom=fixture();pos=address(5,0x7a00);rom[pos:pos+5]=bytes([128,31,0,0,255])
        with self.assertRaises(ValueError):profiles(rom)
    def test_unidentified_template_rejects(self):
        rom=fixture();rom[address(4,0x7a00)+1]=31
        with self.assertRaises(ValueError):profiles(rom)
    def test_unidentified_actor_rejects(self):
        rom=fixture();rom[0x3500]=35
        with self.assertRaises(ValueError):profiles(rom)
    def test_invalid_sprite_extent_rejects(self):
        rom=fixture();rom[address(3,0x608f)]=14
        with self.assertRaises(ValueError):profiles(rom)
    def test_invalid_bcd_timer_rejects(self):
        rom=fixture();rom[0xc21]=0x4a
        with self.assertRaises(ValueError):profiles(rom)
    def test_binary_contains_only_eight_fixed_metadata_records(self):
        local=Path(__file__).resolve().parents[1]/'local';local.mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=local,suffix='.dat',delete=False) as temporary:path=Path(temporary.name)
        try:values=extract(fixture(),path);data=path.read_bytes()
        finally:path.unlink()
        self.assertEqual(data[:8],b'TICDFS01');self.assertEqual(len(data),104)
        self.assertEqual(struct.unpack_from('<6H',data,8),values[0])

if __name__=='__main__':unittest.main()
