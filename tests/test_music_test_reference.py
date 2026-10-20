"""Synthetic provenance, state order and coverage rejection tests; no ROM data."""
import argparse,copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from music_test_reference import analyze,attachment,tail,CASES,compare_many
from air_title_actions_reference import event_sha

def fixture():
    common=dict(countdown=54,tune=0,effect=0,lastTune=255,musicEnabled=0,song=-1,musicActive=0,pending=-1,day=1,difficulty=0,center=0,windowY=112,stat=1,lcdc=195,scrollY=0,lyc=23)
    names=['wait','ready','tunePositioned','tuneRendered','effectPositioned','numbersReady','leftReturned','rightReturned','downReturned','upReturned','bReturned','aReturned','exitDecision','end']
    points=[dict(common,name=name,cycles=1000 if i==0 else 10000+i*1000,tick=65535 if i==0 else 0,held=0 if i==0 else 8,pressed=0 if i==0 else 8) for i,name in enumerate(names)]
    service=dict(kind='vblank',start=2000,tick=65535,countdown=54,held=8,pressed=8,musicEnabled=0,voiceStates=[dict(active=0) for _ in range(6)],phases={},returnAddress=0x261d)
    stamp=2000
    for phase,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,116,240,64,68,60)):
        stamp+=cost;service['phases'][phase]=stamp
    service['end']=stamp+120
    writes=[dict(cycle=14000+i*100,address=a,value=1) for i,a in enumerate((0x9e70,0x9e71,0x9eb0,0x9eb1))]
    before=[19]*2048;maps=list(before)
    for p in writes:maps[p['address']-0x9800]=p['value']
    parent=dict(controlMemorySha256='parent',points=[dict(points[0])],maps=before,objects=[0]*256)
    data=dict(version=1,inputCase='stop-restart',parentControlMemorySha256='parent',points=points,interrupts=[service],rawSongs=[7]*len(points),rawMusicFlags=[[255]*4 for _ in points],rawPending=[255]*len(points),reference=dict(titleStorageObserver='direct-vram-title-v1'),storageReadOwner='direct-vram-title-v1',beforeMaps=before,maps=maps,beforeObjects=[0]*256,objects=[0]*256,writes=writes,rasters=[])
    return data,parent

class MusicEvidence(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete_and_tick_wrap(self):self.assertEqual(len(analyze(self.data,self.parent)),1)
    def test_parent(self):self.data['parentControlMemorySha256']='other';self.reject()
    def test_initial_selectors(self):self.data['points'][0]['lastTune']=0;self.reject()
    def test_order(self):self.data['points'][6]['name']='rightReturned';self.reject()
    def test_fresh_input(self):self.data['interrupts'][0]['pressed']=0;self.reject()
    def test_volume_slots(self):self.data['interrupts'][0]['voiceStates'].pop();self.reject()
    def test_display_owner(self):self.data['interrupts'][0]['phases']['bookkeeping']+=4;self.reject()
    def test_raw_count(self):self.data['rawMusicFlags'].pop();self.reject()
    def test_disabled_payload_retained(self):before=copy.deepcopy(self.data);analyze(self.data,self.parent);self.assertEqual(self.data,before)
    def test_disabled_active_projection(self):self.data['points'][-1]['musicActive']=1;self.reject()
    def test_disabled_song_projection(self):self.data['points'][-1]['song']=7;self.reject()
    def test_pending_projection(self):self.data['points'][-1]['pending']=0;self.reject()
    def test_range(self):self.data['points'][-1]['tune']=14;self.reject()
    def test_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_observer(self):self.data['reference']={};self.reject()
    def test_changed_image(self):self.data['maps'][0]=0;self.reject()
    def test_glyph_order(self):self.data['writes'][0]['address']=0x9e71;self.reject()
    def test_zero_high_nibble(self):self.data['writes'][0]['value']=2;self.reject()
    def test_objects(self):self.data['objects'][0]=1;self.reject()
    def test_tick(self):self.data['points'][-1]['tick']=1;self.reject()
    def test_early_exit(self):self.data['points'][-1]['pressed']=0;self.reject()
    def test_no_invented_selection(self):self.data['points'][6]['tune']=13;self.reject()
    def test_all_tunes_required(self):self.data['inputCase']='tunes';self.reject()
    def test_all_effects_required(self):self.data['inputCase']='effects';self.reject()
    def test_completed_restart_required(self):self.data['inputCase']='completed';self.reject()

class MusicControls(unittest.TestCase):
    def setUp(self):
        self.events=[['tick',2,True]];self.changed=self.events+tail('navigation');self.parent=dict(controlMemorySha256='parent',romSha256='rom');self.child=dict(inputCase='navigation',parentControlMemorySha256='parent',parentEventsSha256=event_sha(self.events),setupSha256='setup',romSha256='rom',controlDifferences=[],prefixControlHashes=['parent']*2,unhookedControlHashes=['child']*2,controlMemorySha256='child')
    def check(self):attachment(self.parent,self.child,self.events,self.changed,'setup')
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_complete(self):self.check()
    def test_all_cases_have_exit(self):
        for case in CASES:self.assertIn(['press','start'],tail(case))
    def test_case_domain(self):
        with self.assertRaises(ValueError):tail('other')
    def test_parent(self):self.child['parentControlMemorySha256']='other';self.reject()
    def test_setup(self):self.child['setupSha256']='other';self.reject()
    def test_rom(self):self.child['romSha256']='other';self.reject()
    def test_observed_change(self):self.child['controlDifferences']=[1];self.reject()
    def test_prefix_repetition(self):self.child['prefixControlHashes'].pop();self.reject()
    def test_full_repetition(self):self.child['unhookedControlHashes'][1]='other';self.reject()
    def test_changed_tail(self):self.changed[-1]=['tick',11,True];self.reject()
    def test_changed_events(self):self.child['parentEventsSha256']='other';self.reject()

class MusicBatch(unittest.TestCase):
    def cases(self):return [argparse.Namespace(native_base=Path('test'+str(i)),test_out=Path('out'+str(i)),test_control=Path('control'+str(i)),return_screen_base=Path('parent'),feedback_base=Path('feedback')) for i in range(2)]
    def test_parent_once_all_children(self):
        with patch('password_return_reference.compare') as parent,patch('music_test_reference.compare') as children:
            compare_many(self.cases());self.assertEqual(parent.call_count,1);self.assertEqual(parent.call_args.args[0].native_base,Path('parent'));self.assertEqual(children.call_count,2)
    def test_mixed_ancestry(self):
        cases=self.cases();cases[1].return_screen_base=Path('other')
        with self.assertRaises(ValueError):compare_many(cases)
    def test_empty(self):
        with self.assertRaises(ValueError):compare_many([])

if __name__=='__main__':unittest.main()
