"""Synthetic fourth-attempt continuation integrity; no original recordings."""
import copy,sys,unittest
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_fourth_gameplay_reference import fourth_first_update,native_prefix


class FirstUpdate(unittest.TestCase):
    def setUp(self):
        self.first=dict(afterRetry=2,nextRetry=True,updates=1,precedingDisplays=10,points=[dict(index=i) for i in range(10)],interrupts=[dict(index=i) for i in range(2)])
        self.long=copy.deepcopy(self.first);self.long['updates']=1000;self.long['points'].append(dict(index=10))
    def test_same_first_update(self):fourth_first_update(self.first,self.long)
    def test_wrong_generation(self):
        self.long['afterRetry']=1
        with self.assertRaises(ValueError):fourth_first_update(self.first,self.long)
    def test_changed_inherited_timer(self):
        self.long['points'][0]['secondTicks']=0
        with self.assertRaises(ValueError):fourth_first_update(self.first,self.long)
    def test_changed_first_display(self):
        self.long['interrupts'][0]['tick']=0
        with self.assertRaises(ValueError):fourth_first_update(self.first,self.long)


class NativePrefix(unittest.TestCase):
    def setUp(self):
        parent=Path(__file__).resolve().parents[1]/'build'/'test-temp';parent.mkdir(parents=True,exist_ok=True)
        self.root=parent/str(uuid4());self.root.mkdir();self.first=self.root/'first.csv';self.long=self.root/'long.csv'
        self.suffixes=['','.third.next-text.summary.csv','.fourth.next-entry.summary.csv','.fourth.next-gameplay.csv','.fourth.next-gameplay.entities.csv','.fourth.next-gameplay.services.csv','.fourth.next-gameplay.interrupts.csv','.fourth.next-gameplay.sprites.csv','.fourth.next-gameplay.map.csv']
        for suffix in self.suffixes:
            for base in (self.first,self.long):Path(str(base)+suffix).write_bytes(b'header\nsame\n')
        Path(str(self.first)+'.fourth.next-gameplay.map.csv').write_bytes(b'header\nstartup\nend,1\n')
        Path(str(self.long)+'.fourth.next-gameplay.map.csv').write_bytes(b'header\nstartup\nmore\nend,1000\n')
        Path(str(self.long)+'.fourth.next-gameplay.csv').write_bytes(b'header\nsame\nmore\n')
    def tearDown(self):
        for p in self.root.iterdir():p.unlink()
        self.root.rmdir()
    def test_first_prefix_retained(self):self.assertEqual(len(native_prefix(self.first,self.long)),9)
    def test_changed_parent_text(self):
        Path(str(self.long)+'.third.next-text.summary.csv').write_bytes(b'changed\n')
        with self.assertRaises(ValueError):native_prefix(self.first,self.long)
    def test_missing_accepted_scope(self):
        Path(str(self.first)+'.fourth.next-gameplay.entities.csv').unlink()
        with self.assertRaises(ValueError):native_prefix(self.first,self.long)
    def test_missing_continued_scope(self):
        Path(str(self.long)+'.fourth.next-entry.summary.csv').unlink()
        with self.assertRaises(ValueError):native_prefix(self.first,self.long)
    def test_map_prefix_needs_terminal_marker(self):
        Path(str(self.first)+'.fourth.next-gameplay.map.csv').write_bytes(b'header\nstartup\n')
        with self.assertRaises(ValueError):native_prefix(self.first,self.long)
    def test_changed_first_gameplay(self):
        Path(str(self.long)+'.fourth.next-gameplay.csv').write_bytes(b'changed\n')
        with self.assertRaises(ValueError):native_prefix(self.first,self.long)


if __name__=='__main__':unittest.main()
