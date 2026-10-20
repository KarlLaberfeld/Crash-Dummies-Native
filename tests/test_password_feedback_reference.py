"""Synthetic feedback provenance and explicit stopped-driver exclusions."""
import sys,unittest,copy,argparse
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from password_feedback_reference import analyze,logical_voice_projection,attachment,TAIL,event_sha,compare_many

def fixture():
    names=['begin','finalWait','waitReturned','audioStopped','objectsCleared','validate']+[name for i in range(11) for name in (('check',) if i==10 else ('check','compareReturned'))]+['rejected']+['closeWait','closeReady','centerStored']*40+['clearEntry','closeReturned','clearEntry','clearReturned','textReturned']+['openWait','openReady','openStored']*40+['opened']+['holdWait','holdReady']*60+['end']
    points=[];irqs=[];rasters=[];tick=65520;candidate=-1;remaining=60;now=1000;stopped=False;held=8;center=0;y=112
    for name in names:
        previous=now;now+=10000
        if name=='audioStopped':
            now=previous+12880;start=previous+1000;irqs.append(dict(kind='stat',start=start,end=start+460,returnAddress=0x36c8));rasters.extend([dict(boundary='begin',cycle=start),dict(boundary='end',cycle=start+460)]);stopped=True
        if name in ('waitReturned','closeReady','clearReturned','openReady','holdReady'):
            start=previous+4000
            for j in range(2):
                stamp=previous+1000+1000*j;irqs.append(dict(kind='stat',start=stamp,end=stamp+400,returnAddress=0x261d));rasters.extend([dict(boundary='begin',cycle=stamp),dict(boundary='end',cycle=stamp+400)])
            r=dict(kind='vblank',start=start,tick=tick,countdown=54,held=0,pressed=0,musicEnabled=int(not stopped),phases={},returnAddress=0x261d,voiceStates=[dict(active=128 if stopped and i<4 else 0) for i in range(6)])
            time=start
            for phase,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,116,240,64,68,60)):time+=cost;r['phases'][phase]=time
            r['end']=time+120;irqs.append(r);tick=(tick+1)&65535;held=0
        if name=='check':candidate+=1
        if name=='centerStored':center=(center-2)&255;y-=1
        if name=='openStored':center=(center+2)&255;y+=1
        points.append(dict(name=name,cycles=now,tick=tick,countdown=54,center=center,windowY=y,candidate=candidate,action=-1,remaining=remaining,day=1,difficulty=0,musicEnabled=int(not stopped),held=held,pressed=8 if name in ('begin','finalWait') else 0,stat=1,lcdc=0xc3,scrollY=0,lyc=23))
        if name=='holdReady':remaining-=1
    points[-1]['remaining']=0;writes=[];stamp=next(p['cycles'] for p in points if p['name']=='audioStopped')+100
    writes.extend(dict(cycle=stamp+8*i,address=0xc100+i,value=0) for i in range(160))
    for p in [p for p in points if p['name']=='clearEntry']:writes.extend(dict(cycle=p['cycles']+100+4*i,address=0x9dc0+i,value=0) for i in range(320))
    stamp=next(p['cycles'] for p in points if p['name']=='clearReturned')+100;writes.extend(dict(cycle=stamp+100*i,address=0x9e61+i,value=1) for i in range(18))
    before=[19]*2048;maps=list(before)
    for w in writes:
        if 0x9800<=w['address']<0xa000:maps[w['address']-0x9800]=w['value']
    objects=[96,56,69,128]+[0]*252;parent=dict(controlMemorySha256='parent',inputCase='submit-start',points=[dict(points[0])],maps=before,objects=objects)
    data=dict(version=1,inputCase='submit-start',parentControlMemorySha256='parent',reference=dict(titleStorageObserver='direct-vram-title-v1'),storageReadOwner='direct-vram-title-v1',points=points,interrupts=irqs,rasters=rasters,writes=writes,polls=[dict(cycle=w['cycle']-1,mode=0) for w in writes if 0x9800<=w['address']<0xa000],beforeMaps=before,maps=maps,beforeObjects=objects,objects=[0]*256)
    return data,parent

