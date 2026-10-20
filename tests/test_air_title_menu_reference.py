"""Reject detached, shortened, input-modified or incomplete menu recordings."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_menu_reference import analyze,IRQ_PHASES


class TitleMenuScope(unittest.TestCase):
    def setUp(self):
        names=['begin']+['wait','ready','unlockEntry','unlockReturned','startDecision','selectDecision','actionDecision','timer','timerStored']*480+['advance','pageStored','end']
        points=[]
        for i,name in enumerate(names):
            if not i:remaining,waits,index=480,0,0
            elif i<=4320:
                loop,phase=divmod(i-1,9);remaining=480-loop-(phase==8);waits=loop+(phase>0);index=0
            else:remaining,waits,index=0,480,int(i>4321)
            points.append(dict(name=name,cycles=100+10000*i,remaining=remaining,waits=waits,index=index,pattern=0,tick=(65300+waits)&65535,countdown=54,inputHeld=33,inputPressed=0,stat=1,lcdc=0xc3,scrollY=0,lyc=23))
        maps=[19]*2048;self.parent=dict(points=[dict(points[0])],maps=maps[:])
        stores=[(0xff40,0xfb),(0xff42,88),(0xff42,88),(0xff45,103),(0xc099,2),(0xff40,0xc3),(0xff42,0),(0xff45,23),(0xc099,1)]*480
        writes=[dict(cycle=200+4*i,address=a,value=v) for i,(a,v) in enumerate(stores)]+[dict(cycle=points[-3]['cycles']+100,address=0xc03e,value=1)]
        irqs=[];rasters=[]
        for i in range(480):
            start=1000+50000*i
            for j in range(2):
                t=start+1000*j;irqs.append(dict(kind='stat',start=t,end=t+100));rasters.extend([dict(boundary='begin',cycle=t),dict(boundary='end',cycle=t+100)])
            t=start+4000;irqs.append(dict(kind='vblank',start=t,end=t+90,tick=(65300+i)&65535,countdown=54,phases={name:t+10*(j+1) for j,name in enumerate(IRQ_PHASES.values())}))
        self.data=dict(storageReadOwner='direct-vram-title-v1',reference=dict(titleStorageObserver='direct-vram-title-v1'),points=points,writes=writes,interrupts=irqs,rasters=rasters,beforeMaps=maps[:],maps=maps[:])
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete_timeout_with_tick_wrap(self):self.assertEqual(len(analyze(self.data,self.parent)),480)
    def test_direct_owner_required(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_adapter_provenance_required(self):self.data['reference']={};self.reject()
    def test_detached_page(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_detached_entry_maps(self):self.parent['maps'][0]=0;self.reject()
    def test_blocked_entry_reads_reject(self):self.data['beforeMaps']=[255]*2048;self.reject()
    def test_unchanged_full_maps(self):self.data['maps'][900]=0;self.reject()
    def test_complete_duration(self):self.data['points'].pop(4000);self.reject()
    def test_no_missing_decrement(self):self.data['points'][9]['remaining']=480;self.reject()
    def test_wait_count_is_not_display_counter(self):self.data['points'][1]['waits']=1;self.reject()
    def test_late_fresh_edge_rejects(self):self.data['points'][4000]['inputPressed']=8;self.reject()
    def test_unlock_progress_rejects(self):self.data['points'][4000]['pattern']=1;self.reject()
    def test_held_input_preserved(self):self.data['points'][4000]['inputHeld']=0;self.reject()
    def test_countdown_frozen(self):self.data['points'][-1]['countdown']=53;self.reject()
    def test_page_index_advances_once(self):self.data['points'][-1]['index']=2;self.reject()
    def test_all_native_ticks(self):self.data['points'][-1]['tick']-=1;self.reject()
    def test_all_raster_stores(self):self.data['writes'].pop(4);self.reject()
    def test_no_extra_map_store(self):self.data['writes'][0]['address']=0x9800;self.reject()
    def test_page_store_value(self):self.data['writes'][-1]['value']=2;self.reject()
    def test_page_store_order(self):self.data['writes'][-1]['cycle']=4324;self.reject()
    def test_missing_vectors(self):self.data['interrupts'].pop();self.reject()
    def test_reordered_vectors(self):self.data['interrupts'][0],self.data['interrupts'][1]=self.data['interrupts'][1],self.data['interrupts'][0];self.reject()
    def test_overlapping_vectors(self):self.data['interrupts'][1]['start']=self.data['interrupts'][0]['end'];self.reject()
    def test_vector_outside_owner(self):self.data['interrupts'][-1]['end']=self.data['points'][-1]['cycles'];self.reject()
    def test_no_missing_raster_boundary(self):self.data['rasters'].pop();self.reject()
    def test_boundaries_monotonic(self):self.data['points'][2]['cycles']=self.data['points'][1]['cycles'];self.reject()


if __name__=='__main__':unittest.main()
