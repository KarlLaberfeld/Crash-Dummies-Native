"""Synthetic complete-coverage and inheritance integrity tests, no ROM."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_following_gameplay_reference import ORDER,FIELDS,analyze,compare_gameplay
from extract_air import HANDLERS

def fixture():
    first=100000;times=[first+n for n in (0,96,3092,3344,12484,13664,15892,18900,18932)]
    stat=dict(kind='stat',start=145000,end=145288,selector=4,display=4,returnAddress=0x261d,ready=1)
    service=dict(kind='vblank',start=149104,selector=4,display=4,returnAddress=0x261d,ready=1,tick=6,held=33,pressed=0,resetEnabled=1,resetLatched=0,effectRequest=-1,musicEnabled=1,phases={})
    now=service['start']
    for name,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,1676,240,64,68,60)):
        now+=cost;service['phases'][name]=now
    service['end']=now+120;times.append(service['end']+120)
    points=[]
    for i,(name,time) in enumerate(zip(ORDER,times)):
        entities=[dict(frame=255,flags=255,handler=65535,x=65535,y=65535,params=[255]*7,state=17,delay=19,period=23) for _ in range(16)]
        for slot in (0,1):entities[slot]=dict(frame=0 if slot==0 else 27,flags=0 if slot==0 else 16,handler=(0x5fa6 if i<2 else 0x5fae) if slot==0 else 0x6759,x=21000-slot*1000,y=46000-slot*1000,params=[216+i,0,0,0,0,0,25],state=128 if i<2 else 0,delay=0,period=2)
        points.append(dict(name=name,cycles=time,tick=6+(i==9),secondTicks=35,seconds=40,random=0xf200,ready=0,map=1,lastMapCamera=44800 if i<6 else 44672,mapScratch=440 if i<6 else 432,cameraX=20224,cameraY=44672,hudCursor=2+(i==9),fadeRemaining=7-(i==9),held=33,pressed=0,lcdc=0xe7,display=4,transfer=0,remaining=0,effect=-1,reverse=int(i>=4),entities=entities))
    data=dict(version=1,points=points,interrupts=[stat,service],precedingDisplays=1195)
    native=[dict(boundary=p['name'],cycle=p['cycles']-1000,**{k:p[k] for k in FIELDS}) for p in points];actors=[]
    for p in points:
        for slot,e in enumerate(p['entities']):
            actors.append(dict(boundary=p['name'],slot=slot,alive=int(e['frame']!=255),frame=e['frame'],flags=e['flags'],handler=HANDLERS.get(e['handler'],0),x=e['x'],y=e['y'],done=int(bool(e['state']&128)),waiting=int(bool(e['state']&64)),delay=e['delay'],period=e['period'],**{f'param{j}':v for j,v in enumerate(e['params'])}))
    services=[dict(service=1195,cycle=service['start']-1000,tick=6,display=1676,effects=64,music=60,inputHeld=33,inputPressed=0)]
    vectors=[dict(kind=r['kind'],vectorCycle=r['start']-1000,owner=2) for r in (stat,service)]
    entry=[dict(end=first-1000,tick=6,countdown=73,displays=1195,stats=1196,randomState=0xf200,lcdEpoch=12216,nextStat=143980,nextVBlank=148084)]
    summary=[dict(end=times[-1]-1000,tick=7,countdown=73,displays=1196,stats=1197,lcdEpoch=12216,nextStat=214204,nextVBlank=218308)]
    return [data,native,actors,services,vectors,summary,entry]

class FollowingGameplayIntegrity(unittest.TestCase):
    def setUp(self):self.values=fixture();self.data=self.values[0]
    def compare(self):return compare_gameplay(*self.values,1000)
    def test_complete_fixture(self):self.assertEqual(self.compare(),([],20))
    def test_missing_original_end_rejects(self):
        self.data['points'].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_native_truncated_actor_pool_rejects(self):
        self.values[2].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_reordered_source_phase_rejects(self):
        self.data['points'][3],self.data['points'][4]=self.data['points'][4],self.data['points'][3]
        with self.assertRaises(ValueError):self.compare()
    def test_reordered_native_actor_rejects(self):
        self.values[2][0],self.values[2][1]=self.values[2][1],self.values[2][0]
        with self.assertRaises(ValueError):self.compare()
    def test_lost_timer_inheritance_detected(self):
        self.values[1][0]['secondTicks']=0
        self.assertEqual(self.compare()[0][0]['category'],'boundary')
    def test_lost_live_animation_delay_detected(self):
        self.values[2][1]['period']=0
        self.assertEqual(self.compare()[0][0]['category'],'actor')
    def test_unused_vacant_payload_is_explicitly_excluded(self):
        self.values[2][2]['handler']=70;self.values[2][2]['param0']=0;self.values[2][2]['delay']=40
        self.assertEqual(self.compare(),([],20))
    def test_vacant_allocation_is_compared(self):
        self.values[2][2]['frame']=27;self.values[2][2]['alive']=1
        self.assertEqual(self.compare()[0][0]['fields']['alive'],[0,1])
    def test_busy_display_rejects(self):
        self.data['interrupts'][1]['ready']=0
        with self.assertRaises(ValueError):self.compare()
    def test_interrupted_actor_body_rejects(self):
        self.data['interrupts'][0]['start']=101000;self.data['interrupts'][0]['end']=101288
        with self.assertRaises(ValueError):self.compare()
    def test_truncated_vectors_rejects(self):
        self.values[4].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_unknown_acceptance_owner_rejects(self):
        self.values[4][0]['owner']=0
        with self.assertRaises(ValueError):self.compare()
    def test_next_fresh_start_requires_pause(self):
        self.data['points'][-1]['held']=8;self.data['points'][-1]['pressed']=8
        with self.assertRaises(ValueError):self.compare()
    def test_detached_scene_seed_rejects(self):
        self.values[6][0]['randomState']=0
        with self.assertRaises(ValueError):self.compare()
    def test_reset_input_rejects(self):
        self.data['points'][0]['held']=15
        with self.assertRaises(ValueError):self.compare()
    def test_changed_display_work_rejects(self):
        self.data['interrupts'][1]['phases']['bookkeeping']+=4
        with self.assertRaises(ValueError):self.compare()
    def test_lost_epoch_deadline_rejects(self):
        self.values[6][0]['nextStat']-=4
        with self.assertRaises(ValueError):self.compare()
    def test_terminal_counter_detected(self):
        self.values[5][0]['tick']=6
        self.assertEqual(self.compare()[0][0]['category'],'summary')
    def test_altered_actor_parameter_detected(self):
        self.values[2][32]['param0']=0
        self.assertEqual(self.compare()[0][0]['category'],'actor')

if __name__=='__main__':unittest.main()
