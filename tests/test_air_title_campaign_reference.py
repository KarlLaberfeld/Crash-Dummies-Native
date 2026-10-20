"""Retained choices, complete masked map clear and restart evidence guards."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_campaign_reference import analyze,POINTS

class TitleCampaignEvidence(unittest.TestCase):
    def setUp(self):
        cycles=[100,200,300,400,500,200000,200024,200056,200072]
        points=[dict(name=name,cycles=cycle,tick=9,countdown=54,inputHeld=0,inputPressed=0,day0=1,day1=1,difficulty0=0,difficulty1=0,lives0=0 if i<3 else 5,lives1=0,lcdc=0x51 if i<7 else 0xd1,pendingRequests=3) for i,(name,cycle) in enumerate(zip(POINTS.values(),cycles))]
        self.parent=dict(points=[dict(points[0])]);polls=[dict(cycle=600+144*i,mode=0) for i in range(1024)]
        writes=[dict(cycle=cycle,address=a,value=v) for cycle,a,v in [(110,0xc088,1),(126,0xc090,1),(210,0xc089,0),(226,0xc091,0),(328,0xc08a,5),(360,0xc092,0),(500,0xc035,0x9c)]]
        writes += [dict(cycle=p['cycle']+28,address=0x9c00+i,value=0) for i,p in enumerate(polls)]
        writes.append(dict(cycle=200044,address=0xff40,value=0xd1))
        before=[19]*1024+[23]*1024
        self.data=dict(choices=dict(day=1,difficulty=0,twoPlayers=False),storageReadOwner='direct-vram-title-v1',reference=dict(titleStorageObserver='direct-vram-title-v1'),points=points,polls=polls,writes=writes,vectors=[],beforeMaps=before,maps=[19]*1024+[0]*1024,objectsUnchanged=True)
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete(self):analyze(self.data,self.parent)
    def test_detached_entry(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_direct_provenance(self):self.data['storageReadOwner']='cpu';self.reject()
    def test_observer_provenance(self):self.data['reference']={};self.reject()
    def test_unqualified_two_player_original(self):self.data['choices']['twoPlayers']=True;self.reject()
    def test_unqualified_original_difficulty(self):self.data['choices']['difficulty']=1;self.reject()
    def test_masked_vectors(self):self.data['vectors']=[dict(cycle=700,pc=0x40)];self.reject()
    def test_objects_preserved(self):self.data['objectsUnchanged']=False;self.reject()
    def test_tick_preserved(self):self.data['points'][-1]['tick']=10;self.reject()
    def test_input_preserved(self):self.data['points'][-1]['inputHeld']=8;self.reject()
    def test_lives_initialized_at_owned_boundary(self):self.data['points'][2]['lives0']=5;self.reject()
    def test_unused_player_lives(self):self.data['points'][-1]['lives1']=5;self.reject()
    def test_retained_if_requests(self):self.data['points'][-1]['pendingRequests']=0;self.reject()
    def test_lcd_restarts_late(self):self.data['points'][5]['lcdc']=0xd1;self.reject()
    def test_all_readiness_reads(self):self.data['polls'].pop(400);self.reject()
    def test_no_unowned_busy_poll(self):self.data['polls'][400]['mode']=3;self.reject()
    def test_read_timing(self):self.data['polls'][400]['cycle']+=4;self.reject()
    def test_store_read_attachment(self):self.data['writes'][400]['cycle']+=4;self.reject()
    def test_every_clear_store(self):self.data['writes'].pop(400);self.reject()
    def test_no_game_data_write(self):self.data['writes'][400]['address']=0xc200;self.reject()
    def test_window_padding_cleared(self):self.data['maps'][-1]=23;self.reject()
    def test_background_unchanged(self):self.data['maps'][0]=0;self.reject()
    def test_store_endpoint(self):self.data['writes'][-1]['cycle']=200056;self.reject()
    def test_return_after_lcd_write(self):self.data['points'][-1]['cycles']=200056;self.reject()

if __name__=='__main__':unittest.main()
