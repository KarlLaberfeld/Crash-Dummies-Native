"""Explicit subsequent-turn active scope cannot borrow an initial game's input."""
import copy,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from selected_turn_active_reference import extension,native_prefix,TAIL
from selected_turn_reference import TAIL as TURN_TAIL
from selected_following_instruction_reference import tail
from air_title_actions_reference import event_sha

class ActiveTurnControls(unittest.TestCase):
    def setUp(self):
        self.events=[['tick',500,True]]+tail('full-prompt')+TURN_TAIL
        self.parent=dict(inputCase='full-prompt',romSha256='rom',controlMemorySha256='parent')
        self.child=dict(inputCase='full-prompt',romSha256='rom',controlMemorySha256='child',parentControlMemorySha256='parent',parentEventsSha256=event_sha(self.events),setupSha256='setup',controlDifferences=[],prefixControlHashes=['parent']*2,unhookedControlHashes=['child']*2,gameplayScope='selected-turn-active',gameplayUpdates=320)
    def check(self):return extension(self.parent,self.child,self.events,self.events+TAIL,'setup')
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_explicit_scope(self):self.check()
    def test_initial_game_cannot_borrow_turn_scope(self):self.child['gameplayScope']='initial-selected';self.reject()
    def test_unsupported_extent(self):self.child['gameplayUpdates']=640;self.reject()
    def test_terminal_requires_own_owner(self):self.child['gameplayTerminal']=True;self.reject()
    def test_missing_accepted_turn_idle_suffix(self):
        self.events=self.events[:-1];self.child['parentEventsSha256']=event_sha(self.events);self.reject()
    def test_instruction_paths_need_their_own_complete_suffix(self):
        self.parent['inputCase']=self.child['inputCase']='skip-held';self.reject()
    def test_scroll_held_extension_retains_its_actual_input_suffix(self):
        self.events=[['tick',500,True]]+tail('scroll-held')+TURN_TAIL
        self.parent['inputCase']=self.child['inputCase']='scroll-held';self.child['parentEventsSha256']=event_sha(self.events);self.check()
    def test_original_control_must_be_unchanged(self):self.child['prefixControlHashes'][1]='other';self.reject()
    def test_timing_change_in_active_buttons_rejects(self):
        changed=copy.deepcopy(self.events+TAIL);changed[-4][1]=299
        with self.assertRaises(ValueError):extension(self.parent,self.child,self.events,changed,'setup')
class NativeTurnPrefix(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name);self.parent=root/'old.csv';self.base=root/'new.csv'
        complete=['','.next-gameplay.csv','.next-incoming.summary.csv','.third.next-text.summary.csv']+[f'.prior{i}.csv' for i in range(576)]
        for suffix in complete:
            Path(str(self.parent)+suffix).write_text('header\nold\n');Path(str(self.base)+suffix).write_text('header\nold\n')
        for suffix in ('.csv','.entities.csv','.services.csv','.interrupts.csv','.sprites.csv'):
            stem='.fifth.selected.turn.title-gameplay'+suffix
            Path(str(self.parent)+stem).write_text('header\nold\n');Path(str(self.base)+stem).write_text('header\nold\nnew\n')
    def tearDown(self):self.tmp.cleanup()
    def test_includes_base_csv_in_complete_ancestors(self):self.assertEqual(native_prefix(self.base,self.parent),580)
    def test_changed_base_csv_cannot_escape_glob(self):
        self.base.write_text('changed\n')
        with self.assertRaises(ValueError):native_prefix(self.base,self.parent)
    def test_missing_required_earlier_family_rejects(self):
        Path(str(self.parent)+'.next-gameplay.csv').unlink()
        with self.assertRaises(ValueError):native_prefix(self.base,self.parent)
    def test_old_gameplay_must_be_exact_byte_prefix(self):
        Path(str(self.base)+'.fifth.selected.turn.title-gameplay.entities.csv').write_text('header\nchanged\n')
        with self.assertRaises(ValueError):native_prefix(self.base,self.parent)

if __name__=='__main__':unittest.main()
