"""Synthetic continuation attachment and reference-scope integrity tests."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_following_scope import FollowingAirCaptureScope,instruction_capture_scope
from air_next_instruction_reference import attachments,PARTS,require_generation
from types import SimpleNamespace


def fixture():
    # This tiny fixture tests attachment only. The CLI additionally requires
    # each component's complete source/poll/write/vector analyzer to pass.
    end=dict(name='failureResultReturned',cycles=100000,tick=65534,countdown=86,inputHeld=33,inputPressed=0,player=0,lives=3,result=33)
    result=dict(followingResult=True,failureHold=True,points=[dict(end,name='enable',cycles=1000),end],interrupts=[dict(kind='vblank'),dict(kind='stat')])
    records={};previous=end;displays=1
    for part in PARTS:
        first=copy.deepcopy(previous);first['name']='begin'
        last=copy.deepcopy(first);last.update(name='end',cycles=first['cycles']+10000,tick=(first['tick']+1)&65535)
        if part=='handoff':
            for p in (first,last):p.update(lives0=3,lives1=0)
            last['result']=0
        if part=='header':
            for p in (first,last):p.update(stage=1,difficulty=0)
        data=dict(followingResult=True,points=[first,last],precedingDisplays=displays,interrupts=[dict(kind='stat'),dict(kind='vblank')])
        if part=='text':data['campaign']=dict(player=0,stage=1,difficulty=0)
        records[part]=data;previous=last;displays+=1
    return result,records


class CaptureScopeIntegrity(unittest.TestCase):
    def setUp(self):self.scope=FollowingAirCaptureScope(True)
    def enter(self):self.scope.observe(0x268b,10);self.scope.observe(0x03d8,4)
    def test_legacy_scope_is_immediately_available(self):self.assertTrue(FollowingAirCaptureScope().ready)
    def test_initial_air_is_not_the_retry(self):self.scope.observe(0x03d8,4);self.assertFalse(self.scope.ready)
    def test_instruction_alone_does_not_select_its_handoff(self):self.scope.observe(0x268b,10);self.assertFalse(self.scope.ready)
    def test_wrong_instruction_selector_rejects(self):self.scope.observe(0x268b,5);self.scope.observe(0x03d8,4);self.assertFalse(self.scope.ready)
    def test_wrong_gameplay_selector_rejects(self):self.scope.observe(0x268b,10);self.scope.observe(0x03d8,6);self.assertFalse(self.scope.ready)
    def test_real_retry_selects_following_result(self):self.enter();self.assertTrue(self.scope.ready)
    def test_initial_result_cannot_supply_display_origin(self):self.scope.observe(0x0462,10,99);self.assertFalse(self.scope.result_seen)
    def test_new_result_retains_preceding_raw_sample_count(self):self.enter();self.scope.observe(0x0462,10,3020);self.assertEqual(self.scope.display_offset,3020)
    def test_repeated_result_point_does_not_rebase_services(self):
        self.enter();self.scope.observe(0x0462,10,3020);self.scope.observe(0x0462,10,3040);self.assertEqual(self.scope.display_offset,3020)
    def test_initial_instruction_samples_are_bounded(self):self.assertFalse(self.scope.samples(5));self.assertTrue(self.scope.samples(10))
    def test_all_qualified_intermediate_display_inputs_retained(self):
        self.enter()
        self.assertTrue(all(self.scope.samples(d) for d in (1,2,4,5,6,10)))
        self.assertFalse(self.scope.samples(7))


class AttachmentIntegrity(unittest.TestCase):
    def setUp(self):self.result,self.records=fixture()
    def rejected(self):
        with self.assertRaises(ValueError):attachments(self.result,self.records)
    def test_complete_endpoint_chain_and_wrap(self):
        states,epoch,stage,difficulty=attachments(self.result,self.records)
        self.assertEqual((epoch,stage,difficulty),(980,1,0))
        self.assertEqual((states[-1]['displays'],states[-1]['stats'],states[-1]['last']['tick']),(6,6,3))
    def test_parent_scope_required(self):self.result['followingResult']=False;self.rejected()
    def test_complete_parent_hold_required(self):self.result['failureHold']=False;self.rejected()
    def test_parent_endpoint_required(self):self.result['points'][-1]['name']='fadeReturned';self.rejected()
    def test_eliminated_parent_requires_other_owner(self):self.result['points'][-1]['lives']=0;self.rejected()
    def test_perfect_parent_requires_other_owner(self):self.result['points'][-1]['result']=7;self.rejected()
    def test_every_component_scope_required(self):
        for part in PARTS:
            previous=self.records[part]['followingResult'];self.records[part]['followingResult']=False;self.rejected();self.records[part]['followingResult']=previous
    def test_every_endpoint_must_attach(self):
        for part in PARTS:
            p=self.records[part]['points'][0];p['cycles']+=4;self.rejected();p['cycles']-=4
    def test_raw_input_history_cannot_restart(self):self.records['header']['points'][0]['inputHeld']=0;self.rejected()
    def test_display_numbers_cannot_restart(self):self.records['map']['precedingDisplays']=0;self.rejected()
    def test_consumed_life_must_survive_handoff(self):self.records['handoff']['points'][0]['lives0']=4;self.rejected()
    def test_handoff_cannot_consume_another_life(self):self.records['handoff']['points'][-1]['lives0']=2;self.rejected()
    def test_handoff_must_clear_result(self):self.records['handoff']['points'][-1]['result']=33;self.rejected()
    def test_header_must_keep_remaining_lives(self):self.records['header']['points'][0]['lives']=4;self.rejected()
    def test_header_must_keep_player(self):self.records['header']['points'][-1]['player']=1;self.rejected()
    def test_header_must_keep_stunt(self):self.records['header']['points'][-1]['stage']=2;self.rejected()
    def test_picture_cannot_select_ski(self):self.records['picture']['points'][0]['stage']=2;self.rejected()
    def test_text_cannot_select_another_difficulty(self):self.records['text']['campaign']['difficulty']=1;self.rejected()
    def test_counter_cannot_skip_its_display(self):self.records['map']['points'][-1]['tick']+=1;self.rejected()
    def test_missing_vector_counter_is_detected(self):self.records['picture']['interrupts'].pop();self.rejected()
    def test_two_life_campaign_is_retained(self):
        self.result['points'][-1]['lives']=2
        for p in self.records['handoff']['points']:p['lives0']=2
        for p in self.records['header']['points']:p['lives']=2
        states,_,_,_=attachments(self.result,self.records);self.assertEqual(states[-1]['lives'],2)
    def test_two_life_header_cannot_return_to_three(self):
        self.result['points'][-1]['lives']=2
        for p in self.records['handoff']['points']:p['lives0']=2
        self.rejected()


class InstructionGeneration(unittest.TestCase):
    def setUp(self):self.result,self.records=fixture()
    def third(self):
        self.result['nextRetry']=True
        for data in self.records.values():data['afterRetry']=2
    def test_legacy_generation_preserved(self):require_generation(self.result,self.records,1)
    def test_third_generation_requires_completed_third_result(self):
        for data in self.records.values():data['afterRetry']=2
        with self.assertRaises(ValueError):require_generation(self.result,self.records,2)
    def test_third_generation_accepted(self):self.third();require_generation(self.result,self.records,2)
    def test_each_mixed_component_rejects(self):
        self.third()
        for data in self.records.values():
            data['afterRetry']=1
            with self.assertRaises(ValueError):require_generation(self.result,self.records,2)
            data['afterRetry']=2
    def test_legacy_cannot_relabel_later_recordings(self):
        self.third()
        with self.assertRaises(ValueError):require_generation(self.result,self.records,1)
    def test_later_capture_requires_following(self):
        with self.assertRaises(ValueError):instruction_capture_scope(SimpleNamespace(after_retry=2,following=False))
    def test_capture_defaults_remain_legacy(self):self.assertEqual(instruction_capture_scope(SimpleNamespace()).retry,1)
    def test_later_capture_selects_second_retry(self):self.assertEqual(instruction_capture_scope(SimpleNamespace(after_retry=2,following=True)).retry,2)


if __name__=='__main__':unittest.main()
