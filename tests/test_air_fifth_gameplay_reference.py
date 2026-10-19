"""Final-life gameplay attachment guards; synthetic data, no ROM/recordings."""
import copy,sys,unittest
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_fifth_gameplay_reference import final_scope
from air_fourth_gameplay_reference import native_prefix


class FinalGameplay(unittest.TestCase):
    def setUp(self):
        self.first=dict(afterRetry=3,nextRetry=True,updates=1,precedingDisplays=10,points=[dict(index=i) for i in range(10)],interrupts=[dict(index=i) for i in range(2)])
        game=copy.deepcopy(self.first);game.update(updates=1700,terminalWait=True)
        game['points'].append(dict(name='terminalEnd',result=33))
        self.records={key:dict(afterRetry=3) for key in ('outro','map','side-push')};self.records['gameplay']=game
    def reject(self):
        with self.assertRaises(ValueError):final_scope(self.first,self.records)
    def test_attached_final_failure(self):final_scope(self.first,self.records)
    def test_every_record_needs_final_generation(self):
        for record in self.records.values():
            record['afterRetry']=2;self.reject();record['afterRetry']=3
    def test_parent_needs_final_generation(self):self.first['afterRetry']=2;self.reject()
    def test_failure_cannot_be_success(self):self.records['gameplay']['points'][-1]['result']=3;self.reject()
    def test_terminal_wait_is_required(self):self.records['gameplay']['terminalWait']=False;self.reject()
    def test_first_timer_cannot_be_reinitialized(self):self.records['gameplay']['points'][0]['secondTicks']=0;self.reject()
    def test_first_vector_cannot_be_shifted(self):self.records['gameplay']['interrupts'][0]['cycles']=100;self.reject()
    def test_first_display_number_is_inherited(self):self.records['gameplay']['precedingDisplays']+=1;self.reject()


class NativeAttachment(unittest.TestCase):
    def setUp(self):
        parent=Path(__file__).resolve().parents[1]/'build'/'test-temp';parent.mkdir(parents=True,exist_ok=True)
        self.root=parent/str(uuid4());self.root.mkdir();self.first=self.root/'first.csv';self.long=self.root/'long.csv'
        suffixes=['','.fourth.next-incoming.summary.csv','.fifth.next-text.summary.csv','.fifth.next-entry.summary.csv']+['.fifth.next-gameplay'+s for s in ('.csv','.entities.csv','.services.csv','.interrupts.csv','.sprites.csv','.map.csv','.side-push.csv')]
        for suffix in suffixes:
            for base in (self.first,self.long):Path(str(base)+suffix).write_bytes(b'header\nsame\n')
        Path(str(self.first)+'.fifth.next-gameplay.map.csv').write_bytes(b'header\nstartup\nend,1\n')
        Path(str(self.long)+'.fifth.next-gameplay.map.csv').write_bytes(b'header\nstartup\nmore\nend,1700\n')
        Path(str(self.long)+'.fifth.next-gameplay.csv').write_bytes(b'header\nsame\nmore\n')
    def tearDown(self):
        for path in self.root.iterdir():path.unlink()
        self.root.rmdir()
    def verify(self):return native_prefix(self.first,self.long,'fifth')
    def test_first_update_is_prefix_and_older_game_is_exact(self):self.assertEqual(len(self.verify()),11)
    def test_old_result_cannot_be_replaced(self):
        Path(str(self.long)+'.fourth.next-incoming.summary.csv').write_bytes(b'changed\n')
        with self.assertRaises(ValueError):self.verify()
    def test_current_instruction_cannot_be_replaced(self):
        Path(str(self.long)+'.fifth.next-text.summary.csv').write_bytes(b'changed\n')
        with self.assertRaises(ValueError):self.verify()
    def test_actor_prefix_cannot_be_missing(self):
        Path(str(self.first)+'.fifth.next-gameplay.entities.csv').unlink()
        with self.assertRaises(ValueError):self.verify()
    def test_map_only_discards_explicit_end_marker(self):
        Path(str(self.first)+'.fifth.next-gameplay.map.csv').write_bytes(b'header\nstartup\n')
        with self.assertRaises(ValueError):self.verify()
    def test_map_prefix_cannot_be_replaced(self):
        Path(str(self.long)+'.fifth.next-gameplay.map.csv').write_bytes(b'changed\nend,1700\n')
        with self.assertRaises(ValueError):self.verify()
    def test_side_push_prefix_cannot_be_changed(self):
        Path(str(self.long)+'.fifth.next-gameplay.side-push.csv').write_bytes(b'changed\n')
        with self.assertRaises(ValueError):self.verify()
    def test_future_generations_are_not_opened(self):
        with self.assertRaises(ValueError):native_prefix(self.first,self.long,'sixth')


if __name__=='__main__':unittest.main()
