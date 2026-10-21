import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from test_air_map_reference import fixture
from selected_map_reference import owners

class SelectedRowOwners(unittest.TestCase):
 def setUp(self):
  self.data=fixture()[0];self.game=dict(romSha256='rom',controlMemorySha256='control',inputCase='full-prompt',parentInputCase='two-start',players=1,selectedEntryCycle=1020,updates=1,points=[dict(cycles=1020),dict(cycles=4000)],interrupts=[dict(kind='vblank',phases=dict(display=2884))]);self.data.update({k:self.game[k] for k in ('romSha256','controlMemorySha256','inputCase','parentInputCase','players','selectedEntryCycle','updates')})
  self.data['reference']=dict(titleStorageObserver='direct-vram-title-v1')
  for p in self.data['points']:p['tilesReadOwner']='direct-vram-title-v1'
 def reject(self):
  with self.assertRaises(ValueError):owners(self.data,self.game)
 def test_complete(self):self.assertEqual(len(owners(self.data,self.game)),4)
 def test_terminal_row_owner_is_explicit(self):self.data['terminalWait']=self.game['terminalWait']=True;self.assertEqual(len(owners(self.data,self.game)),4)
 def test_terminal_row_cannot_borrow_nonterminal_owner(self):self.data['terminalWait']=True;self.reject()
 def test_integer_terminal_owner_rejected(self):self.data['terminalWait']=self.game['terminalWait']=1;self.reject()
 def test_rom(self):self.data['romSha256']='other';self.reject()
 def test_control(self):self.data['controlMemorySha256']='other';self.reject()
 def test_players(self):self.data['players']=0;self.reject()
 def test_case(self):self.data['inputCase']='skip-held';self.reject()
 def test_selection(self):self.data['parentInputCase']='one-start';self.reject()
 def test_entry(self):self.data['selectedEntryCycle']+=4;self.reject()
 def test_updates(self):self.data['updates']+=1;self.reject()
 def test_start_cycle(self):self.game['points'][0]['cycles']+=4;self.reject()
 def test_end_cycle(self):self.game['points'][-1]['cycles']+=4;self.reject()
 def test_display_count(self):self.game['interrupts']*=2;self.reject()
 def test_phase(self):self.game['interrupts'][0]['phases']['display']+=4;self.reject()
 def test_direct_storage_retains_blocked_cpu_status(self):self.data['points'][0]['lcd']['readBlocked']=1;self.assertEqual(len(owners(self.data,self.game)),4)
 def test_missing_direct_observer(self):self.data['reference'].clear();self.reject()
 def test_wrong_read_owner(self):self.data['points'][0]['tilesReadOwner']='cpu-read';self.reject()
 def test_transfer_byte(self):self.data['points'][2]['tiles'][224]=127;self.reject()
 def test_short_row(self):self.data['points'][0]['buffer'].pop();self.reject()
 def test_reordered(self):self.data['points'][1],self.data['points'][2]=self.data['points'][2],self.data['points'][1];self.reject()
if __name__=='__main__':unittest.main()
