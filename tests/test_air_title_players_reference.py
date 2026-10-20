"""Synthetic provenance, complete presentation, cursor and input integrity."""
import argparse,copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_players_reference import analyze,attachment,tail,CASES,compare_many
from air_title_actions_reference import event_sha

def fixture():
    names=['begin']+['closeWait','closeReady','centerStored']*40+['clearEntry','closeReturned','clearEntry','clearReturned','textReturned']+['openWait','openReady','openStored']*40+['wait','ready','cursorEntry','cursorReturned','toggleReturned','end']
    points=[];services=[];tick=65520;now=1000;closed=cleared=opened=waits=0;center=0;y=112;held=pressed=4
    for name in names:
        previous=now;now+=10000
        if name in ('closeReady','closeReturned','openReady','ready'):
            held=8 if name=='ready' else 0;pressed=8 if name=='ready' else 0;stamp=previous+1000;r=dict(kind='vblank',start=stamp,tick=tick,countdown=54,held=held,pressed=pressed,musicEnabled=1,phases={},voiceStates=[dict(active=0) for _ in range(6)],returnAddress=0x261d)
            for phase,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,116,240,64,68,60)):stamp+=cost;r['phases'][phase]=stamp
            r['end']=stamp+120;services.append(r);tick=(tick+1)&65535
        if name=='centerStored':closed+=1;center=(center-2)&255;y-=1
        if name in ('closeReturned','clearReturned'):cleared+=1
        if name=='openStored':opened+=1;center=(center+2)&255;y+=1
        if name=='ready':waits+=1
        points.append(dict(name=name,cycles=now,tick=tick,countdown=54,center=center,windowY=y,closed=closed,cleared=cleared,opened=opened,waits=waits,players=0,route=2 if name=='end' else 0,song=1,musicEnabled=1,held=held,pressed=pressed,stat=1,lcdc=195,scrollY=0,lyc=23))
    addresses=[0x9dc0+i for _ in range(2) for i in range(320)]+[0x9c00+32*y+x+i for x,y,n in ((3,15,14),(3,18,15),(3,20,15)) for i in range(n)]
    writes=[dict(cycle=1000000+i*100,address=a,value=int(i>=640)) for i,a in enumerate(addresses)]
    writes+=[dict(cycle=2000000+i*100,address=a,value=v) for i,(a,v) in enumerate(zip(range(0xc100,0xc104),(72,24,254+((tick&16)>>4),128)))]
    before=[19]*2048;maps=list(before);objects=[0]*256
    for w in writes:
        if w['address']>=0xc100:objects[w['address']-0xc100]=w['value']
        else:maps[w['address']-0x9800]=w['value']
    end=dict(points[0],route=3,inputHeld=4,inputPressed=4);parent=dict(inputCase='select',controlMemorySha256='parent',points=[end],maps=before)
    data=dict(version=1,inputCase='one-start',parentControlMemorySha256='parent',points=points,interrupts=services,reference=dict(titleStorageObserver='direct-vram-title-v1'),storageReadOwner='direct-vram-title-v1',beforeMaps=before,maps=maps,beforeObjects=[0]*256,objects=objects,writes=writes,rasters=[])
    return data,parent

class PlayerEvidence(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete(self):self.assertEqual(len(analyze(self.data,self.parent)),82)
    def test_parent(self):self.data['parentControlMemorySha256']='other';self.reject()
    def test_parent_choice(self):self.parent['inputCase']='start';self.reject()
    def test_parent_route(self):self.parent['points'][0]['route']=2;self.reject()
    def test_geometry(self):self.data['points'][3]['windowY']=112;self.reject()
    def test_missing_point(self):self.data['points'].pop(5);self.reject()
    def test_missing_loop(self):self.data['points']=self.data['points'][:246];self.reject()
    def test_truncated_loop(self):self.data['points'].pop(-2);self.reject()
    def test_selection(self):self.data['points'][-1]['players']=1;self.reject()
    def test_route(self):self.data['points'][-1]['route']=1;self.reject()
    def test_tick(self):self.data['points'][-1]['tick']+=1;self.reject()
    def test_music(self):self.data['points'][-1]['song']=7;self.reject()
    def test_service(self):self.data['interrupts'].pop();self.reject()
    def test_input(self):self.data['interrupts'][0]['pressed']=4;self.reject()
    def test_voice_slots(self):self.data['interrupts'][0]['voiceStates'].pop();self.reject()
    def test_object_provenance(self):self.data['beforeObjects'][10]=1;self.reject()
    def test_cursor(self):self.data['objects'][0]=88;self.reject()
    def test_blink(self):self.data['writes'][-2]['value']^=1;self.reject()
    def test_cursor_order(self):self.data['writes'][-1]['address']=0xc102;self.reject()
    def test_map(self):self.data['maps'][0]=0;self.reject()
    def test_missing_text(self):self.data['writes'].pop(670);self.reject()
    def test_clear(self):self.data['writes'][0]['value']=1;self.reject()
    def test_storage_owner(self):self.data['storageReadOwner']='cpu';self.reject()

class PlayerControls(unittest.TestCase):
    def setUp(self):
        self.events=[['tick',1,True]];self.parent=dict(inputCase='select',controlMemorySha256='parent',romSha256='rom');self.child=dict(inputCase='one-start',parentControlMemorySha256='parent',parentEventsSha256=event_sha(self.events),setupSha256='setup',romSha256='rom',controlMemorySha256='child',controlDifferences=[],prefixControlHashes=['parent']*2,unhookedControlHashes=['child']*2);self.changed=self.events+tail('one-start')
    def check(self):attachment(self.parent,self.child,self.events,self.changed,'setup')
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_complete(self):self.check()
    def test_all_cases_exit(self):
        for case in CASES:self.assertTrue(any(e[0]=='press' and e[1] in ('a','b','start') for e in tail(case)))
    def test_case_domain(self):
        with self.assertRaises(ValueError):tail('other')
    def test_parent_action(self):self.parent['inputCase']='start';self.reject()
    def test_repeated_prefix(self):self.child['prefixControlHashes'].pop();self.reject()
    def test_repeated_full(self):self.child['unhookedControlHashes'][1]='other';self.reject()
    def test_mutated_tail(self):self.changed.pop();self.reject()
    def test_setup(self):self.child['setupSha256']='other';self.reject()

class PlayerBatch(unittest.TestCase):
    def cases(self):return [argparse.Namespace(native_base=Path('player'+str(i)),players_out=Path('ref'+str(i)),players_control=Path('control'+str(i)),actions_base=Path('parent')) for i in range(2)]
    def test_one_parent_all_children(self):
        with patch('air_title_actions_reference.compare') as parent,patch('air_title_players_reference.compare') as child:
            compare_many(self.cases());self.assertEqual(parent.call_count,1);self.assertEqual(parent.call_args.args[0].native_base,Path('parent'));self.assertEqual(child.call_count,2)
    def test_mixed(self):
        cases=self.cases();cases[1].actions_base=Path('other')
        with self.assertRaises(ValueError):compare_many(cases)
    def test_empty(self):
        with self.assertRaises(ValueError):compare_many([])

if __name__=='__main__':unittest.main()
