import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_pause_irq_compare import compare_pause_waits


class PauseInterruptEvidence(unittest.TestCase):
    def setUp(self):
        self.expected = [dict(kind='stat',vectorCycle=1000),dict(kind='vblank',vectorCycle=2000)]
        self.native = [dict(kind='stat',vectorCycle=1000,owner=2),dict(kind='vblank',vectorCycle=2000,owner=2)]

    def test_exact_wait_edges_and_unrelated_outside_services(self):
        rows = [dict(kind='vblank',vectorCycle=52,owner=3),*self.native]
        self.assertEqual(compare_pause_waits(self.expected,rows,900,2200),[])

    def test_four_cycle_shift_cannot_hide_in_counter_wait(self):
        self.native[0]['vectorCycle'] += 4
        self.assertEqual(compare_pause_waits(self.expected,self.native,900,2200)[0]['fields'],{'vectorCycle':[1000,1004]})

    def test_missing_or_out_of_interval_service_rejects(self):
        for rows in (self.native[:1],[dict(self.native[0],vectorCycle=899),self.native[1]]):
            with self.assertRaises(ValueError):compare_pause_waits(self.expected,rows,900,2200)

    def test_unsupported_aggregate_or_protected_owner_rejects(self):
        for owner in (0,1,3,4):
            rows = [dict(self.native[0],owner=owner),self.native[1]]
            with self.assertRaises(ValueError):compare_pause_waits(self.expected,rows,900,2200)

    def test_reordered_or_empty_evidence_rejects(self):
        with self.assertRaises(ValueError):compare_pause_waits(self.expected,list(reversed(self.native)),900,2200)
        with self.assertRaises(ValueError):compare_pause_waits([],[],900,2200)
        with self.assertRaises(ValueError):compare_pause_waits(self.expected,self.native,2200,900)


if __name__ == '__main__':unittest.main()
