"""Synthetic restarted-result attachment checks; no original game data."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from test_air_following_terminal_reference import outro_fixture
import test_air_result_prefix_reference as prefix_fixture
from test_air_result_transition_reference import synthetic_transition
from air_following_result_reference import analyze,compare_result


def fixture():
    outgoing=outro_fixture();outro,gameplay=outgoing[:2];end=outro['points'][-1]
    case=prefix_fixture.ResultPrefixEvidence();case.setUp();prefix=copy.deepcopy(case.data)
    shift=end['cycles']-prefix['points'][0]['cycles']
    for p in prefix['points']:p['cycles']+=shift;p['result']=33
    for p in prefix['polls']:p['cycles']+=shift
    prefix['lcdOff']['cycles']+=shift;prefix['followingResult']=True
    for i,p in enumerate(prefix['points']):
        p['state']=dict(tick=end['tick'],random=gameplay['points'][-1]['random'],player=0,lives=4,held=33,pressed=0,
            display=4 if i<5 else 10,stat=4 if i<5 else 0,countdown=outgoing[-1][0]['countdown'] if i<5 else 600)
    transition,points,services,irqs,summary=synthetic_transition(True,True)
    delta=prefix['points'][-1]['cycles']-transition['points'][0]['cycles'];ticks=end['tick']-1000
    consumed=False
    for p in transition['points']:
        p['cycles']+=delta;p['tick']=(p['tick']+ticks)&65535;p['result']=33;p['inputHeld']|=33
        if p['name']=='failureWait':consumed=True
        p.update(player=0,lives=3 if consumed else 4)
    for r in transition['interrupts']:
        r['start']+=delta;r['end']+=delta
        if r['kind']=='vblank':
            r['tick']=(r['tick']+ticks)&65535;r['held']|=33;r['phases']={k:v+delta for k,v in r['phases'].items()}
    transition['followingResult']=True
    for row in points:
        row['cycle']+=delta-900;row['tick']=(row['tick']+ticks)&65535;row['inputHeld']|=33
    for row in services:
        row['cycle']+=delta-900;row['tick']=(row['tick']+ticks)&65535;row['inputHeld']|=33
    for row in irqs:row['vectorCycle']+=delta-900
    for key in ('end','lcdEpoch'):summary[0][key]+=delta-900
    summary[0]['tick']=(summary[0]['tick']+ticks)&65535
    summary[0].update(player=0,lives=3,nextStat=summary[0]['lcdEpoch']+143*456+(len(services)-1)*70224,nextVBlank=summary[0]['lcdEpoch']+144*456+(len(services)-1)*70224)
    state=prefix['points'][0]['state']
    prefix_summary=dict(end=prefix['points'][-1]['cycles']-1000,lcdDisabled=prefix['lcdOff']['cycles']-1000,pollReads=1,pendingRequests=3,display=10,stat=0,countdown=600,random=state['random'],tick=state['tick'],player=0,lives=4,inputHeld=33,inputPressed=0)
    native=dict(prefix=[dict(boundary=p['name'],cycle=p['cycles']-1000) for p in prefix['points']]+[dict(boundary='lcdDisabled',cycle=prefix['lcdOff']['cycles']-1000)],
        polls=[dict(cycle=p['cycles']-1000,ly=p['ly']) for p in prefix['polls']],prefixSummary=[prefix_summary],points=points,services=services,irqs=irqs,summary=summary,entry=outgoing[6])
    return [prefix,transition,gameplay,outro,native]


class FollowingResultIntegrity(unittest.TestCase):
    def setUp(self):self.values=fixture();self.prefix,self.transition,self.gameplay,self.outro,self.native=self.values
    def compare(self):return compare_result(*self.values,1000)
    def rejected(self):
        with self.assertRaises(ValueError):analyze(*self.values[:4])
    def test_complete_attached_result_and_hold(self):self.assertEqual(self.compare(),[])
    def test_following_prefix_scope_required(self):self.prefix.pop('followingResult');self.rejected()
    def test_following_incoming_scope_required(self):self.transition.pop('followingResult');self.rejected()
    def test_detached_result_clock(self):self.outro['points'][-1]['cycles']+=4;self.rejected()
    def test_detached_game_result(self):
        for p in self.prefix['points']:p['result']=1
        self.rejected()
    def test_detached_input_history(self):
        for p in self.prefix['points']:p['state']['held']=32
        self.rejected()
    def test_lost_native_seed(self):
        for p in self.prefix['points']:p['state']['random']+=1
        self.rejected()
    def test_lost_display_counter(self):self.prefix['points'][0]['state']['tick']+=1;self.rejected()
    def test_final_life_needs_another_owner(self):self.prefix['points'][0]['state']['lives']=1;self.rejected()
    def test_player_cannot_change_with_lcd_disabled(self):self.prefix['points'][2]['state']['player']=1;self.rejected()
    def test_missing_campaign_state(self):self.prefix['points'][0]['state'].pop('lives');self.rejected()
    def test_countdown_store_cannot_happen_early(self):self.prefix['points'][4]['state']['countdown']=600;self.rejected()
    def test_selector_store_required(self):self.prefix['points'][5]['state']['display']=4;self.rejected()
    def test_masked_life_change_rejects(self):self.prefix['points'][3]['state']['lives']=3;self.rejected()
    def test_incoming_tick_detached(self):self.transition['points'][0]['tick']+=1;self.rejected()
    def test_incoming_input_detached(self):self.transition['points'][0]['inputHeld']=32;self.rejected()
    def test_incoming_player_detached(self):self.transition['points'][0]['player']=1;self.rejected()
    def test_life_cannot_decrement_before_its_store(self):self.transition['points'][1]['lives']=3;self.rejected()
    def test_life_must_decrement(self):next(p for p in self.transition['points'] if p['name']=='failureWait')['lives']=4;self.rejected()
    def test_life_cannot_decrement_twice(self):self.transition['points'][-1]['lives']=2;self.rejected()
    def test_native_detached_outgoing_endpoint(self):
        self.native['entry'][0]['end']+=4
        with self.assertRaises(ValueError):self.compare()
    def test_native_missing_attachment(self):
        self.native['entry']=[]
        with self.assertRaises(ValueError):self.compare()
    def test_native_poll_cycle_compared(self):
        self.native['polls'][0]['cycle']+=4
        self.assertIn('poll',self.compare()[0])
    def test_native_seed_compared(self):
        self.native['prefixSummary'][0]['random']+=1
        self.assertEqual(self.compare()[0]['category'],'prefixState')
    def test_native_inherited_lives_compared(self):
        self.native['prefixSummary'][0]['lives']=5
        self.assertEqual(self.compare()[0]['category'],'prefixState')
    def test_native_remaining_lives_compared(self):
        self.native['summary'][0]['lives']=4
        self.assertEqual(self.compare()[0]['category'],'resultState')
    def test_native_retained_countdown_compared(self):
        self.native['entry'][0]['countdown']+=1
        self.assertEqual(self.compare()[0]['category'],'inheritedState')
    def test_native_deadlines_compared(self):
        self.native['summary'][0]['nextStat']-=70224
        self.assertEqual(self.compare()[0]['category'],'resultState')
    def test_native_campaign_field_required(self):
        self.native['summary'][0].pop('lives')
        with self.assertRaises(ValueError):self.compare()
    def test_native_music_work_compared(self):
        self.native['services'][0]['music']+=4
        self.assertIn('service',self.compare()[0])
    def test_native_return_counter_compared(self):
        self.native['summary'][0]['tick']+=1
        self.assertIn('summary',self.compare()[0])


if __name__=='__main__':unittest.main()
