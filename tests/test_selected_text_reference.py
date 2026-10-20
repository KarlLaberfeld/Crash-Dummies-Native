"""Synthetic retained-player instruction extent, publication and attachment checks."""
import argparse,copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from test_air_title_entrance_reference import fixture as entrance_fixture
from test_air_instruction_text_reference import fixture as text_fixture
from test_air_instruction_exit_reference import fixture as exit_fixture
from selected_text_reference import analyze,compare_many

def fixture(players=0,preceding=1200):
    entered,parent=entrance_fixture();typed=text_fixture()[0];exited=exit_fixture()[0]
    groups=[entered,typed,exited];maps=parent['maps'];tiles=parent['tiles'];last=None
    for index,group in enumerate(groups):
        group['name']=('entrance','text','instruction-exit')[index];group['precedingInputSamples']=preceding;group['polls']=group.get('polls',[])
        group['beforeMaps']=list(maps);group['beforeTiles']=list(tiles);group['beforeObjects']=[0]*256;group['objects']=[0]*256
        if index==0:group['scrollWrites']=group['writes'];group['writes']=[]
        else:
            shift=last['cycles']-group['points'][0]['cycles'];tick=last['tick']-group['points'][0]['tick']
            for p in group['points']:
                p['cycles']+=shift;p['tick']=(p['tick']+tick)&65535;p['countdown']=54
                if index==2:p['scroll']=0
            for r in group['interrupts']:
                r['start']+=shift;r['end']+=shift;r['tick']=(r['tick']+tick)&65535;r['countdown']=54
                r['phases']={k:v+shift for k,v in r['phases'].items()};r['voiceStates']=[dict(active=0) for _ in range(6)]
            for p in group['polls']+group['writes']:p['cycles']+=shift
            if index==1:
                group['points'][5]['name']='skip';group['points'][5]['skipContext']=0
                for p in group['points'][3:]:p.update(inputHeld=8,inputPressed=8)
                group['interrupts'][0].update(held=8,pressed=8)
                group['scrollWrites']=[dict(cycle=r['start']+1284,address=0xff42,value=0) for r in group['interrupts']]
            else:
                first=group['interrupts'][0]['end']+16
                for p in group['points']:
                    if p['cycles']<first:p['inputPressed']=8
                colors=[]
                for p in group['points']:
                    if p['name']=='fadePalette':colors+= [dict(cycle=p['cycles']+off,address=address,value=p['bgp']&mask) for off,address,mask in ((8,0xff47,255),(28,0xff49,243),(56,0xff48,207))]
                group['scrollWrites']=sorted(colors+[dict(cycle=r['start']+1284,address=0xff42,value=0) for r in group['interrupts']],key=lambda p:p['cycle']);group['endRawActiveFlags']=4
        for w in group['writes']:maps=list(maps);maps[w['address']-0x9800]=w['value']
        group['maps']=list(maps);group['tiles']=list(tiles);last=group['points'][-1];preceding+=sum(r['kind']=='vblank' for r in group['interrupts'])
    parent.update(inputCase='two-start' if players else 'one-start',players=players,controlMemorySha256='parent',groups=[dict(parent)])
    data=dict(version=1,inputCase='skip-held',parentInputCase=parent['inputCase'],players=players,parentControlMemorySha256='parent',campaign=dict(player=0,stage=1,difficulty=0),storageReadOwner='direct-vram-instruction-v1',reference=dict(instructionStorageObserver='direct-vram-instruction-v1'),groups=groups)
    return data,parent

class SelectedTextIntegrity(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent,1200)
    def test_both_players_with_actual_retained_counters(self):
        for players in (0,1):self.assertEqual(len(analyze(*fixture(players),1200)),66)
    def test_other_preceding_counts_are_not_fitted(self):self.assertEqual(len(analyze(*fixture(1,1500),1500)),66)
    def test_parent_case(self):self.data['parentInputCase']='one-other';self.reject()
    def test_player_choice(self):self.data['players']=1;self.reject()
    def test_parent_hash(self):self.data['parentControlMemorySha256']='other';self.reject()
    def test_campaign(self):self.data['campaign']['difficulty']=1;self.reject()
    def test_order(self):self.data['groups'].reverse();self.reject()
    def test_storage_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_storage_backend(self):self.data['reference']={};self.reject()
    def test_retained_display_count(self):self.data['groups'][1]['precedingInputSamples']+=1;self.reject()
    def test_segment_gap(self):self.data['groups'][1]['points'][0]['cycles']+=4;self.reject()
    def test_segment_input(self):self.data['groups'][2]['points'][0]['inputHeld']=0;self.reject()
    def test_segment_tick(self):self.data['groups'][1]['points'][0]['tick']+=1;self.reject()
    def test_parent_maps(self):self.data['groups'][1]['beforeMaps'][0]^=1;self.reject()
    def test_parent_tiles(self):self.data['groups'][2]['beforeTiles'][0]^=1;self.reject()
    def test_output_tiles(self):self.data['groups'][1]['tiles'][0]^=1;self.reject()
    def test_output_objects(self):self.data['groups'][2]['objects'][0]=1;self.reject()
    def test_unrelated_map(self):self.data['groups'][1]['maps'][2047]^=1;self.reject()
    def test_missing_glyph(self):self.data['groups'][1]['writes'].clear();self.reject()
    def test_missing_scroll(self):self.data['groups'][1]['scrollWrites'].clear();self.reject()
    def test_missing_voice(self):self.data['groups'][1]['interrupts'][0]['voiceStates'].pop();self.reject()
    def test_wrong_skip_case(self):self.data['inputCase']='full-prompt';self.reject()
    def test_missing_exit_palette(self):self.data['groups'][2]['scrollWrites'].pop(0);self.reject()
    def test_exit_palette_mask(self):next(p for p in self.data['groups'][2]['scrollWrites'] if p['address']==0xff49)['value']=255;self.reject()
    def test_exit_scroll(self):next(p for p in self.data['groups'][2]['scrollWrites'] if p['address']==0xff42)['value']=1;self.reject()
    def test_parked_raw_flags_are_not_playback(self):self.data['groups'][2]['endRawActiveFlags']=0;self.assertEqual(len(analyze(self.data,self.parent,1200)),66)
    def test_raw_flags_bound(self):self.data['groups'][2]['endRawActiveFlags']=7;self.reject()
    def test_raw_flags_boolean(self):self.data['groups'][2]['endRawActiveFlags']=True;self.reject()
    def test_raw_flags_missing(self):del self.data['groups'][2]['endRawActiveFlags'];self.reject()
    def test_empty_batch(self):
        with self.assertRaises(ValueError):compare_many([])
    def test_mixed_batch_ancestry(self):
        with self.assertRaises(ValueError):compare_many([argparse.Namespace(startup=Path('a')),argparse.Namespace(startup=Path('b'))])
    def test_ancestors_qualified_once_and_duplicate_parent_deduplicated(self):
        args=argparse.Namespace(native_base=Path('child'),selected_base=Path('parent'),text_control=Path('text'),selected_text_out=Path('capture'),selected_out=Path('selected'),exit_base=Path('exit'),exit_control=Path('controls'),startup=Path('startup'))
        with patch('selected_instruction_reference.compare_many') as prior,patch('selected_text_reference.compare') as child:
            compare_many([args,copy.deepcopy(args)]);self.assertEqual(len(prior.call_args.args[0]),1);self.assertEqual(prior.call_args.args[0][0].native_base,Path('parent'));self.assertEqual(child.call_count,2)
if __name__=='__main__':unittest.main()
