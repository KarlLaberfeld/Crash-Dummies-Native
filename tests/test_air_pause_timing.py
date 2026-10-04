from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_pause_timing import analyze,copy_cycles,script_cycles,VERSION,PHASES


class AirPauseTests(unittest.TestCase):
    def fixture(self):
        points=[]
        def point(name,cycles,counter=9,selector=1,audio=0):
            points.append(dict(name=name,cycles=cycles,counter=counter,selector=selector,audioEnabled=audio))
        point('enter',0,selector=4,audio=255);point('copyEntry',192);point('script',16104)
        point('wait',20500);point('wake',25000,10);point('wait',25032,10);point('wake',95000,11)
        point('restore',95028,11);point('restoreAudio',110940,11);point('return',111080,11,4,255);point('update',111096,11,4,255)
        copies=[dict(start=a,end=b,size=n,failedPolls=0,destinationWraps=0) for a,b,n in
            ((252,2528,20),(2596,16104,128),(95088,97364,20),(97432,110940,128))]
        interrupts=[]
        for start,tick in ((22000,65535),(92000,0)):
            phases={};now=start+180
            for name,cost in zip(PHASES.values(),(704,280,160,240,64,68,60,120)):
                phases[name]=now;now+=cost
            interrupts.append(dict(kind='vblank',start=start,end=now,displaySelector=1,audioEnabled=0,
                resetEnabled=1,held=33,resetLatched=0,phases=phases,tick=tick,world=[42,3,9],effectRequest=-1))
        return dict(version=VERSION,pauses=[dict(points=points,copies=copies,interrupts=interrupts,scriptFailedPolls=0)])

    def test_pause_freezes_world_but_wraps_global_counter(self):
        result=analyze(self.fixture())
        self.assertEqual(result['sourceMismatches'],[])
        self.assertEqual(result['frozenGameplayIntervals'],1)
        self.assertEqual(result['waits'],2)
        self.assertFalse(result['runtimeSchedulingFixed'])

    def test_copy_poll_and_destination_wrap_are_separate_work(self):
        self.assertEqual(copy_cycles(20,0),2276)
        self.assertEqual(copy_cycles(128,0),13508)
        self.assertEqual(copy_cycles(20,1,1)-copy_cycles(20,0),36)
        self.assertEqual(script_cycles(1)-script_cycles(0),32)
        for args in ((0,0),(1,-1),(1,0,2)):
            with self.assertRaises(ValueError):copy_cycles(*args)

    def test_active_work_difference_cannot_be_attributed_to_idle(self):
        data=self.fixture();data['pauses'][0]['points'][1]['cycles']+=4
        self.assertTrue(analyze(data)['sourceMismatches'])

    def test_moving_world_or_stopped_global_counter_is_rejected(self):
        for field,value in (('world',[43,3,9]),('tick',65535)):
            data=self.fixture();data['pauses'][0]['interrupts'][1][field]=value
            with self.assertRaises(ValueError):analyze(data)

    def test_incomplete_wait_copy_or_music_restore_is_rejected(self):
        for kind in range(3):
            data=self.fixture();p=data['pauses'][0]
            if kind==0:p['points'][4]['name']='restore'
            elif kind==1:p['copies'].pop()
            else:p['points'][-1]['audioEnabled']=0
            with self.assertRaises(ValueError):analyze(data)

    def test_unmodeled_effect_or_missing_display_phase_is_rejected(self):
        for kind in range(2):
            data=self.fixture();r=data['pauses'][0]['interrupts'][0]
            if kind==0:r['effectRequest']=4
            else:r['phases'].pop('dma')
            with self.assertRaises(ValueError):analyze(data)


if __name__=='__main__':unittest.main()
