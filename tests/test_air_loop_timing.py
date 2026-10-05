from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_loop_timing import analyze, stat_cycles, wait_active_cycles, VERSION


class AirLoopTests(unittest.TestCase):
    def data(self):
        return dict(version=VERSION,interrupts=[dict(kind='vblank',start=100,end=200)],
            points=[dict(name='wait',cycles=0,counter=255),dict(name='resume',cycles=400,counter=0),
                    dict(name='update',cycles=448,counter=0),dict(name='done',cycles=500,counter=0),
                    dict(name='wait',cycles=552,counter=0)])

    def test_wait_counter_wrap_and_fixed_main_loop_costs(self):
        result=analyze(self.data())
        self.assertEqual(result['sourceMismatches'],[])
        self.assertEqual(result['waits'],1)
        self.assertEqual(result['idleRange'],[144,144])
        self.assertFalse(result['runtimeSchedulingFixed'])

    def test_source_stat_and_wait_wake_costs(self):
        self.assertEqual(stat_cycles(4),288)
        self.assertEqual(stat_cycles(0),248)
        self.assertEqual(stat_cycles(1),-1)
        self.assertEqual(wait_active_cycles(0),120)
        self.assertEqual(wait_active_cycles(1),156)
        with self.assertRaises(ValueError):wait_active_cycles(-1)

    def test_display_before_counter_snapshot_needs_a_later_service(self):
        data=self.data()
        data['interrupts']=[dict(kind='vblank',start=44,end=144,returnAddress=0x2618),
                            dict(kind='vblank',start=180,end=280,returnAddress=0x261d)]
        data['points'][1]['counter']=1
        result=analyze(data)
        self.assertEqual(result['sourceMismatches'],[])
        self.assertEqual(result['waitDisplayCounts'],[2])
        self.assertEqual(result['idleRange'],[8,8])
        data['interrupts'][0]['returnAddress']=0x261d
        with self.assertRaises(ValueError):analyze(data)

    def test_partial_final_interrupt_is_explicit_and_never_completed_work(self):
        data=self.data()
        data.update(captureComplete=False,partialFinalInterrupt=dict(kind='vblank',start=600,captureEnd=620))
        result=analyze(data)
        self.assertFalse(result['captureComplete'])
        self.assertEqual(result['waits'],1)
        data['partialFinalInterrupt']['start']=300
        with self.assertRaises(ValueError):analyze(data)

    def test_final_wait_retains_busy_gate(self):
        data=self.data();data['points']=data['points'][:2]
        data['points'][0].update(name='finalWait',ready=0)
        data['points'][1].update(name='finalResume',ready=0)
        self.assertEqual(analyze(data)['waitDisplayCounts'],[1])
        self.assertEqual(analyze(data)['finalWaits'],1)
        data['points'][1]['ready']=1
        with self.assertRaises(ValueError):analyze(data)

    def test_missing_counter_change_or_resume_is_rejected(self):
        data=self.data();data['points'][1]['counter']=255
        with self.assertRaises(ValueError):analyze(data)
        data=self.data();data['interrupts']=[]
        with self.assertRaises(ValueError):analyze(data)
        data=self.data();data['points'][1]['name']='done'
        with self.assertRaises(ValueError):analyze(data)

    def test_prefix_work_difference_is_not_treated_as_halt_idle(self):
        data=self.data();data['points'][2]['cycles']=452
        self.assertEqual(analyze(data)['sourceMismatches'][0]['source'],48)

    def test_unknown_stat_callback_cannot_certify_work(self):
        data=self.data();data['interrupts'].append(dict(kind='stat',selector=1,start=600,end=700))
        self.assertEqual(analyze(data)['unknownStatServices'],[1])


if __name__=='__main__':unittest.main()
