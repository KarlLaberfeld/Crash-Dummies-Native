"""Synthetic interrupted-scene comparison integrity; no original assets."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_following_scene_reference import analyze,compare_publications
from air_following_resource_reference import compare_resources
from air_following_gameplay_reference import FIELDS
from air_timing import vblank_work
from test_air_following_resource_reference import fixture as resource_fixture


def fixture():
    values=resource_fixture();data=values[0];data['busyScenes']=True
    # An invented source timeline places STAT in map preparation and VBlank
    # in the placement scan. The subsequent counter wait owns another frame.
    block=data['points'][10:20]
    for i,time in ((5,215000),(6,216000),(7,223000),(8,223032)):
        block[i]['cycles']=time
    block[6]['lcdc']=0xe5
    for p in block[7:]:p['tick']+=1;p['hudCursor']+=1
    block[9]['cycles']+=70224
    for p in data['points'][20:]:p['cycles']+=70224;p['tick']+=1;p['hudCursor']+=1
    busy=copy.deepcopy(data['interrupts'][2:4]);wait=copy.deepcopy(busy)
    busy[0].update(returnAddress=0x1eb1,ready=0)
    busy[1].update(returnAddress=0x19f1,ready=0)
    for r in wait:
        r['start']+=70224;r['end']+=70224
        if r['kind']=='vblank':r['tick']+=1;r['phases']={k:v+70224 for k,v in r['phases'].items()}
    rest=copy.deepcopy(data['interrupts'][4:])
    for r in rest:
        r['start']+=70224;r['end']+=70224
        if r['kind']=='vblank':r['tick']+=1;r['phases']={k:v+70224 for k,v in r['phases'].items()}
    data['interrupts']=data['interrupts'][:2]+busy+wait+rest
    for r in data['interrupts']:
        if r['kind']=='vblank':r['oam']=[0]*160
    values[1]=[dict(boundary=p['name'],cycle=p['cycles']-1000,**{k:p[k] for k in (*FIELDS,'transferFrame','transferFlags')}) for p in data['points']]
    values[3]=[dict(service=1195+i,cycle=r['start']-1000,tick=r['tick'],display=vblank_work(r)['display'],effects=64,music=60,inputHeld=33,inputPressed=0)
               for i,r in enumerate(r for r in data['interrupts'] if r['kind']=='vblank')]
    values[4]=[dict(kind=r['kind'],vectorCycle=r['start']-1000,owner=2 if r['returnAddress']==0x261d else 1) for r in data['interrupts']]
    summary=values[5][0]
    for k in ('end','nextStat','nextVBlank'):summary[k]+=70224
    for k in ('tick','displays','stats'):summary[k]+=1
    return values


class FollowingSceneIntegrity(unittest.TestCase):
    def setUp(self):self.values=fixture();self.data=self.values[0]
    def rejected(self):
        with self.assertRaises(ValueError):analyze(self.data)
    def compare(self):return compare_resources(*self.values,1000)
    def test_complete_scene_and_final_counter_wait(self):
        self.assertEqual(len(analyze(self.data)),7)
        differences,occupied,extent=self.compare()
        self.assertEqual(differences,[]);self.assertEqual(occupied,120)
        self.assertEqual((extent['uploads'],extent['completions']),(4,1))
    def test_scope_required(self):self.data.pop('busyScenes');self.rejected()
    def test_unknown_actor_interrupt_rejects(self):self.data['interrupts'][2]['returnAddress']=0x6000;self.rejected()
    def test_actor_body_cannot_borrow_map_owner(self):self.data['interrupts'][2]['start']=154000;self.rejected()
    def test_map_cannot_open_resource_gate(self):self.data['interrupts'][2]['ready']=1;self.rejected()
    def test_partial_row_display_requires_storage_owner(self):
        r=self.data['interrupts'][3];r.update(start=215600,end=215900,returnAddress=0x1f0e)
        self.rejected()
    def test_missing_final_wait_rejects(self):del self.data['interrupts'][4:6];self.rejected()
    def test_missing_scene_vector_rejects(self):del self.data['interrupts'][2];self.rejected()
    def test_lost_busy_counter_is_detected(self):self.data['points'][17]['tick']-=1;self.rejected()
    def test_stat_objects_disabled_until_display(self):self.data['points'][16]['lcdc']=0xe7;self.rejected()
    def test_display_reenables_objects(self):self.data['points'][17]['lcdc']=0xe5;self.rejected()
    def test_busy_input_fresh_edge_cannot_be_invented(self):self.data['interrupts'][3]['pressed']=1;self.rejected()
    def test_effect_must_come_from_completed_actor_work(self):self.data['interrupts'][3]['effectRequest']=20;self.rejected()
    def test_consumed_effect_cannot_reappear_at_wait(self):self.data['interrupts'][5]['effectRequest']=20;self.rejected()
    def test_busy_service_cannot_lose_counter(self):self.data['interrupts'][5]['tick']-=1;self.rejected()
    def test_unowned_wait_prefix_rejects(self):self.data['interrupts'][4]['returnAddress']=0x2618;self.rejected()
    def test_native_busy_vector_must_have_completion_owner(self):
        self.values[4][2]['owner']=0
        with self.assertRaises(ValueError):self.compare()
    def test_native_busy_acceptance_latency_is_compared(self):
        self.values[4][2]['vectorCycle']+=4
        self.assertEqual(self.compare()[0][0]['category'],'interrupt')
    def test_native_busy_display_work_is_compared(self):
        self.values[3][1]['display']+=4
        self.assertEqual(self.compare()[0][0]['category'],'service')
    def test_final_deadline_includes_extra_display(self):
        self.values[5][0]['nextVBlank']-=70224
        self.assertEqual(self.compare()[0][0]['category'],'summary')
    def sprite_rows(self):
        return [dict(service=1195+i//40,slot=i%40,present=0,x=0,y=0,flags=0) for i in range(7*40)]
    def test_complete_sprite_publications(self):self.assertEqual(compare_publications(self.data,self.sprite_rows()),[])
    def test_missing_original_sprite_snapshot(self):self.data['interrupts'][3]['oam'].pop();self.rejected()
    def test_missing_native_sprite_publication(self):
        with self.assertRaises(ValueError):compare_publications(self.data,self.sprite_rows()[:-1])
    def test_reordered_native_sprite_slot(self):
        rows=self.sprite_rows();rows[40]['slot']=1
        with self.assertRaises(ValueError):compare_publications(self.data,rows)
    def test_partial_list_at_busy_display_is_compared(self):
        rows=self.sprite_rows();rows[40]['present']=1
        self.assertEqual(compare_publications(self.data,rows)[0]['service'],1)
    def test_original_present_sprite_geometry_is_compared(self):
        self.data['interrupts'][3]['oam'][:4]=[16,8,17,32]
        rows=self.sprite_rows();rows[40].update(present=1,x=8,y=16,flags=32)
        self.assertEqual(compare_publications(self.data,rows),[])
        rows[40]['flags']=0
        self.assertEqual(compare_publications(self.data,rows)[0]['fields']['flags'],[32,0])
    def test_point_cannot_run_during_interrupt_return(self):
        self.data['points'][16]['cycles']=self.data['interrupts'][2]['end']+4
        self.rejected()
    def result_test_fixture(self):
        r=self.data['interrupts'][2];r.update(start=223016,end=223304,returnAddress=0x03fd)
        self.data['interrupts'][2:4]=[self.data['interrupts'][3],r]
        self.data['points'][16]['lcdc']=0xe7
        self.data['points'][18]['cycles']+=324;self.data['points'][18]['lcdc']=0xe5
    def test_result_test_interrupt_owns_its_completion_cost(self):
        self.result_test_fixture();self.assertEqual(len(analyze(self.data)),7)
    def test_result_test_cannot_hide_extra_work(self):
        self.result_test_fixture();self.data['points'][18]['cycles']+=4;self.rejected()
    def test_original_acceptance_outside_completion_bound_rejects(self):
        r=self.data['interrupts'][2];r['start']+=24;r['end']+=24
        with self.assertRaises(ValueError):self.compare()
    def test_busy_display_cannot_open_resource_queue(self):
        self.data['interrupts'][3]['ready']=1;self.rejected()
    def test_busy_clear_sees_previous_background_row_gate(self):
        block=self.data['points'][10:20]
        for i,time in ((4,219000),(5,223000),(6,223100),(7,224000),(8,224032)):block[i]['cycles']=time
        block[4]['lcdc']=0xe5;block[6]['lcdc']=0xe7
        for p in block[5:7]:p['tick']+=1;p['hudCursor']+=1
        self.data['interrupts'][2]['returnAddress']=0x1c78
        self.data['interrupts'][3]['returnAddress']=0x1bd5
        # Native rows are not retimed for this source-only integrity check.
        from air_following_resource_reference import analyze as resources
        self.assertEqual(resources(self.data)['mapDeferredDisplays'],1)


if __name__=='__main__':unittest.main()
