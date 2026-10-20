"""Synthetic initial-gameplay attachment and bounded source-observer integrity."""
import argparse,copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from test_air_following_quiet_reference import fixture as quiet_fixture
from test_air_following_setup_reference import entry_fixture
from selected_gameplay_reference import analyze,compare_many
from air_following_gameplay_reference import selected_entry_boundary

def fixture(players=0):
    data=quiet_fixture()[0];template=copy.deepcopy(data['points'][10:20]);irqs=copy.deepcopy(data['interrupts'][2:4])
    for update in range(2,32):
        delta=70224*(update-1)
        for point in template:
            q=copy.deepcopy(point);q['cycles']+=delta;q['tick']=(q['tick']+update-1)&65535;q['hudCursor']+=update-1;data['points'].append(q)
        for irq in irqs:
            q=copy.deepcopy(irq);q['start']+=delta;q['end']+=delta
            if q['kind']=='vblank':q['tick']=(q['tick']+update-1)&65535;q['phases']={k:v+delta for k,v in q['phases'].items()}
            data['interrupts'].append(q)
    first=data['points'][0];data.update(updates=32,selectedEntryCycle=first['cycles'],romSha256='rom',controlMemorySha256='control',inputCase='skip-held',parentInputCase='two-start' if players else 'one-start',players=players,entryPauseConsumed=False)
    parent={k:data[k] for k in ('romSha256','controlMemorySha256','inputCase','parentInputCase','players')};parent['groups']=[dict(points=[dict(cycles=first['cycles'],**{v:first[k] for k,v in [('tick','tick'),('random','randomState'),('cameraX','cameraX'),('cameraY','cameraY'),('mapScratch','mapScratch'),('hudCursor','hudCursor'),('fadeRemaining','fadeRemaining'),('held','inputHeld'),('pressed','inputPressed')]})])]
    return data,parent

class SelectedGameplayIntegrity(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_both_players_and_complete_extent(self):
        for players in (0,1):self.assertEqual(len(analyze(*fixture(players))),32)
    def test_parent_hash(self):self.data['controlMemorySha256']='other';self.reject()
    def test_parent_case(self):self.data['parentInputCase']='other';self.reject()
    def test_player_choice(self):self.data['players']=1;self.reject()
    def test_missing_update(self):self.data['points'].pop();self.reject()
    def test_wrong_extent(self):self.data['updates']=31;self.reject()
    def test_wrong_boundary(self):self.data['selectedEntryCycle']+=4;self.reject()
    def test_retained_scene_seed(self):self.data['points'][0]['random']+=1;self.reject()
    def test_retained_input(self):self.parent['groups'][-1]['points'][-1]['inputHeld']=0;self.reject()
    def test_retained_scratch(self):self.parent['groups'][-1]['points'][-1]['mapScratch']+=8;self.reject()
    def test_retained_hud(self):self.parent['groups'][-1]['points'][-1]['hudCursor']=0;self.reject()
    def test_no_borrowed_old_pause(self):self.data['entryPauseConsumed']=True;self.reject()
    def test_missing_vector(self):self.data['interrupts'].pop();self.reject()
    def test_resource_crossing_requires_other_owner(self):self.data['points'][15]['transfer']=1;self.reject()
    def test_empty_batch(self):
        with self.assertRaises(ValueError):compare_many([])
    def test_qualified_parent_batch_then_independent_children(self):
        args=argparse.Namespace(native_base=Path('child'),game_entry_base=Path('parent'),gameplay_out=Path('game'),startup=Path('startup'))
        with patch('selected_game_entry_reference.compare_many') as parent,patch('selected_gameplay_reference.compare') as child:
            compare_many([args]);self.assertEqual(parent.call_args.args[0][0].native_base,Path('parent'));self.assertNotIn('gameplay_out',vars(parent.call_args.args[0][0]));child.assert_called_once_with(args,_parent_qualified=True)

class SourceEntryBoundary(unittest.TestCase):
    def setUp(self):
        entry=entry_fixture()[0];entry['name']='entry';self.parent=dict(version=1,romSha256='rom',controlMemorySha256='control',inputCase='skip-held',groups=[dict(name='prefix'),dict(name='stage'),entry]);self.manifest=dict(romSha256='rom',controlMemorySha256='control',inputCase='skip-held')
    def check(self):
        with patch('air_following_gameplay_reference.require_capture_reference') as backend:
            value=selected_entry_boundary(self.parent,self.manifest);backend.assert_called_once_with(self.manifest,self.parent);return value
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_actual_completed_entry_owns_filter(self):self.assertEqual(self.check(),self.parent['groups'][-1]['points'][-1]['cycles'])
    def test_changed_control(self):self.parent['controlMemorySha256']='other';self.reject()
    def test_changed_rom(self):self.parent['romSha256']='other';self.reject()
    def test_wrong_case(self):self.parent['inputCase']='other';self.reject()
    def test_missing_segment(self):self.parent['groups'].pop(0);self.reject()
    def test_incomplete_entry(self):self.parent['groups'][-1]['points'].pop();self.reject()
    def test_wrong_entry_vectors(self):self.parent['groups'][-1]['interrupts'].reverse();self.reject()
if __name__=='__main__':unittest.main()
