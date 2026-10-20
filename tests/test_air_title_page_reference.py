"""Synthetic full-map, duplicate clear, direct-storage and reopening guards."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_page_reference import analyze,IRQ_PHASES


class TitlePageScope(unittest.TestCase):
    def setUp(self):
        points=[]
        def point(name,clear=2,row=10,opened=0,tick=1):
            points.append(dict(name=name,cycles=100+10000*len(points),cleared=clear,rows=row,opened=opened,center=(176+2*opened)&255,windowY=72+opened,tick=tick,countdown=54,stat=1,lcdc=0xc3,scrollY=0,lyc=23,inputHeld=33,inputPressed=0))
        for name,clear in [('begin',0),('clearEntry',0),('closeReturned',1),('clearEntry',1),('clearReturned',2),('pageCall',2),('pageEntry',2),('rectangleEntry',2)]:point(name,clear,0)
        points[1]['cycles']=points[0]['cycles']
        for row in range(1,11):point('rowReady',row=row)
        for name in ('copyReturned','pageReturn','pageReturned'):point(name)
        for i in range(40):point('openWait',opened=i,tick=1+i);point('openReady',opened=i,tick=2+i);point('centerStored',opened=i+1,tick=2+i)
        point('end',opened=40,tick=41);self.parent=dict(points=[dict(points[0])])
        addresses=list(range(0x9dc0,0x9f00))*2+[0x9dc0+32*r+c for r in range(10) for c in range(20)]
        writes=[dict(cycle=200+4*i,address=a,value=0 if i<640 else i%256) for i,a in enumerate(addresses)]
        before=[19]*2048;maps=list(before)
        for p in writes:maps[p['address']-0x9800]=p['value']
        irqs=[];rasters=[]
        for i in range(40):
            start=10000+20000*i
            if i:
                for j in range(3):
                    t=start+1000*j;irqs.append(dict(kind='stat',start=t,end=t+100));rasters.extend([dict(boundary='begin',cycle=t),dict(boundary='end',cycle=t+100)])
            t=start+4000;irqs.append(dict(kind='vblank',start=t,end=t+90,tick=1+i,countdown=54,phases={name:t+10*(j+1) for j,name in enumerate(IRQ_PHASES.values())}))
        self.data=dict(storageReadOwner='direct-vram-title-v1',reference=dict(titleStorageObserver='direct-vram-title-v1'),points=points,writes=writes,polls=[dict(cycle=150,mode=1)],interrupts=irqs,rasters=rasters,beforeMaps=before,maps=maps)
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete_structure(self):self.assertEqual(len(analyze(self.data,self.parent)),40)
    def test_direct_owner_required(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_adapter_provenance_required(self):self.data['reference']={};self.reject()
    def test_detached_close(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_both_clears_required(self):self.data['writes'].pop(100);self.reject()
    def test_padding_stays_cleared(self):self.data['maps'][0x5d4]=1;self.reject()
    def test_other_map_stays_unchanged(self):self.data['maps'][0]=0;self.reject()
    def test_unknown_storage_bytes_reject(self):self.data['beforeMaps']=[255]*2048;self.reject()
    def test_full_rectangle_rows(self):next(p for p in self.data['points'] if p['name']=='rowReady')['rows']=2;self.reject()
    def test_window_center_independent(self):self.data['points'][-1]['windowY']=111;self.reject()
    def test_no_timer_decrement(self):self.data['points'][-1]['countdown']=53;self.reject()
    def test_no_missing_reopen_wait(self):self.data['points'].pop(21);self.reject()
    def test_all_display_ticks(self):self.data['points'][-1]['tick']-=1;self.reject()
    def test_bounded_readiness_modes(self):self.data['polls'][0]['mode']=-1;self.reject()
    def test_no_discarded_rasters(self):self.data['rasters'].pop();self.reject()


if __name__=='__main__':unittest.main()
