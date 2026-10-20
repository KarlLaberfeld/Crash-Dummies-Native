"""Input-only forks and bounded fresh-action evidence must remain attached."""
import sys,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_actions_reference import ACTIONS,IRQ_PHASES,analyze,attachment,event_sha,tail
from air_title_menu_reference import inherited_title_epoch


def recording(key='start',first=0):
    names=['begin']+['wait','ready','unlockEntry','unlockReturned','startDecision','selectDecision','actionDecision','timer','timerStored']*2
    names+=['wait','ready','unlockEntry','unlockReturned','startDecision']
    if key!='start':names+=['selectDecision']
    if key in ('a','b'):names+=['actionDecision','advance','pageStored']
    names+=['end'];points=[];waits=0;remaining=480;index=0
    for i,name in enumerate(names):
        if name=='ready':waits+=1
        if name=='timerStored':remaining-=1
        if name=='pageStored':index=1
        current=33 if not waits else first if waits==1 else 0 if waits==2 else ACTIONS[key]
        points.append(dict(name=name,cycles=100+1000*i,waits=waits,remaining=remaining,index=index,pattern=0,countdown=54,tick=(65534+waits)&65535,inputHeld=current,inputPressed=ACTIONS[key] if waits==3 else 0,route=0 if name!='end' else 2 if key=='start' else 3 if key=='select' else 1,stat=1,lcdc=0xc3,scrollY=0,lyc=23))
    maps=[19]*2048;parent=dict(controlMemorySha256='parent',points=[dict(points[0])],maps=maps[:]);irqs=[];rasters=[]
    for i in range(3):
        start=1000+5000*i
        for j in range(2):
            t=start+200*j;irqs.append(dict(kind='stat',start=t,end=t+100));rasters.extend([dict(boundary='begin',cycle=t),dict(boundary='end',cycle=t+100)])
        t=start+400;held=first if i==0 else 0 if i==1 else ACTIONS[key]
        irqs.append(dict(kind='vblank',start=t,end=t+90,held=held,pressed=ACTIONS[key] if i==2 else 0,tick=(65534+i)&65535,countdown=54,phases={name:t+10*(j+1) for j,name in enumerate(IRQ_PHASES.values())}))
    stores=[(0xff40,0xfb),(0xff42,88),(0xff42,88),(0xff45,103),(0xc099,2),(0xff40,0xc3),(0xff42,0),(0xff45,23),(0xc099,1)]*3+[(0xc0b5,0x15),(0xc0b6,0x2b)]+([(0xc03e,1)] if key in ('a','b') else [])
    data=dict(inputCase=key,storageReadOwner='direct-vram-title-v1',reference=dict(titleStorageObserver='direct-vram-title-v1'),parentControlMemorySha256='parent',points=points,writes=[dict(cycle=200+4*i,address=a,value=v) for i,(a,v) in enumerate(stores)],interrupts=irqs,rasters=rasters,beforeMaps=maps[:],maps=maps[:])
    return data,parent


