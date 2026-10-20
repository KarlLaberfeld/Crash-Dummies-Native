"""Synthetic control/storage integrity; not a source timing qualification."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_password_reference import analyze,attachment,TAIL,event_sha

def fixture():
    names=['begin','closeCall']+['closeWait','closeReady','centerStored']*40+['clearEntry','closeReturned','clearEntry','clearReturned','textReturned','musicWaitReturned','musicReady']+['openWait','openReady','openStored']*40+['openReturned','end']
    points=[];irqs=[];rasters=[];writes=[];tick=65520;count=0;center=0;y=112
    for i,name in enumerate(names):
        now=1000+i*10000
        if name in ('closeReady','openReady','clearReturned','musicWaitReturned'):
            start=now-4000
            for j in range(2 if count<4 else 3):
                stamp=start-3000+j*700;irqs.append(dict(kind='stat',start=stamp,end=stamp+352,returnAddress=0x261d));rasters.extend([dict(boundary='begin',cycle=stamp),dict(boundary='end',cycle=stamp+352)])
            r=dict(kind='vblank',start=start,tick=tick,countdown=54,held=0,pressed=0,phases={},voiceStates=[dict(active=0) for _ in range(6)],returnAddress=0x261d)
            time=start
            for phase,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,116,240,64,68,60)):time+=cost;r['phases'][phase]=time
            r['end']=time+120;irqs.append(r);tick=(tick+1)&65535;count+=1
        if name in ('centerStored','openStored'):
            closing=name=='centerStored';center=(center+(-2 if closing else 2))&255;y+=-1 if closing else 1
            writes.extend([dict(cycle=now-52,address=0xff4a,value=y),dict(cycle=now-16,address=0xc09c,value=center)])
        points.append(dict(name=name,cycles=now,tick=tick,countdown=54,center=center,windowY=y,display=0,held=16 if not count else 0,pressed=16 if not count else 0,song=7 if i>=names.index('musicReady') else 1,musicEnabled=1,stat=1,lcdc=0xc3,scrollY=0,lyc=23))
    glyphs=[];clears=[p for p in points if p['name']=='clearEntry']
    for p in clears:
        glyphs.extend(dict(cycle=p['cycles']+100+4*i,address=0x9dc0+i,value=0) for i in range(320))
    stamp=next(p['cycles'] for p in points if p['name']=='clearReturned')+100
    for column,row,length in ((5,16,10),(3,19,14),(6,21,8)):
        for i in range(length):glyphs.append(dict(cycle=stamp,address=0x9c00+32*row+column+i,value=i+1));stamp+=100
    maps=[19]*2048
    for w in glyphs:maps[w['address']-0x9800]=w['value']
    parent=dict(controlMemorySha256='parent',points=[dict(points[0],inputHeld=16,inputPressed=16)],maps=[19]*2048)
    data=dict(version=1,parentControlMemorySha256='parent',storageReadOwner='direct-vram-title-v1',reference=dict(titleStorageObserver='direct-vram-title-v1'),points=points,interrupts=irqs,rasters=rasters,writes=writes,glyphs=glyphs,polls=[dict(cycle=w['cycle']-1,mode=0) for w in glyphs],beforeMaps=[19]*2048,maps=maps,objectsUnchanged=True,digits=[0]*8,cursor=0)
    return data,parent

class PasswordEvidence(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete(self):self.assertEqual(len(analyze(self.data,self.parent)),82)
    def test_ancestry(self):self.data['parentControlMemorySha256']='other';self.reject()
    def test_parent_cycle(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_parent_input(self):self.parent['points'][0]['inputPressed']=0;self.reject()
    def test_callback(self):self.data['points'][2]['display']=1;self.reject()
    def test_missing_step(self):self.data['points'].pop(2);self.reject()
    def test_center_motion(self):self.data['points'][4]['center']=0;self.reject()
    def test_window_motion(self):self.data['points'][4]['windowY']=112;self.reject()
    def test_counter(self):self.data['points'][-1]['tick']-=1;self.reject()
    def test_countdown(self):self.data['points'][-1]['countdown']=53;self.reject()
    def test_music_switch(self):self.data['points'][-1]['song']=1;self.reject()
    def test_music_disabled(self):self.data['points'][-1]['musicEnabled']=0;self.reject()
    def test_missing_service(self):self.data['interrupts'].pop();self.reject()
    def test_missing_raster_extent(self):self.data['interrupts'].pop(0);self.data['rasters']=self.data['rasters'][2:];self.reject()
    def test_detached_raster(self):self.data['rasters'][0]['cycle']+=4;self.reject()
    def test_voice_count(self):next(p for p in self.data['interrupts'] if p['kind']=='vblank')['voiceStates'].pop();self.reject()
    def test_fresh_input(self):next(p for p in self.data['interrupts'] if p['kind']=='vblank')['pressed']=16;self.reject()
    def test_display_work(self):next(p for p in self.data['interrupts'] if p['kind']=='vblank')['phases']['bookkeeping']+=4;self.reject()
    def test_storage_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_storage_provenance(self):self.data['reference']={};self.reject()
    def test_objects(self):self.data['objectsUnchanged']=False;self.reject()
    def test_digits(self):self.data['digits'][0]=1;self.reject()
    def test_cursor(self):self.data['cursor']=1;self.reject()
    def test_map(self):self.data['maps'][0]=1;self.reject()
    def test_clear(self):self.data['glyphs'][0]['value']=1;self.reject()
    def test_text_rows(self):self.data['glyphs'][-1]['address']-=1;self.reject()
    def test_missing_glyph(self):self.data['glyphs'].pop();self.reject()
    def test_reordered_access(self):self.data['polls'][0]['cycle']=0;self.reject()
    def test_readiness_mode(self):self.data['polls'][0]['mode']=4;self.reject()
    def test_readiness_complete(self):self.data['polls'].pop();self.reject()
    def test_actual_motion_store(self):self.data['writes'][0]['value']=112;self.reject()
    def test_actual_motion_complete(self):self.data['writes'].pop();self.reject()

class PasswordControls(unittest.TestCase):
    def setUp(self):
        self.events=[['tick',4,True]];self.changed=self.events+copy.deepcopy(TAIL);self.parent=dict(controlMemorySha256='parent',romSha256='rom')
        self.child=dict(inputCase='first-password',parentControlMemorySha256='parent',parentEventsSha256=event_sha(self.events),setupSha256='setup',romSha256='rom',controlMemorySha256='child',controlDifferences=[],prefixControlHashes=['parent']*2,unhookedControlHashes=['child']*2)
    def check(self):attachment(self.parent,self.child,self.events,self.changed,'setup')
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_complete(self):self.check()
    def test_prefix(self):self.changed[0]=['tick',3,True];self.reject()
    def test_tail(self):self.changed[-1]=['tick',99,True];self.reject()
    def test_setup(self):self.child['setupSha256']='changed';self.reject()
    def test_parent(self):self.child['parentControlMemorySha256']='changed';self.reject()
    def test_events(self):self.child['parentEventsSha256']='changed';self.reject()
    def test_rom(self):self.child['romSha256']='changed';self.reject()
    def test_repeated_prefix(self):self.child['prefixControlHashes'][1]='changed';self.reject()
    def test_repeated_full(self):self.child['unhookedControlHashes'].pop();self.reject()
    def test_control_difference(self):self.child['controlDifferences']=['changed'];self.reject()

if __name__=='__main__':unittest.main()
