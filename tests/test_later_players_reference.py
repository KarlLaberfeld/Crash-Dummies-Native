"""Retained later Select ancestry and page-index ownership on both exits."""
import copy,sys,unittest,argparse
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_players_reference import later_select_parent,analyze,attachment,tail,later_arguments,compare_later_many,observation_start,continuation_observation_start
from air_title_players_exit_reference import analyze as analyze_exit
from test_air_title_players_reference import fixture
from test_air_title_players_exit_reference import fixture as exit_fixture
class LaterSelect(unittest.TestCase):
 def setUp(self):
  self.data,parent=fixture();end=dict(parent['points'][0],name='end',index=2,pattern=0);self.cycle=dict(version=1,inputCase='carousel',laterAction='select',targetPage=2,controlMemorySha256=parent['controlMemorySha256'],groups=[dict(name='0.page'),dict(name='0.idle'),dict(name='1.page'),dict(name='1.idle',points=[end],maps=parent['maps'],objects=[0]*256)]);self.data.update(origin='later-title-select',targetPage=2)
 def reject(self):
  with self.assertRaises(ValueError):analyze(self.data,self.cycle)
 def test_complete(self):self.assertEqual(len(analyze(self.data,self.cycle)),82)
 def test_retains_raw_parent_case(self):self.assertEqual(later_select_parent(self.cycle)['inputCase'],'carousel')
 def test_wrong_route(self):self.cycle['groups'][-1]['points'][-1]['route']=2;self.reject()
 def test_wrong_action(self):self.cycle['laterAction']='start';self.reject()
 def test_wrong_index(self):self.cycle['groups'][-1]['points'][-1]['index']=3;self.reject()
 def test_wrong_edge(self):self.cycle['groups'][-1]['points'][-1]['inputPressed']=8;self.reject()
 def test_missing_previous(self):self.cycle['groups'].pop(0);self.reject()
 def test_missing_origin(self):self.data.pop('origin');self.reject()
 def test_wrong_page(self):self.data['targetPage']=1;self.reject()
 def test_changed_map(self):self.cycle['groups'][-1]['maps']=[0]*2048;self.reject()
 def test_nonempty_objects(self):self.cycle['groups'][-1]['objects'][0]=1;self.reject()
 def test_first_page_relabel_rejected(self):self.cycle['inputCase']='select';self.reject()
class RetainedExit(unittest.TestCase):
 def cases(self,route):
  data,parent=exit_fixture(route);data.update(origin='later-title-select',targetPage=3);parent.update(origin='later-title-select',targetPage=3)
  for p in data['points'][:3] if route==1 else data['points']:p['page']=3
  parent['points'][0]['page']=3
  return data,parent
 def test_start_keeps_page(self):self.assertEqual(len(analyze_exit(*self.cases(2))),0)
 def test_back_resets_after_actual_store(self):self.assertEqual(len(analyze_exit(*self.cases(1))),82)
 def test_start_cannot_pretend_page_zero(self):
  data,parent=self.cases(2);data['points'][-1]['page']=0
  with self.assertRaises(ValueError):analyze_exit(data,parent)
 def test_back_cannot_reset_early(self):
  data,parent=self.cases(1);data['points'][1]['page']=0
  with self.assertRaises(ValueError):analyze_exit(data,parent)
 def test_back_cannot_retain_after_store(self):
  data,parent=self.cases(1);data['points'][3]['page']=3
  with self.assertRaises(ValueError):analyze_exit(data,parent)
 def test_missing_origin(self):
  data,parent=self.cases(1);data.pop('origin')
  with self.assertRaises(ValueError):analyze_exit(data,parent)
class LaterBatch(unittest.TestCase):
 def test_preserves_first_action_and_full_control(self):
  args=argparse.Namespace(native_base=Path('child'),later_base=Path('cycle'),later_out=Path('source'),later_control=Path('cycleControl'),case_control=Path('firstA'),players_control=Path('new'),players_out=Path('newSource'))
  parent=later_arguments(args);self.assertEqual(parent.case_control,Path('firstA'));self.assertEqual(parent.cycle_control,Path('cycleControl'));self.assertEqual(parent.native_base,Path('cycle'));self.assertFalse(hasattr(parent,'later_control'))
 def test_empty(self):
  with self.assertRaises(ValueError):compare_later_many([])
class ObservationSuffix(unittest.TestCase):
 def test_first_page_keeps_full_observer(self):self.assertEqual(observation_start([],False),0)
 def test_later_fresh_select_is_armed_before_input(self):
  events=[['tick',100,True]]+[['press','select'],['tick',4,True],['release','select'],['tick',2,True],['tick',100,True]]
  self.assertEqual(observation_start(events,True),1)
 def test_unknown_select_suffix(self):
  with self.assertRaises(ValueError):observation_start([['tick',100,True]],True)
 def test_every_player_exit_arms_before_controls(self):
  from air_title_players_reference import CASES
  for case in CASES:self.assertEqual(continuation_observation_start([['tick',1,True]]+tail(case),case),1)
 def test_instruction_keeps_exact_extension(self):self.assertEqual(continuation_observation_start([['tick',1,True]]+tail('two-start')+[['tick',100,True]],'two-start',[['tick',100,True]]),1)
 def test_missing_extension_rejected(self):
  with self.assertRaises(ValueError):continuation_observation_start(tail('two-start'),'two-start',[['tick',100,True]])

if __name__=='__main__':unittest.main()
