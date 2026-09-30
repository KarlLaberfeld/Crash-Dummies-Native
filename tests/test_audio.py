from pathlib import Path
import sys
import unittest

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'tools'))
import analyze_audio
from extract import address,read_rom

class MusicLanguage(unittest.TestCase):
    def fixture(self,data):
        rom=bytearray(131072);start=address(2,0x6000);rom[start:start+len(data)]=bytes(data);return rom

    def test_note_lengths_and_counted_loop(self):
        # Loop twice over a three-frame note, then stop.
        result=analyze_audio.inspect_track(self.fixture([0x80,2,24,3,0x81,0x83]),0x6000,0)
        self.assertEqual((result['frames'],result['notes'],result['end']),(6,2,'stop'))
        result=analyze_audio.inspect_track(self.fixture([24,0,0x83]),0x6000,0)
        self.assertEqual(result['frames'],256)

    def test_call_returns_with_changed_fixed_duration(self):
        # Call changes fixed duration; caller's next note has no length byte.
        result=analyze_audio.inspect_track(self.fixture([0x84,5,0x60,25,0x83,0x82,7,24,0x85]),0x6000,1)
        self.assertEqual((result['frames'],result['notes'],result['max_stack']),(14,2,1))

    def test_loop_and_invalid_commands(self):
        result=analyze_audio.inspect_track(self.fixture([24,5,0x88,0,0x60]),0x6000,0)
        self.assertEqual((result['intro_frames'],result['loop_frames']),(0,5))
        with self.assertRaisesRegex(ValueError,'Unknown music command'):
            analyze_audio.inspect_track(self.fixture([0xc3]),0x6000,0)
        with self.assertRaisesRegex(ValueError,'register'):
            analyze_audio.inspect_track(self.fixture([0x89,1,0,0x80]),0x6000,0)
        with self.assertRaisesRegex(ValueError,'underflow'):
            analyze_audio.inspect_track(self.fixture([0x85]),0x6000,0)

    def test_original_music_control_flow(self):
        files=list(PROJECT.glob('*.gb'))
        if not files:self.skipTest('Original ROM is local only')
        result=analyze_audio.analyze(read_rom(files[0]))
        self.assertEqual(len(result['songs']),14)
        self.assertEqual(len(result['effects']),26)
        self.assertEqual(sum(len(e['channels']) for e in result['effects']),29)
        for effect in result['effects']:
            for channel in effect['channels']:self.assertEqual(channel['end'],'stop')
        self.assertEqual([c['loop_frames'] for c in result['songs'][1]['channels']],[2112]*4)
        for song in result['songs']:
            self.assertEqual(len(song['channels']),4)
            for channel in song['channels']:
                self.assertIn(channel['end'],('loop','stop','stop_all'))
                self.assertLessEqual(channel['max_stack'],3)
                self.assertGreater(channel['notes'],0)

    def test_note_must_not_read_the_next_bank(self):
        rom=bytearray(131072);rom[address(2,0x7fff)]=24
        with self.assertRaisesRegex(ValueError,'bank end'):
            analyze_audio.command(rom,0x7fff,0,0)
        self.assertEqual(analyze_audio.command(rom,0x7fff,0,8),('note',[24,8],0x8000))

if __name__=='__main__':unittest.main()
