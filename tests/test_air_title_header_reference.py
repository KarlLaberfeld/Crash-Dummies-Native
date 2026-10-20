"""Post-title header evidence guards; synthetic data only."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_header_reference import analyze
from air_instruction_header_reference import compare_header
from test_air_instruction_header_reference import fixture as result_fixture

def fixture():
    data,*_=result_fixture();data.update(afterTitle=True,precedingDisplays=702,storageReadOwner='direct-vram-title-v1',reference=dict(titleStorageObserver='direct-vram-title-v1'),objectsUnchanged=True)
    for p in data['points']:p.update(stage=1,display=5,stat=5,countdown=54,lcdc=0xd1,scrollY=0,pendingRequests=0)
    r=data['interrupts'][0];r['countdown']=54;r['selector']=5
    for name in ('bookkeeping','effects','audioBank','music','restore'):r['phases'][name]-=128
    r['end']-=128
    data['points'][-1]['cycles']=r['end']+72
    data['interrupts'].insert(0,dict(kind='stat',start=15000,end=15288,selector=5,returnAddress=0x2120,phases={}))
    data['scrollWrites']=[dict(cycles=15216,address=0xff42,value=0),dict(cycles=r['start']+1284,address=0xff42,value=0)]
    data['beforeMaps']=[0]*2048;data['maps']=[1]+[0]*2047
    parent=dict(points=[dict(data['points'][0])],maps=[0]*2048)
    return data,parent

class TitleHeaderEvidence(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete(self):self.assertEqual(len(analyze(self.data,self.parent)),1)
    def test_explicit_title_provenance(self):del self.data['afterTitle'];self.reject()
    def test_result_callback_cannot_borrow_title_scope(self):self.data['points'][0]['display']=10;self.reject()
    def test_detached_header_entry(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_actual_service_counter(self):self.data['precedingDisplays']=0;self.reject()
    def test_retained_countdown(self):self.data['points'][-1]['countdown']=53;self.reject()
    def test_display_countdown(self):self.data['interrupts'][1]['countdown']=53;self.reject()
    def test_wrong_display_body(self):self.data['interrupts'][1]['phases']['bookkeeping']+=128;self.reject()
    def test_actual_service_tick(self):self.data['interrupts'][1]['tick']=4;self.reject()
    def test_actual_boundary_tick(self):self.data['points'][4]['tick']=6;self.reject()
    def test_actual_boundary_input(self):self.data['points'][4]['inputHeld']=8;self.reject()
    def test_native_lives(self):self.data['points'][3]['lives']=4;self.reject()
    def test_unqualified_player(self):self.data['points'][0]['player']=1;self.reject()
    def test_unqualified_day(self):self.data['points'][0]['stage']=2;self.reject()
    def test_unqualified_difficulty(self):self.data['points'][0]['difficulty']=1;self.reject()
    def test_no_pending_requests(self):self.data['points'][0]['pendingRequests']=2;self.reject()
    def test_direct_storage_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_direct_storage_observer(self):self.data['reference']={};self.reject()
    def test_map_ancestry(self):self.parent['maps'][0]=1;self.reject()
    def test_complete_background_writes(self):self.data['maps'][30]=1;self.reject()
    def test_full_window_preserved(self):self.data['maps'][2047]=1;self.reject()
    def test_full_objects_preserved(self):self.data['objectsUnchanged']=False;self.reject()
    def test_stat_callback(self):self.data['interrupts'][0]['selector']=0;self.reject()
    def test_scroll_store_count(self):self.data['scrollWrites'].pop();self.reject()
    def test_scroll_store_boundary(self):self.data['scrollWrites'][0]['cycles']+=4;self.reject()
    def test_scroll_store_value(self):self.data['scrollWrites'][0]['value']=88;self.reject()
    def test_counter_wait_return(self):self.data['interrupts'][-1]['returnAddress']=0x2120;self.reject()
    def test_counter_wait_tail(self):self.data['points'][-1]['cycles']+=4;self.reject()
    def test_input_edge(self):self.data['interrupts'][-1]['pressed']=8;self.reject()
    def test_shared_native_comparator_retains_countdown(self):
        d=self.data;native=[dict(boundary=p['name'],cycle=p['cycles']-1000,**{k:p[k] for k in ('tick','countdown','player','stage','difficulty','inputHeld','inputPressed')}) for p in d['points']]
        r=d['interrupts'][-1];services=[dict(service=702,cycle=r['start']-1000,tick=5,countdown=54,display=144,effects=64,music=60,inputHeld=0,inputPressed=0)]
        irqs=[dict(kind=p['kind'],vectorCycle=p['start']-1000,owner=2 if p['returnAddress']==0x261d else 1) for p in d['interrupts']]
        polls=[dict(cycle=1000,mode=0)];writes=[dict(cycle=1028,address=0x9800,value=1)];summary=[dict(end=d['points'][-1]['cycles']-1000,tick=6,countdown=54,displays=703)]
        self.assertEqual(compare_header(d,native,services,irqs,polls,writes,summary,1000),[])
        services[0]['countdown']=53
        self.assertEqual(compare_header(d,native,services,irqs,polls,writes,summary,1000)[0]['category'],'service')

if __name__=='__main__':unittest.main()
