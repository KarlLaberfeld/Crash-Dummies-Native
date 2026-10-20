"""Synthetic attachment, pending-service and full title-raster scope guards."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_fade_reference import analyze,IRQ_PHASES


class TitleFadeScope(unittest.TestCase):
    def setUp(self):
        names=['begin','fadeEntry']+[n for _ in range(8) for n in ('palette','wait','tail','wait','tail','wait','tail','wait','tail')]+['fadeReturned','end']
        points=[dict(name=n,cycles=100+10000*i,tick=1,countdown=54,inputHeld=255,inputPressed=0,lcdc=0xc3,stat=1) for i,n in enumerate(names)];points[-1]['tick']=35
        self.parent=dict(points=[dict(points[0])]);irqs=[];rasters=[];writes=[];display=0;stat=0
        def irq(kind):
            nonlocal display,stat
            i=len(irqs);start=1000+2000*i if i<2 else 11000+2000*(i-2)
            p=dict(kind=kind,start=start,returnAddress=0x20d1 if i<2 else 0x261d,tick=1+display,countdown=54,phases={})
            if kind=='vblank':
                p['phases']={name:start+10*(j+1) for j,name in enumerate(IRQ_PHASES.values())};p['end']=start+90;display+=1
            else:
                top=stat%2==0;p['end']=start+(460 if top else 384)
                rasters.extend([dict(boundary='begin',cycle=start,stat=1 if top else 2,lcdc=0xc3 if top else 0xfb,scrollY=0 if top else 88,lyc=23 if top else 103),dict(boundary='end',cycle=p['end'],stat=2 if top else 1,lcdc=0xfb if top else 0xc3,scrollY=88 if top else 0,lyc=103 if top else 23)])
                stores=list(zip((0xff40,0xff42,0xff42,0xff45,0xc099),(0xfb,88,88,103,2))) if top else list(zip((0xff40,0xff42,0xff45,0xc099),(0xc3,0,23,1)))
                writes.extend(dict(cycle=start+4*(j+1),address=a,value=v) for j,(a,v) in enumerate(stores));stat+=1
            irqs.append(p)
        irq('vblank');irq('stat')
        for i in range(33):
            if i:irq('stat')
            irq('stat');irq('vblank')
        for i in range(8):writes.extend(dict(cycle=500000+16*i+4*j,address=a,value=v) for j,(a,v) in enumerate(((0xff47,0xe4),(0xff49,0xe0),(0xff48,0xc4))))
        writes.sort(key=lambda p:p['cycle']);self.data=dict(points=points,interrupts=irqs,rasters=rasters,writes=writes)
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete_scope(self):self.assertEqual(len(analyze(self.data,self.parent)),34)
    def test_detached_layout(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_missing_fade_wait(self):self.data['points'].pop(3);self.reject()
    def test_countdown_is_not_a_title_timer(self):self.data['points'][5]['countdown']-=1;self.reject()
    def test_pending_priority(self):self.data['interrupts'][0]['kind']='stat';self.reject()
    def test_wrong_return_owner(self):self.data['interrupts'][2]['returnAddress']=0x20d1;self.reject()
    def test_missing_raster_service(self):self.data['interrupts'].pop(2);self.reject()
    def test_no_extra_display(self):self.data['points'][-1]['tick']+=1;self.reject()
    def test_wrong_top_geometry(self):self.data['rasters'][0]['lyc']=103;self.reject()
    def test_missing_raster_endpoint(self):self.data['rasters'].pop();self.reject()
    def test_missing_duplicate_scroll_store(self):self.data['writes'].pop(1);self.reject()
    def test_wrong_raster_store(self):self.data['writes'][0]['value']=0xc3;self.reject()
    def test_palette_mask(self):self.data['writes'][-1]['value']=0xe4;self.reject()
    def test_store_order(self):self.data['writes'][1]['cycle']=self.data['writes'][0]['cycle'];self.reject()
    def test_vectors_must_finish_before_endpoint(self):self.data['interrupts'][-1]['end']=self.data['points'][-1]['cycles'];self.reject()


if __name__=='__main__':unittest.main()
