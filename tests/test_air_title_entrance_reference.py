"""Synthetic first-instruction incoming-fade evidence integrity."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_entrance_reference import analyze
from air_title_picture_reference import VOICE_FIELDS
def fixture():
    irqs=[];writes=[dict(cycle=1040,address=0xc09d,value=1)];raw=[('begin',1000,0,0),('firstInstruction',1032,0,0),('fadeEntry',1072,0,0)];now=1092;index=0
    for palette,color in enumerate((0,0,64,80,144,160,208,228),1):
        raw.append(('palette',now,palette,index))
        writes += [dict(cycle=now+8,address=0xff47,value=color),dict(cycle=now+28,address=0xff49,value=color&0xf3),dict(cycle=now+56,address=0xff48,value=color&0xcf)];now+=76
        for step in range(4):
            raw.append(('wait',now,palette,index));start=10000+70224*index
            irqs.append(dict(kind='stat',start=start-2000,end=start-1712,selector=5,returnAddress=0x261d,tick=(65520+index)&65535,countdown=54,phases={}))
            r=dict(kind='vblank',start=start,selector=5,returnAddress=0x261d,tick=(65520+index)&65535,countdown=54,held=0,pressed=0,phases={},voiceStates=[dict(active=0,**dict.fromkeys(VOICE_FIELDS,0)) for _ in range(6)])
            time=start
            for name,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,144,240,64,68,60)):time+=cost;r['phases'][name]=time
            r['end']=time+120;irqs.append(r);writes += [dict(cycle=start-1784,address=0xff42,value=0),dict(cycle=start+1284,address=0xff42,value=0)]
            index+=1;now=r['end']+72;raw.append(('tail',now,palette,index));now+=16 if step<3 else 28
        if palette==8:now+=12
    raw.append(('end',now,8,32));writes.sort(key=lambda p:p['cycle']);services=[p for p in irqs if p['kind']=='vblank'];points=[]
    for name,time,palettes,waits in raw:
        p=dict(name=name,cycles=time,palettes=palettes,waits=waits,tick=(65520+sum(r['end']+16<=time for r in services))&65535,countdown=54,alternate=int(time>=1056),inputHeld=0,inputPressed=0,display=5,stat=5,lcdc=0xd1,lyc=95,musicEnabled=1)
        for key,address in [('bgp',0xff47),('obp0',0xff48),('obp1',0xff49)]:
            committed=[w for w in writes if w['address']==address and w['cycle']+12<=time];p[key]=committed[-1]['value'] if committed else 0
        points.append(p)
    data=dict(points=points,interrupts=irqs,writes=writes,storageReadOwner='direct-vram-instruction-v1',reference=dict(instructionStorageObserver='direct-vram-instruction-v1'),beforeMaps=[19]*2048,maps=[19]*2048,beforeTiles=[37]*1024,tiles=[37]*1024,objectsUnchanged=True)
    return data,dict(points=[dict(points[0])],maps=[19]*2048,tiles=[37]*1024)
class EntranceEvidence(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete(self):self.assertEqual(len(analyze(self.data,self.parent)),32)
    def test_parent_boundary(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_first_branch(self):self.data['points'][1]['cycles']+=4;self.reject()
    def test_wrong_alternate_owner(self):self.data['points'][0]['alternate']=1;self.reject()
    def test_alternate_store(self):self.data['writes'][0]['value']=0;self.reject()
    def test_missing_selector_store(self):self.data['writes'].pop(0);self.reject()
    def test_direct_storage_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_direct_storage_provenance(self):self.data['reference']={};self.reject()
    def test_attached_picture(self):self.parent['tiles'][0]=0;self.reject()
    def test_tiles_unchanged(self):self.data['tiles'][0]=0;self.reject()
    def test_maps_unchanged(self):self.data['maps'][2047]=0;self.reject()
    def test_objects_unchanged(self):self.data['objectsUnchanged']=False;self.reject()
    def test_complete_waits(self):self.data['points'].pop(5);self.reject()
    def test_no_wait_shortcut(self):self.data['points'][-1]['waits']=31;self.reject()
    def test_music_services_complete(self):self.data['interrupts'].pop();self.reject()
    def test_voice_observations_complete(self):self.data['interrupts'][1]['voiceStates'].pop();self.reject()
    def test_music_work_owner(self):self.data['interrupts'][1]['phases']['bookkeeping']+=128;self.reject()
    def test_no_result_countdown(self):self.data['points'][-1]['countdown']=22;self.reject()
    def test_retained_source_tick(self):self.data['interrupts'][1]['tick']=5;self.reject()
    def test_actual_boundary_tick(self):self.data['points'][-1]['tick']-=1;self.reject()
    def test_palette_masks(self):next(p for p in self.data['writes'] if p['address']==0xff49)['value']=255;self.reject()
    def test_palette_commit(self):self.data['points'][5]['bgp']=255;self.reject()
    def test_scroll_store_complete(self):self.data['writes'].pop(5);self.reject()
    def test_terminal_palette(self):self.data['points'][-1]['bgp']=0;self.reject()
    def test_first_instruction_route_delay(self):self.data['points'][2]['cycles']+=4;self.reject()
if __name__=='__main__':unittest.main()
