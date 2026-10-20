"""Synthetic selected initial-game attachment, masked setup and service integrity."""
import argparse,copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from test_air_following_setup_reference import prefix_fixture,stage_fixture,entry_fixture
from selected_game_entry_reference import analyze,compare_many

def fixture(players=0):
    groups=[prefix_fixture()[0],stage_fixture()[0],entry_fixture()[0]];now=1000
    parent=dict(romSha256='rom',controlMemorySha256='control',inputCase='skip-held',parentInputCase='two-start' if players else 'one-start',players=players,groups=[dict(points=[dict(cycles=now,tick=5,countdown=54,inputHeld=8,inputPressed=0,musicEnabled=0)])])
    for name,group in zip(('prefix','stage','entry'),groups):
        group['name']=name;offset=now-group['points'][0]['cycles']
        for p in group['points']:
            p['cycles']+=offset;p['countdown']=54
            if 'lives' in p:p['lives']=5
        for p in group.get('writes',[])+group.get('polls',[]):p['cycles']+=offset
        for irq in group['interrupts']:
            irq['start']+=offset;irq['end']+=offset
            if irq['kind']=='vblank':irq['phases']={k:v+offset for k,v in irq['phases'].items()};irq['voiceStates']=[dict(active=0) for _ in range(6)]
        now=group['points'][-1]['cycles']
    data={k:v for k,v in parent.items() if k!='groups'};data.update(version=1,groups=groups);return data,parent

class SelectedGameEntryIntegrity(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_one_and_two_players(self):
        for players in (0,1):self.assertEqual(len(analyze(*fixture(players))),2)
    def test_control(self):self.data['controlMemorySha256']='other';self.reject()
    def test_rom(self):self.data['romSha256']='other';self.reject()
    def test_input_case(self):self.data['inputCase']='other';self.reject()
    def test_player_choice(self):self.data['players']=1;self.reject()
    def test_parent_case(self):self.data['parentInputCase']='other';self.reject()
    def test_segment_order(self):self.data['groups'].reverse();self.reject()
    def test_prefix_time(self):self.data['groups'][0]['points'][0]['cycles']+=4;self.reject()
    def test_prefix_initial_lives(self):
        for p in self.data['groups'][0]['points']:p['lives']=4
        self.reject()
    def test_initial_difficulty(self):
        for p in self.data['groups'][0]['points']:p['difficulty']=1
        self.reject()
    def test_incomplete_clear(self):self.data['groups'][0]['writes'].pop();self.reject()
    def test_stage_time(self):self.data['groups'][1]['points'][0]['cycles']+=4;self.reject()
    def test_stage_campaign(self):self.data['groups'][1]['points'][0]['lives']=4;self.reject()
    def test_stage_tick(self):self.data['groups'][1]['points'][0]['tick']=4;self.reject()
    def test_stage_countdown(self):self.data['groups'][1]['points'][0]['countdown']=53;self.reject()
    def test_entry_scene_camera(self):self.data['groups'][2]['points'][0]['cameraX']+=128;self.reject()
    def test_entry_scene_scratch(self):self.data['groups'][2]['points'][0]['mapScratch']+=8;self.reject()
    def test_entry_pending(self):self.data['groups'][2]['points'][0]['pendingRequests']=0;self.reject()
    def test_missing_entry_voice(self):self.data['groups'][2]['interrupts'][0]['voiceStates'].pop();self.reject()
    def test_entry_vector_order(self):self.data['groups'][2]['interrupts'].reverse();self.reject()
    def test_fresh_start_requires_its_pause_owner(self):self.data['groups'][2]['points'][-1]['inputPressed']=8;self.reject()
    def test_empty_batch(self):
        with self.assertRaises(ValueError):compare_many([])
    def test_parent_batch_qualified_and_child_prefix_separately_checked(self):
        args=argparse.Namespace(native_base=Path('child'),text_base=Path('parent'),game_entry_out=Path('entry'),startup=Path('startup'))
        with patch('selected_text_reference.compare_many') as prior,patch('selected_game_entry_reference.compare') as child:
            compare_many([args]);self.assertEqual(prior.call_args.args[0][0].native_base,Path('parent'));self.assertNotIn('game_entry_out',vars(prior.call_args.args[0][0]));child.assert_called_once_with(args,_parent_qualified=True)
if __name__=='__main__':unittest.main()
