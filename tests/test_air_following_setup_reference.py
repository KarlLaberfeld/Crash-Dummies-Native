import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_following_setup_reference import analyze as prefix_analyze,compare_prefix,FIELDS
from air_following_stage_reference import analyze as stage_analyze,compare_stage,AIR,SKI
from air_following_entry_reference import analyze as entry_analyze,compare_entry,POINTS as ENTRY_POINTS,FIELDS as ENTRY_FIELDS

def prefix_fixture():
    base=dict(tick=5,countdown=73,player=0,stage=1,difficulty=0,lives=4,display=5,stat=5,lcdc=0xd1,lyc=95,pendingRequests=0,interruptEnable=3,musicEnabled=0)
    points=[]
    for i,(name,time) in enumerate(zip(('begin','lcdOffReturned','objectsCleared','stateReset','stagePointer'),(1000,1240,7436,13704,13792))):
        points.append(dict(base,name=name,cycles=time,lcdc=0xd1 if i==0 else 0x51,pendingRequests=0 if i==0 else 3))
    writes=[dict(cycles=1280+24*i,address=0xc100+i,value=0) for i in range(256)]+[dict(cycles=7516+24*i,address=0xc200+i,value=255) for i in range(256)]
    data=dict(version=1,points=points,polls=[dict(cycles=1116,ly=144),dict(cycles=1148,ly=145)],writes=writes,interrupts=[])
    native=[dict(boundary=p['name'],cycle=p['cycles']-1000,**{k:p[k] for k in FIELDS}) for p in points]
    rows=lambda source:[dict(cycle=r['cycles']-1000,**{k:v for k,v in r.items() if k!='cycles'}) for r in source]
    return [data,native,rows(data['polls']),rows(writes),[dict(end=12792,tick=5,countdown=73,pollReads=2,lcdDisabled=196,pendingRequests=3)]]

def stage_fixture(air=True):
    names=['begin',*(AIR.values() if air else SKI.values()),'stageReady','registersReady'];points=[];time=1000
    scalar=names.index('scalarsReady');sprite=names.index('spritesReady');song=names.index('stageReady')
    for i,name in enumerate(names):
        if i:time+=14052 if name=='stageReady' else 240 if name=='registersReady' else 400
        points.append(dict(name=name,cycles=time,tick=5,countdown=73,player=0,stage=1 if air else 2,difficulty=0,lives=4,
            display=5 if i<scalar else 4 if air else 6,stat=4 if name=='registersReady' else 5,lcdc=0x67 if name=='registersReady' else 0x51,
            lyc=135 if name=='registersReady' else 95,pendingRequests=3,interruptEnable=3,cameraX=0x5000,cameraY=0xae80 if air else 0,
            mapScratch=440 if air else 464,ready=int(i>=sprite),musicEnabled=int(i>=song)))
    data=dict(version=1,points=points,interrupts=[])
    native=[dict(boundary=p['name'],cycle=p['cycles']-1000,**{k:v for k,v in p.items() if k not in ('cycles','name')}) for p in points[1:]]
    summary=[dict(end=time-1000,tick=5,countdown=73,displays=100,stats=100)]
    return [data,native,summary,[dict(end=0,tick=5,countdown=73,displays=100,stats=100)]]

def entry_fixture():
    first=50000;times=[first,first+72,first+140,first+164,first+14140,first+39788,first+39876,first+39932,first+39948]
    epoch=times[7]-4;irqs=[]
    def vblank(start,tick,work,address):
        r=dict(kind='vblank',start=start,tick=tick,selector=4,display=4,returnAddress=address,ready=1,held=8,pressed=0,resetEnabled=1,resetLatched=0,effectRequest=-1,musicEnabled=1,phases={});time=start
        for name,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,work,240,64,68,60)):
            time+=cost;r['phases'][name]=time
        r['end']=time+120;return r
    irqs.append(vblank(times[8]+32,5,1508,0x03c9));start=irqs[0]['end']+36
    irqs.append(dict(kind='stat',start=start,end=start+288,selector=4,returnAddress=0x03c9))
    start=epoch+135*456+20;irqs.append(dict(kind='stat',start=start,end=start+288,selector=4,returnAddress=0x261d))
    irqs.append(vblank(epoch+144*456+20,6,1676,0x261d))
    times+=[irqs[1]['end']+16,irqs[1]['end']+28,irqs[-1]['end']+120]
    points=[]
    for i,(name,time) in enumerate(zip(ENTRY_POINTS.values(),times)):
        points.append(dict(name=name,cycles=time,tick=5 if i<9 else 6 if i<11 else 7,countdown=73,display=4,stat=4,lcdc=0x67 if i<7 else 0xe5 if i in (9,10) else 0xe7,
            lyc=135,pendingRequests=3 if i<9 else 0,cameraX=0x5000,cameraY=0xae80,mapScratch=440,randomState=0 if i==0 else 0x500,
            ready=int(i!=11),musicEnabled=1,inputHeld=8,inputPressed=0,hudCursor=2 if i==11 else 0,fadeRemaining=7 if i==11 else 8))
    data=dict(version=1,points=points,interrupts=irqs,precedingDisplays=100)
    native=[dict(boundary=p['name'],cycle=p['cycles']-first,**{k:v for k,v in p.items() if k not in ('name','cycles')}) for p in points]
    services=[dict(service=100+i,cycle=r['start']-first,tick=r['tick'],display=1508 if i==0 else 1676,effects=64,music=60,inputHeld=8,inputPressed=0) for i,r in enumerate((irqs[0],irqs[3]))]
    vectors=[dict(kind=r['kind'],vectorCycle=r['start']-first,owner=3 if i<2 else 2) for i,r in enumerate(irqs)]
    new_epoch=epoch-first
    summary=[dict(end=times[-1]-first,tick=7,countdown=73,displays=102,stats=102,lcdEpoch=new_epoch,nextStat=new_epoch+135*456+70224,
        nextVBlank=new_epoch+144*456+70224,randomState=0x500,hudCursor=2,fadeRemaining=7)]
    stage=[dict(end=0,displays=100,stats=100)]
    return [data,native,services,vectors,summary,stage]

