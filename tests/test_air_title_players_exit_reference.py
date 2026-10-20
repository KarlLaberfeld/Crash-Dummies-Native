"""Synthetic object-clear, retained music/input and complete return integrity."""
import argparse,copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from test_password_return_reference import fixture as title_fixture
from air_title_players_exit_reference import analyze,compare_many

def fixture(route):
    common=dict(tick=65520,countdown=54,center=0,windowY=112,closed=0,cleared=0,opened=0,rows=0,page=0,players=0,route=route,song=1,musicEnabled=1,held=1 if route==1 else 8,pressed=1 if route==1 else 8,stat=1,lcdc=195,scrollY=0,lyc=23)
    points=[dict(common,name='begin',cycles=1000),dict(common,name='objectsCleared',cycles=2296),dict(common,name='objectsReturned' if route==1 else 'end',cycles=2316)];irqs=[];before=[19]*2048;maps=list(before);writes=[dict(cycle=1016+8*i,address=0xc100+i,value=0) for i in range(160)]
    if route==1:
        old,_=title_fixture(1);start=next(i for i,p in enumerate(old['points']) if p['name']=='closeCall');points.extend([dict(common,name='pageStored',cycles=2332),dict(common,name='closeCall',cycles=2348)])
        irqs=old['interrupts'][1:];closed=cleared=opened=0
        for i,p in enumerate(irqs):p.update(tick=(65520+i)&65535,musicEnabled=1)
        for p in old['points'][start+1:]:
            if p['name']=='centerStored':closed+=1
            if p['name'] in ('closeReturned','clearReturned'):cleared+=1
            if p['name']=='openStored':opened+=1
            completed=[r for r in irqs if r['end']+16<=p['cycles']];owner=completed[-1] if completed else common
            points.append(dict(common,name=p['name'],cycles=p['cycles'],center=p['center'],windowY=p['windowY'],rows=p['rows'],closed=closed,cleared=cleared,opened=opened,tick=(65520+len(completed))&65535,held=owner['held'],pressed=owner['pressed']))
        before=old['beforeMaps'];maps=old['maps'];writes+=[dict(cycle=2316,address=0xc03e,value=0)]+old['writes']
    objects=[72,24,254,128]+[0]*252;case='back-a' if route==1 else 'one-start'
    parent=dict(inputCase=case,controlMemorySha256='parent',points=[dict(points[0])],maps=before,objects=objects)
    data=dict(version=1,inputCase=case,parentControlMemorySha256='parent',points=points,interrupts=irqs,storageReadOwner='direct-vram-title-v1',reference=dict(titleStorageObserver='direct-vram-title-v1'),beforeMaps=before,maps=maps,beforeObjects=objects,objects=[0]*256,writes=writes,rasters=[])
    return data,parent

class PlayerExitEvidence(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture(1)
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_both_routes(self):
        for route,count in ((1,82),(2,0)):self.assertEqual(len(analyze(*fixture(route))),count)
    def test_parent(self):self.data['parentControlMemorySha256']='other';self.reject()
    def test_case(self):self.data['inputCase']='back-b';self.reject()
    def test_retained_players(self):self.data['points'][-1]['players']=1;self.reject()
    def test_song(self):self.data['points'][-1]['song']=7;self.reject()
    def test_stop(self):self.data['points'][-1]['musicEnabled']=0;self.reject()
    def test_clear_duration(self):self.data['points'][1]['cycles']+=4;self.reject()
    def test_return_duration(self):self.data['points'][2]['cycles']+=4;self.reject()
    def test_clear_store_cycle(self):self.data['writes'][10]['cycle']+=4;self.reject()
    def test_clear_store_value(self):self.data['writes'][10]['value']=1;self.reject()
    def test_clear_extent(self):self.data['writes'].pop(159);self.reject()
    def test_clear_does_not_write_tail(self):self.data['writes'].insert(160,dict(cycle=2296,address=0xc1a0,value=0));self.reject()
    def test_tail_remains_owned(self):
        data,parent=fixture(2);data['beforeObjects'][200]=parent['objects'][200]=data['objects'][200]=17;analyze(data,parent)
        data['objects'][200]=0
        with self.assertRaises(ValueError):analyze(data,parent)
    def test_arrow_cleared(self):self.data['objects'][0]=72;self.reject()
    def test_missing_page_store(self):self.data['writes'].pop(160);self.reject()
    def test_missing_presentation(self):self.data['points'].pop(12);self.reject()
    def test_input_ownership(self):self.data['points'][-1]['pressed']=1;self.reject()
    def test_tick(self):self.data['points'][-1]['tick']+=1;self.reject()
    def test_service_extent(self):self.data['interrupts'].pop();self.reject()
    def test_voice_slots(self):self.data['interrupts'][0]['voiceStates'].pop();self.reject()
    def test_map(self):self.data['maps'][0]=0;self.reject()
    def test_storage_owner(self):self.data['storageReadOwner']='cpu';self.reject()

class PlayerExitBatch(unittest.TestCase):
    def cases(self):return [argparse.Namespace(native_base=Path('exit'+str(i)),players_base=Path('player'+str(i)),players_out=Path('player-ref'+str(i)),players_control=Path('player-control'+str(i)),exit_out=Path('exit-ref'+str(i)),exit_control=Path('exit-control'+str(i)),actions_base=Path('shared')) for i in range(2)]
    def test_all_parents_and_children(self):
        with patch('air_title_players_reference.compare_many') as parents,patch('air_title_players_exit_reference.compare') as children:
            compare_many(self.cases());self.assertEqual([p.native_base for p in parents.call_args.args[0]],[Path('player0'),Path('player1')]);self.assertEqual(children.call_count,2)
    def test_mixed(self):
        cases=self.cases();cases[1].actions_base=Path('other')
        with self.assertRaises(ValueError):compare_many(cases)
    def test_empty(self):
        with self.assertRaises(ValueError):compare_many([])

if __name__=='__main__':unittest.main()
