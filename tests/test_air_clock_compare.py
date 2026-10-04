from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_clock_compare import compare_states, compare_services, compare_sprites, compare_phase_work
from air_timing import STAGES


class AirClockCompareTests(unittest.TestCase):
    def state(self):
        names='tick frame flags x y cameraX cameraY speed rate tilt count crash done waiting delay period transfer remaining map result seconds secondTicks random'.split()
        original=dict.fromkeys(names,0);original['handler']=0x23e2
        native=dict(original);native['handler']=0
        return original,native

    def test_clock_difference_is_never_normalized_away(self):
        original,native=self.state();native['tick']=1
        difference=compare_states([original],[native])
        self.assertEqual(difference[0]['fields'],{'tick':[0,1]})

    def test_result_means_completed_result_not_pending_finish_flags(self):
        original,native=self.state();native['result']=17
        self.assertEqual(compare_states([original],[native])[0]['fields']['result'],[0,17])

    def test_missing_or_excess_native_updates_are_rejected(self):
        original,native=self.state()
        for rows in ([],[native,native]):
            with self.assertRaises(ValueError):compare_states([original],rows)

    def test_service_counter_and_closed_gate_are_required(self):
        original=dict(tick=10,transfer=0,phases=dict(display=0,bookkeeping=100,effects=200,audioBank=264,music=332,restore=800),
            displayWorkload=dict(cursor=12),effectWorkload=dict(pending=255),hudBar=[0]*6)
        native=dict(service=0,tick=10,ready=0,display=100,effects=64,music=468,cursor=0,pending=-1,**{'bar'+str(i):0 for i in range(6)})
        self.assertEqual(compare_services([original],[native]),[])
        native['ready']=1
        self.assertEqual(compare_services([original],[native])[0]['fields']['ready'],[0,1])
        native['service']=1
        with self.assertRaises(ValueError):compare_services([original],[native])

    def test_partial_sprite_publication_must_preserve_each_live_slot(self):
        original=dict(oam=[0]*160);original['oam'][4:8]=[20,30,4,32]
        native=[dict(service=0,slot=i,present=int(i==1),x=30,y=20,flags=32) for i in range(40)]
        self.assertEqual(compare_sprites([original],native),[])
        native[1]['present']=0
        self.assertEqual(compare_sprites([original],native)[0]['slot'],1)
        with self.assertRaises(ValueError):compare_sprites([original],native[:-1])
        with self.assertRaises(ValueError):compare_sprites([dict()],native)

    def test_short_sprite_log_cannot_certify_all_display_services(self):
        original=[dict(oam=[0]*160)]*2
        native=[dict(service=0,slot=i,present=0) for i in range(40)]
        with self.assertRaises(ValueError):compare_sprites(original,native,2)
        self.assertEqual(compare_sprites(original,native,1),[])

    def test_phase_work_checks_entry_counter_and_complete_order(self):
        original=[{name:dict(cycles=i*100,tick=4) for i,name in enumerate(STAGES.values())}]
        native=[dict(update=0,phase=i,tick=4,work=100) for i in range(6)]
        self.assertEqual(compare_phase_work(original,[],native,1),[])
        native[0]['tick']=5
        self.assertEqual(compare_phase_work(original,[],native,1)[0]['fields'],{'tick':[4,5]})
        with self.assertRaises(ValueError):compare_phase_work(original,[],native[:-1],1)
        native[1]['phase']=0
        with self.assertRaises(ValueError):compare_phase_work(original,[],native,1)


if __name__=='__main__':unittest.main()
