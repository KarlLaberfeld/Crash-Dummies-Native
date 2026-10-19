"""Synthetic source-order and inherited-scratch qualification guards."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_side_push_reference import analyze


def fixture(force=4):
    # Exact source sequence: first two RET NZs, followed by either the early
    # return or the LD HL/LD A/AND/RET Z zero-rate tail. No ROM is needed.
    branch=[(0x5fd6,100),(0x5ff3,120),(0x6574,144),(0x6578,168),(0x657b,184)]
    if not force:branch += [(0x657c,192),(0x6581,216)]
    branch += [(0x5ff6,204 if force else 236),(0x602c,300),(0x602f,316)]
    return dict(afterRetry=2,previousTerminal=dict(cycles=10,result=33,lastForce=force,player=0),points=[dict(index=0,name='begin',cycles=50,lastForce=force),dict(index=1,name='entitiesDone',cycles=400,lastForce=0)],
        steering=[dict(pc=pc,cycles=cycle,lastForce=0 if pc==0x602f else force,rate=0,transfer=0) for pc,cycle in branch])


class SidePushIntegrity(unittest.TestCase):
    def setUp(self):self.data=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data)
    def test_retained_nonzero_branch(self):self.assertEqual(analyze(self.data)['firstSteeringBody'],60)
    def test_zero_branch(self):self.assertEqual(analyze(fixture(0))['firstSteeringBody'],92)
    def test_negative_and_terrain_bounce_scratch(self):
        for force in (-4,12):self.assertEqual(analyze(fixture(force))['inheritedSidePush'],force)
    def test_wrong_generation(self):self.data['afterRetry']=1;self.reject()
    def test_wrong_preceding_result(self):self.data['previousTerminal']['result']=3;self.reject()
    def test_lost_initial_inheritance(self):self.data['points'][0]['lastForce']=0;self.reject()
    def test_lost_before_first_input(self):
        for p in self.data['steering'][:-1]:p['lastForce']=0
        self.reject()
    def test_wrong_nonzero_branch_cost(self):self.data['steering'][-3]['cycles']+=32;self.reject()
    def test_clear_too_early(self):self.data['steering'][-2]['lastForce']=0;self.reject()
    def test_clear_missing(self):self.data['steering'][-1]['lastForce']=4;self.reject()
    def test_clear_work_not_fitted(self):self.data['steering'][-1]['cycles']+=4;self.reject()
    def test_early_return_cannot_run_zero_rate_tail(self):
        self.data['steering'].insert(5,dict(pc=0x657c,cycles=192,lastForce=4,rate=0,transfer=0));self.reject()
    def test_zero_branch_requires_rate_test(self):
        self.data=fixture(0);self.data['steering']=[p for p in self.data['steering'] if p['pc']!=0x6581];self.reject()
    def test_transfer_gate_requires_another_owner(self):self.data['steering'][2]['transfer']=1;self.reject()


if __name__=='__main__':unittest.main()
