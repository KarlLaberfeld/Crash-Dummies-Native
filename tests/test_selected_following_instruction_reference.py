"""Actual lives/turn, source storage and append-only instruction attachment."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from selected_following_instruction_reference import attachment_scope,projected,attachment,tail
from air_title_actions_reference import event_sha
from test_air_instruction_map_reference import fixture as map_fixture
from air_instruction_map_reference import analyze as map_scope

def fixture(two=False,skip=False):
    campaign=dict(player=int(two),stage=1,difficulty=0,lives0=4,lives1=5 if two else 0,result=0)
    storage=dict(maps=[0]*2048,tiles=[0]*1024,objects=[0]*256)
    point=lambda n,t:dict(name=n,cycles=t,tick=100,countdown=54,inputHeld=8 if skip else 0,inputPressed=0,scroll=0)
    groups=[]
    for i,name in enumerate(('map','text','exit')):
        points=[point('begin',100+i*100),point('end',200+i*100)]
        if i==1 and skip:points.insert(1,point('skip',250))
        if i==2 and not skip:points.insert(1,point('prompt',350))
        groups.append(dict(name=name,points=points,campaignBefore=copy.deepcopy(campaign),campaignAfter=copy.deepcopy(campaign),before=copy.deepcopy(storage),after=copy.deepcopy(storage),rawPrecedingInputSamples=500,interrupts=[],writes=[],endRawActiveFlags=4))
    data=dict(version=1,origin='selected-following-instruction',reference=dict(instructionStorageObserver='direct-vram-instruction-v1'),storageReadOwner='direct-vram-instruction-v1',inputCase='skip-held' if skip else 'full-prompt',parentInputCase='full-prompt',players=int(two),parentControlMemorySha256='parent',romSha256='rom',campaign=campaign,groups=groups)
    parent=dict(origin='selected-initial-outcome',players=int(two),inputCase='full-prompt',controlMemorySha256='parent',romSha256='rom',groups=[dict(points=[point('end',100)])])
    return data,parent,500

class FollowingInstructionAttachment(unittest.TestCase):
    def setUp(self):self.data,self.parent,self.raw=fixture()
    def reject(self):
        with self.assertRaises(ValueError):attachment_scope(self.data,self.parent,self.raw)
    def test_one_two_player_full_and_skip(self):
        for two in (False,True):
            for skip in (False,True):attachment_scope(*fixture(two,skip))
    def test_detached_campaign_parent(self):self.parent['origin']='following-retry';self.reject()
    def test_changed_rom(self):self.data['romSha256']='other';self.reject()
    def test_changed_parent_fingerprint(self):self.data['parentControlMemorySha256']='other';self.reject()
    def test_lost_player_choice(self):self.data['players']=1;self.reject()
    def test_second_player_cannot_be_replaced_by_first(self):
        self.data,self.parent,self.raw=fixture(True);self.data['campaign']['player']=0;self.reject()
    def test_second_player_lives_are_not_first_players(self):
        self.data,self.parent,self.raw=fixture(True);self.data['campaign']['lives1']=4;self.reject()
    def test_consumed_life_cannot_be_restored(self):self.data['campaign']['lives0']=5;self.reject()
    def test_stage_cannot_change(self):self.data['campaign']['stage']=2;self.reject()
    def test_no_borrowed_source_observer(self):self.data['reference']['instructionStorageObserver']='unknown';self.reject()
    def test_missing_group(self):self.data['groups'].pop();self.reject()
    def test_reordered_group(self):self.data['groups'].reverse();self.reject()
    def test_missing_raw_input_prefix(self):self.raw+=1;self.reject()
    def test_raw_index_cannot_reset_for_text(self):self.data['groups'][1]['rawPrecedingInputSamples']=0;self.reject()
    def test_time_cannot_reset(self):self.data['groups'][1]['points'][0]['cycles']-=4;self.reject()
    def test_tick_cannot_reset(self):self.data['groups'][1]['points'][0]['tick']=0;self.reject()
    def test_pressed_edge_cannot_be_invented(self):self.data['groups'][2]['points'][0]['inputPressed']=8;self.reject()
    def test_live_player_cannot_change_during_text(self):self.data['groups'][1]['campaignAfter']['player']=1;self.reject()
    def test_native_control_cannot_change_source_tiles(self):self.data['groups'][0]['after']['tiles'][0]=1;self.reject()
    def test_incomplete_source_tile_extent(self):self.data['groups'][0]['before']['tiles'].pop();self.reject()
    def test_storage_cannot_be_reset_between_owners(self):self.data['groups'][1]['before']['maps'][1024]=1;self.reject()
    def test_unexplained_background_store(self):self.data['groups'][0]['after']['maps'][4]=1;self.reject()
    def test_unexplained_window_store(self):self.data['groups'][0]['after']['maps'][1024]=1;self.reject()
    def test_text_glyphs_must_target_owned_background(self):self.data['groups'][1]['writes']=[dict(address=0x9c00,value=4)];self.reject()
    def test_prepared_sprite_storage_must_remain_blank(self):self.data['groups'][0]['before']['objects'][0]=1;self.reject()
    def test_full_path_cannot_omit_prompt(self):self.data['groups'][2]['points'].pop(1);self.reject()
    def test_full_path_cannot_skip_text(self):self.data['groups'][1]['points'].insert(1,dict(name='skip'));self.reject()
    def test_unknown_raw_audio_endpoint_is_rejected(self):self.data['groups'][2]['endRawActiveFlags']=7;self.reject()

class RetainedScrollScope(unittest.TestCase):
    def source(self):
        group=map_fixture()[0]
        for p in group['points'][:3]:p['scroll']=64
        return projected(dict(reference={},campaign={}),group,554)
    def test_actual_post_result_projection_preserves_scroll(self):self.assertEqual(len(map_scope(self.source())),65)
    def test_early_scroll_reset_is_rejected(self):
        source=self.source();source['points'][2]['scroll']=0
        with self.assertRaises(ValueError):map_scope(source)
    def test_missing_clear_is_rejected(self):
        source=self.source();source['points'][3]['scroll']=64
        with self.assertRaises(ValueError):map_scope(source)

class FollowingControlIntegrity(unittest.TestCase):
    def setUp(self):
        self.old=[['tick',800,True]];self.parent=dict(controlMemorySha256='parent',romSha256='rom')
        self.child=dict(inputCase='skip-held',parentControlMemorySha256='parent',parentEventsSha256=event_sha(self.old),setupSha256='setup',romSha256='rom',controlMemorySha256='child',controlDifferences=[],prefixControlHashes=['parent']*2,unhookedControlHashes=['child']*2)
        self.events=self.old+tail('skip-held')
    def test_complete_late_skip_control(self):attachment(self.parent,self.child,self.old,self.events,'setup')
    def test_earlier_rejected_skip_is_not_relabelled(self):
        with self.assertRaises(ValueError):attachment(self.parent,self.child,self.old,self.old+tail('skip-held')[1:],'setup')
    def test_missing_repeated_prefix_is_rejected(self):
        self.child['prefixControlHashes'].pop()
        with self.assertRaises(ValueError):attachment(self.parent,self.child,self.old,self.events,'setup')
    def test_changed_unobserved_endpoint_is_rejected(self):
        self.child['unhookedControlHashes'][1]='other'
        with self.assertRaises(ValueError):attachment(self.parent,self.child,self.old,self.events,'setup')

class IgnoredScrollStart(unittest.TestCase):
    def setUp(self):
        self.data,self.parent,self.raw=fixture(True)
        self.data['inputCase']='scroll-held';g=self.data['groups'][1];p=g['points'][0]
        g['points']=[p,dict(p,name='scrollWait',cycles=250),dict(p,name='scrollReady',cycles=260),dict(p,name='end',cycles=300,inputHeld=8)]
        g['interrupts']=[dict(kind='vblank',start=255,pressed=8)]
        end=self.data['groups'][2];end['points'].pop(1);end['points'][0]['inputHeld']=8;end['points'][-1]['inputHeld']=8;end['rawPrecedingInputSamples']+=1
    def test_actual_edge_inside_scroll_does_not_require_skip(self):attachment_scope(self.data,self.parent,self.raw)
    def test_edge_outside_scroll_cannot_claim_ignored_path(self):
        self.data['groups'][1]['interrupts'][0]['start']=265
        with self.assertRaises(ValueError):attachment_scope(self.data,self.parent,self.raw)
    def test_missing_edge_is_not_an_ignored_start(self):
        self.data['groups'][1]['interrupts'][0]['pressed']=0
        with self.assertRaises(ValueError):attachment_scope(self.data,self.parent,self.raw)
    def test_released_start_cannot_claim_held_exit(self):
        self.data['groups'][1]['points'][-1]['inputHeld']=0;self.data['groups'][2]['points'][0]['inputHeld']=0
        with self.assertRaises(ValueError):attachment_scope(self.data,self.parent,self.raw)

if __name__=='__main__':unittest.main()
