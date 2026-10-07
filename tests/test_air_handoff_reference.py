import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_handoff_reference import analyze,compare_handoff

def fixture():
    common=dict(tick=5,countdown=86,player=0,lives0=5,lives1=5,result=3,display=10,musicEnabled=0,
        inputHeld=0,inputPressed=0,lcd=dict(lcdc=219))
    points=[]
    for name,time,player in [('begin',1000,0),('switchEntry',1048,0),('selectionEntry',1104,1),('livesTest',1192,1),
                             ('backgroundClear',1216,1),('backgroundCleared',148768,1),('instructionEntry',148788,1)]:
        p=dict(common,name=name,cycles=time,player=player);points.append(p)
    points[-1]['result']=0
    # Source-shaped access fixture, not original/hardware timing evidence.
    polls=[dict(cycles=1356+144*i,mode=0) for i in range(1024)]
    writes=[dict(cycles=1384+144*i,address=0x9800+i,value=0) for i in range(1024)]
    return dict(version=1,points=points,interrupts=[],polls=polls,writes=writes)

def native(data):
    points=[dict(boundary=p['name'],cycle=p['cycles']-1000,**{k:p[k] for k in ('tick','countdown','player','lives0','lives1','result','inputHeld','inputPressed')}) for p in data['points']]
    polls=[dict(cycle=p['cycles']-1000,mode=p['mode']) for p in data['polls']]
    writes=[dict(cycle=p['cycles']-1000,address=p['address'],value=p['value']) for p in data['writes']]
    last=data['points'][-1];summary=[dict(end=last['cycles']-1000,displays=0,**{k:last[k] for k in ('tick','countdown','player','lives0','lives1','result')})]
    return [points,[],[],polls,writes,summary]

class HandoffIntegrity(unittest.TestCase):
    def setUp(self):self.data=fixture()
    def test_complete_source_shaped_map_clear(self):self.assertEqual(analyze(self.data),[])
    def test_native_full_coverage(self):self.assertEqual(compare_handoff(self.data,*native(self.data),1000),[])
    def test_missing_terminal_rejects(self):
        self.data['points'].pop()
        with self.assertRaises(ValueError):analyze(self.data)
    def test_missing_selection_rejects(self):
        self.data['points'].pop(1)
        with self.assertRaises(ValueError):analyze(self.data)
    def test_early_player_mutation_rejects(self):
        self.data['points'][1]['player']=1
        with self.assertRaises(ValueError):analyze(self.data)
    def test_unselected_live_player_rejects(self):
        for p in self.data['points']:p['lives1']=0
        with self.assertRaises(ValueError):analyze(self.data)
    def test_unowned_life_mutation_rejects(self):
        self.data['points'][4]['lives0']=4
        with self.assertRaises(ValueError):analyze(self.data)
    def test_unowned_reset_rejects(self):
        self.data['points'][0]['inputHeld']=15
        with self.assertRaises(ValueError):analyze(self.data)
    def test_lcd_off_rejects(self):
        self.data['points'][1]['lcd']=dict(lcdc=91)
        with self.assertRaises(ValueError):analyze(self.data)
    def test_missing_final_store_rejects(self):
        self.data['writes'].pop()
        with self.assertRaises(ValueError):analyze(self.data)
    def test_wrong_destination_rejects(self):
        self.data['writes'][13]['address']+=1
        with self.assertRaises(ValueError):analyze(self.data)
    def test_busy_final_poll_rejects(self):
        self.data['polls'][13]['mode']=3
        with self.assertRaises(ValueError):analyze(self.data)
    def test_duplicated_poll_cannot_cover_missing_poll(self):
        self.data['polls'].pop(13);self.data['polls'].insert(14,dict(cycles=self.data['polls'][14]['cycles']-32,mode=3))
        with self.assertRaises(ValueError):analyze(self.data)
    def test_native_truncated_access_rejects(self):
        rows=native(self.data);rows[4].pop()
        with self.assertRaises(ValueError):compare_handoff(self.data,*rows,1000)
    def test_native_wrong_completion_is_reported(self):
        rows=native(self.data);rows[0][-1]['cycle']+=4
        self.assertEqual(len(compare_handoff(self.data,*rows,1000)),1)
    def test_native_wrong_glyph_is_reported(self):
        rows=native(self.data);rows[4][13]['value']=1
        self.assertEqual(len(compare_handoff(self.data,*rows,1000)),1)
if __name__=='__main__':unittest.main()
