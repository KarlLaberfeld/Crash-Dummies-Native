"""Synthetic evidence integrity; contains no ROM or original recordings."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_resume_reference import analyze,POINTS

def fixture():
    irqs=[];writes=[];polls=[];tick=9
    def irq(kind,start,ret):
        nonlocal tick
        p=dict(kind=kind,start=start,returnAddress=ret,tick=tick,countdown=54,phases={})
        if kind=='vblank':
            p.update(held=0,pressed=0);time=start
            for name,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,144,240,64,68,60)):
                time+=cost;p['phases'][name]=time
            p['end']=time+120;tick+=1;offset=1284
        else:p['end']=start+288;offset=216
        irqs.append(p);writes.append(dict(cycle=start+offset,address=0xff42,value=0));return p['end']+16
    begin=1000;selection=irq('stat',irq('vblank',begin+48,0x26de)+20,0x26de)
    times=[begin,selection,selection+64,selection+88,selection+120]
    writes.append(dict(cycle=times[-1],address=0xc035,value=0x98));time=times[-1]+108
    for cell in range(1024):
        if cell in (100,200,300,400,500,600):
            kind='stat' if cell in (100,300,500) else 'vblank'
            start=time-88;duration=irq(kind,start,0x2129)-(start-20);time+=duration
        busy=3 if cell<495 else 2
        for _ in range(busy):polls.append(dict(cycle=time,mode=3));time+=32
        polls.append(dict(cycle=time,mode=0));writes.append(dict(cycle=time+28,address=0x9800+cell,value=0));time+=144
    cleared=time-144+28+72;times += [cleared,cleared+20];writes.append(dict(cycle=cleared+4,address=0xc095,value=0));points=[]
    for i,(name,time) in enumerate(zip(POINTS.values(),times)):
        finished=sum(p['kind']=='vblank' and p['end']+16<=time for p in irqs)
        points.append(dict(name=name,cycles=time,tick=9+finished,countdown=54,inputHeld=0,inputPressed=0,lcdc=0xd1,scrollY=0,display=5,stat=5,pendingRequests=3 if not i else 0,lives=5,result=0 if i==6 else 33))
    before=[19]*1024+[0]*1024
    data=dict(storageReadOwner='direct-vram-title-v1',reference=dict(titleStorageObserver='direct-vram-title-v1'),points=points,polls=polls,writes=sorted(writes,key=lambda p:p['cycle']),interrupts=irqs,beforeMaps=before,maps=[0]*2048,objectsUnchanged=True)
    return data,dict(points=[dict(points[0])],maps=list(before))

class ResumeEvidence(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete(self):self.assertEqual(len(analyze(self.data,self.parent)),4)
    def test_detached_entry(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_map_ancestry(self):self.parent['maps'][0]=18;self.reject()
    def test_direct_storage_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_direct_storage_observer(self):self.data['reference']={};self.reject()
    def test_objects_preserved(self):self.data['objectsUnchanged']=False;self.reject()
    def test_offscreen_background_clear(self):self.data['maps'][1023]=19;self.reject()
    def test_window_preserved(self):self.data['maps'][2047]=1;self.reject()
    def test_boundary_order(self):self.data['points'][2]['name']='selectionEntry';self.reject()
    def test_pending_acceptance_after_whole_follower(self):self.data['interrupts'][0]['start']-=4;self.reject()
    def test_pending_priority(self):self.data['interrupts'][0]['kind']='stat';self.reject()
    def test_pending_follower_return(self):self.data['interrupts'][1]['returnAddress']=0x261d;self.reject()
    def test_no_fitted_display_work(self):self.data['interrupts'][0]['phases']['bookkeeping']+=4;self.reject()
    def test_raster_duration(self):self.data['interrupts'][1]['end']+=4;self.reject()
    def test_periodic_access_owner(self):self.data['interrupts'][2]['returnAddress']=0x261d;self.reject()
    def test_missing_vector(self):self.data['interrupts'].pop();self.reject()
    def test_input_edge(self):self.data['interrupts'][0]['pressed']=8;self.reject()
    def test_countdown_preserved(self):self.data['points'][-1]['countdown']-=1;self.reject()
    def test_tick_from_actual_displays(self):self.data['points'][1]['tick']-=1;self.reject()
    def test_lives_preserved(self):self.data['points'][1]['lives']=4;self.reject()
    def test_requests_consumed(self):self.data['points'][1]['pendingRequests']=2;self.reject()
    def test_result_not_cleared_early(self):self.data['points'][5]['result']=0;self.reject()
    def test_all_readiness_samples(self):self.data['polls'].pop(100);self.reject()
    def test_independent_ready_read(self):self.data['polls'][3]['mode']=3;self.reject()
    def test_busy_samples_remain_busy(self):self.data['polls'][1]['mode']=0;self.reject()
    def test_busy_sample_boundary(self):self.data['polls'][1]['cycle']+=4;self.reject()
    def test_store_attached_to_ready_read(self):
        next(p for p in self.data['writes'] if p['address']==0x9800)['cycle']+=4;self.reject()
    def test_every_cell_store(self):self.data['writes'].pop(300);self.reject()
    def test_raster_store_boundary(self):self.data['writes'][0]['cycle']+=4;self.reject()
    def test_result_store_owner(self):self.data['writes'][-1]['value']=33;self.reject()
    def test_first_player_selection_work(self):self.data['points'][2]['cycles']+=4;self.reject()
    def test_clear_return_work(self):self.data['points'][-2]['cycles']+=4;self.reject()
    def test_poll_cannot_run_in_interrupt(self):self.data['polls'][300]['cycle']=self.data['interrupts'][2]['start'];self.reject()

if __name__=='__main__':unittest.main()
