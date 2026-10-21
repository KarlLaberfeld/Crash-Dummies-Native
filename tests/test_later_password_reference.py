"""Later unlock-to-password linkage rejects detached decisions and storage."""
import argparse,copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_password_reference import later_parent,later_arguments,analyze
from test_air_title_password_reference import fixture

class LaterPasswordParent(unittest.TestCase):
 def setUp(self):
  self.data,self.parent=fixture();end=dict(self.parent['points'][-1],name='end',route=4,index=2,pattern=0);self.cycle=dict(version=1,inputCase='carousel',laterAction='unlock',targetPage=2,controlMemorySha256='parent',groups=[dict(name='0.page'),dict(name='0.idle'),dict(name='1.page'),dict(name='1.idle',points=[end],objects=[0]*256,maps=self.parent['maps'])])
 def reject(self):
  with self.assertRaises(ValueError):later_parent(self.cycle)
 def test_complete_parent_preserves_actual_source_point(self):
  parent=later_parent(self.cycle);self.assertIs(parent['points'][-1],self.cycle['groups'][-1]['points'][-1]);self.assertEqual(len(analyze(self.data,parent)),82)
 def test_wrong_route(self):self.cycle['groups'][-1]['points'][-1]['route']=2;self.reject()
 def test_wrong_action(self):self.cycle['laterAction']='start';self.reject()
 def test_wrong_index(self):self.cycle['groups'][-1]['points'][-1]['index']=1;self.reject()
 def test_unfinished_unlock(self):self.cycle['groups'][-1]['points'][-1]['pattern']=3;self.reject()
 def test_wrong_edge(self):self.cycle['groups'][-1]['points'][-1]['inputPressed']=8;self.reject()
 def test_missing_group(self):self.cycle['groups'].pop(0);self.reject()
 def test_wrong_final_group(self):self.cycle['groups'][-1]['name']='0.idle';self.reject()
 def test_incomplete_objects(self):self.cycle['groups'][-1]['objects'].pop();self.reject()
 def test_live_objects(self):self.cycle['groups'][-1]['objects'][0]=1;self.reject()
 def test_incomplete_maps(self):self.cycle['groups'][-1]['maps'].pop();self.reject()
 def test_zero_target(self):self.cycle['targetPage']=0;self.reject()
 def test_other_carousel_kind(self):self.cycle['inputCase']='first-password';self.reject()
 def test_child_paths_are_removed_before_parent_qualification(self):
  args=argparse.Namespace(native_base=Path('child'),later_base=Path('parent'),later_out=Path('parent-out'),password_out=Path('child-out'),password_control=Path('control'),startup=Path('startup'));self.assertEqual(vars(later_arguments(args)),dict(native_base=Path('parent'),cycle_out=Path('parent-out'),cycle_control=Path('control'),startup=Path('startup')))
if __name__=='__main__':unittest.main()
