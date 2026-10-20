"""Synthetic return provenance and narrowly scoped scratch exclusions."""
import sys,copy,argparse,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from password_return_reference import analyze,boundary_projection,attachment,TAIL,compare_many
from air_title_actions_reference import event_sha

def fixture(target):
    names=['begin']+(['titleWait','titleWaitReturned','titleMusicReady'] if target==1 else [])+['closeCall']+['closeWait','closeReady','centerStored']*40+['clearEntry','closeReturned','clearEntry','clearReturned']
    names+=(['pageCall','pageEntry','rectangleEntry']+['rowReady']*10+['copyReturned','pageReturn','pageReturned']) if target==1 else ['textReturned']+(['passwordWaitReturned','passwordMusicReady'] if target==2 else [])
    names+=['openWait','openReady','openStored']*40+([] if target==1 else ['openReturned'])+['end']
    points=[];raw=[];irqs=[];tick=65520;center=0;y=112;rows=0;enabled=False;cursor=7;now=1000
    for name in names:
        previous=now;now+=10000
        if target==3 and name=='closeCall':now=previous
        if name in ('titleWaitReturned','closeReady','clearReturned','passwordWaitReturned','openReady') or target==1 and name=='copyReturned':
            start=previous+4000;r=dict(kind='vblank',start=start,tick=tick,countdown=54,held=0,pressed=0,musicEnabled=int(enabled),phases={},voiceStates=[dict(active=0) for _ in range(6)],returnAddress=0x261d);time=start
            for phase,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,116,240,64,68,60)):time+=cost;r['phases'][phase]=time
            r['end']=time+120;irqs.append(r);tick=(tick+1)&65535
        if name in ('titleMusicReady','passwordMusicReady'):enabled=True
        if name=='centerStored':center=(center-2)&255;y-=1
        if name=='openStored':center=(center+2)&255;y+=1
        if name=='rowReady':rows+=1;cursor=7
        if name=='rectangleEntry':cursor=14
        if name=='end' and target!=1:cursor=0
        points.append(dict(name=name,cycles=now,target=target,tick=tick,countdown=54,center=center,windowY=y,rows=rows,day=1,difficulty=0,musicEnabled=int(enabled),song=(1 if target==1 else 7) if enabled else -1,held=0,pressed=0,cursor=cursor,**{'digit'+str(i):0 for i in range(8)},stat=1,lcdc=0xc3,scrollY=0,lyc=23));raw.append(1 if enabled and target==1 else 7)
    writes=[]
    for p in [p for p in points if p['name']=='clearEntry']:writes.extend(dict(cycle=p['cycles']+100+4*i,address=0x9dc0+i,value=0) for i in range(320))
    if target==1:
        for row,p in enumerate([p for p in points if p['name']=='rowReady']):writes.extend(dict(cycle=p['cycles']-500+4*i,address=0x9dc0+32*row+i,value=i+1) for i in range(20))
    else:
        stamp=next(p['cycles'] for p in points if p['name']=='clearReturned')+100
        for x,y,length in (((5,16,10),(3,19,14),(6,21,8)) if target==2 else ((5,16,10),(2,19,16),(2,21,16))):
            for i in range(length):writes.append(dict(cycle=stamp,address=0x9c00+32*y+x+i,value=i+1));stamp+=100
    before=[19]*2048;maps=list(before)
    for w in writes:maps[w['address']-0x9800]=w['value']
    case={1:'submit-start',2:'submit-a',3:'valid-9'}[target]
    parent=dict(inputCase=case,controlMemorySha256='parent',points=[dict(points[0],action=9 if target==3 else -1)],maps=before,objects=[0]*256)
    data=dict(version=1,inputCase=case,parentControlMemorySha256='parent',target=target,points=points,rawSongs=raw,interrupts=irqs,rasters=[],writes=writes,polls=[],reference=dict(titleStorageObserver='direct-vram-title-v1'),storageReadOwner='direct-vram-title-v1',beforeMaps=before,maps=maps,beforeObjects=[0]*256,objects=[0]*256,endTestTune=0,endTestEffect=0,endTestLast=255)
    return data,parent

