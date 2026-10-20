"""Direct instruction image and music evidence integrity, synthetic only."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_picture_reference import analyze,compare_voices,VOICE_FIELDS
from test_air_instruction_picture_reference import fixture as result_fixture

def fixture():
    data,*_=result_fixture();data.update(afterTitle=True,precedingDisplays=703,storageReadOwner='direct-vram-title-v1',reference=dict(instructionStorageObserver='direct-vram-instruction-v1'),objectsUnchanged=True)
    for i,p in enumerate(data['points']):p.update(player=0,stage=1,difficulty=0,lives=5,display=5,stat=5,countdown=54,lcdc=0xd1,scrollY=0,pendingRequests=0,musicSelected=2 if i else 1)
    r=data['interrupts'][0];r.update(countdown=54,selector=5)
    for name in ('bookkeeping','effects','audioBank','music','restore'):r['phases'][name]-=128
    r['end']-=128
    r['voiceStates']=[dict(active=0,**dict.fromkeys(VOICE_FIELDS,0)) for _ in range(6)]
    r['voiceStates'][0].update(active=128,position=0x5000,remaining=2)
    data['scrollWrites']=[dict(cycles=r['start']+1284,address=0xff42,value=0)]
    data['beforeMaps']=[13]+[0]*2047;data['maps']=list(data['beforeMaps'])
    for p in data['writes']:
        if p['kind']=='map':data['maps'][p['address']-0x9800]=p['value']
    data['beforeTiles']=[99]*1024;data['tiles']=[p['value'] for p in data['writes'] if p['kind']=='tile']
    parent=dict(points=[dict(data['points'][0])],maps=list(data['beforeMaps']))
    return data,parent

class TitlePictureEvidence(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete(self):self.assertEqual(len(analyze(self.data,self.parent)),1)
    def test_explicit_post_title_owner(self):del self.data['afterTitle'];self.reject()
    def test_direct_instruction_observer(self):self.data['reference']={};self.reject()
    def test_direct_maps_owner(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_native_service_counter(self):self.data['precedingDisplays']=0;self.reject()
    def test_attached_header_boundary(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_attached_header_maps(self):self.parent['maps'][0]=9;self.reject()
    def test_direct_tiles_not_attempted_writes(self):self.data['tiles'][500]=99;self.reject()
    def test_complete_tile_storage(self):self.data['tiles'].pop();self.reject()
    def test_complete_initial_tile_storage(self):self.data['beforeTiles'].pop();self.reject()
    def test_full_object_storage(self):self.data['objectsUnchanged']=False;self.reject()
    def test_native_day(self):self.data['points'][-1]['stage']=2;self.reject()
    def test_native_player(self):self.data['points'][-1]['player']=1;self.reject()
    def test_native_difficulty(self):self.data['points'][-1]['difficulty']=1;self.reject()
    def test_native_lives(self):self.data['points'][-1]['lives']=4;self.reject()
    def test_retained_countdown(self):self.data['points'][-1]['countdown']=53;self.reject()
    def test_actual_display_counter(self):self.data['interrupts'][0]['tick']=4;self.reject()
    def test_no_result_countdown_decrement(self):self.data['interrupts'][0]['countdown']=53;self.reject()
    def test_actual_boundary_counter(self):self.data['points'][2]['tick']=6;self.reject()
    def test_actual_input_owner(self):self.data['points'][2]['inputHeld']=8;self.reject()
    def test_selected_instruction_song(self):self.data['points'][1]['musicSelected']=1;self.reject()
    def test_selected_song_enabled(self):self.data['points'][1]['musicEnabled']=0;self.reject()
    def test_scroll_store_count(self):self.data['scrollWrites'].clear();self.reject()
    def test_scroll_store_boundary(self):self.data['scrollWrites'][0]['cycles']+=4;self.reject()
    def test_picture_not_unrelated_header_change(self):self.data['maps'][0]=0;self.reject()
    def test_window_preserved(self):self.data['maps'][2047]=1;self.reject()
    def test_every_picture_cell(self):self.data['writes'].pop();self.reject()
    def test_music_voices_complete(self):self.data['interrupts'][0]['voiceStates'].pop();self.reject()
    def test_native_voice_projection_and_changes(self):
        services=analyze(self.data,self.parent);states=services[0]['voiceStates']
        rows=[dict(service=703,voice=i,musicCost=60,**{k:v for k,v in p.items() if k!='active'},active=int(bool(p['active']&128))) for i,p in enumerate(states)]
        self.assertEqual(compare_voices(services,rows),[])
        rows[0]['position']+=1;self.assertEqual(compare_voices(services,rows)[0]['category'],'voice')
    def test_inactive_voice_payload_not_claimed(self):
        services=analyze(self.data,self.parent);rows=[dict(service=703,voice=i,musicCost=60,**dict(p,active=int(bool(p['active']&128)))) for i,p in enumerate(services[0]['voiceStates'])]
        rows[1]['position']=12345;self.assertEqual(compare_voices(services,rows),[])
    def test_native_voice_order(self):
        services=analyze(self.data,self.parent);rows=[dict(service=703,voice=i,musicCost=60,**dict(p,active=int(bool(p['active']&128)))) for i,p in enumerate(services[0]['voiceStates'])]
        rows[1]['voice']=0
        with self.assertRaises(ValueError):compare_voices(services,rows)
    def test_native_voices_count(self):
        with self.assertRaises(ValueError):compare_voices(analyze(self.data,self.parent),[])

if __name__=='__main__':unittest.main()
