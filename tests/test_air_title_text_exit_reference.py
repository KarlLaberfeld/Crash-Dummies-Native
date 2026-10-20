"""Synthetic attachment/storage integrity, independent of local recordings."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from test_air_instruction_text_reference import fixture as text_fixture
from test_air_instruction_exit_reference import fixture as exit_fixture
from air_title_text_reference import analyze as text_analyze
from air_title_instruction_exit_reference import analyze as exit_analyze
from air_title_text_controls import attachment,tail,event_sha

def storage(data,parent):
    data.update(storageReadOwner='direct-vram-instruction-v1',reference=dict(instructionStorageObserver='direct-vram-instruction-v1'),
        beforeMaps=[0]*2048,beforeTiles=[37]*1024,tiles=[37]*1024,objectsUnchanged=True)
    parent.update(maps=list(data['beforeMaps']),tiles=list(data['beforeTiles']))
    data['maps']=list(data['beforeMaps'])
    for w in data['writes']:data['maps'][w['address']-0x9800]=w['value']
    for r in data['interrupts']:
        if r['kind']=='vblank':r['voiceStates']=[dict(active=0) for _ in range(6)]

def text_data():
    data=text_fixture()[0];data['campaign']=dict(player=0,stage=1,difficulty=0)
    data.update(inputCase='full-prompt',precedingDisplays=739)
    for p in data['points']+data['interrupts']:p['countdown']=54
    parent=dict(points=[copy.deepcopy(data['points'][0])]);storage(data,parent)
    data['scrollWrites']=[dict(cycle=r['start']+1284,address=0xff42,value=0) for r in data['interrupts']]
    return data,parent

def exit_data():
    data=exit_fixture()[0];data.update(inputCase='skip-held',precedingDisplays=739,endActiveVoices=0,endRawActiveFlags=4)
    parent=dict(inputCase='skip-held',points=[copy.deepcopy(data['points'][0])],interrupts=[]);storage(data,parent)
    colors=[]
    for p in data['points']:
        if p['name']=='fadePalette':colors.extend(dict(cycle=p['cycles']+offset,address=address,value=p['bgp']&mask) for offset,address,mask in ((8,0xff47,255),(28,0xff49,243),(56,0xff48,207)))
    data['extraWrites']=sorted(colors+[dict(cycle=r['start']+1284,address=0xff42,value=0) for r in data['interrupts']],key=lambda p:p['cycle'])
    return data,parent

class TextIntegrity(unittest.TestCase):
    def setUp(self):self.data,self.parent=text_data()
    def reject(self):
        with self.assertRaises(ValueError):text_analyze(self.data,self.parent)
    def test_complete(self):self.assertEqual(len(text_analyze(self.data,self.parent)),1)
    def test_parent_cycle(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_parent_counter(self):self.parent['points'][0]['tick']-=1;self.reject()
    def test_campaign(self):self.data['campaign']['player']=1;self.reject()
    def test_case(self):self.data['inputCase']='skip-held';self.reject()
    def test_preceding(self):self.data['precedingDisplays']=738;self.reject()
    def test_voice_count(self):self.data['interrupts'][0]['voiceStates'].pop();self.reject()
    def test_scroll_missing(self):self.data['scrollWrites'].clear();self.reject()
    def test_scroll_value(self):self.data['scrollWrites'][0]['value']=1;self.reject()
    def test_scroll_time(self):self.data['scrollWrites'][0]['cycle']+=4;self.reject()
    def test_unpublished_glyph(self):self.data['maps'][0x220]=0;self.reject()
    def test_other_map(self):self.data['maps'][2047]=1;self.reject()
    def test_picture_mutation(self):self.data['tiles'][0]=0;self.reject()
    def test_parent_picture(self):self.parent['tiles'][0]=0;self.reject()
    def test_objects(self):self.data['objectsUnchanged']=False;self.reject()
    def test_storage_owner(self):self.data['storageReadOwner']='cpu-bus';self.reject()
    def test_storage_provenance(self):self.data['reference']={};self.reject()

class ExitIntegrity(unittest.TestCase):
    def setUp(self):self.data,self.parent=exit_data()
    def reject(self):
        with self.assertRaises(ValueError):exit_analyze(self.data,self.parent)
    def test_parked_raw_flags_with_disabled_driver(self):self.assertEqual(len(exit_analyze(self.data,self.parent)),33)
    def test_logical_voice_not_stopped(self):self.data['endActiveVoices']=4;self.reject()
    def test_driver_not_stopped(self):self.data['points'][-1]['musicEnabled']=1;self.reject()
    def test_raw_flags_missing(self):del self.data['endRawActiveFlags'];self.reject()
    def test_raw_flags_bounds(self):self.data['endRawActiveFlags']=7;self.reject()
    def test_raw_flags_type(self):self.data['endRawActiveFlags']=True;self.reject()
    def test_other_parked_flags_not_payload_parity(self):self.data['endRawActiveFlags']=0;self.assertEqual(len(exit_analyze(self.data,self.parent)),33)
    def test_parent_cycle(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_parent_scroll(self):self.parent['points'][0]['scroll']=0;self.reject()
    def test_prompt_branch(self):self.data['inputCase']=self.parent['inputCase']='full-prompt';self.reject()
    def test_voice_count(self):self.data['interrupts'][0]['voiceStates'].pop();self.reject()
    def test_palette_missing(self):self.data['extraWrites'].pop(0);self.reject()
    def test_palette_mask(self):next(p for p in self.data['extraWrites'] if p['address']==0xff49)['value']=255;self.reject()
    def test_scroll_missing(self):self.data['extraWrites']=[p for p in self.data['extraWrites'] if p['address']!=0xff42];self.reject()
    def test_unrelated_map(self):self.data['maps'][2047]=1;self.reject()
    def test_picture(self):self.data['tiles'][0]=0;self.reject()
    def test_parent_picture(self):self.parent['tiles'][0]=0;self.reject()
    def test_objects(self):self.data['objectsUnchanged']=False;self.reject()
    def test_storage_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_storage_provenance(self):self.data['reference']={};self.reject()

class ControlIntegrity(unittest.TestCase):
    def setUp(self):
        self.events=[['tick',80,True]];self.parent=dict(controlMemorySha256='parent',romSha256='rom')
        self.child=dict(inputCase='full-prompt',parentControlMemorySha256='parent',parentEventsSha256=event_sha(self.events),setupSha256='setup',romSha256='rom',controlMemorySha256='child',controlDifferences=[],prefixControlHashes=['parent']*2,unhookedControlHashes=['child']*2)
        self.changed=self.events+tail('full-prompt')
    def check(self):attachment(self.parent,self.child,self.events,self.changed,'setup')
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_complete(self):self.check()
    def test_skip_tail(self):self.child['inputCase']='skip-held';self.changed=self.events+tail('skip-held');self.check()
    def test_changed_prefix(self):self.changed[0]=['tick',79,True];self.reject()
    def test_changed_tail(self):self.changed.pop();self.reject()
    def test_setup(self):self.child['setupSha256']='changed';self.reject()
    def test_rom(self):self.child['romSha256']='changed';self.reject()
    def test_parent(self):self.child['parentControlMemorySha256']='changed';self.reject()
    def test_parent_events(self):self.child['parentEventsSha256']='changed';self.reject()
    def test_missing_repetition(self):self.child['unhookedControlHashes'].pop();self.reject()
    def test_changed_unobserved_prefix(self):self.child['prefixControlHashes'][1]='changed';self.reject()
    def test_changed_unobserved_full(self):self.child['unhookedControlHashes'][1]='changed';self.reject()
    def test_control_differences(self):self.child['controlDifferences']=['changed'];self.reject()
    def test_unknown_case(self):self.child['inputCase']='other';self.reject()
    def test_unknown_tail(self):
        with self.assertRaises(ValueError):tail('other')

if __name__=='__main__':unittest.main()
