"""Final-life generation, single decrement and unskippable hold guards."""
import copy,sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_final_result_reference import PREFIX,final_life_scope
from air_following_scope import result_capture_scope,instruction_capture_scope,retry_capture_scope


class FinalLife(unittest.TestCase):
    def setUp(self):
        names=PREFIX+[n for _ in range(8) for n in ('palette','wait','tail','wait','tail','wait','tail','wait','tail')]+['fadeReturned']+['holdWait','holdTail']*480+['gameOverHoldReturned']
        self.data=dict(version=1,afterRetry=3,points=[dict(name=n,cycles=100+i*100,player=0,lives=int(i<7),savings=0,result=33,display=10) for i,n in enumerate(names)])
    def reject(self):
        with self.assertRaises(ValueError):final_life_scope(self.data)
    def test_complete_final_result(self):self.assertEqual(len(final_life_scope(self.data)),1054)
    def test_nonfinal_generation(self):self.data['afterRetry']=2;self.reject()
    def test_missing_life_store(self):self.data['points'][7]['name']='failureWait';self.reject()
    def test_cannot_consume_life_at_start(self):self.data['points'][0]['lives']=0;self.reject()
    def test_life_is_stored_before_taken_branch(self):self.data['points'][7]['lives']=1;self.reject()
    def test_cannot_consume_second_life(self):self.data['points'][-1]['lives']=-1;self.reject()
    def test_savings_not_loaded_from_later_result(self):self.data['points'][-1]['savings']=100;self.reject()
    def test_success_is_not_game_over(self):self.data['points'][0]['result']=3;self.reject()
    def test_fixed_hold_cannot_be_shortened(self):self.data['points'].pop(-3);self.reject()
    def test_fixed_hold_cannot_be_extended(self):self.data['points'].insert(-1,copy.deepcopy(self.data['points'][-2]));self.reject()
    def test_reordered_clock(self):self.data['points'][10]['cycles']=0;self.reject()
    def test_wrong_player(self):self.data['points'][-1]['player']=1;self.reject()
    def test_last_result_generation_requires_next_retry(self):
        with self.assertRaises(ValueError):result_capture_scope(SimpleNamespace(after_retry=3,following=True))
    def test_final_result_selection_does_not_open_later_game(self):
        self.assertEqual(result_capture_scope(SimpleNamespace(after_retry=3,next_retry=True)).retry,4)
        for fn in (instruction_capture_scope,retry_capture_scope):
            with self.assertRaises(ValueError):fn(SimpleNamespace(after_retry=4,next_retry=True,following=True))


if __name__=='__main__':unittest.main()
