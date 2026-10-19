"""Synthetic final-entry generation, one-life and immediate-parent guards."""
import copy,sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_next_instruction_reference import require_generation
from air_following_scope import instruction_capture_scope,retry_capture_scope
from air_fourth_entry_reference import generation,current_game_inheritance
from test_air_next_retry_reference import chain


class OneLifeEntry(unittest.TestCase):
    def setUp(self):
        self.text,self.hand,self.records=chain()
        for r in (self.text,self.hand,*self.records.values()):r['afterRetry']=3
        self.hand['points'][-1]['lives0']=1
        for part in ('prefix','stage'):
            for p in self.records[part]['points']:p['lives']=1
    def check(self):generation(self.text,self.hand,self.records,3,1)
    def test_one_life_is_retained(self):self.check()
    def test_life_cannot_reset_to_two(self):
        self.hand['points'][-1]['lives0']=2
        with self.assertRaises(ValueError):self.check()
    def test_final_life_not_consumed_at_entry(self):
        self.records['stage']['points'][-1]['lives']=0
        with self.assertRaises(ValueError):self.check()
    def test_every_generation_required(self):
        for r in (self.text,self.hand,*self.records.values()):
            r['afterRetry']=2
            with self.assertRaises(ValueError):self.check()
            r['afterRetry']=3
    def test_explicit_generation_must_match_life(self):
        with self.assertRaises(ValueError):generation(self.text,self.hand,self.records,3,2)
    def test_source_endpoint_must_still_attach(self):
        self.records['entry']['points'][0]['cycles']+=4
        with self.assertRaises(ValueError):self.check()


class FourthGameInheritance(unittest.TestCase):
    def setUp(self):
        last=dict(name='terminalEnd',result=33,secondTicks=27,entities=[dict(delay=50+i,period=70+i,state=192) for i in range(16)])
        self.old=dict(afterRetry=2,nextRetry=True,terminalWait=True,points=[last])
        self.new=dict(afterRetry=3,points=[copy.deepcopy(last)])
        for p in self.new['points'][0]['entities'][:2]:p['state']=128
    def test_current_fourth_game_inherited(self):current_game_inheritance(self.old,self.new,3)
    def test_older_third_game_is_not_parent(self):
        self.old['afterRetry']=1
        with self.assertRaises(ValueError):current_game_inheritance(self.old,self.new,3)
    def test_partial_second_is_not_restarted(self):
        self.new['points'][0]['secondTicks']=0
        with self.assertRaises(ValueError):current_game_inheritance(self.old,self.new,3)
    def test_vacant_delay_still_retained(self):
        self.new['points'][0]['entities'][15]['delay']=0
        with self.assertRaises(ValueError):current_game_inheritance(self.old,self.new,3)


class InstructionGeneration(unittest.TestCase):
    def setUp(self):
        self.result=dict(nextRetry=True,afterRetry=2)
        self.records={k:dict(afterRetry=3) for k in ('handoff','header','picture','map','text')}
    def test_completed_fourth_result(self):require_generation(self.result,self.records,3)
    def test_older_result_rejects(self):
        self.result['afterRetry']=1
        with self.assertRaises(ValueError):require_generation(self.result,self.records,3)
    def test_every_component_selects_fifth_instruction(self):
        for r in self.records.values():
            r['afterRetry']=2
            with self.assertRaises(ValueError):require_generation(self.result,self.records,3)
            r['afterRetry']=3
    def test_source_scopes_skip_three_earlier_entries(self):
        for fn,args in ((instruction_capture_scope,dict(following=True)),(retry_capture_scope,dict(next_retry=True))):
            scope=fn(SimpleNamespace(after_retry=3,**args))
            scope.observe(0x03d8,4)
            for _ in range(2):
                scope.observe(0x268b,10);scope.observe(0x03d8,4);self.assertFalse(scope.ready)
                for _ in range(20):scope.observe(0x03d8,4)
            scope.observe(0x268b,10);scope.observe(0x03d8,4);self.assertTrue(scope.ready)


if __name__=='__main__':unittest.main()
