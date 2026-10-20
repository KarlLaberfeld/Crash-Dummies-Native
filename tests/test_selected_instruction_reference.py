"""Synthetic selected-Start provenance, fresh lives, storage and service integrity."""
import argparse,copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from selected_instruction_reference import GROUPS,TABLES,analyze,compare_many

def fixture(players=0):
    groups=[];now=1000;tick=65500;held=8;pressed=8;maps=[19]*2048;objects=[0]*256;restart=None
    parent=dict(inputCase='two-start' if players else 'one-start',controlMemorySha256='same-control',points=[dict(cycles=now,tick=tick,countdown=54,route=2,players=players,held=held,pressed=pressed,stat=1,lcdc=195,scrollY=0,lyc=23)],maps=list(maps),objects=objects)
    for index,name in enumerate(GROUPS):
        names=list(TABLES[index].values())
        if index==0:names=['begin','fadeEntry']+['palette','wait','tail','wait','tail','wait','tail','wait','tail']*8+['fadeReturned','audioStop','stopEntry','resetEntry','stateCleared','presetsReady','waveReady','resetReturned','audioDisabled','end']
        group=dict(name=name,points=[],rawSongs=[],interrupts=[],polls=[],writes=[],rasters=[],beforeMaps=list(maps),beforeObjects=list(objects),objects=list(objects));palettes=waits=0
        def stat(start):
            r=dict(kind='stat',start=start,end=start+288,phases={},returnAddress=0x261d);group['interrupts'].append(r)
            if index==0:group['rasters']+= [dict(boundary='begin',cycle=start),dict(boundary='end',cycle=start+288)]
        for n,label in enumerate(names):
            previous=now
            if n:now+=50000
            count= int(label in ('tail','audioStop')) if index==0 else (1 if n==1 else 3 if label=='backgroundCleared' else 0) if index==3 else int(label=='end') if index==4 else 4 if index==5 and label=='copyReturned' else 0
            for k in range(count):
                start=previous+1000+8000*k
                if index==0:stat(start-900);stat(start-500)
                elif index!=3 or n!=1:stat(start-500)
                r=dict(kind='vblank',start=start,tick=tick,countdown=54,held=0,pressed=0,musicEnabled=int(index in (0,5)),voiceStates=[dict(active=0) for _ in range(6)],phases={},returnAddress=0x261d);stamp=start
                for phase,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,116 if index==0 else 144,240,64,68,520 if index in (0,5) else 60)):stamp+=cost;r['phases'][phase]=stamp
                r['end']=stamp+120;group['interrupts'].append(r)
                if index==3 and n==1:stat(r['end']+40)
                tick=(tick+1)&65535;held=pressed=0
            if index==0 and label=='audioDisabled':stat(previous+1000)
            palettes+= index==0 and label=='palette';waits+=index==0 and label=='tail'
            p=dict(name=label,cycles=now,tick=tick,countdown=54,inputHeld=held,inputPressed=pressed)
            if index==0:p.update(palettes=palettes,waits=waits,bgp=0 if label=='end' else 228,obp0=0 if label=='end' else 196,obp1=0 if label=='end' else 224,musicEnabled=int(label not in ('audioDisabled','end')),stat=1,lcdc=195,scrollY=0,lyc=23)
            elif index==2:p.update(day0=1,day1=1,difficulty0=0,difficulty1=0,lives0=5 if n>=3 else 0,lives1=5 if players and n>=3 else 0)
            elif index==4:p.update(player=0,stage=1,difficulty=0,lives=5,result=0,display=5,stat=5,pendingRequests=0,musicEnabled=0)
            elif index==5:p.update(stage=1,display=5,stat=5,pendingRequests=0,musicEnabled=int(n!=0),song=2 if n else -1)
            group['points'].append(p);group['rawSongs'].append(2 if index==5 and n else 1)
        if index in (2,3):
            base=0x9c00 if index==2 else 0x9800
            group['writes'] += [dict(cycle=group['points'][0]['cycles']+4*i,address=base+i,value=0) for i in range(1024)]
            maps[base-0x9800:base-0x9800+1024]=[0]*1024
        if index==2:
            restart=group['points'][-2]['cycles']+8;group['writes'].append(dict(cycle=restart-8,address=0xff40,value=209))
        if index==5:
            group['beforeTiles']=[99]*1024;group['tiles']=[3]*1024;group['writes']+=[dict(kind='tile',cycle=now-10000+4*i,address=0x8340+i,value=3) for i in range(1024)]
        group['maps']=list(maps);groups.append(group)
    data=dict(version=1,inputCase=parent['inputCase'],players=players,controlMemorySha256='same-control',parentControlMemorySha256='same-control',reference=dict(titleStorageObserver='direct-vram-title-v1',instructionStorageObserver='direct-vram-instruction-v1'),storageReadOwner='direct-vram-title-v1',instructionReadOwner='direct-vram-instruction-v1',groups=groups,restartEpoch=restart)
    return data,parent

