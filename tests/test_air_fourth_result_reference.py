"""Synthetic fourth failure, generation and saved-counter completion guards."""
import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_following_scope import result_capture_scope,instruction_capture_scope,retry_capture_scope
from air_fourth_result_reference import fourth_result_scope
from air_following_scene_reference import scene_owner


class FourthFailure(unittest.TestCase):
    def setUp(self):
        self.records={key:dict(afterRetry=2) for key in ('gameplay','outro','result-prefix','result-transition','map')}
        self.records['gameplay'].update(terminalWait=True,points=[dict(result=33)])
        self.records['result-prefix']['points']=[dict(state=dict(lives=2))]
        self.records['result-transition'].update(failureHold=True,points=[dict(name='failureResultReturned',lives=1)])
    def reject(self):
        with self.assertRaises(ValueError):fourth_result_scope(self.records)
    def test_two_to_one_life(self):fourth_result_scope(self.records)
    def test_each_generation_attaches(self):
        for record in self.records.values():
            record['afterRetry']=1;self.reject();record['afterRetry']=2
    def test_terminal_game_required(self):self.records['gameplay']['terminalWait']=False;self.reject()
    def test_failure_required(self):self.records['gameplay']['points'][-1]['result']=3;self.reject()
    def test_complete_hold_required(self):self.records['result-transition']['failureHold']=False;self.reject()
    def test_result_return_required(self):self.records['result-transition']['points'][-1]['name']='fadeReturned';self.reject()
    def test_two_lives_not_reset(self):self.records['result-prefix']['points'][0]['state']['lives']=3;self.reject()
    def test_last_life_not_consumed_early(self):self.records['result-transition']['points'][-1]['lives']=0;self.reject()
    def test_life_consumed_exactly_once(self):self.records['result-transition']['points'][-1]['lives']=2;self.reject()


class ResultGeneration(unittest.TestCase):
    def test_legacy_following_result(self):self.assertEqual(result_capture_scope(SimpleNamespace(following=True)).retry,1)
    def test_legacy_next_result(self):self.assertEqual(result_capture_scope(SimpleNamespace(next_retry=True)).retry,2)
    def test_fourth_result_requires_explicit_next_retry(self):
        with self.assertRaises(ValueError):result_capture_scope(SimpleNamespace(following=True,after_retry=2))
    def test_fourth_entry_selects_result_origin(self):
        scope=result_capture_scope(SimpleNamespace(next_retry=True,after_retry=2))
        for i in range(3):
            scope.observe(0x0462,10,100*i);self.assertFalse(scope.result_seen)
            scope.observe(0x268b,10);scope.observe(0x03d8,4)
            for _ in range(5):scope.observe(0x03d8,4)
        scope.observe(0x0462,10,400);self.assertTrue(scope.result_seen);self.assertEqual(scope.display_offset,400)
    def test_unsupported_entry_generation_is_not_implicitly_opened(self):
        for fn in (instruction_capture_scope,retry_capture_scope):
            with self.assertRaises(ValueError):fn(SimpleNamespace(following=True,next_retry=True,after_retry=4))


class SavedCounterCompletion(unittest.TestCase):
    def setUp(self):
        self.block=[dict(cycles=100*i,name='end' if i==9 else 'point') for i in range(10)]
        self.block[-1]['cycles']=1100
        self.irq=dict(start=904,kind='stat',ready=1,returnAddress=0x261c)
    def test_first_halt_stat_edge(self):self.assertEqual(scene_owner(self.block,self.irq),2)
    def test_halt_return_requires_exact_prefix(self):
        self.irq['start']-=4
        with self.assertRaises(ValueError):scene_owner(self.block,self.irq)
    def test_display_halt_edge_needs_another_owner(self):
        self.irq['kind']='vblank'
        with self.assertRaises(ValueError):scene_owner(self.block,self.irq)
    def test_wrong_ready_rejects(self):
        self.irq['ready']=0
        with self.assertRaises(ValueError):scene_owner(self.block,self.irq)
    def test_wrong_phase_rejects(self):
        self.irq['start']=750
        with self.assertRaises(ValueError):scene_owner(self.block,self.irq)
    def test_inside_ld_b_not_owned(self):
        self.irq['returnAddress']=0x261b
        with self.assertRaises(ValueError):scene_owner(self.block,self.irq)


if __name__=='__main__':unittest.main()
