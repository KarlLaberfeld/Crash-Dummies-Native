"""Later selection preserves actual players and exact origin through instruction."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from test_selected_instruction_reference import fixture
from selected_instruction_reference import analyze
class LaterSelectedInstruction(unittest.TestCase):
 def cases(self,players=0,page=2):
  data,parent=fixture(players);data.update(origin='later-title-selected-start',targetPage=page);parent.update(origin='later-title-select',targetPage=page);return data,parent
 def test_both_players_all_pages(self):
  for page in range(1,5):
   for players in (0,1):self.assertEqual(len(analyze(*self.cases(players,page))),42)
 def test_missing_retained_origin(self):
  data,parent=self.cases();data.pop('origin')
  with self.assertRaises(ValueError):analyze(data,parent)
 def test_missing_parent_origin(self):
  data,parent=self.cases();parent.pop('origin')
  with self.assertRaises(ValueError):analyze(data,parent)
 def test_mixed_page(self):
  data,parent=self.cases();data['targetPage']=1
  with self.assertRaises(ValueError):analyze(data,parent)
 def test_invalid_page(self):
  with self.assertRaises(ValueError):analyze(*self.cases(page=0))
 def test_wrong_players(self):
  data,parent=self.cases(1);data['players']=0
  with self.assertRaises(ValueError):analyze(data,parent)
if __name__=='__main__':unittest.main()
