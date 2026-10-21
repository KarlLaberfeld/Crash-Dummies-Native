"""Cross-owner campaign checks; component timing has its own strict tests."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from selected_outcome_reference import campaign_attachment,analyze

def fixture(two=False):
    state=dict(tick=50,random=1234,player=0,lives=5,held=0,pressed=0,display=4,stat=4,countdown=1)
    prefix=[dict(cycles=2+n,state=dict(state,**(dict(display=10,stat=0,countdown=600) if n>=5 else {})),result=1) for n in range(10)]
    # Each endpoint is the next owner's first boundary.
    result=[dict(name='playerReady',cycles=11,tick=50,player=0,lives=5,inputHeld=0,inputPressed=0,countdown=600,result=1),dict(name='failureWait',cycles=12,tick=50,player=0,lives=4,inputHeld=0,inputPressed=0,countdown=566,result=1)]
    hand=[dict(cycles=12,tick=50,countdown=566,inputHeld=0,inputPressed=0,lives0=4,lives1=5 if two else 0,player=0),dict(cycles=13,tick=50,countdown=566,inputHeld=0,inputPressed=0,lives0=4,lives1=5 if two else 0,player=int(two))]
    header=[dict(cycles=13+i,tick=50,countdown=566,inputHeld=0,inputPressed=0,player=int(two),stage=1,difficulty=0,lives=5 if two else 4) for i in range(2)]
    picture=[dict(cycles=14+i,tick=50,countdown=566,inputHeld=0,inputPressed=0,song=-1 if not i else 2) for i in range(2)]
    groups=[dict(points=[dict(cycles=1),dict(cycles=2,tick=50)],interrupts=[dict(kind='vblank',held=0,pressed=0)]),dict(points=prefix,interrupts=[])]
    groups += [dict(points=points,precedingDisplays=0,interrupts=[]) for points in (result,hand,header,picture)]
    return dict(groups=groups,players=int(two)),dict(points=[dict(cycles=1,random=1234,result=1)])

class SelectedOutcomeCampaign(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):campaign_attachment(self.data,self.parent)
    def test_one_player_returns_to_first_player(self):campaign_attachment(self.data,self.parent)
    def test_two_players_retains_five_lives_for_second_player(self):campaign_attachment(*fixture(True))
    def test_gap_between_owners(self):self.data['groups'][3]['points'][0]['cycles']+=4;self.reject()
    def test_seed_inherited_from_actual_game(self):self.parent['points'][-1]['random']+=1;self.reject()
    def test_masked_seed_cannot_mutate(self):self.data['groups'][1]['points'][4]['state']['random']+=1;self.reject()
    def test_masked_input_cannot_mutate(self):self.data['groups'][1]['points'][3]['state']['held']=1;self.reject()
    def test_incoming_cannot_borrow_other_lives(self):self.data['groups'][2]['points'][0]['lives']=1;self.reject()
    def test_consumption_before_wait(self):self.data['groups'][2]['points'][0]['lives']=4;self.reject()
    def test_missing_consumption(self):self.data['groups'][2]['points'][1]['lives']=5;self.reject()
    def test_non_failure_cannot_use_this_owner(self):self.parent['points'][-1]['result']=3;self.reject()
    def test_other_player_cannot_gain_lives(self):self.data['groups'][3]['points'][0]['lives1']=5;self.reject()
    def test_two_player_handoff_must_switch(self):
        self.data,self.parent=fixture(True);self.data['groups'][3]['points'][-1]['player']=0;self.reject()
    def test_header_inherits_target_player(self):self.data['groups'][4]['points'][0]['player']=1;self.reject()
    def test_header_cannot_restore_consumed_life(self):self.data['groups'][4]['points'][0]['lives']=5;self.reject()
    def test_header_cannot_change_difficulty(self):self.data['groups'][4]['points'][0]['difficulty']=1;self.reject()
    def test_new_instruction_requires_its_own_song(self):self.data['groups'][5]['points'][1]['song']=1;self.reject()
    def test_service_indices_are_owned_by_result_restart(self):self.data['groups'][4]['precedingDisplays']=4;self.reject()
    def test_picture_cannot_reset_time(self):self.data['groups'][5]['points'][0]['tick']=0;self.reject()
    def test_picture_cannot_invent_button_edges(self):self.data['groups'][5]['points'][0]['inputPressed']=1;self.reject()
    def test_wrong_origin_rejected_before_component_work(self):
        self.data.update(version=1,origin='following-retry')
        with self.assertRaises(ValueError):analyze(self.data,self.parent)

if __name__=='__main__':unittest.main()
