"""Later-page Start/Select/unlock coverage and accepted-carousel attachment."""
import argparse,copy,sys,unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from title_cycle_reference import BRANCHES,later_tail,branch_extent,preceding_carousel,accepted_cycle_arguments,attachment,event_sha,compare_many


def branch(action='start',index=1):
 edges=[64,0,128,0,32,0,16] if action=='unlock' else [0,8 if action=='start' else 4];count=len(edges);duration=(480,480,960,480,960)[index]
 names=['begin']+['wait','ready','timerStored']*(count-1)+['wait','ready'];points=[dict(name=n) for n in names]+[dict(name='end',remaining=duration-count+1,waits=count,index=index,route=BRANCHES[action],inputPressed=edges[-1],pattern=0)];values=[0x16,0x17,0x18,0x15] if action=='unlock' else [0x15]
 return dict(points=points,interrupts=[dict(kind='vblank',pressed=v) for v in edges],writes=sum(([dict(address=0xc0b5,value=v),dict(address=0xc0b6,value=0x2b)] for v in values),[]))

class LaterBranches(unittest.TestCase):
 def setUp(self):self.group=branch()
 def check(self):branch_extent(self.group,1,'start')
 def reject(self):
  with self.assertRaises(ValueError):self.check()
 def test_all_actions_on_all_pages(self):
  for page in range(1,5):
   for action in BRANCHES:branch_extent(branch(action,page),page,action)
 def test_combined_edge_is_a_different_scope(self):self.group['interrupts'][-1]['pressed']=12;self.reject()
 def test_held_start_is_not_fresh(self):self.group['interrupts'][-1]['pressed']=0;self.reject()
 def test_wrong_route(self):self.group['points'][-1]['route']=3;self.reject()
 def test_wrong_page(self):self.group['points'][-1]['index']=2;self.reject()
 def test_wrong_counter(self):self.group['points'][-1]['remaining']-=1;self.reject()
 def test_extra_decrement(self):self.group['points'].insert(-1,dict(name='timerStored'));self.reject()
 def test_missing_service(self):self.group['interrupts'].pop();self.reject()
 def test_wrong_waits(self):self.group['points'][-1]['waits']+=1;self.reject()
 def test_missing_pointer_store(self):self.group['writes'].pop();self.reject()
 def test_wrong_pointer_value(self):self.group['writes'][0]['value']+=1;self.reject()
 def test_branch_cannot_advance_page(self):self.group['writes'].append(dict(address=0xc03e,value=2));self.reject()
 def test_unlock_requires_complete_fresh_sequence(self):
  group=branch('unlock');group['interrupts'][2]['pressed']=16
  with self.assertRaises(ValueError):branch_extent(group,1,'unlock')
 def test_unlock_requires_reset_selector_at_exit(self):
  group=branch('unlock');group['points'][-1]['pattern']=3
  with self.assertRaises(ValueError):branch_extent(group,1,'unlock')
 def test_unlock_requires_intermediate_selector_stores(self):
  group=branch('unlock');group['writes'][2]['value']-=1
  with self.assertRaises(ValueError):branch_extent(group,1,'unlock')

class LaterControlAttachment(unittest.TestCase):
 def setUp(self):
  self.events=[['tick',40,True]];self.parent=dict(romSha256='rom',controlMemorySha256='parent');self.child=dict(inputCase='carousel',laterAction='start',targetPage=2,parentControlMemorySha256='parent',parentEventsSha256=event_sha(self.events),setupSha256='setup',romSha256='rom',controlMemorySha256='child',controlDifferences=[],prefixControlHashes=['parent']*2,unhookedControlHashes=['child']*2);self.changed=self.events+later_tail('start',2)
 def check(self):attachment(self.parent,self.child,self.events,self.changed,'setup')
 def reject(self):
  with self.assertRaises(ValueError):self.check()
 def test_complete(self):self.check()
 def test_target_is_not_a_label_only(self):self.child['targetPage']=1;self.reject()
 def test_wrong_action(self):self.child['laterAction']='select';self.reject()
 def test_changed_tail(self):self.changed[-1][1]-=1;self.reject()
 def test_changed_prefix(self):self.changed[0]=['tick',39,True];self.reject()
 def test_missing_unobserved_full(self):self.child['unhookedControlHashes'].pop();self.reject()
 def test_missing_unobserved_prefix(self):self.child['prefixControlHashes'].pop();self.reject()
 def test_non_branch_cannot_have_target(self):
  with self.assertRaises(ValueError):later_tail('a',2)
 def test_zero_target_rejected(self):
  with self.assertRaises(ValueError):later_tail('start',0)
 def test_fifth_target_rejected(self):
  with self.assertRaises(ValueError):later_tail('select',5)
 def test_target_durations_use_actual_page_lengths(self):self.assertEqual(later_tail('start',4)[0],['tick',2263,True])
 def test_unlock_has_four_edges(self):self.assertEqual([e[1] for e in later_tail('unlock',3) if e[0]=='press'],['up','down','left','right'])

