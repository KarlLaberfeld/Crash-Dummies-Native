"""Synthetic fresh/held direction and control-attachment evidence guards."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_unlock_reference import analyze,attachment,tail,event_sha
def fixture():
    end=dict(name='end',cycles=1000,tick=5,countdown=54,inputHeld=0,inputPressed=0,stat=1,lcdc=0xc3,scrollY=0,lyc=23)
    parent=dict(controlMemorySha256='parent',points=[end],maps=[19]*2048)
    points=[dict(end,name='begin',waits=0,remaining=480,index=0,pattern=0,route=0)];irqs=[];rasters=[];writes=[]
    progress=0;previous=0;remaining=480;inputs=(0,0,64,0,128,0,32,0,16)
    for i,held in enumerate(inputs):
        base=1000+70224*i;pressed=held&~previous;previous=held
        def point(name,time,waits,pattern):points.append(dict(end,name=name,cycles=time,waits=waits,remaining=remaining,index=0,pattern=pattern,route=4 if name=='end' else 0,tick=5+waits,inputHeld=held if waits==i+1 else inputs[i-1] if i else 0,inputPressed=pressed if waits==i+1 else inputs[i-1]&~(inputs[i-2] if i>1 else 0) if i else 0))
        point('wait',base+4,i,progress)
        for j,start in enumerate((base+100,base+37000)):
            irqs.append(dict(kind='stat',start=start,end=start+288,returnAddress=0x261d,phases={}))
            rasters.extend([dict(boundary='begin',cycle=start),dict(boundary='end',cycle=start+288)])
        r=dict(kind='vblank',start=base+65000,tick=5+i,countdown=54,held=held,pressed=pressed,returnAddress=0x261d,phases={});time=r['start']
        for name,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,116,240,64,68,60)):time+=cost;r['phases'][name]=time
        r['end']=time+120;irqs.append(r)
        raster=[(0xff40,0xfb),(0xff42,88),(0xff42,88),(0xff45,103),(0xc099,2),(0xff40,0xc3),(0xff42,0),(0xff45,23),(0xc099,1)]
        writes.extend(dict(cycle=base+(200+16*j if j<5 else 37100+16*(j-5)),address=a,value=v) for j,(a,v) in enumerate(raster))
        point('ready',base+66900,i+1,progress);point('unlockEntry',base+66924,i+1,progress)
        if pressed:
            progress+=1
            if progress==4:progress=0
            writes.extend([dict(cycle=base+66960,address=0xc0b5,value=0x15+progress),dict(cycle=base+66980,address=0xc0b6,value=0x2b)])
        if i==len(inputs)-1:point('end',base+67024,i+1,progress)
        else:
            for j,name in enumerate(('unlockReturned','startDecision','selectDecision','actionDecision','timer','timerStored')):
                if name=='timerStored':remaining-=1
                point(name,base+67024+4*j,i+1,progress)
    return dict(inputCase='sequence',parentControlMemorySha256='parent',storageReadOwner='direct-vram-title-v1',reference=dict(titleStorageObserver='direct-vram-title-v1'),points=points,interrupts=irqs,rasters=rasters,writes=writes,beforeMaps=[19]*2048,maps=[19]*2048),parent

class UnlockEvidence(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete(self):self.assertEqual(len(analyze(self.data,self.parent)),9)
    def test_detached_page(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_detached_control(self):self.data['parentControlMemorySha256']='other';self.reject()
    def test_direct_storage_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_direct_storage_provenance(self):self.data['reference']={};self.reject()
    def test_preserved_maps(self):self.data['maps'][2047]=0;self.reject()
    def test_attached_maps(self):self.parent['maps'][0]=0;self.reject()
    def test_native_progress(self):self.data['points'][22]['pattern']=3;self.reject()
    def test_remaining_timer(self):self.data['points'][-1]['remaining']-=1;self.reject()
    def test_wrong_route(self):self.data['points'][-1]['route']=1;self.reject()
    def test_no_page_advance(self):self.data['points'][-1]['index']=1;self.reject()
    def test_held_not_fresh(self):self.data['interrupts'][11]['pressed']=64;self.reject()
    def test_wrong_order(self):self.data['interrupts'][8]['held']=128;self.data['interrupts'][8]['pressed']=128;self.reject()
    def test_no_game_timer_spend(self):self.data['points'][-1]['countdown']=53;self.reject()
    def test_complete_service_sequence(self):self.data['interrupts'].pop();self.reject()
    def test_complete_rasters(self):self.data['rasters'].pop();self.reject()
    def test_complete_stores(self):self.data['writes'].pop();self.reject()
    def test_wrong_pointer_projection(self):self.data['writes'][-1]['value']=0;self.reject()
    def test_missing_boundary(self):self.data['points'].pop(3);self.reject()
    def test_actual_display_tick(self):self.data['interrupts'][2]['tick']=4;self.reject()
    def test_fixed_case_controls(self):
        events=[['tick',100,True]];case='combined';prefix=[['tick',10,True]]
        parent=dict(controlMemorySha256='parent',romSha256='rom')
        manifest=dict(splitFrames=10,inputCase=case,parentControlMemorySha256='parent',parentEventsSha256=event_sha(events),setupSha256='setup',romSha256='rom',controlDifferences=[],prefixMemorySha256='prefix',prefixControlHashes=['prefix']*2,controlMemorySha256='full',unhookedControlHashes=['full']*2)
        self.assertEqual(attachment(parent,manifest,events,prefix+tail(case),'setup'),prefix)
        with self.assertRaises(ValueError):attachment(parent,manifest,events,prefix+tail('sequence'),'setup')
        manifest['unhookedControlHashes'][1]='different'
        with self.assertRaises(ValueError):attachment(parent,manifest,events,prefix+tail(case),'setup')
    def test_long_held_input_is_explicit(self):self.assertIn(['tick',12,True],tail('held'))
    def test_direction_reset_case_is_distinct(self):self.assertNotEqual(tail('reset'),tail('sequence'))

if __name__=='__main__':unittest.main()
