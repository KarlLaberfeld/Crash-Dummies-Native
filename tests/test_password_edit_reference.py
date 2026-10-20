"""Synthetic fresh-input, pointer-publication and comparison batch integrity."""
import sys,copy,argparse,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from password_edit_reference import analyze,tail,attachment,event_sha,compare_many

def fixture():
    points=[];irqs=[];rasters=[];writes=[]
    names=('wait','ready','pointerReady','leftReturned','rightReturned','upReturned','downReturned','submitDecision')
    for i in range(2):
        base=1000+20000*i;held=8 if i else 0
        for j in range(2):
            start=base+1000+j*1000;body=460 if j==0 else 384;irqs.append(dict(kind='stat',start=start,end=start+body,returnAddress=0x261d))
            before=(1,0xc3,0,23) if j==0 else (2,0xfb,88,103);after=(2,0xfb,88,103) if j==0 else (1,0xc3,0,23)
            rasters.extend([dict(boundary='begin',cycle=start,**dict(zip(('stat','lcdc','scrollY','lyc'),before))),dict(boundary='end',cycle=start+body,**dict(zip(('stat','lcdc','scrollY','lyc'),after)))])
            stores=[(220,0xff40,0xfb),(256,0xff42,88),(344,0xff42,88),(364,0xff45,103),(388,0xc099,2)] if j==0 else [(252,0xff40,0xc3),(268,0xff42,0),(288,0xff45,23),(308,0xc099,1)]
            writes.extend(dict(cycle=start+offset,address=address,value=value) for offset,address,value in stores)
        r=dict(kind='vblank',start=base+4000,tick=(65535+i)&65535,countdown=54,held=held,pressed=held,phases={},voiceStates=[dict(active=0) for _ in range(6)],returnAddress=0x261d)
        time=r['start']
        for phase,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,116,240,64,68,60)):time+=cost;r['phases'][phase]=time
        r['end']=time+120;irqs.append(r)
        for j,name in enumerate(names):points.append(dict(name=name,cycles=base if j==0 else base+8000+j*1000,tick=(65535+i+(j!=0))&65535,countdown=54,cursor=0,submit=0,held=held if j else 0,pressed=held if j else 0,**{'digit'+str(n):0 for n in range(8)}))
        writes.extend(dict(cycle=base+9500+16*j,address=address,value=value) for j,(address,value) in enumerate(((0xc101,56),(0xc100,96),(0xc102,0x45),(0xc103,128))))
    points.append(dict(points[-1],name='end',cycles=points[-1]['cycles']+8,submit=8))
    objects=[96,56,0x45,128]+[0]*252
    parent=dict(controlMemorySha256='parent',maps=[19]*2048,points=[dict(points[0])])
    data=dict(version=1,inputCase='submit-start',parentControlMemorySha256='parent',storageReadOwner='direct-vram-title-v1',reference=dict(titleStorageObserver='direct-vram-title-v1'),points=points,interrupts=irqs,writes=writes,polls=[],rasters=rasters,beforeMaps=[19]*2048,maps=[19]*2048,beforeObjects=[0]*256,objects=objects)
    return data,parent