class ReturnEvidence(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture(1)
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_all_destinations(self):
        for target,count in ((1,83),(2,82),(3,81)):self.assertEqual(len(analyze(*fixture(target))),count)
    def test_parent(self):self.data['parentControlMemorySha256']='other';self.reject()
    def test_parent_clock(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_destination(self):self.data['target']=2;self.reject()
    def test_missing_step(self):self.data['points'].pop(5);self.reject()
    def test_selection_retained(self):self.data['points'][-1]['day']=0;self.reject()
    def test_countdown(self):self.data['points'][-1]['countdown']=53;self.reject()
    def test_storage_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_storage_provenance(self):self.data['reference']={};self.reject()
    def test_map(self):self.data['maps'][0]=0;self.reject()
    def test_objects(self):self.data['objects'][0]=96;self.reject()
    def test_missing_clear(self):self.data['writes'].pop(0);self.reject()
    def test_motion(self):next(p for p in self.data['points'] if p['name']=='centerStored')['windowY']=112;self.reject()
    def test_service_extent(self):self.data['interrupts'].pop();self.reject()
    def test_voices(self):self.data['interrupts'][0]['voiceStates'].pop();self.reject()
    def test_tick(self):self.data['points'][-1]['tick']-=1;self.reject()
    def test_raw_song_count(self):self.data['rawSongs'].pop();self.reject()
    def test_active_song_projection(self):self.data['rawSongs'][-1]=7;self.reject()
    def test_final_song(self):self.data['points'][-1]['song']=7;self.reject()
    def test_password_reset(self):self.data,self.parent=fixture(2);self.data['points'][-1]['digit0']=1;self.reject()
    def test_music_test_initialized(self):self.data,self.parent=fixture(3);self.data['endTestLast']=0;self.reject()

class ScratchProjection(unittest.TestCase):
    def test_raw_observations_retained(self):
        data,_=fixture(1);before=copy.deepcopy(data);rows=boundary_projection(data);self.assertEqual(data,before)
        index=next(i for i,p in enumerate(data['points']) if p['name']=='rectangleEntry');self.assertEqual(rows[index-1]['cursor'],7);self.assertNotIn('cursor',rows[index]);self.assertIn('tick',rows[index]);self.assertIn('digit0',rows[index]);self.assertEqual(data['points'][index]['cursor'],14)
    def test_active_cursor_never_excluded(self):
        for target in (2,3):
            data,_=fixture(target);rows=boundary_projection(data);self.assertTrue(all('cursor' in p for p in rows));self.assertEqual(rows[-1]['cursor'],0)

class ReturnControls(unittest.TestCase):
    def setUp(self):
        self.events=[['tick',4,True]];self.changed=self.events+copy.deepcopy(TAIL);self.parent=dict(inputCase='submit-start',controlMemorySha256='parent',romSha256='rom');self.child=dict(inputCase='submit-start',parentControlMemorySha256='parent',parentEventsSha256=event_sha(self.events),setupSha256='setup',romSha256='rom',controlMemorySha256='child',controlDifferences=[],prefixControlHashes=['parent']*2,unhookedControlHashes=['child']*2)
    def check(self):attachment(self.parent,self.child,self.events,self.changed,'setup')
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_complete(self):self.check()
    def test_correct_extension(self):self.changed[-1]=['tick',200,True];self.reject()
    def test_prefix(self):self.changed[0]=['tick',3,True];self.reject()
    def test_setup(self):self.child['setupSha256']='other';self.reject()
    def test_case(self):self.child['inputCase']='other';self.reject()
    def test_repetition(self):self.child['prefixControlHashes'].pop();self.reject()

class ReturnBatch(unittest.TestCase):
    def cases(self):return [argparse.Namespace(native_base=Path('new'+str(i)),feedback_base=Path('feedback'+str(i)),edit_base=Path('edit'+str(i)),edit_out=Path('ref'+str(i)),edit_control=Path('control'+str(i)),feedback_out=Path('feedback-ref'+str(i)),feedback_control=Path('feedback-control'+str(i)),return_screen_out=Path('return'+str(i)),return_screen_control=Path('return-control'+str(i)),password_base=Path('parent')) for i in range(2)]
    def test_each_feedback_parent_qualified(self):
        with patch('password_feedback_reference.compare_many') as parents,patch('password_return_reference.compare') as children:
            compare_many(self.cases());self.assertEqual([p.native_base for p in parents.call_args.args[0]],[Path('feedback0'),Path('feedback1')]);self.assertEqual(children.call_count,2)
    def test_mixed_parent(self):
        cases=self.cases();cases[1].password_base=Path('other')
        with self.assertRaises(ValueError):compare_many(cases)

if __name__=='__main__':unittest.main()