class ActionEvidence(unittest.TestCase):
    def setUp(self):self.data,self.parent=recording()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_all_actions_and_partial_releases(self):
        for key in ACTIONS:
            for first in (0,1,32,33):
                with self.subTest(key=key,first=first):self.assertEqual(len(analyze(*recording(key,first))),3)
    def test_no_unknown_case(self):self.data['inputCase']='up';self.reject()
    def test_direct_storage_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_observer_identity(self):self.data['reference']={};self.reject()
    def test_parent_control_hash(self):self.data['parentControlMemorySha256']='wrong';self.reject()
    def test_parent_endpoint(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_no_detached_maps(self):self.parent['maps'][0]=0;self.reject()
    def test_no_map_mutation(self):self.data['maps'][0]=0;self.reject()
    def test_complete_decision_order(self):self.data['points'].pop(4);self.reject()
    def test_tick_wrap(self):self.data['points'][-1]['tick']-=1;self.reject()
    def test_frozen_countdown(self):self.data['points'][-1]['countdown']=53;self.reject()
    def test_no_action_duration_decrement(self):self.data['points'][-1]['remaining']=477;self.reject()
    def test_correct_route(self):self.data['points'][-1]['route']=1;self.reject()
    def test_empty_unlock_selector(self):self.data['points'][15]['pattern']=1;self.reject()
    def test_both_mismatch_stores(self):self.data['writes'].pop();self.reject()
    def test_reset_stores_not_fitted_values(self):self.data['writes'][-1]['value']=0;self.reject()
    def test_no_new_release_edge(self):self.data['interrupts'][2]['held']=64;self.reject()
    def test_second_release_complete(self):self.data['interrupts'][5]['held']=32;self.reject()
    def test_original_input_edges(self):self.data['interrupts'][-1]['pressed']=0;self.reject()
    def test_no_incomplete_vectors(self):self.data['interrupts'].pop();self.reject()
    def test_no_overlapping_vectors(self):self.data['interrupts'][1]['start']=self.data['interrupts'][0]['end'];self.reject()
    def test_no_escaped_vector(self):self.data['interrupts'][-1]['end']=self.data['points'][-1]['cycles'];self.reject()
    def test_all_raster_boundaries(self):self.data['rasters'].pop();self.reject()


class ActionFork(unittest.TestCase):
    def setUp(self):
        self.events=[['press','a'],['tick',1000,True]];self.parent=dict(romSha256='rom',controlMemorySha256='original')
        self.child=dict(inputCase='start',splitFrames=400,parentControlMemorySha256='original',parentEventsSha256=event_sha(self.events),setupSha256='setup',romSha256='rom',controlMemorySha256='child',controlDifferences=[],unhookedControlHashes=['child']*2,prefixMemorySha256='prefix',prefixControlHashes=['prefix']*2)
        self.changed=self.events[:-1]+[['tick',400,True]]+tail('start')
    def accept(self):return attachment(self.parent,self.child,self.events,self.changed,'setup')
    def reject(self):
        with self.assertRaises(ValueError):self.accept()
    def test_exact_input_only_prefix_and_tail(self):self.assertEqual(self.accept(),self.changed[:2])
    def test_no_earlier_button_edit(self):self.changed[0]=['press','b'];self.reject()
    def test_no_earlier_tick_edit(self):self.changed[1][1]=399;self.reject()
    def test_no_unrecorded_tail(self):self.changed.append(['tick',1,True]);self.reject()
    def test_no_action_substitution(self):self.child['inputCase']='select';self.reject()
    def test_no_setup_change(self):self.child['setupSha256']='different';self.reject()
    def test_parent_events_checked(self):self.child['parentEventsSha256']='different';self.reject()
    def test_original_control_checked(self):self.child['parentControlMemorySha256']='different';self.reject()
    def test_two_unhooked_repetitions(self):self.child['unhookedControlHashes'].pop();self.reject()
    def test_identical_prefix_hashes(self):self.child['prefixControlHashes'][0]='different';self.reject()
    def test_only_partial_last_tick_split(self):self.child['splitFrames']=1000;self.reject()


class InheritedEpoch(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[1]/'build'/'test-temp';root.mkdir(parents=True,exist_ok=True)
        self.folder=root/uuid.uuid4().hex;self.folder.mkdir();self.base=self.folder/'native.csv'
        self.page=Path(str(self.base)+'.fifth.title-page.summary.csv');self.menu=Path(str(self.base)+'.fifth.title-menu.summary.csv')
        self.page.write_text('lcdEpoch\n123\n');self.menu.write_text('lcdEpoch\n456\n')
    def tearDown(self):
        for p in self.folder.iterdir():p.unlink()
        self.folder.rmdir()
    def test_reads_parent_not_current_owner(self):self.assertEqual(inherited_title_epoch(self.base),123)
    def test_current_summary_cannot_supply_epoch(self):self.page.unlink();self.assertRaises(FileNotFoundError,inherited_title_epoch,self.base)
    def test_no_empty_parent(self):self.page.write_text('lcdEpoch\n');self.assertRaises(ValueError,inherited_title_epoch,self.base)
    def test_no_duplicate_parent(self):self.page.write_text('lcdEpoch\n123\n789\n');self.assertRaises(ValueError,inherited_title_epoch,self.base)
    def test_no_negative_parent(self):self.page.write_text('lcdEpoch\n-1\n');self.assertRaises(ValueError,inherited_title_epoch,self.base)


if __name__=='__main__':unittest.main()