class FeedbackEvidence(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete_interrupted_reset(self):self.assertEqual(len(analyze(self.data,self.parent)),142)
    def test_parent(self):self.data['parentControlMemorySha256']='other';self.reject()
    def test_parent_cycle(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_intended_action(self):self.data['points'][-1]['action']=0;self.reject()
    def test_candidate_search(self):next(p for p in self.data['points'] if p['name']=='check')['candidate']=1;self.reject()
    def test_missing_candidate(self):self.data['points'].pop(6);self.reject()
    def test_countdown(self):self.data['points'][-1]['countdown']=53;self.reject()
    def test_audio_stop_work(self):next(p for p in self.data['points'] if p['name']=='audioStopped')['cycles']+=4;self.reject()
    def test_missing_reset_interrupt(self):
        self.data['interrupts']=[r for r in self.data['interrupts'] if r['returnAddress']!=0x36c8];self.reject()
    def test_logical_driver_not_disabled(self):next(p for p in self.data['points'] if p['name']=='audioStopped')['musicEnabled']=1;self.reject()
    def test_hold_shortcut(self):next(p for p in self.data['points'] if p['name']=='holdWait')['remaining']=59;self.reject()
    def test_final_hold(self):self.data['points'][-1]['remaining']=1;self.reject()
    def test_storage_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_storage_provenance(self):self.data['reference']={};self.reject()
    def test_parent_objects(self):self.data['beforeObjects']=list(self.data['beforeObjects']);self.data['beforeObjects'][0]=0;self.reject()
    def test_objects_not_cleared(self):self.data['objects'][0]=96;self.reject()
    def test_map(self):self.data['maps'][0]=0;self.reject()
    def test_missing_object_store(self):self.data['writes'].pop(0);self.reject()
    def test_unowned_selection(self):self.data['points'][-1]['day']=0;self.reject()
    def test_voice_count(self):next(r for r in self.data['interrupts'] if r['kind']=='vblank')['voiceStates'].pop();self.reject()
    def test_disabled_music_work(self):next(r for r in self.data['interrupts'] if r['kind']=='vblank' and not r['musicEnabled'])['phases']['restore']+=4;self.reject()
    def test_tick(self):self.data['points'][-1]['tick']-=1;self.reject()
    def test_clear_missing(self):self.data['writes'].pop(160);self.reject()
    def test_clear_changed(self):self.data['writes'][160]['value']=1;self.reject()
    def test_window_motion(self):next(p for p in self.data['points'] if p['name']=='centerStored')['center']=0;self.reject()
    def test_text_shape(self):self.data['writes'][-1]['address']+=1;self.reject()
    def test_polls_missing(self):self.data['polls'].pop();self.reject()
    def test_poll_mode(self):self.data['polls'][0]['mode']=4;self.reject()

class StoppedProjection(unittest.TestCase):
    def setUp(self):self.services=analyze(*fixture())
    def test_records_preserved(self):
        before=copy.deepcopy(self.services);logical=logical_voice_projection(self.services);self.assertEqual(self.services,before);self.assertTrue(any(v['active']&128 for p in self.services if not p['musicEnabled'] for v in p['voiceStates']));self.assertFalse(any(v['active'] for p in logical if not p['musicEnabled'] for v in p['voiceStates']))
    def test_enabled_projection_not_masked(self):
        self.services[0]['voiceStates'][0]['active']=128;self.assertEqual(logical_voice_projection(self.services)[0]['voiceStates'][0]['active'],128)
    def test_unknown_driver_rejects(self):
        self.services[0]['musicEnabled']=2
        with self.assertRaises(ValueError):logical_voice_projection(self.services)
    def test_disabled_active_work_rejects(self):
        self.services[1]['phases']['restore']+=4
        with self.assertRaises(ValueError):logical_voice_projection(self.services)

class FeedbackControls(unittest.TestCase):
    def setUp(self):
        self.events=[['tick',4,True]];self.changed=self.events+copy.deepcopy(TAIL);self.parent=dict(inputCase='submit-start',controlMemorySha256='parent',romSha256='rom');self.child=dict(inputCase='submit-start',parentControlMemorySha256='parent',parentEventsSha256=event_sha(self.events),setupSha256='setup',romSha256='rom',controlMemorySha256='child',controlDifferences=[],prefixControlHashes=['parent']*2,unhookedControlHashes=['child']*2)
    def check(self):attachment(self.parent,self.child,self.events,self.changed,'setup')
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_complete(self):self.check()
    def test_case(self):self.child['inputCase']='submit-a';self.reject()
    def test_tail(self):self.changed[-1]=['tick',199,True];self.reject()
    def test_setup(self):self.child['setupSha256']='other';self.reject()
    def test_parent(self):self.child['parentControlMemorySha256']='other';self.reject()
    def test_repetition(self):self.child['prefixControlHashes'].pop();self.reject()

class FeedbackBatch(unittest.TestCase):
    def cases(self):return [argparse.Namespace(native_base=Path('new'+str(i)),edit_base=Path('edit'+str(i)),edit_out=Path('ref'+str(i)),edit_control=Path('control'+str(i)),feedback_out=Path('feedback'+str(i)),feedback_control=Path('feedback-control'+str(i)),password_base=Path('parent')) for i in range(2)]
    def test_qualifies_every_distinct_edit_parent(self):
        with patch('password_edit_reference.compare_many') as parents,patch('password_feedback_reference.compare') as children:
            compare_many(self.cases());self.assertEqual(parents.call_count,1);self.assertEqual([p.native_base for p in parents.call_args.args[0]],[Path('edit0'),Path('edit1')]);self.assertEqual(children.call_count,2)
    def test_mixed_ancestry(self):
        cases=self.cases();cases[1].password_base=Path('other')
        with self.assertRaises(ValueError):compare_many(cases)

if __name__=='__main__':unittest.main()