class CarouselPrefix(unittest.TestCase):
 def setUp(self):
  self.old=dict(romSha256='rom',parentInputCase='a',parentControlMemorySha256='parent',groups=[dict(name=str(n),content=[n]) for n in range(9)]);self.child=dict(self.old,laterAction='select',targetPage=3,groups=copy.deepcopy(self.old['groups'][:6]))
 def check(self):return preceding_carousel(self.child,self.old)
 def reject(self):
  with self.assertRaises(ValueError):self.check()
 def test_all_preceding_groups_preserved(self):self.assertEqual(len(self.check()),5)
 def test_changed_page_payload(self):self.child['groups'][2]['content'][0]+=1;self.reject()
 def test_missing_earlier_idle(self):self.child['groups'].pop(1);self.reject()
 def test_wrong_rom(self):self.child['romSha256']='other';self.reject()
 def test_wrong_initial_action(self):self.child['parentInputCase']='b';self.reject()
 def test_wrong_parent_hash(self):self.child['parentControlMemorySha256']='other';self.reject()
 def test_incomplete_accepted_carousel(self):self.old['groups'].pop();self.reject()
 def test_accepted_fresh_carousel_is_not_automatic(self):self.old['laterAction']='a';self.reject()
 def test_missing_native_accepted_scope(self):
  with self.assertRaises(ValueError):accepted_cycle_arguments(argparse.Namespace())
 def test_accepted_scope_is_separately_qualified(self):
  args=argparse.Namespace(native_base=Path('child'),cycle_out=Path('child-out'),cycle_control=Path('child-control'),accepted_cycle_base=Path('parent'),accepted_cycle_out=Path('parent-out'),accepted_cycle_control=Path('parent-control'));self.assertEqual(vars(accepted_cycle_arguments(args)),dict(native_base=Path('parent'),cycle_out=Path('parent-out'),cycle_control=Path('parent-control')))
class SharedQualification(unittest.TestCase):
 def test_shared_parents_once_complete_children_separately(self):
  a=argparse.Namespace(native_base=Path('child-a'),actions_base=Path('actions'),case_control=Path('control'),actions_out=Path('actions-out'),cycle_out=Path('child-out'),cycle_control=Path('child-control'),accepted_cycle_base=Path('auto'),accepted_cycle_out=Path('auto-out'),accepted_cycle_control=Path('auto-control'),startup=Path('startup'));b=copy.copy(a);b.native_base=Path('child-b');b.cycle_out=Path('child-b-out')
  with patch('air_title_page_reference.compare') as page,patch('air_title_actions_reference.compare') as action,patch('title_cycle_reference.compare') as child:
   compare_many([a,b]);self.assertEqual(page.call_count,1);self.assertEqual(action.call_count,1);self.assertEqual(child.call_count,3);self.assertEqual(child.call_args_list[0].args[0].native_base,Path('auto'));self.assertEqual([call.args[0].native_base for call in child.call_args_list[1:]],[Path('child-a'),Path('child-b')]);self.assertTrue(all(call.kwargs['_cycle_parent_qualified'] for call in child.call_args_list[1:]))

if __name__=='__main__':unittest.main()
