"""Synthetic nested-helper ownership and complete retry attachment checks."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_following_scope import FollowingAirCaptureScope
from air_following_scene_reference import scene_owner
from air_third_result_reference import original_prefix
from air_following_resource_reference import qualify_rows
from test_air_map_reference import fixture as row_fixture


class ResultSelection(unittest.TestCase):
    def setUp(self):self.scope=FollowingAirCaptureScope(True,2)
    def instruction(self):self.scope.observe(0x268b,10)
    def entry(self):self.scope.observe(0x03d8,4)
    def test_initial_game_is_not_a_retry(self):self.entry();self.assertFalse(self.scope.ready)
    def test_first_retry_is_not_second_retry(self):self.instruction();self.entry();self.assertFalse(self.scope.ready)
    def test_repeated_updates_cannot_count_as_entries(self):
        self.instruction()
        for _ in range(10):self.entry()
        self.assertFalse(self.scope.ready)
    def test_second_retry_requires_another_instruction(self):
        self.instruction();self.entry();self.instruction();self.assertFalse(self.scope.ready);self.entry();self.assertTrue(self.scope.ready)
    def test_second_result_cannot_supply_third_result_origin(self):
        self.instruction();self.entry();self.scope.observe(0x0462,10,1000);self.assertFalse(self.scope.result_seen)
    def test_third_result_origin_inherits_full_input_count(self):
        for _ in range(2):self.instruction();self.entry()
        self.scope.observe(0x0462,10,5000);self.assertEqual(self.scope.display_offset,5000)
    def test_wrong_selector_cannot_count_as_entry(self):
        self.instruction();self.scope.observe(0x03d8,6);self.instruction();self.entry();self.assertFalse(self.scope.ready)
    def test_unowned_retry_index_rejects(self):
        for retry in (0,4,True,1.0):
            with self.assertRaises(ValueError):FollowingAirCaptureScope(True,retry)


class PlacementHelperOwnership(unittest.TestCase):
    def setUp(self):
        self.block=[dict(cycles=100*i,name='end' if i==9 else 'point') for i in range(10)]
        self.irq=dict(start=650,ready=0,kind='stat',returnAddress=0x20,callerAddress=0x1ae0)
    def test_identified_shared_offset_boundaries(self):
        for pc in (0x20,0x21,0x22):self.irq['returnAddress']=pc;self.assertEqual(scene_owner(self.block,self.irq),1)
    def test_missing_caller_rejects(self):
        self.irq.pop('callerAddress')
        with self.assertRaises(ValueError):scene_owner(self.block,self.irq)
    def test_other_callsite_rejects(self):
        self.irq['callerAddress']=0x186f
        with self.assertRaises(ValueError):scene_owner(self.block,self.irq)
    def test_wrong_phase_rejects(self):
        self.irq['start']=350
        with self.assertRaises(ValueError):scene_owner(self.block,self.irq)
    def test_open_resource_gate_rejects(self):
        self.irq['ready']=1
        with self.assertRaises(ValueError):scene_owner(self.block,self.irq)
    def test_unowned_carry_path_rejects(self):
        self.irq['returnAddress']=0x23
        with self.assertRaises(ValueError):scene_owner(self.block,self.irq)


class TerminalPrefixIntegrity(unittest.TestCase):
    def setUp(self):
        self.prior=dict(nextRetry=True,updates=1000,points=[dict(index=i) for i in range(4)],interrupts=[dict(index=i) for i in range(2)],precedingDisplays=2350)
        self.later=copy.deepcopy(self.prior);self.later.update(updates=1789,terminalWait=True);self.later['points'].append(dict(index=4))
    def check(self):original_prefix(self.prior,self.later)
    def test_complete_prefix(self):self.check()
    def test_timer_changes_in_prefix_reject(self):
        self.later['points'][2]['secondTicks']=0
        with self.assertRaises(ValueError):self.check()
    def test_vector_changes_in_prefix_reject(self):
        self.later['interrupts'][1]['cycle']=100
        with self.assertRaises(ValueError):self.check()
    def test_wrong_origin_rejects(self):
        self.later['precedingDisplays']=0
        with self.assertRaises(ValueError):self.check()
    def test_missing_terminal_owner_rejects(self):
        self.later['terminalWait']=False
        with self.assertRaises(ValueError):self.check()
    def test_reused_short_extent_rejects(self):
        self.later['updates']=1000
        with self.assertRaises(ValueError):self.check()


class PartialRowProof(unittest.TestCase):
    def setUp(self):
        self.data,self.native=row_fixture();self.manifest=dict(emulator='PyBoy',version='2.7.0',romSha256='rom',controlMemorySha256='digest')
        self.data.update(nextRetry=True,romSha256='rom',controlMemorySha256='digest',reference=dict(emulator='PyBoy',version='2.7.0'))
    def check(self):return qualify_rows(self.manifest,self.data,self.native,1000)
    def test_complete_storage_evidence(self):self.assertEqual(self.check(),[])
    def test_wrong_retry_scope_rejects(self):
        self.data['nextRetry']=False
        with self.assertRaises(ValueError):self.check()
    def test_mixed_original_control_rejects(self):
        self.data['controlMemorySha256']='other'
        with self.assertRaises(ValueError):self.check()
    def test_truncated_native_map_rejects(self):
        self.native.pop()
        with self.assertRaises(ValueError):self.check()
    def test_wrong_retained_byte_is_compared(self):
        self.native[1]['buffer31']=99;self.assertTrue(self.check())
    def test_blocked_source_read_rejects(self):
        self.data['points'][0]['lcd']['readBlocked']=1
        with self.assertRaises(ValueError):self.check()
    def test_terminal_tiles_can_retain_a_proven_write_free_interval(self):
        end=self.data['points'][-1];end['lcd']['readBlocked']=1
        end.update(tilesReadOwner='retained-unblocked-vram-v1',tilesObservedAt=self.data['points'][-2]['cycles'],tilesWriteAttemptsSince=0)
        self.assertEqual(self.check(),[])
    def test_retained_terminal_tiles_require_zero_write_attempts(self):
        end=self.data['points'][-1];end['lcd']['readBlocked']=1
        end.update(tilesReadOwner='retained-unblocked-vram-v1',tilesObservedAt=self.data['points'][-2]['cycles'],tilesWriteAttemptsSince=1)
        with self.assertRaises(ValueError):self.check()
    def test_retained_terminal_tiles_cannot_change(self):
        end=self.data['points'][-1];end['lcd']['readBlocked']=1
        end.update(tilesReadOwner='retained-unblocked-vram-v1',tilesObservedAt=self.data['points'][-2]['cycles'],tilesWriteAttemptsSince=0);end['tiles'][0]=7
        with self.assertRaises(ValueError):self.check()


if __name__=='__main__':unittest.main()