class EditEvidence(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete(self):self.assertEqual(len(analyze(self.data,self.parent)),2)
    def test_parent(self):self.data['parentControlMemorySha256']='other';self.reject()
    def test_entry_cycle(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_entry_cursor(self):self.data['points'][0]['cursor']=1;self.reject()
    def test_order(self):self.data['points'].pop(2);self.reject()
    def test_cursor_bounds(self):self.data['points'][3]['cursor']=8;self.reject()
    def test_digit_bounds(self):self.data['points'][3]['digit0']=11;self.reject()
    def test_unowned_digit(self):self.data['points'][5]['digit0']=1;self.reject()
    def test_actual_tick(self):self.data['points'][3]['tick']=1;self.reject()
    def test_held_state(self):self.data['points'][3]['held']=8;self.reject()
    def test_fresh_state(self):self.data['points'][3]['pressed']=8;self.reject()
    def test_counter(self):self.data['points'][3]['countdown']=53;self.reject()
    def test_submit_early(self):self.data['interrupts'][2]['held']=8;self.data['interrupts'][2]['pressed']=8;self.reject()
    def test_wrong_submit(self):self.data['points'][-1]['submit']=1;self.reject()
    def test_terminal_tick(self):self.data['points'][-1]['tick']=0;self.reject()
    def test_voices(self):self.data['interrupts'][2]['voiceStates'].pop();self.reject()
    def test_display_work(self):self.data['interrupts'][2]['phases']['bookkeeping']+=4;self.reject()
    def test_storage_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_storage_provenance(self):self.data['reference']={};self.reject()
    def test_before_objects(self):self.data['beforeObjects'][0]=1;self.reject()
    def test_objects(self):self.data['objects'][0]=0;self.reject()
    def test_map(self):self.data['maps'][2047]=0;self.reject()
    def test_pointer_missing(self):self.data['writes'].pop(9);self.reject()
    def test_pointer_lag(self):self.data['writes'][9]['value']=64;self.data['objects'][1]=64;self.reject()
    def test_writes_reordered(self):self.data['writes'][0]['cycle']=self.data['writes'][1]['cycle'];self.reject()
    def test_access_mode(self):self.data['polls']=[dict(cycle=12000,mode=4)];self.reject()
    def test_raster_missing(self):self.data['interrupts'].pop(0);self.reject()
    def test_raster_boundary(self):self.data['rasters'][0]['cycle']+=4;self.reject()
    def test_raster_work(self):self.data['interrupts'][0]['end']-=4;self.data['rasters'][1]['cycle']-=4;self.reject()
    def test_raster_geometry(self):self.data['rasters'][0]['lyc']=24;self.reject()
    def test_raster_store(self):self.data['writes'][0]['value']=0;self.reject()

class EditControls(unittest.TestCase):
    def setUp(self):
        self.events=[['tick',4,True]];self.parent=dict(controlMemorySha256='parent',romSha256='rom');self.child=dict(inputCase='submit-start',parentControlMemorySha256='parent',parentEventsSha256=event_sha(self.events),setupSha256='setup',romSha256='rom',controlMemorySha256='child',controlDifferences=[],prefixControlHashes=['parent']*2,unhookedControlHashes=['child']*2);self.changed=self.events+tail('submit-start')
    def check(self):attachment(self.parent,self.child,self.events,self.changed,'setup')
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_complete(self):self.check()
    def test_prefix(self):self.changed[0]=['tick',3,True];self.reject()
    def test_tail(self):self.changed.pop();self.reject()
    def test_setup(self):self.child['setupSha256']='other';self.reject()
    def test_parent(self):self.child['parentControlMemorySha256']='other';self.reject()
    def test_repetition(self):self.child['unhookedControlHashes'].pop();self.reject()
    def test_valid_digits_required(self):
        with self.assertRaises(ValueError):tail('valid-0')
    def test_valid_digit_bounds(self):
        with self.assertRaises(ValueError):tail('valid-0',[0]*8)
    def test_valid_digits(self):self.assertTrue(tail('valid-0',[1,2,3,4,5,6,7,10]))
    def test_held_not_repeated_press_events(self):self.assertEqual(sum(e==['press','up'] for e in tail('held')),1)

class BatchQualification(unittest.TestCase):
    def cases(self):return [argparse.Namespace(native_base=Path('case'+str(i)),password_base=Path('parent'),edit_out=Path('ref'+str(i)),edit_control=Path('control'+str(i)),unlock_base=Path('unlock')) for i in range(2)]
    def test_one_full_parent_and_individual_children(self):
        cases=self.cases()
        with patch('air_title_password_reference.compare') as parent,patch('password_edit_reference.compare') as child:
            compare_many(cases);self.assertEqual(parent.call_count,1);self.assertEqual(parent.call_args.args[0].native_base,Path('parent'));self.assertEqual(child.call_count,2);self.assertTrue(all(c.kwargs['_parent_qualified'] for c in child.call_args_list))
    def test_mixed_parent_rejected(self):
        cases=self.cases();cases[1].password_base=Path('different')
        with patch('air_title_password_reference.compare') as parent:
            with self.assertRaises(ValueError):compare_many(cases)
            parent.assert_not_called()
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):compare_many([])

if __name__=='__main__':unittest.main()