class SelectedEvidence(unittest.TestCase):
    def setUp(self):self.data,self.parent=fixture()
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_one_and_two_players(self):
        for players in (0,1):self.assertEqual(len(analyze(*fixture(players))),42)
    def test_case(self):self.data['inputCase']='back-a';self.reject()
    def test_parent(self):self.data['parentControlMemorySha256']='other';self.reject()
    def test_same_input_control(self):self.data['controlMemorySha256']='other';self.reject()
    def test_start_route(self):self.parent['points'][-1]['route']=1;self.reject()
    def test_player_choice(self):self.data['players']=1;self.reject()
    def test_segment_order(self):self.data['groups'].reverse();self.reject()
    def test_clock_attachment(self):self.data['groups'][2]['points'][0]['cycles']+=4;self.reject()
    def test_missing_boundary(self):self.data['groups'][1]['points'].pop();self.reject()
    def test_storage_observer(self):self.data['instructionReadOwner']='cpu';self.reject()
    def test_map_attachment(self):self.data['groups'][1]['beforeMaps'][0]=0;self.reject()
    def test_map_publication(self):self.data['groups'][2]['maps'][1024]=19;self.reject()
    def test_objects(self):self.data['groups'][3]['objects'][0]=72;self.reject()
    def test_missing_vblank(self):self.data['groups'][5]['interrupts'].pop();self.reject()
    def test_missing_stat(self):self.data['groups'][0]['interrupts'].pop(0);self.reject()
    def test_pending_priority(self):self.data['groups'][3]['interrupts'][:2]=list(reversed(self.data['groups'][3]['interrupts'][:2]));self.reject()
    def test_partial_reset_vblank(self):
        group=self.data['groups'][0];stop=next(p for p in group['points'] if p['name']=='audioStop');last=next(p for p in reversed(group['interrupts']) if p['kind']=='vblank');stop['cycles']=last['start']-4;stop['tick']=(stop['tick']-1)&65535;self.reject()
    def test_display_callback(self):self.data['groups'][4]['interrupts'][-1]['phases']['bookkeeping']+=4;self.reject()
    def test_voice_slots(self):self.data['groups'][5]['interrupts'][-1]['voiceStates'].pop();self.reject()
    def test_second_player_lives(self):self.data,self.parent=fixture(1);self.data['groups'][2]['points'][-1]['lives1']=0;self.reject()
    def test_single_player_lives(self):self.data['groups'][2]['points'][-1]['lives1']=5;self.reject()
    def test_day(self):self.data['groups'][2]['points'][0]['day0']=2;self.reject()
    def test_restart(self):self.data['restartEpoch']+=4;self.reject()
    def test_header(self):self.data['groups'][4]['points'][0]['player']=1;self.reject()
    def test_disabled_song_projection(self):self.data['groups'][5]['points'][0]['song']=1;self.reject()
    def test_selected_music(self):self.data['groups'][5]['rawSongs'][-1]=7;self.reject()
    def test_tile_extent(self):self.data['groups'][5]['tiles'].pop();self.reject()
    def test_tile_storage(self):self.data['groups'][5]['tiles'][0]=2;self.reject()
    def test_raw_song_extent(self):self.data['groups'][0]['rawSongs'].pop();self.reject()
    def test_tick(self):self.data['groups'][5]['points'][-1]['tick']+=1;self.reject()

class SelectedBatch(unittest.TestCase):
    def cases(self):return [argparse.Namespace(native_base=Path('selected'+str(i)),exit_base=Path('exit'+str(i)),players_base=Path('player'+str(i)),players_out=Path('players-ref'+str(i)),players_control=Path('players-control'+str(i)),exit_out=Path('exit-ref'+str(i)),exit_control=Path('exit-control'+str(i)),selected_out=Path('selected-ref'+str(i)),actions_base=Path('shared')) for i in range(2)]
    def test_each_parent_and_child(self):
        with patch('air_title_players_exit_reference.compare_many') as parents,patch('selected_instruction_reference.compare') as children:
            compare_many(self.cases());self.assertEqual([p.native_base for p in parents.call_args.args[0]],[Path('exit0'),Path('exit1')]);self.assertEqual(children.call_count,2)
    def test_mixed_parent(self):
        cases=self.cases();cases[1].actions_base=Path('other')
        with self.assertRaises(ValueError):compare_many(cases)
    def test_empty(self):
        with self.assertRaises(ValueError):compare_many([])

if __name__=='__main__':unittest.main()
