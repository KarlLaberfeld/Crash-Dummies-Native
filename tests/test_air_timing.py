"""Synthetic timing checks; no original recordings or emulator dependency."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from air_timing import elapsed_work, placement_cycles, map_cycles, sprite_cycles, clear_cycles, entity_difference


class AirTimingTests(unittest.TestCase):
    def test_irq_cost_includes_entry_and_return_not_just_hook_span(self):
        irq = dict(start=1100, end=1300)
        self.assertEqual(elapsed_work(1000, 1500, [irq]), 264)
        self.assertEqual(elapsed_work(1400, 1500, [irq]), 100)

    def test_partial_interrupt_at_either_work_boundary_is_rejected(self):
        for start, end in ((1090, 1500), (1000, 1305)):
            with self.assertRaises(ValueError):
                elapsed_work(start, end, [dict(start=1100, end=1300)])

    def test_overlapping_or_reversed_intervals_are_rejected(self):
        for interrupts in ([dict(start=1100, end=1300), dict(start=1300, end=1400)],
                           [dict(start=1400, end=1100)]):
            with self.assertRaises(ValueError):
                elapsed_work(1000, 1500, interrupts)
        with self.assertRaises(ValueError):
            elapsed_work(1500, 1000, [])

    def test_scan_range_boundaries_and_active_records(self):
        # Sixteen entries prevent a pointer wrap during this eight-entry scan.
        records = [dict(row=7, active=0) for _ in range(16)]
        self.assertEqual(placement_cycles(10, 0, records, 0), 3008)  # low == row+3 rejected
        records = [dict(row=22, active=0) for _ in range(16)]
        self.assertEqual(placement_cycles(10, 0, records, 0), 3200)  # high < row+3 rejected
        records = [dict(row=21, active=1) for _ in range(16)]
        self.assertEqual(placement_cycles(10, 0, records, 0), 3360)  # high == row+3 accepted

    def test_slot_search_and_pointer_wrap_have_separate_costs(self):
        records = [dict(row=11, active=0) for _ in range(16)]
        self.assertEqual(placement_cycles(10, 0, records, 0), 12496)
        self.assertEqual(placement_cycles(10, 0, records, 65535), 10976)
        # One spawn followed by seven active tests, wrapping each time. The
        # caller's records must remain unchanged by the workload calculation.
        single = [dict(row=11, active=0)]
        self.assertEqual(placement_cycles(10, 0, single, 0), 4992)
        self.assertEqual(single, [dict(row=11, active=0)])

    def test_invalid_workload_is_rejected(self):
        for records, scan, mask in (([], 0, 0), ([dict(row=11, active=0)], 1, 0),
                                    ([dict(row=11, active=0)], 0, 65536)):
            with self.assertRaises(ValueError):
                placement_cycles(10, scan, records, mask)

    def test_map_crossing_direction_and_sixteen_bit_wrap(self):
        self.assertEqual(map_cycles(0x8001, 0x807f), 304)
        self.assertEqual(map_cycles(0x8000, 0x7fff), 2228)
        self.assertEqual(map_cycles(0x807f, 0x8080), 2232)
        self.assertEqual(map_cycles(0xffff, 0), 2232)

    def test_empty_sprite_pool_still_scans_all_slots_and_clears_oam(self):
        empty = [dict(frame=255) for _ in range(16)]
        self.assertEqual(sprite_cycles(empty, 0, 0, False, {}), (2044, 0))
        self.assertEqual(sprite_cycles(empty, 0, 0, True, {}), (2044, 156))
        self.assertEqual(clear_cycles(0, False), 1552)
        self.assertEqual(clear_cycles(156, True), 1564)

    def test_exhausted_sprite_list_skips_the_unused_tail_clear(self):
        self.assertEqual(clear_cycles(160, False), 168)
        self.assertEqual(clear_cycles(252, True), 172)

    def test_dead_slot_garbage_is_ignored_but_object_lifetime_differences_are_not(self):
        old = dict(frame=255, flags=20, x=600, y=700)
        empty = dict(frame=255, flags=0, x=0, y=0)
        self.assertEqual(entity_difference(old, empty), {})
        empty['frame'] = 21
        self.assertEqual(set(entity_difference(old, empty)), {'frame', 'flags', 'x', 'y'})


if __name__ == '__main__':
    unittest.main()
