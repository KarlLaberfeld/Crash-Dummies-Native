"""Synthetic following pause coverage/inheritance checks, no original assets."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_following_pause_reference import analyze_paused_entry,compare_paused_entry
from air_following_entry_reference import FIELDS
from test_air_following_setup_reference import entry_fixture

def fixture():
    values=entry_fixture();data=values[0];points=data['points'];irqs=data['interrupts']
    for p in points:p['inputHeld']=p['inputPressed']=0
    irqs[0]['held']=irqs[0]['pressed']=0;irqs[3]['held']=8;irqs[3]['pressed']=8
    pause=dict(points[-1]);pause.update(name='pauseEntry',cycles=pause['cycles']+12,inputHeld=8,inputPressed=8)
    points[-1]=pause;epoch=points[7]['cycles']-4
    for frame in (1,2):
        start=epoch+frame*70224+135*456+20;irqs.append(dict(kind='stat',start=start,end=start+288,selector=4,returnAddress=0x261d))
        start=epoch+frame*70224+144*456+20;held=0 if frame==1 else 8
        r=dict(kind='vblank',start=start,tick=6+frame,selector=4,display=1,returnAddress=0x261d,ready=0,held=held,pressed=held,resetEnabled=1,resetLatched=0,effectRequest=-1,musicEnabled=0,phases={});time=start
        for name,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,160,240,64,68,60)):
            time+=cost;r['phases'][name]=time
        r['end']=time+120;irqs.append(r)
    end=dict(pause);end.update(name='end',cycles=irqs[-1]['end']+40000,tick=9,lcdc=0xe7,inputHeld=8,inputPressed=8);points.append(end)
    native=[dict(boundary=p['name'],cycle=p['cycles']-50000,**{k:p[k] for k in (*FIELDS,'randomState')}) for p in points]
    services=[]
    for i,r in enumerate(q for q in irqs if q['kind']=='vblank'):
        services.append(dict(service=100+i,cycle=r['start']-50000,tick=r['tick'],display=1508 if i==0 else 1676 if i==1 else 160,effects=64,music=60,inputHeld=r['held'],inputPressed=r['pressed']))
    vectors=[dict(kind=r['kind'],vectorCycle=r['start']-50000,owner=3 if i<2 else 2) for i,r in enumerate(irqs)]
    new_epoch=epoch-50000;summary=[dict(end=end['cycles']-50000,tick=9,countdown=73,displays=104,stats=104,lcdEpoch=new_epoch,nextStat=new_epoch+135*456+3*70224,nextVBlank=new_epoch+144*456+3*70224,randomState=0x500,hudCursor=2,fadeRemaining=7,entryPauseComplete=1)]
    stage=[dict(end=0,displays=100,stats=100)]
    return [data,native,services,vectors,summary,stage]

class FollowingPauseIntegrity(unittest.TestCase):
    def setUp(self):self.values=fixture();self.data=self.values[0]
    def compare(self):return compare_paused_entry(*self.values,50000)
    def test_complete_fixture(self):self.assertEqual(self.compare(),[])
    def test_missing_first_pause_boundary_rejects(self):
        self.data['points'].pop(11)
        with self.assertRaises(ValueError):self.compare()
    def test_truncated_native_pause_service_rejects(self):
        self.values[2].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_missing_complete_native_vector_rejects(self):
        self.values[3].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_lost_lcd_epoch_detected(self):
        self.values[4][0]['lcdEpoch']=0
        self.assertEqual(self.compare()[0]['category'],'summary')
    def test_changed_paused_audio_detected(self):
        self.values[2][2]['music']=1676
        self.assertEqual(self.compare()[0]['category'],'service')
    def test_changed_pause_seed_detected(self):
        self.values[1][-1]['randomState']=0
        self.assertEqual(self.compare()[0]['category'],'boundary')
    def test_fresh_start_is_required(self):
        self.data['points'][11]['inputPressed']=0
        with self.assertRaises(ValueError):self.compare()
    def test_paused_music_progress_rejects(self):
        self.data['interrupts'][-1]['musicEnabled']=1
        with self.assertRaises(ValueError):self.compare()
    def test_paused_gameplay_callback_rejects(self):
        self.data['interrupts'][-1]['display']=4
        with self.assertRaises(ValueError):self.compare()
    def test_unknown_irq_return_rejects(self):
        self.data['interrupts'][-1]['returnAddress']=0x2365
        with self.assertRaises(ValueError):self.compare()
    def test_wrong_native_irq_owner_rejects(self):
        self.values[3][-1]['owner']=0
        with self.assertRaises(ValueError):self.compare()
    def test_detached_preceding_stage_rejects(self):
        self.values[5][0]['displays']=99
        with self.assertRaises(ValueError):self.compare()
    def test_hud_progress_during_pause_rejects(self):
        self.data['points'][-1]['hudCursor']=3
        with self.assertRaises(ValueError):self.compare()
    def test_pause_deadline_drift_rejects(self):
        self.data['interrupts'][-1]['start']+=4
        with self.assertRaises(ValueError):self.compare()
    def test_pause_global_counter_drift_rejects(self):
        self.data['interrupts'][-1]['tick']+=1
        with self.assertRaises(ValueError):self.compare()
    def test_frozen_countdown_change_rejects(self):
        self.data['points'][-1]['countdown']-=1
        with self.assertRaises(ValueError):self.compare()
    def test_pause_object_restore_is_compared(self):
        self.values[1][-1]['lcdc']=0xe5
        self.assertEqual(self.compare()[0]['category'],'boundary')

if __name__=='__main__':unittest.main()
