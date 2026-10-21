"""Turn ownership, shared map cursor and complete observation suffix integrity."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from test_selected_game_entry_reference import fixture as initial_fixture
from selected_turn_reference import analyze_entry,component_scope,gameplay_entry_boundary,observation_start,TAIL
from selected_following_instruction_reference import tail

def fixture(two=False,case='full-prompt'):
    data,parent=initial_fixture(int(two));data.update(origin='selected-turn-entry',inputCase=case,parentInputCase='full-prompt',parentControlMemorySha256='parent',controlMemorySha256='child')
    parent.update(origin='selected-following-instruction',inputCase=case,parentInputCase='full-prompt',controlMemorySha256='parent',campaign=dict(player=int(two),stage=1,difficulty=0,lives0=4,lives1=5 if two else 0,result=0))
    mapped=False
    for index,g in enumerate(data['groups']):
        for p in g['points']:
            p['countdown']=73
            if index<2:p.update(player=int(two),lives=5 if two else 4)
            if index==1 and p['name']=='mapPrepared':mapped=True
            p['previousMapCamera']=(p.get('cameraY',44672)+128)&65535 if mapped else 0
    parent['groups'][-1]['points'][-1]['countdown']=73
    return data,parent

class SelectedTurnEntry(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze_entry(self.data,self.parent)
    def test_actual_one_two_player_and_three_instruction_paths(self):
        for two in (False,True):
            for case in ('full-prompt','skip-held','scroll-held'):
                if two or case!='scroll-held':self.assertEqual(len(analyze_entry(*fixture(two,case))),2)
    def test_unqualified_ignored_scroll_input_cannot_borrow_turn_entry(self):
        self.data,self.parent=fixture(False,'scroll-held');self.reject()
    def test_initial_entry_cannot_be_relabelled(self):self.data['origin']='initial-entry';self.reject()
    def test_wrong_instruction_parent(self):self.parent['origin']='selected-initial-text';self.reject()
    def test_source_control_must_inherit_instruction(self):self.data['parentControlMemorySha256']='other';self.reject()
    def test_other_rom_rejects(self):self.parent['romSha256']='other';self.reject()
    def test_actual_selected_player_is_not_reset(self):self.data['players']=1;self.reject()
    def test_remaining_lives_are_not_restored(self):self.data['groups'][0]['points'][0]['lives']=5;self.reject()
    def test_second_player_keeps_its_own_lives(self):
        self.data,self.parent=fixture(True);self.data['groups'][1]['points'][0]['lives']=4;self.reject()
    def test_no_borrowed_time(self):self.data['groups'][0]['points'][0]['cycles']+=4;self.reject()
    def test_no_countdown_reset_to_initial_constant(self):self.data['groups'][0]['points'][0]['countdown']=54;self.reject()
    def test_missing_map_cursor(self):self.data['groups'][0]['points'][0].pop('previousMapCamera');self.reject()
    def test_map_cursor_not_reset_during_masked_prefix(self):self.data['groups'][0]['points'][2]['previousMapCamera']=0x8000;self.reject()
    def test_map_cursor_survives_stage_until_actual_rows(self):self.data['groups'][1]['points'][2]['previousMapCamera']=0x8000;self.reject()
    def test_map_preparation_publishes_last_native_world_row(self):
        next(p for p in self.data['groups'][1]['points'] if p['name']=='mapPrepared')['previousMapCamera']^=128;self.reject()
    def test_complete_entry_keeps_prepared_map_cursor(self):self.data['groups'][2]['points'][-1]['previousMapCamera']=0;self.reject()
    def test_entry_boundary_requires_same_control(self):
        with self.assertRaises(ValueError):gameplay_entry_boundary(self.data,dict(romSha256='rom',controlMemorySha256='wrong',inputCase='full-prompt'))

class TurnObservationSuffix(unittest.TestCase):
    def test_all_three_exact_suffixes(self):
        for case in ('full-prompt','skip-held','scroll-held'):self.assertEqual(observation_start([['tick',500,True]]+tail(case)+TAIL,case),1)
    def test_missing_idle_extension(self):
        with self.assertRaises(ValueError):observation_start(tail('full-prompt'),'full-prompt')
    def test_changed_skip_offset(self):
        events=tail('skip-held')+TAIL;events[0]=['tick',15,True]
        with self.assertRaises(ValueError):observation_start(events,'skip-held')

if __name__=='__main__':unittest.main()
