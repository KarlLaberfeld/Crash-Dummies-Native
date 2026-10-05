from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_pause_compare import compare_bus,compare_graphics,paused_inputs


class NativePauseComparisonTests(unittest.TestCase):
    def fixture(self):
        objects=[dict(x=40,y=28)]+[dict(x=0,y=0) for _ in range(39)]
        prefix=dict(version=1,cycle=100000,scrollX=240,scrollY=36,windowX=7,windowY=136,objects=deepcopy(objects))
        original=dict(pauses=[dict(entryDmaSourceObjects=objects,points=[dict(pc=0x1476,cycles=200000,
            lcd=dict(scx=240,scy=36,wx=7,wy=136))],bus=[
                dict(phase='copy1',kind='read',address=0xff41,data=0xc0,cycles=200120),
                dict(phase='copy1',kind='write',address=0x8f80,data=29,cycles=200152)])])
        native=[dict(phase='copy1',kind='read',address=0xff41,value=0,cycle=100120),
                dict(phase='copy1',kind='write',address=0x8f80,value=29,cycle=100152)]
        return original,prefix,native

    def test_relative_comparison_checks_data_without_injecting_original_epoch(self):
        self.assertEqual(compare_bus(*self.fixture()),[])

    def test_shifted_or_changed_status_access_is_detected(self):
        for key in ('cycle','value','address'):
            original,prefix,native=self.fixture();native[0][key]+=1
            self.assertTrue(compare_bus(original,prefix,native))

    def test_missing_or_extra_event_is_not_a_matching_prefix(self):
        for missing in (True,False):
            original,prefix,native=self.fixture()
            if missing:native.pop()
            else:native.append(native[-1])
            with self.assertRaises(ValueError):compare_bus(original,prefix,native)

    def test_visible_geometry_and_scroll_are_comparison_targets(self):
        for field in ('x','y'):
            original,prefix,native=self.fixture();prefix['objects'][0][field]+=1
            self.assertEqual(compare_bus(original,prefix,native)[0]['owner'],'geometry')
        original,prefix,native=self.fixture();prefix['scrollX']+=1
        self.assertEqual(compare_bus(original,prefix,native)[0]['owner'],'scrollX')
        original,prefix,native=self.fixture();prefix['objects'][1]['x']=99
        self.assertEqual(compare_bus(original,prefix,native),[])

    def test_raw_display_samples_preserve_paused_coverage(self):
        data=[dict(service=i,displaySelector=s,held=h) for i,(s,h) in enumerate(((4,0),(4,8),(1,8),(1,0),(1,8),(4,0)))]
        before,paused=paused_inputs(data)
        self.assertEqual([s['held'] for s in before],[0,8])
        self.assertEqual([s['held'] for s in paused],[8,0,8])
        data[2]['service']=99
        with self.assertRaises(ValueError):paused_inputs(data)

    def test_graphics_read_back_requires_all_owned_stores(self):
        original,prefix,_=self.fixture();source=[];native=[]
        for i,(pc,name) in enumerate(((0x1476,'enter'),(0x14b9,'wait'),(0x14dc,'restoreAudio'))):
            source.append(dict(pc=pc,cycles=200000+1000*i,storageReadOwner='direct-vram-pause-v1',statusRow=list(range(20)),font=list(range(128))))
            native.append(dict(phase=name,cycle=100000+1000*i,**{'status'+str(j):j for j in range(20)},**{'font'+str(j):j for j in range(128)}))
        original['pauses'][0]['graphicsStates']=source
        self.assertEqual(compare_graphics(original,prefix,native),[])
        native[1]['font127']=0
        self.assertIn('font127',compare_graphics(original,prefix,native)[0]['fields'])
        for invalid in ('missing','blocked','unordered','byte'):
            a=deepcopy(original);b=deepcopy(native)
            if invalid=='missing':a['pauses'][0]['graphicsStates'].pop()
            elif invalid=='blocked':a['pauses'][0]['graphicsStates'][0]['storageReadOwner']='cpu-bus-read'
            elif invalid=='unordered':b.reverse()
            else:del b[0]['status0']
            with self.assertRaises(ValueError):compare_graphics(a,prefix,b)


if __name__=='__main__':unittest.main()
