"""Synthetic timing checks; no original recordings or emulator dependency."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from air_timing import elapsed_work, placement_cycles, map_cycles, sprite_cycles, clear_cycles, entity_difference, resource_cycles, analyze, scoped_work, collision_work, vblank_work, vblank_bookkeeping_work, IRQ_PHASES
from air_timing import display_cycles, display_work, progress_bar_tiles, DISPLAY_PHASES, effect_cycles


class AirTimingTests(unittest.TestCase):
    def test_interrupted_range_reads_change_placement_work_without_fitting_a_delay(self):
        records=[dict(row=row,active=0) for row in (33,35,39,40,41,42,43,44,150)]
        reads=[dict(low=86) for _ in range(4)]+[dict(low=0,high=100) for _ in range(4)]
        self.assertEqual(placement_cycles(86,0,records,8191,reads),9200)
        self.assertEqual(placement_cycles(86,0,records,8191),3008)
        with self.assertRaises(ValueError):placement_cycles(86,0,records,8191,reads[:-1])
        reads[-1].pop('high')
        with self.assertRaises(ValueError):placement_cycles(86,0,records,8191,reads)

    def test_effect_setup_keeps_absent_roots_and_no_pending_request_distinct(self):
        self.assertEqual(effect_cycles(255, 0, 0), 64)
        self.assertEqual(effect_cycles(0, 0, 0), 220)
        self.assertEqual(effect_cycles(0, 1, 0), 472)
        self.assertEqual(effect_cycles(0, 0, 1), 368)
        self.assertEqual(effect_cycles(0, 1, 1), 620)
        with self.assertRaises(ValueError):
            effect_cycles(26, 0, 0)

    def test_display_priority_and_ready_gate_are_independent(self):
        w = dict(map_pending=0, ready=1, chunks=8, cursor=0, tick=1, fade_remaining=0, collected=0, quota=6)
        self.assertEqual(display_cycles(**w)['resources'], 3156)
        w['ready'] = 0
        self.assertEqual(display_cycles(**w)['resources'], 80)
        w['map_pending'] = 1
        self.assertEqual(display_cycles(**w)['map'], 760)
        self.assertEqual(display_cycles(**w)['resources'], 32)

    def test_progress_bar_exact_boundaries_and_low_byte_wrap(self):
        self.assertEqual(progress_bar_tiles(0), [0]*6)
        self.assertEqual(progress_bar_tiles(8), [0xe9, 0xf0, 0, 0, 0, 0])
        self.assertEqual(progress_bar_tiles(40), [0xe9]*5+[0xf0])
        self.assertEqual(progress_bar_tiles(48), [0xe9]*6)
        self.assertEqual(progress_bar_tiles(256), [0]*6)

    def test_display_rejects_unordered_or_incomplete_nested_phases(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete display'):
            display_work(dict(displayPhases={}))
        with self.assertRaisesRegex(ValueError, 'phase order'):
            display_work(dict(displayPhases=dict.fromkeys(DISPLAY_PHASES.values(), 100), phases=dict(display=0, bookkeeping=1000)))

    def test_invalid_display_quota_or_hud_cursor_cannot_certify_work(self):
        w = dict(map_pending=0, ready=1, chunks=0, cursor=0, tick=1, fade_remaining=0, collected=0, quota=6)
        for field, value in [('quota', 0), ('cursor', 13), ('collected', 256)]:
            with self.assertRaisesRegex(ValueError, 'Invalid display workload'):
                display_cycles(**{**w, field: value})

    def test_software_reset_guard_is_variable_work_not_a_fixed_irq_allowance(self):
        self.assertEqual(vblank_bookkeeping_work(0, 15, 0), 160)
        self.assertEqual(vblank_bookkeeping_work(1, 1, 0), 240)
        self.assertEqual(vblank_bookkeeping_work(1, 15, 1), 248)
        self.assertEqual(vblank_bookkeeping_work(1, 15, 0), -1)

    def test_vblank_decomposition_retains_variable_music_display_and_effect_work(self):
        names = ['prefix', *IRQ_PHASES.values()]
        values = [180, 704, 280, 2000, 160, 900, 68, 5000, 120]
        phases, cursor = {}, 1000+values[0]
        for name, cost in zip(list(IRQ_PHASES.values()), values[1:]):
            phases[name] = cursor
            cursor += cost
        parts = vblank_work(dict(start=1000, end=cursor, phases=phases))
        self.assertEqual(parts, dict(zip(names, values)))
        self.assertEqual(sum(parts.values())+36, cursor-1000+36)

    def test_missing_or_unordered_vblank_phases_cannot_certify_fixed_work(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete VBlank'):
            vblank_work(dict(start=0, end=1000, phases={}))
        with self.assertRaisesRegex(ValueError, 'phase order'):
            vblank_work(dict(start=0, end=1000, phases=dict.fromkeys(IRQ_PHASES.values(), 100)))

    def test_collision_callbacks_are_removed_once_and_keep_interrupt_cost_separate(self):
        calls = [dict(start=1000, end=1800, slots=[dict(start=1050, end=1600)],
                      callbacks=[dict(start=1200, end=1500)])]
        self.assertEqual(collision_work(calls, 900, 1900, [dict(start=1300, end=1400)]), (500, 164))

    def test_component_scopes_reject_missing_reversed_overlapping_or_escaped_boundaries(self):
        for calls in ([dict(start=100)], [dict(start=200, end=100)],
                      [dict(start=100, end=250), dict(start=200, end=300)],
                      [dict(start=0, end=100)], [dict(start=100, end=400)]):
            with self.assertRaisesRegex(ValueError, 'component scope'):
                scoped_work(calls, 50, 350, [])

    def test_callback_or_slot_cannot_escape_its_collision_call(self):
        for key in ('callbacks', 'slots'):
            call = dict(start=100, end=300, callbacks=[], slots=[])
            call[key] = [dict(start=90, end=200)]
            with self.assertRaisesRegex(ValueError, 'component scope'):
                collision_work([call], 0, 400, [])

    def test_old_capture_cannot_silently_certify_missing_handler_measurements(self):
        with self.assertRaisesRegex(ValueError, 'schema changed'):
            analyze(dict(updates=[]))

    def test_resource_upload_acknowledgement_and_replacement_paths(self):
        self.assertEqual(resource_cycles(1, 0, 0, 0, 4), 688)
        self.assertEqual(resource_cycles(1, 1, 0, 0, 4), 252)
        self.assertEqual(resource_cycles(1, 1, 2, 0, 4), 268)
        self.assertEqual(resource_cycles(1, 0, 1, 1, 4), 384)
        self.assertEqual(resource_cycles(1, 0, 1, 2, 4), 716)
        self.assertEqual(resource_cycles(1, 0, 1, 2, 0), 412)
        self.assertEqual(resource_cycles(1, 0, 0, 0, 0), 384)
        self.assertEqual(resource_cycles(12, 0, 0, 0, 4), 212)

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
