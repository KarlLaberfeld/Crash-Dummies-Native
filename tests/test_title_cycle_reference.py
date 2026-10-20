"""Synthetic carousel provenance, duration, BCD-row and wrap coverage integrity."""
import argparse,copy,sys,unittest
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from title_cycle_reference import DURATIONS,TAIL,analyze,attachment,compare_many,event_sha

@lru_cache(maxsize=1)
def fixture():
    geometry=dict(stat=1,lcdc=195,scrollY=0,lyc=23);now=1000000;tick=65000;maps=[0]*2048;groups=[]
    parent=dict(inputCase='a',controlMemorySha256='parent',maps=list(maps),points=[dict(cycles=now,tick=tick,countdown=54,inputHeld=0,inputPressed=0,index=1,route=1,**geometry)])
    for n in range(5):
      index=(n+1)%5
      for page in ((True,) if n==4 else (True,False)):
        names=['begin']
        if page:
            names+=['closeWait','closeReady','centerStored']*40+['clearEntry','closeReturned','clearEntry','clearReturned','pageCall','pageEntry']+(['rowReady']*10+['copyReturned'] if index==0 else ['scoreRow']*8 if index==2 else [])+['pageReturn','pageReturned']+['openWait','openReady','openStored']*40
            count=82
        else:names+=['wait','ready','unlockEntry','unlockReturned','startDecision','selectDecision','actionDecision','timer','timerStored']*DURATIONS[index]+['advance','pageStored']+(['wrapStored'] if index==4 else []);count=DURATIONS[index]
        names+=['end'];group=dict(name=str(n)+('.page' if page else '.idle'),page=index,points=[],interrupts=[],writes=[],polls=[],rasters=[],beforeMaps=list(maps),maps=list(maps),beforeObjects=[0]*256,objects=[0]*256)
        for i in range(count):
            start=now+10000+20000*i;irq=dict(kind='vblank',start=start,returnAddress=0x261d,tick=(tick+i)&65535,countdown=54,held=0,pressed=0,musicEnabled=1,voiceStates=[dict(active=0) for _ in range(6)],phases={});stamp=start
            for name,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,116,240,64,68,60)):stamp+=cost;irq['phases'][name]=stamp
            irq['end']=stamp+120;group['interrupts'].append(irq)
        for i,name in enumerate(names):
            time=now+i*20000;finished=sum(r['end']+16<=time for r in group['interrupts']);selector=(index+1)%5 if name=='end' and not page else index
            point=dict(name=name,cycles=time,index=selector,tick=(tick+finished)&65535,countdown=54,inputHeld=0,inputPressed=0,**geometry)
            if page:point.update(center=0,closed=40,cleared=2,opened=40,rows=10 if index==0 else 0,windowY=112)
            else:point.update(remaining=0 if name=='end' else DURATIONS[index],waits=DURATIONS[index] if name=='end' else 0,pattern=0,route=1 if name=='end' else 0)
            group['points'].append(point)
        if page:group['writes']=[dict(cycle=now+4*(i+1),address=0x9dc0+i%320,value=0) for i in range(640)]
        else:group['writes']=[dict(cycle=group['points'][-1]['cycles']-16+4*i,address=0xc03e,value=value) for i,value in enumerate([5,0] if index==4 else [index+1])]
        now=group['points'][-1]['cycles'];tick=group['points'][-1]['tick'];groups.append(group)
    return dict(version=1,inputCase='carousel',parentInputCase='a',parentControlMemorySha256='parent',storageReadOwner='direct-vram-title-v1',reference=dict(titleStorageObserver='direct-vram-title-v1'),groups=groups),parent