class FollowingPrefixIntegrity(unittest.TestCase):
    def setUp(self):self.values=prefix_fixture();self.data=self.values[0]
    def compare(self):return compare_prefix(*self.values,1000)
    def test_complete_fixture(self):self.assertEqual(self.compare(),[])
    def test_missing_terminal_rejects(self):
        self.data['points'].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_missing_native_store_rejects(self):
        self.values[3].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_reordered_actor_store_rejects(self):
        self.data['writes'][256]['address']+=1
        with self.assertRaises(ValueError):self.compare()
    def test_skipped_poll_rejects(self):
        self.data['polls'].pop(0)
        with self.assertRaises(ValueError):self.compare()
    def test_reading_past_line145_rejects(self):
        self.data['polls'][0]['ly']=145
        with self.assertRaises(ValueError):self.compare()
    def test_masked_display_rejects(self):
        self.data['interrupts'].append(dict(kind='vblank',cycles=1100))
        with self.assertRaises(ValueError):self.compare()
    def test_bad_pending_flags_reject(self):
        self.data['points'][-1]['pendingRequests']=1
        with self.assertRaises(ValueError):self.compare()
    def test_native_line_difference_reported(self):
        self.values[2][0]['ly']=143;self.assertEqual(self.compare()[0]['category'],'polls')

class FollowingStageIntegrity(unittest.TestCase):
    def setUp(self):self.values=stage_fixture();self.data=self.values[0]
    def compare(self):return compare_stage(*self.values,1000)
    def test_both_complete_stages(self):
        self.assertEqual(self.compare(),[]);self.assertEqual(compare_stage(*stage_fixture(False),1000),[])
    def test_next_retry_observes_explicit_allocation_reset(self):
        self.data['nextRetry']=True
        for p in self.data['points']:p['reverse']=1
        self.data['points'][-1]['reverse']=0
        self.assertEqual(self.compare(),[])
    def test_next_retry_missing_allocation_observation_rejects(self):
        self.data['nextRetry']=True
        with self.assertRaises(ValueError):self.compare()
    def test_next_retry_allocation_not_cleared_rejects(self):
        self.data['nextRetry']=True
        for p in self.data['points']:p['reverse']=1
        with self.assertRaises(ValueError):self.compare()
    def test_missing_stage_phase_rejects(self):
        self.data['points'].pop(4)
        with self.assertRaises(ValueError):self.compare()
    def test_truncated_native_stage_rejects(self):
        self.values[1].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_unowned_service_rejects(self):
        self.data['interrupts'].append({})
        with self.assertRaises(ValueError):self.compare()
    def test_early_callback_change_rejects(self):
        self.data['points'][2]['stat']=4
        with self.assertRaises(ValueError):self.compare()
    def test_clock_not_attached_rejects(self):
        self.values[3][0]['end']=4
        with self.assertRaises(ValueError):self.compare()
    def test_overwritten_camera_difference_reported(self):
        self.values[1][-1]['cameraY']+=128;self.assertEqual(self.compare()[0]['category'],'boundary')
    def test_inherited_camera_is_not_claimed(self):
        self.values[1][0]['cameraY']+=128;self.assertEqual(self.compare(),[])

class FollowingEntryIntegrity(unittest.TestCase):
    def setUp(self):self.values=entry_fixture();self.data=self.values[0]
    def compare(self):return compare_entry(*self.values,50000)
    def test_complete_fixture(self):self.assertEqual(self.compare(),[])
    def test_missing_periodic_vector_rejects(self):
        self.data['interrupts'].pop(2)
        with self.assertRaises(ValueError):self.compare()
    def test_missing_native_service_rejects(self):
        self.values[2].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_pending_vector_reordering_rejects(self):
        self.data['interrupts'][0],self.data['interrupts'][1]=self.data['interrupts'][1],self.data['interrupts'][0]
        with self.assertRaises(ValueError):self.compare()
    def test_wrong_irq_owner_rejects(self):
        self.values[3][0]['owner']=2
        with self.assertRaises(ValueError):self.compare()
    def test_wrong_scene_seed_rejects(self):
        self.data['points'][1]['randomState']+=256
        with self.assertRaises(ValueError):self.compare()
    def test_source_fresh_pause_rejects(self):
        self.data['points'][-1]['inputPressed']=8
        with self.assertRaises(ValueError):self.compare()
    def test_row_role_is_not_an_rng_seed(self):
        self.values[1][-1]['randomState']=440;self.assertEqual(self.compare()[0]['category'],'boundary')
    def test_native_audio_difference_reported(self):
        self.values[2][0]['music']+=4;self.assertEqual(self.compare()[0]['category'],'service')
    def test_service_counters_must_continue(self):
        self.values[4][0]['stats']+=1
        with self.assertRaises(ValueError):self.compare()

if __name__=='__main__':unittest.main()
