"""Synthetic source attachment, partial-reset observer and closing scope guards."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_close_reference import analyze,POINTS,IRQ_PHASES


class TitleCloseScope(unittest.TestCase):
    def setUp(self):
        points=[]
        def point(name,cycle,step=0,tick=1):
            points.append(dict(name=name,cycles=cycle,center=(-2*step)&255,steps=step,windowY=112-step,tick=tick,countdown=54,inputHeld=33,inputPressed=0,lcdc=0xc3,stat=1,lyc=23,scrollY=0,sourceSong=1))
        for i,name in enumerate(list(POINTS.values())[:11]):point(name,[10000,10100,10200,10300,10400,10500,10600,10700,11500,12000,12100][i])
        self.parent=dict(points=[dict(points[0])]);irqs=[];rasters=[];writes=[]
        def stat(start,center,phase,first=False):
            lyc=23 if phase==1 else ((23-center)&255 if center else 103) if phase==2 else 103
            a=dict(boundary='begin',cycle=start,center=center,stat=phase,lcdc=0xc3 if phase==1 else 0xfb,scrollY=0 if phase==1 else (center+88)&255 if phase==2 else 88,lyc=lyc)
            if phase==1 and center==0:stores=list(zip((0xff40,0xff42,0xff42,0xff45,0xc099),(0xfb,88,88,103,2)));after=(2,0xfb,88,103);body=460
            elif phase==1:stores=list(zip((0xff40,0xff42,0xff45,0xc099),(0xfb,(center+88)&255,(23-center)&255,2)));after=(2,0xfb,(center+88)&255,(23-center)&255);body=408
            elif phase==2 and lyc!=103:stores=list(zip((0xff42,0xff45,0xc099),(88,103,3)));after=(3,0xfb,88,103);body=352
            else:stores=list(zip((0xff40,0xff42,0xff45,0xc099),(0xc3,0,23,1)));after=(1,0xc3,0,23);body=384 if phase==2 else 352
            irqs.append(dict(kind='stat',start=start,end=start+body,returnAddress=0x23af if first else 0x261d));rasters.append(a)
            rasters.append(dict(boundary='end',cycle=start+body,center=center,**dict(zip(('stat','lcdc','scrollY','lyc'),after))))
            writes.extend(dict(cycle=start+4*(j+1),address=a,value=v) for j,(a,v) in enumerate(stores))
        stat(10800,0,1,True)
        for i in range(40):
            start=20000+10000*i;point('closeWait',start,i,1+i)
            for j,phase in enumerate((2,) if i==0 else (1,2,3)):stat(start+1000*(j+1),(-2*i)&255,phase)
            vstart=start+4000;irqs.append(dict(kind='vblank',start=vstart,end=vstart+90,returnAddress=0x261d,tick=1+i,countdown=54,phases={name:vstart+10*(j+1) for j,name in enumerate(IRQ_PHASES.values())}))
            point('closeReady',start+6000,i,2+i);point('centerStored',start+6100,i+1,2+i)
            writes.extend([dict(cycle=start+6012,address=0xff4a,value=111-i),dict(cycle=start+6048,address=0xc09c,value=(-2*(i+1))&255)])
        point('end',start+6200,40,41);writes.sort(key=lambda p:p['cycle']);self.data=dict(points=points,interrupts=irqs,rasters=rasters,writes=writes)
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete_scope(self):self.assertEqual(len(analyze(self.data,self.parent)),40)
    def test_detached_fade(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_skip_a_motion_step(self):self.data['points'].pop(11);self.reject()
    def test_unknown_music_interrupt_return(self):self.data['interrupts'][0]['returnAddress']=0x23b2;self.reject()
    def test_no_display_of_partial_reset(self):next(p for p in self.data['interrupts'] if p['kind']=='vblank')['start']=11000;self.reject()
    def test_window_and_center_are_distinct(self):self.data['points'][-1]['windowY']=71;self.reject()
    def test_no_result_countdown(self):self.data['points'][-1]['countdown']=53;self.reject()
    def test_title_song_remains_selected(self):self.data['points'][-1]['sourceSong']=13;self.reject()
    def test_all_forty_displays_required(self):self.data['interrupts'].pop();self.reject()
    def test_third_phase_required(self):self.data['rasters'][8]['stat']=2;self.reject()
    def test_no_missing_register_store(self):self.data['writes'].pop();self.reject()
    def test_window_store_value(self):next(w for w in self.data['writes'] if w['address']==0xff4a)['value']=112;self.reject()
    def test_middle_branch_geometry(self):next(p for p in self.data['rasters'] if p['stat']==3)['lyc']=23;self.reject()
    def test_display_ticks_complete(self):self.data['points'][-1]['tick']=40;self.reject()
    def test_all_raster_endpoints_required(self):self.data['rasters'].pop();self.reject()


if __name__=='__main__':unittest.main()
