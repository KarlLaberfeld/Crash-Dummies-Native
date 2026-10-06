import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_irq_compare import compare_placements,placement_targets


class PlacementInterruptEvidence(unittest.TestCase):
    def setUp(self):
        self.expected=[dict(update=3,kind='stat',vectorCycle=1000)]
        self.native=[dict(update=3,phase=5,kind='stat',vectorCycle=1000,owner=1)]

    def test_exact_source_boundary(self):
        self.assertEqual(compare_placements(self.expected,self.native),[])

    def test_shift_cannot_hide_in_later_halt(self):
        self.native[0]['vectorCycle']+=4
        self.assertEqual(compare_placements(self.expected,self.native)[0]['fields'],{'vectorCycle':[1000,1004]})

    def test_aggregate_cost_has_no_completion_owner(self):
        self.native[0]['owner']=0
        with self.assertRaises(ValueError):compare_placements(self.expected,self.native)

    def test_missing_or_wrong_phase_is_incomplete(self):
        self.native[0]['phase']=4
        with self.assertRaises(ValueError):compare_placements(self.expected,self.native)

    def test_wrong_update_is_a_difference(self):
        self.native[0]['update']=4
        self.assertEqual(compare_placements(self.expected,self.native)[0]['fields'],{'update':[3,4]})

    def test_duplicate_vector_rejects(self):
        with self.assertRaises(ValueError):compare_placements(self.expected,self.native*2)

    def test_empty_control_provides_no_edge_evidence(self):
        self.assertEqual(compare_placements([],[]),[])
        with self.assertRaises(ValueError):compare_placements([],self.native)

    def test_target_epoch_and_interval(self):
        data=dict(interrupts=[dict(kind='vblank',start=552,end=600,returnAddress=0x03c9),
            dict(kind='stat',start=1000,end=1288)],updates=[dict(placements=dict(cycles=900),done=dict(cycles=1310))])
        self.assertEqual(placement_targets(data),[dict(update=0,kind='stat',vectorCycle=500)])
        data['interrupts'][0]['returnAddress']=0x261d
        with self.assertRaises(ValueError):placement_targets(data)

    def test_incomplete_return_rejects(self):
        data=dict(interrupts=[dict(kind='vblank',start=552,end=600,returnAddress=0x03c9),
            dict(kind='stat',start=1000,end=1288)],updates=[dict(placements=dict(cycles=900),done=dict(cycles=1290))])
        with self.assertRaises(ValueError):placement_targets(data)


if __name__=='__main__':unittest.main()
