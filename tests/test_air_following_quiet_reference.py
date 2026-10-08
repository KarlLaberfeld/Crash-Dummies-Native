"""Synthetic continued following gameplay coverage; no original data."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_following_quiet_reference import analyze,compare_quiet,FIELDS
from test_air_following_gameplay_reference import fixture as first_fixture
from extract_air import HANDLERS

def fixture():
    values=first_fixture();data=values[0];start=data['points'][0];end=data['points'][-1]
    second=[]
    for i,p in enumerate(data['points']):
        q=copy.deepcopy(end);q['name']=p['name'];q['cycles']=end['cycles']+p['cycles']-start['cycles'];q['tick']=7+(i==9);q['hudCursor']=3+(i==9)
        if i==9:q['cycles']=end['cycles']+70224
        second.append(q)
    data['points']+=second
    pair=copy.deepcopy(data['interrupts'])
    for r in pair:
        r['start']+=70224;r['end']+=70224
        if r['kind']=='vblank':
            r['tick']=7;r['phases']={k:v+70224 for k,v in r['phases'].items()}
    data['interrupts']+=pair;data['updates']=2
    native=[dict(boundary=p['name'],cycle=p['cycles']-1000,**{k:p[k] for k in FIELDS}) for p in data['points']];actors=[]
    for p in data['points']:
        for slot,e in enumerate(p['entities']):
            actors.append(dict(boundary=p['name'],slot=slot,alive=int(e['frame']!=255),frame=e['frame'],flags=e['flags'],handler=HANDLERS.get(e['handler'],0),x=e['x'],y=e['y'],done=int(bool(e['state']&128)),waiting=int(bool(e['state']&64)),delay=e['delay'],period=e['period'],**{f'param{j}':v for j,v in enumerate(e['params'])}))
    service=dict(values[3][0]);service.update(service=1196,cycle=service['cycle']+70224,tick=7)
    vectors=[dict(kind=r['kind'],vectorCycle=r['start']-1000,owner=2) for r in data['interrupts']]
    summary=dict(values[5][0]);summary.update(end=summary['end']+70224,tick=8,displays=1197,stats=1198,nextStat=summary['nextStat']+70224,nextVBlank=summary['nextVBlank']+70224)
    values[6][0]['entryPauseComplete']=0
    return [data,native,actors,[values[3][0],service],vectors,[summary],values[6]]

class FollowingQuietIntegrity(unittest.TestCase):
    def setUp(self):self.values=fixture();self.data=self.values[0]
    def compare(self):return compare_quiet(*self.values,1000)
    def test_complete_fixture(self):self.assertEqual(self.compare(),([],40))
    def test_missing_update_rejects(self):
        self.data['points'].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_missing_original_vector_rejects(self):
        self.data['interrupts'].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_missing_native_actor_rejects(self):
        self.values[2].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_missing_native_service_rejects(self):
        self.values[3].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_detached_source_update_rejects(self):
        self.data['points'][10]['secondTicks']+=1
        with self.assertRaises(ValueError):self.compare()
    def test_changed_retained_timer_is_detected(self):
        self.values[1][-1]['secondTicks']+=1
        self.assertEqual(self.compare()[0][0]['category'],'boundary')
    def test_stale_row_gate_high_byte_is_detected(self):
        self.values[1][16]['mapScratch']+=256
        self.assertEqual(self.compare()[0][0]['fields']['mapScratch'],[432,688])
    def test_changed_music_work_is_detected(self):
        self.values[3][1]['music']+=4
        self.assertEqual(self.compare()[0][0]['category'],'service')
    def test_changed_fresh_input_is_detected(self):
        self.values[3][1]['inputPressed']=1
        self.assertEqual(self.compare()[0][0]['category'],'service')
    def test_new_pause_requires_its_owner(self):
        self.data['points'][-1].update(held=41,pressed=8)
        with self.assertRaises(ValueError):self.compare()
    def test_busy_resource_requires_its_owner(self):
        self.data['points'][13]['transfer']=1
        with self.assertRaises(ValueError):self.compare()
    def test_interrupted_body_requires_its_owner(self):
        self.data['interrupts'][2]['returnAddress']=0x03de
        with self.assertRaises(ValueError):self.compare()
    def test_vector_deadline_drift_rejects(self):
        self.data['interrupts'][2]['start']+=4;self.data['interrupts'][2]['end']+=4
        with self.assertRaises(ValueError):self.compare()
    def test_unknown_native_vector_owner_rejects(self):
        self.values[4][-1]['owner']=0
        with self.assertRaises(ValueError):self.compare()
    def test_reordered_live_actor_rejects(self):
        self.values[2][-16]['slot']=1
        with self.assertRaises(ValueError):self.compare()
    def test_queued_effect_must_match_native_body(self):
        for p in self.data['points'][12:19]:p['effect']=20
        self.data['interrupts'][-1]['effectRequest']=19
        with self.assertRaises(ValueError):self.compare()
    def test_effect_must_be_consumed(self):
        self.data['points'][-1]['effect']=20
        with self.assertRaises(ValueError):self.compare()
    def test_wrong_declared_extent_rejects(self):
        self.data['updates']=3
        with self.assertRaises(ValueError):self.compare()
    def test_summary_counter_continues(self):
        self.values[5][0]['tick']=7
        self.assertEqual(self.compare()[0][0]['category'],'summary')
    def test_entry_pause_proof_cannot_be_faked(self):
        self.values[6][0]['entryPauseComplete']=1
        with self.assertRaises(ValueError):self.compare()

if __name__=='__main__':unittest.main()
