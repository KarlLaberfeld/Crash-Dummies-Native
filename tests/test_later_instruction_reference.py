"""Later Start keeps real carousel provenance and all six instruction owners."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from selected_instruction_reference import later_start_parent,analyze
from test_selected_instruction_reference import fixture
class LaterInstructionParent(unittest.TestCase):
 def setUp(self):
  self.data,parent=fixture();end=dict(parent['points'][-1],name='end',index=2,pattern=0,inputHeld=8,inputPressed=8);self.cycle=dict(version=1,inputCase='carousel',laterAction='start',targetPage=2,controlMemorySha256=parent['controlMemorySha256'],groups=[dict(name='0.page'),dict(name='0.idle'),dict(name='1.page'),dict(name='1.idle',points=[end],maps=parent['maps'],objects=parent['objects'])]);self.data.update(origin='later-title-start',inputCase='carousel',targetPage=2)
 def reject(self):
  with self.assertRaises(ValueError):analyze(self.data,self.cycle)
 def test_complete_six_groups_keep_retained_start(self):self.assertEqual(len(analyze(self.data,self.cycle)),42)
 def test_real_input_case_is_not_renamed_to_selection(self):self.assertEqual(later_start_parent(self.cycle)['inputCase'],'carousel')
 def test_wrong_route(self):self.cycle['groups'][-1]['points'][-1]['route']=3;self.reject()
 def test_wrong_action(self):self.cycle['laterAction']='unlock';self.reject()
 def test_wrong_index(self):self.cycle['groups'][-1]['points'][-1]['index']=1;self.reject()
 def test_wrong_fresh_edge(self):self.cycle['groups'][-1]['points'][-1]['inputPressed']=4;self.reject()
 def test_unknown_origin(self):self.data['origin']='first-page';self.reject()
 def test_wrong_control(self):self.data['controlMemorySha256']='other';self.reject()
 def test_wrong_player_choice(self):self.data['players']=1;self.reject()
 def test_missing_previous_page(self):self.cycle['groups'].pop(0);self.reject()
 def test_incomplete_objects(self):self.cycle['groups'][-1]['objects'].pop();self.reject()
 def test_live_object(self):self.cycle['groups'][-1]['objects'][0]=1;self.reject()
 def test_incomplete_map(self):self.cycle['groups'][-1]['maps'].pop();self.reject()
 def test_missing_picture(self):self.data['groups'].pop();self.reject()
if __name__=='__main__':unittest.main()
