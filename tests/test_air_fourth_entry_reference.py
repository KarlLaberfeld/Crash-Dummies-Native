"""Synthetic generation/inheritance guards; no ROM or original recordings."""
import copy,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_following_scope import retry_capture_scope
from air_fourth_entry_reference import generation,current_game_inheritance,preserved_native_prefix,native_animation_blocks
from test_air_next_retry_reference import chain


class FourthGeneration(unittest.TestCase):
    def setUp(self):
        self.text,self.hand,self.records=chain()
        for record in (self.text,self.hand,*self.records.values()):record['afterRetry']=2
        self.hand['points'][-1]['lives0']=2
        for part in ('prefix','stage'):
            for p in self.records[part]['points']:p['lives']=2
    def check(self):generation(self.text,self.hand,self.records)
    def test_two_life_chain(self):self.check()
    def test_every_component_requires_generation(self):
        for record in (self.text,self.hand,*self.records.values()):
            record['afterRetry']=1
            with self.assertRaises(ValueError):self.check()
            record['afterRetry']=2
    def test_cannot_select_three_lives(self):
        self.hand['points'][-1]['lives0']=3
        with self.assertRaises(ValueError):self.check()
    def test_endpoint_still_attaches(self):
        self.records['exit']['points'][0]['cycles']+=4
        with self.assertRaises(ValueError):self.check()
    def test_scope_requires_explicit_retry(self):
        with self.assertRaises(ValueError):retry_capture_scope(SimpleNamespace(after_retry=2))
    def test_legacy_entry_default_preserved(self):
        scope=retry_capture_scope(SimpleNamespace(next_retry=True))
        scope.observe(0x268b,10);scope.observe(0x03d8,4);self.assertTrue(scope.ready)
    def test_fourth_scope_skips_previous_entries_and_repeated_updates(self):
        scope=retry_capture_scope(SimpleNamespace(next_retry=True,after_retry=2))
        scope.observe(0x03d8,4);self.assertFalse(scope.ready)
        scope.observe(0x268b,10);scope.observe(0x03d8,4);self.assertFalse(scope.ready)
        for _ in range(100):scope.observe(0x03d8,4)
        self.assertFalse(scope.ready)
        scope.observe(0x268b,10);scope.observe(0x03d8,4);self.assertTrue(scope.ready)


class CurrentInheritance(unittest.TestCase):
    def setUp(self):
        point=dict(name='terminalEnd',result=33,secondTicks=14,entities=[dict(frame=1 if i<2 else 255,delay=3+i,period=10+i,state=192) for i in range(16)])
        self.old=dict(nextRetry=True,terminalWait=True,points=[point])
        self.new=dict(afterRetry=2,points=[copy.deepcopy(point)])
        for e in self.new['points'][0]['entities'][:2]:e['state']=128
    def check(self):current_game_inheritance(self.old,self.new)
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_third_game_state_retained(self):self.check()
    def test_wrong_ancestor_timer(self):self.new['points'][0]['secondTicks']=54;self.reject()
    def test_reset_timer(self):self.new['points'][0]['secondTicks']=0;self.reject()
    def test_previous_game_must_be_complete(self):self.old['terminalWait']=False;self.reject()
    def test_wrong_previous_generation(self):self.old['afterRetry']=2;self.reject()
    def test_successful_game_requires_other_owner(self):self.old['points'][-1]['result']=3;self.reject()
    def test_every_animation_delay_retained(self):
        for e in self.new['points'][0]['entities']:
            e['delay']+=1;self.reject();e['delay']-=1
    def test_vacant_flags_retained(self):self.new['points'][0]['entities'][15]['state']=128;self.reject()
    def test_missing_vacant_block_rejects(self):self.new['points'][0]['entities'].pop();self.reject()
    def native(self):
        return [dict(boundary='begin',slot=i,delay=e['delay'],period=e['period'],done=int(bool(e['state']&128)),waiting=int(bool(e['state']&64))) for i,e in enumerate(self.new['points'][0]['entities'])]
    def test_all_native_blocks(self):native_animation_blocks(self.new,self.native())
    def test_native_vacant_delay_checked(self):
        rows=self.native();rows[15]['delay']=0
        with self.assertRaises(ValueError):native_animation_blocks(self.new,rows)
    def test_native_slot_order_checked(self):
        rows=self.native();rows[0],rows[1]=rows[1],rows[0]
        with self.assertRaises(ValueError):native_animation_blocks(self.new,rows)
    def test_native_occupied_flags_checked(self):
        rows=self.native();rows[0]['done']=0
        with self.assertRaises(ValueError):native_animation_blocks(self.new,rows)
    def test_vacant_done_flags_are_explicitly_outside_scope(self):
        rows=self.native();rows[15]['done']=0
        native_animation_blocks(self.new,rows)


class AcceptedPrefix(unittest.TestCase):
    def setUp(self):
        parent=Path(__file__).resolve().parents[1]/'build'/'test-temp';parent.mkdir(parents=True,exist_ok=True)
        self.root=parent/str(uuid4());self.root.mkdir();self.accepted=self.root/'accepted.csv';self.base=self.root/'child.csv'
        self.suffixes=['','.next-gameplay.csv','.next-incoming.summary.csv','.third.next-text.summary.csv']
        for suffix in self.suffixes:
            for base in (self.accepted,self.base):Path(str(base)+suffix).write_bytes(b'unchanged\n')
    def tearDown(self):
        for path in self.root.iterdir():path.unlink()
        self.root.rmdir()
    def test_exact_parent_retained(self):self.assertEqual(preserved_native_prefix(self.base,self.accepted),4)
    def test_changed_parent_field_rejected(self):
        Path(str(self.base)+'.third.next-text.summary.csv').write_bytes(b'changed\n')
        with self.assertRaises(ValueError):preserved_native_prefix(self.base,self.accepted)
    def test_missing_accepted_scope_rejected(self):
        self.accepted.unlink()
        with self.assertRaises(ValueError):preserved_native_prefix(self.base,self.accepted)
    def test_missing_replayed_scope_rejected(self):
        self.base.unlink()
        with self.assertRaises(ValueError):preserved_native_prefix(self.base,self.accepted)


if __name__=='__main__':unittest.main()
