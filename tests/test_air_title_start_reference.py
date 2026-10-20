"""Synthetic fade/stop evidence, interrupted reset and input-only extension guards."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_start_reference import analyze,attachment,event_sha,IRQ_PHASES


class StartEvidence(unittest.TestCase):
    def setUp(self):
        names=['begin','fadeEntry']+['palette','wait','tail','wait','tail','wait','tail','wait','tail']*8+['fadeReturned','audioStop','stopEntry','resetEntry','stateCleared','presetsReady','waveReady','resetReturned','audioDisabled','end']
        points=[];irqs=[];rasters=[];writes=[];palettes=waits=displays=0;color=0xe4
        colors=[0xe4,0xe4,0xe4,0xa4,0x90,0x50,0x50,0]
        top=[(0xff40,0xfb),(0xff42,88),(0xff42,88),(0xff45,103),(0xc099,2)]
        bottom=[(0xff40,0xc3),(0xff42,0),(0xff45,23),(0xc099,1)]
        def stat(start,stores):
            irqs.append(dict(kind='stat',start=start,end=start+100));rasters.extend([dict(boundary='begin',cycle=start),dict(boundary='end',cycle=start+100)])
            writes.extend(dict(cycle=start+2+j,address=a,value=v) for j,(a,v) in enumerate(stores))
        for i,name in enumerate(names):
            now=1000+1000*i
            if name=='palette':palettes+=1
            if name=='tail':waits+=1
            if name in ('tail','audioStop'):
                stat(now-800,top);stat(now-600,bottom);start=now-400
                irqs.append(dict(kind='vblank',start=start,end=start+90,tick=(65520+displays)&65535,countdown=54,held=0,pressed=0,phases={n:start+10*(j+1) for j,n in enumerate(IRQ_PHASES.values())}));displays+=1
            if name=='stateCleared':stat(now-500,top)
            points.append(dict(name=name,cycles=now,palettes=palettes,waits=waits,tick=(65520+displays)&65535,countdown=54,bgp=color,obp0=color&0xcf,obp1=color&0xf3,musicEnabled=int(name not in ('audioDisabled','end')),inputHeld=0 if displays else 8,inputPressed=0 if displays else 8,stat=1,lcdc=0xc3,scrollY=0,lyc=23))
            if name=='palette':
                color=colors[palettes-1];writes.extend([dict(cycle=now+20,address=0xff47,value=color),dict(cycle=now+40,address=0xff49,value=color&0xf3),dict(cycle=now+60,address=0xff48,value=color&0xcf)])
            if name=='resetEntry':writes.append(dict(cycle=now+4,address=0xff26,value=0))
            if name=='resetReturned':writes.append(dict(cycle=now+4,address=0xffcf,value=0))
        maps=[19]*2048;self.parent=dict(inputCase='start',controlMemorySha256='parent',points=[dict(points[0],route=2)],maps=maps[:])
        self.data=dict(parentControlMemorySha256='parent',storageReadOwner='direct-vram-title-v1',reference=dict(titleStorageObserver='direct-vram-title-v1'),points=points,interrupts=irqs,rasters=rasters,writes=sorted(writes,key=lambda p:p['cycle']),beforeMaps=maps[:],maps=maps[:])
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete_with_interrupted_reset_and_tick_wrap(self):self.assertEqual(len(analyze(self.data,self.parent)),33)
    def test_parent_route(self):self.parent['points'][-1]['route']=3;self.reject()
    def test_parent_hash(self):self.data['parentControlMemorySha256']='other';self.reject()
    def test_direct_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_observer_identity(self):self.data['reference']={};self.reject()
    def test_complete_fade(self):self.data['points'].pop(10);self.reject()
    def test_all_waits(self):self.data['points'][-1]['waits']=31;self.reject()
    def test_frozen_countdown(self):self.data['points'][-1]['countdown']=53;self.reject()
    def test_final_white_palettes(self):self.data['points'][-1]['bgp']=0xe4;self.reject()
    def test_no_early_audio_disable(self):self.data['points'][10]['musicEnabled']=0;self.reject()
    def test_audio_disabled_at_end(self):self.data['points'][-1]['musicEnabled']=1;self.reject()
    def test_detached_maps(self):self.parent['maps'][0]=0;self.reject()
    def test_no_map_mutation(self):self.data['maps'][0]=0;self.reject()
    def test_reset_stat_retained(self):self.data['interrupts'].pop();self.reject()
    def test_no_audio_display_during_reset(self):
        self.data['interrupts'][-1]['kind']='vblank';self.reject()
    def test_actual_boundary_ticks(self):self.data['points'][-1]['tick']-=1;self.reject()
    def test_actual_input_edges(self):self.data['interrupts'][2]['pressed']=8;self.reject()
    def test_no_extra_raster_store(self):self.data['writes'].append(dict(cycle=999999,address=0xc099,value=1));self.reject()
    def test_all_palette_stores(self):self.data['writes'].pop(0);self.reject()
    def test_reset_audio_register_store(self):next(p for p in self.data['writes'] if p['address']==0xff26)['value']=1;self.reject()
    def test_no_escaped_vector(self):self.data['interrupts'][-1]['end']=self.data['points'][-1]['cycles'];self.reject()
    def test_monotonic_boundaries(self):self.data['points'][1]['cycles']=self.data['points'][0]['cycles'];self.reject()


class StartExtension(unittest.TestCase):
    def setUp(self):
        self.events=[['press','start'],['tick',10,True]];self.changed=self.events+[['tick',80,True]]
        self.parent=dict(controlMemorySha256='parent',romSha256='rom')
        self.child=dict(parentControlMemorySha256='parent',parentEventsSha256=event_sha(self.events),setupSha256='setup',romSha256='rom',extensionFrames=80,controlDifferences=[],controlMemorySha256='child',unhookedControlHashes=['child']*2,prefixControlHashes=['parent']*2)
    def accept(self):attachment(self.parent,self.child,self.events,self.changed,'setup')
    def reject(self):
        with self.assertRaises(ValueError):self.accept()
    def test_exact_held_input_extension(self):self.accept()
    def test_no_parent_event_edit(self):self.changed[0]=['press','select'];self.reject()
    def test_no_new_button_event(self):self.changed.append(['press','a']);self.reject()
    def test_only_declared_frames(self):self.changed[-1][1]=81;self.reject()
    def test_no_setup_change(self):self.child['setupSha256']='other';self.reject()
    def test_same_parent_full_control(self):
        self.child['parentControlMemorySha256']='other';self.reject()
        self.child['parentControlMemorySha256']='parent';self.parent['controlDifferences']=['changed'];self.reject()
    def test_repeated_prefix_hash(self):self.child['prefixControlHashes'][0]='other';self.reject()
    def test_repeated_full_hash(self):self.child['unhookedControlHashes'].pop();self.reject()


if __name__=='__main__':unittest.main()