class CarouselIntegrity(unittest.TestCase):
    def setUp(self):self.data,self.parent=copy.deepcopy(fixture())
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete_five_page_durations_wrap_and_rollover(self):self.assertEqual(len(analyze(self.data,self.parent)),3290)
    def test_parent_hash(self):self.data['parentControlMemorySha256']='changed';self.reject()
    def test_parent_action(self):self.data['parentInputCase']='b';self.reject()
    def test_start_route_not_advance(self):self.parent['points'][-1]['route']=2;self.reject()
    def test_parent_selector(self):self.parent['points'][-1]['index']=0;self.reject()
    def test_direct_storage_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_direct_storage_backend(self):self.data['reference']={};self.reject()
    def test_missing_segment(self):self.data['groups'].pop();self.reject()
    def test_wrong_page_order(self):self.data['groups'][0]['page']=2;self.reject()
    def test_missing_close_wait(self):self.data['groups'][0]['points'].pop(1);self.reject()
    def test_incomplete_reopening(self):self.data['groups'][0]['points'][-1]['opened']=39;self.reject()
    def test_incomplete_clear(self):self.data['groups'][0]['writes'].pop(0);self.reject()
    def test_wrong_clear_destination(self):self.data['groups'][0]['writes'][0]['address']+=1;self.reject()
    def test_wrong_clear_value(self):self.data['groups'][0]['writes'][0]['value']=1;self.reject()
    def test_unrelated_map(self):self.data['groups'][0]['maps'][2047]=1;self.reject()
    def test_objects(self):self.data['groups'][0]['objects'][0]=1;self.reject()
    def test_parent_map(self):self.data['groups'][0]['beforeMaps'][2047]=1;self.reject()
    def test_boundary_input(self):self.data['groups'][0]['points'][-1]['inputPressed']=8;self.reject()
    def test_boundary_tick(self):self.data['groups'][0]['points'][-1]['tick']+=1;self.reject()
    def test_missing_music_voice(self):self.data['groups'][0]['interrupts'][0]['voiceStates'].pop();self.reject()
    def test_wrong_display_work(self):self.data['groups'][0]['interrupts'][0]['phases']['bookkeeping']+=4;self.reject()
    def test_incomplete_high_score_rows(self):self.data['groups'][2]['points']=[p for p in self.data['groups'][2]['points'] if p['name']!='scoreRow'];self.reject()
    def test_wrong_long_page_duration(self):self.data['groups'][3]['points'][-1]['waits']=480;self.reject()
    def test_missing_wrap_store(self):self.data['groups'][7]['writes'].pop();self.reject()

class CarouselControls(unittest.TestCase):
    def setUp(self):
        self.parent=dict(controlMemorySha256='parent',romSha256='rom');self.events=[['tick',40,True]];self.changed=self.events+TAIL
        self.child=dict(inputCase='carousel',parentControlMemorySha256='parent',parentEventsSha256=event_sha(self.events),setupSha256='setup',romSha256='rom',controlDifferences=[],prefixControlHashes=['parent']*2,unhookedControlHashes=['child']*2,controlMemorySha256='child')
    def check(self):attachment(self.parent,self.child,self.events,self.changed,'setup')
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_complete(self):self.check()
    def test_changed_tail(self):self.changed=self.events+[['tick',3999,True]];self.reject()
    def test_changed_prefix(self):self.changed=[['tick',39,True]]+TAIL;self.reject()
    def test_setup(self):self.child['setupSha256']='other';self.reject()
    def test_prefix_hash(self):self.child['prefixControlHashes'][1]='other';self.reject()
    def test_full_hash(self):self.child['unhookedControlHashes'][1]='other';self.reject()
    def test_empty_batch(self):
        with self.assertRaises(ValueError):compare_many([])
    def test_mixed_ancestors(self):
        with self.assertRaises(ValueError):compare_many([argparse.Namespace(startup='a'),argparse.Namespace(startup='b')])
    def test_shared_page_qualified_once(self):
        first=argparse.Namespace(native_base=Path('child-a'),actions_base=Path('a'),case_control=Path('control-a'),actions_out=Path('a-out'),cycle_out=Path('cycle'),cycle_control=Path('cycle-control'),startup=Path('startup'));second=copy.copy(first);second.native_base=Path('child-b');second.actions_base=Path('b')
        with patch('air_title_page_reference.compare') as page,patch('air_title_actions_reference.compare') as action,patch('title_cycle_reference.compare') as child:
            compare_many([first,second]);self.assertEqual(page.call_count,1);self.assertEqual(action.call_count,2);self.assertTrue(action.call_args.kwargs['_parent_qualified']);self.assertEqual(child.call_count,2)
if __name__=='__main__':unittest.main()
