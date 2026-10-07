import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_all_irq_compare import compare_vectors,interval_targets,merge_interrupts


class CompleteIrqEvidence(unittest.TestCase):
    def setUp(self):
        self.source = [dict(kind='vblank',start=552,end=600,returnAddress=0x03c9),
                       dict(kind='stat',start=1000,end=1288,returnAddress=0x1c65)]
        self.rows = [dict(kind='vblank',vectorCycle=52,phase=-1,owner=3),
                     dict(kind='stat',vectorCycle=500,phase=2,owner=1)]

    def test_complete_interval(self):
        expected,excluded = interval_targets(merge_interrupts(self.source),500,1000)
        self.assertEqual(excluded,0);self.assertEqual(compare_vectors(expected,self.rows,1000),[])

    def test_terminal_extra_is_explicitly_outside(self):
        self.source.append(dict(kind='vblank',start=1600,end=1700,returnAddress=0x261d))
        expected,excluded = interval_targets(merge_interrupts(self.source),500,1000)
        self.assertEqual((len(expected),excluded),(2,1))

    def test_common_prefix_cannot_accept_missing_irq(self):
        expected,_ = interval_targets(self.source,500,1000)
        with self.assertRaises(ValueError):compare_vectors(expected,self.rows[:-1],1000)

    def test_native_extra_cannot_be_truncated(self):
        expected,_ = interval_targets(self.source,500,1000)
        with self.assertRaises(ValueError):compare_vectors(expected,self.rows+[dict(self.rows[-1],vectorCycle=900)],1000)

    def test_completion_delay_is_visible(self):
        expected,_ = interval_targets(self.source,500,1000);self.rows[-1]['vectorCycle']-=4
        self.assertEqual(compare_vectors(expected,self.rows,1000)[0]['fields'],{'vectorCycle':[500,496]})

    def test_aggregate_and_protected_owners_reject(self):
        expected,_ = interval_targets(self.source,500,1000)
        for owner in (0,4):
            self.rows[-1]['owner']=owner
            with self.assertRaises(ValueError):compare_vectors(expected,self.rows,1000)

    def test_source_phase_cannot_borrow_halt_owner(self):
        expected,_ = interval_targets(self.source,500,1000);self.rows[-1]['owner']=2
        with self.assertRaises(ValueError):compare_vectors(expected,self.rows,1000)

    def test_partial_original_return_rejects(self):
        with self.assertRaises(ValueError):interval_targets(self.source,500,790)

    def test_terminal_entry_crossing_rejects(self):
        with self.assertRaises(ValueError):interval_targets(self.source,500,490)

    def test_original_overlap_must_agree(self):
        self.assertEqual(merge_interrupts(self.source,self.source),self.source)
        with self.assertRaises(ValueError):merge_interrupts(self.source,[dict(self.source[-1],returnAddress=0x261d)])

    def test_unowned_startup_rejects(self):
        self.source[0]['returnAddress']=0x261d
        with self.assertRaises(ValueError):interval_targets(self.source,500,1000)

    def test_out_of_order_native_rejects(self):
        expected,_ = interval_targets(self.source,500,1000)
        with self.assertRaises(ValueError):compare_vectors(expected,self.rows[::-1],1000)


if __name__ == '__main__':unittest.main()
