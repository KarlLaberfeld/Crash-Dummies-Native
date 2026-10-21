"""Later direct/selected instruction ancestry remains explicit through text."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from test_selected_text_reference import fixture
from selected_text_reference import analyze,instruction_observation_start
class LaterText(unittest.TestCase):
 def cases(self,origin='later-title-selected-start',page=2,players=1):
  data,parent=fixture(players);data.update(origin=origin,targetPage=page);parent.update(origin=origin,targetPage=page)
  if origin=='later-title-start':data['parentInputCase']=parent['inputCase']='carousel'
  return data,parent
 def test_both_native_origins_all_pages(self):
  for page in range(1,5):
   for origin in ('later-title-start','later-title-selected-start'):self.assertEqual(len(analyze(*self.cases(origin,page),1200)),66)
 def test_wrong_page(self):
  data,parent=self.cases();data['targetPage']=3
  with self.assertRaises(ValueError):analyze(data,parent,1200)
 def test_missing_origin(self):
  data,parent=self.cases();data.pop('origin')
  with self.assertRaises(ValueError):analyze(data,parent,1200)
 def test_wrong_origin(self):
  data,parent=self.cases();data['origin']='later-title-start'
  with self.assertRaises(ValueError):analyze(data,parent,1200)
 def test_later_cannot_impersonate_first_page(self):
  data,parent=self.cases();parent.pop('origin')
  with self.assertRaises(ValueError):analyze(data,parent,1200)
 def test_unknown_origin(self):
  data,parent=self.cases();data['origin']=parent['origin']='other'
  with self.assertRaises(ValueError):analyze(data,parent,1200)
 def test_direct_source_start_suffix(self):self.assertEqual(instruction_observation_start([['tick',1,True],['press','start'],['tick',4,True],['release','start'],['tick',2,True],['tick',100,True]]),1)
 def test_select_cannot_impersonate_start_suffix(self):
  with self.assertRaises(ValueError):instruction_observation_start([['press','select'],['tick',4,True],['release','select'],['tick',2,True],['tick',100,True]])
if __name__=='__main__':unittest.main()
