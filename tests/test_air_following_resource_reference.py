"""Synthetic request/upload integrity; no cartridge or original captures."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_following_gameplay_reference import FIELDS
from air_following_resource_reference import analyze,compare_resources
from extract_air import HANDLERS
from test_air_following_gameplay_reference import fixture as first_fixture


def fixture(deferred=False):
    values=first_fixture();data=values[0];template=copy.deepcopy(data['points']);first_end=template[-1]['cycles']
    count=7 if deferred else 6
    data.update(updates=count,resourceTransfers=True,resourceChunks=[13]*12)
    for p in data['points']:p.update(transferFrame=0,transferFlags=0)
    for p in data['points'][3:]:p['entities']=copy.deepcopy(data['points'][2]['entities'])
    original_irqs=copy.deepcopy(data['interrupts'])
    for update in range(1,count):
        before=data['points'][-1];block=[]
        for index,source in enumerate(template):
            p=copy.deepcopy(before);p['name']=source['name']
            p['cycles']=before['cycles']+source['cycles']-template[0]['cycles'] if index<9 else first_end+update*70224
            p['tick']=6+update+(index==9);p['hudCursor']=2+update+(index==9)
            if index>=6 and not (deferred and update==1):p['map']=0;p['mapScratch']&=255
            if update==1:
                if index==2:p['entities'][0].update(frame=1,flags=32)
                if index>=3:p.update(transfer=1,remaining=13,transferFrame=1,transferFlags=32)
            if update==count-1 and index>=3:p['transfer']=0
            if index==9 and p['remaining'] and not p['map']:
                p['remaining']=max(0,p['remaining']-4)
                if not p['remaining']:p['transfer']=2;p['entities'][0].update(frame=1,flags=32)
            block.append(p)
        data['points']+=block
        pair=copy.deepcopy(original_irqs)
        for r in pair:
            r['start']+=update*70224;r['end']+=update*70224
            if r['kind']=='vblank':r['tick']=6+update;r['phases']={k:v+update*70224 for k,v in r['phases'].items()}
        data['interrupts']+=pair
    points=[dict(boundary=p['name'],cycle=p['cycles']-1000,**{k:p[k] for k in (*FIELDS,'transferFrame','transferFlags')}) for p in data['points']]
    entities=[]
    for p in data['points']:
        for slot,e in enumerate(p['entities']):
            entities.append(dict(boundary=p['name'],slot=slot,alive=int(e['frame']!=255),frame=e['frame'],flags=e['flags'],handler=HANDLERS.get(e['handler'],0),
                x=e['x'],y=e['y'],done=int(bool(e['state']&128)),waiting=int(bool(e['state']&64)),delay=e['delay'],period=e['period'],**{f'param{j}':v for j,v in enumerate(e['params'])}))
    services=[]
    for update in range(count):
        p=dict(values[3][0]);p.update(service=1195+update,cycle=p['cycle']+update*70224,tick=6+update);services.append(p)
    vectors=[dict(kind=r['kind'],vectorCycle=r['start']-1000,owner=2) for r in data['interrupts']]
    summary=dict(values[5][0]);summary.update(end=data['points'][-1]['cycles']-1000,tick=6+count,displays=1195+count,stats=1196+count,nextStat=summary['nextStat']+(count-1)*70224,nextVBlank=summary['nextVBlank']+(count-1)*70224)
    values[6][0]['entryPauseComplete']=0
    return [data,points,entities,services,vectors,[summary],values[6]]


class FollowingResourceIntegrity(unittest.TestCase):
    def setUp(self):self.values=fixture();self.data=self.values[0]
    def compare(self):return compare_resources(*self.values,1000)
    def rejected(self):
        with self.assertRaises(ValueError):analyze(self.data)
    def test_complete_transfer_and_cleanup(self):
        differences,occupied,extent=self.compare()
        self.assertEqual(differences,[]);self.assertEqual(occupied,120)
        self.assertEqual({k:v for k,v in extent.items() if k!='services'},dict(requests=1,uploads=4,completions=1,mapDeferredDisplays=0))
    def test_explicit_scope_required(self):self.data.pop('resourceTransfers');self.rejected()
    def test_missing_descriptor_rejects(self):self.data['resourceChunks'].pop();self.rejected()
    def test_invalid_descriptor_rejects(self):self.data['resourceChunks'][1]=256;self.rejected()
    def test_missing_queue_snapshot_rejects(self):self.data['points'][13].pop('transferFrame');self.rejected()
    def test_early_queue_commit_rejects(self):self.data['points'][12]['transfer']=1;self.data['points'][12]['remaining']=13;self.rejected()
    def test_request_loses_chunk_rejects(self):self.data['points'][13]['remaining']=12;self.rejected()
    def test_wrong_requested_frame_rejects(self):self.data['points'][13]['transferFrame']=2;self.rejected()
    def test_wrong_requested_flags_rejects(self):self.data['points'][13]['transferFlags']=0;self.rejected()
    def test_requested_frame_visible_too_early_rejects(self):self.data['points'][13]['entities'][0]['frame']=1;self.rejected()
    def test_unrelated_actor_changed_by_resource_rejects(self):self.data['points'][13]['entities'][1]['x']+=1;self.rejected()
    def test_queue_changes_during_sprite_preparation_rejects(self):self.data['points'][14]['remaining']=12;self.rejected()
    def test_display_loses_extra_chunk_rejects(self):self.data['points'][19]['remaining']=8;self.rejected()
    def test_completed_upload_not_published_rejects(self):self.data['points'][49]['entities'][0]['frame']=0;self.rejected()
    def test_premature_completion_state_rejects(self):self.data['points'][19]['transfer']=2;self.rejected()
    def test_unknown_transfer_state_rejects(self):self.data['points'][13]['transfer']=3;self.rejected()
    def test_resource_body_irq_requires_an_owner(self):self.data['interrupts'][3]['returnAddress']=0x3f54;self.rejected()
    def test_no_completed_transfer_does_not_qualify(self):
        self.data['updates']=2;self.data['points']=self.data['points'][:20];self.data['interrupts']=self.data['interrupts'][:4];self.rejected()
    def test_native_wrong_busy_frame_is_detected(self):
        self.values[1][13]['transferFrame']=2
        self.assertEqual(self.compare()[0][0]['category'],'resource')
    def test_native_wrong_busy_flags_is_detected(self):
        self.values[1][13]['transferFlags']=0
        self.assertEqual(self.compare()[0][0]['category'],'resource')
    def test_native_wrong_upload_work_is_detected(self):
        self.values[3][1]['display']+=4
        self.assertEqual(self.compare()[0][0]['category'],'service')
    def test_native_publication_before_callback_is_detected(self):
        self.values[2][13*16]['frame']=1
        self.assertEqual(self.compare()[0][0]['category'],'actor')
    def test_background_row_defers_upload_then_completes(self):
        values=fixture(deferred=True)
        differences,occupied,extent=compare_resources(*values,1000)
        self.assertEqual(differences,[]);self.assertEqual(occupied,140)
        self.assertEqual((extent['uploads'],extent['completions'],extent['mapDeferredDisplays']),(4,1,1))
    def test_upload_despite_background_row_rejects(self):
        values=fixture(deferred=True);values[0]['points'][19]['remaining']=9
        with self.assertRaises(ValueError):analyze(values[0])


if __name__=='__main__':unittest.main()
