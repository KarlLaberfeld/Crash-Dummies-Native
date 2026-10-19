"""Reject detached, incomplete and service-advancing reset observations."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_reset_reference import POINTS,STORES,analyze


class TitleResetScope(unittest.TestCase):
    def setUp(self):
        points=[dict(name=name,cycles=100+10000*i,tick=2,countdown=54,inputHeld=33 if i<5 else 255,inputPressed=1,lcdc=0xdb if i==0 else 0x5b,bank=3 if 6<=i<=8 else 1) for i,name in enumerate(POINTS.values())]
        points[-1].update(scoresUnchanged=True,mapsBlank=True,objectsBlank=True)
        addresses=list(range(0x9c00,0xa000))+list(range(0x9800,0x9c00))+list(range(0xc100,0xc200))+list(STORES.values())
        writes=[dict(cycle=11000+i,address=a,value=255 if a==0xff8a else 0) for i,a in enumerate(addresses)]
        self.data=dict(points=points,polls=[dict(cycle=150,ly=144),dict(cycle=182,ly=145)],writes=writes,vectors=[])
        self.parent=dict(points=[dict(points[0])])
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete_prefix(self):self.assertEqual(analyze(self.data,self.parent),dict(boundaries=10,polls=2,writes=2320))
    def test_detached_parent(self):self.parent['points'][0]['cycles']-=4;self.reject()
    def test_reordered_boundaries(self):self.data['points'][2]['name']='backgroundCleared';self.reject()
    def test_masked_display_cannot_tick(self):self.data['points'][-1]['tick']+=1;self.reject()
    def test_no_vector_is_allowed(self):self.data['vectors'].append(dict(pc=0x40,cycle=150));self.reject()
    def test_missing_map_cell(self):self.data['writes'].pop(1023);self.reject()
    def test_wrong_sentinel(self):self.data['writes'][-1]['value']=0;self.reject()
    def test_score_names_survive_reset(self):self.data['points'][-1]['scoresUnchanged']=False;self.reject()
    def test_no_early_equal_line(self):self.data['polls'][0]['ly']=145;self.reject()
    def test_no_unbounded_poll_gap(self):self.data['polls'][-1]['cycle']+=4;self.reject()
    def test_no_bank_leak(self):self.data['points'][-1]['bank']=3;self.reject()
    def test_pressed_edge_is_retained(self):self.data['points'][-1]['inputPressed']=0;self.reject()
    def test_stores_stay_in_owner(self):self.data['writes'][-1]['cycle']=90000;self.reject()


if __name__=='__main__':unittest.main()
