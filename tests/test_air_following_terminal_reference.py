"""Invented terminal-wait and outgoing-fade comparison integrity; no ROM."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from test_air_following_scene_reference import fixture as scene_fixture
from air_following_scene_reference import analyze as scenes
from air_following_resource_reference import compare_resources
from air_following_outro_reference import analyze,compare_outro
from air_exit_timing import intervals,stop_work
from air_timing import display_cycles,IRQ_PHASES,VBLANK_FIXED


def terminal_fixture():
    values=scene_fixture();data=values[0];data['terminalWait']=True
    for p in data['points']:p['result']=0
    block=data['points'][-10:]
    for p in block[2:]:p['result']=33
    block[8]['name']='terminalWait';block[8]['cycles']-=4
    block[9]['name']='terminalEnd';block[9]['cycles']-=48
    for r in data['interrupts'][-2:]:r['ready']=0
    for p,q in zip(data['points'],values[1]):
        q.update(result=p['result'],boundary=p['name'],cycle=p['cycles']-1000)
    for i,p in enumerate(data['points']):
        for q in values[2][16*i:16*(i+1)]:q['boundary']=p['name']
    values[5][0]['end']-=48
    return values


def outro_fixture():
    values=terminal_fixture();gameplay=values[0];entry=copy.deepcopy(values[5]);terminal=gameplay['points'][-1]
    now=terminal['cycles'];tick=terminal['tick'];points=[];irqs=[];enabled=1;palette=228
    palettes=[228,228,224,208,192,128,64,0]
    stat=entry[0]['nextStat']+1000+20;vblank=entry[0]['nextVBlank']+1000+20
    def point(name):points.append(dict(name=name,cycles=now,tick=tick,ready=0,musicEnabled=enabled,bgp=palette,obp0=palette&0xcf,obp1=palette&0xf3))
    point('audioStop');now+=stop_work();enabled=0;point('fadeEntry');now+=44
    for segment in range(8):
        point('palette');now+=76;palette=palettes[segment]
        for wait in range(4):
            index=4*segment+wait;point('wait')
            irqs.append(dict(kind='stat',start=stat,end=stat+288,ready=0,selector=4,display=4,returnAddress=0x261d))
            workload=dict(map_pending=0,ready=0,chunks=13,cursor=index%13,tick=tick,fade_remaining=0,collected=0,quota=14)
            work={**VBLANK_FIXED,'display':sum(display_cycles(**workload).values()),'bookkeeping':240,'effects':64,'music':60}
            pos=vblank+work['prefix'];phases={}
            for name in IRQ_PHASES.values():phases[name]=pos;pos+=work[name]
            r=dict(kind='vblank',start=vblank,end=pos,returnAddress=0x261d,selector=4,display=4,ready=0,tick=tick,
                held=33,pressed=0,resetEnabled=1,resetLatched=0,effectRequest=-1,musicEnabled=0,displayWorkload=workload,phases=phases,oam=[0]*160)
            irqs.append(r);now=pos+72;tick=(tick+1)&65535;point('tail')
            now+=16 if wait<3 else 28 if segment<7 else 40
            stat+=70224;vblank+=70224
    point('end')
    data=dict(version=2,points=points,interrupts=irqs,fadePalettes=palettes,precedingDisplays=entry[0]['displays'])
    phases=[{k:r[k] for k in ('phase','index','tickBefore','tickAfter','elapsed','work','bgp','obp0','obp1','musicEnabled')} for r in intervals(data)]
    for i,row in enumerate(phases):row.update(start=points[i]['cycles']-1000,end=points[i+1]['cycles']-1000)
    services=[]
    for i,r in enumerate(irqs[1::2]):
        services.append(dict(service=data['precedingDisplays']+i,cycle=r['start']-1000,tick=r['tick'],display=sum(display_cycles(**r['displayWorkload']).values()),effects=64,music=60,inputHeld=33,inputPressed=0))
    vectors=[dict(kind=r['kind'],vectorCycle=r['start']-1000,owner=2) for r in irqs]
    sprites=[dict(service=data['precedingDisplays']+i//40,slot=i%40,present=0,x=0,y=0,flags=0) for i in range(1280)]
    summary=copy.deepcopy(entry)
    summary[0].update(end=now-1000,tick=tick,displays=entry[0]['displays']+32,stats=entry[0]['stats']+32,nextStat=entry[0]['nextStat']+32*70224,nextVBlank=entry[0]['nextVBlank']+32*70224)
    return [data,gameplay,phases,services,vectors,sprites,summary,entry]


class TerminalIntegrity(unittest.TestCase):
    def setUp(self):self.values=terminal_fixture();self.data=self.values[0]
    def compare(self):return compare_resources(*self.values,1000)
    def rejected(self):
        with self.assertRaises(ValueError):scenes(self.data)
    def test_complete_terminal_update(self):self.assertEqual(self.compare()[0],[])
    def test_terminal_scope_required(self):self.data.pop('terminalWait');self.rejected()
    def test_final_boundary_required(self):self.data['points'][-1]['name']='end';self.rejected()
    def test_terminal_result_required(self):self.data['points'][-8]['result']=0;self.rejected()
    def test_result_cannot_precede_actor_completion(self):self.data['points'][-9]['result']=33;self.rejected()
    def test_earlier_gameplay_cannot_have_result(self):self.data['points'][20]['result']=33;self.rejected()
    def test_result_cannot_change_in_scene(self):self.data['points'][-3]['result']=1;self.rejected()
    def test_result_must_have_completion_bit(self):self.data['points'][-8]['result']=32;self.rejected()
    def test_missing_result_snapshot(self):self.data['points'][0].pop('result');self.rejected()
    def test_shorter_terminal_branch_required(self):self.data['points'][-2]['cycles']+=4;self.rejected()
    def test_next_input_gate_cannot_be_borrowed(self):self.data['points'][-1]['cycles']+=48;self.rejected()
    def test_final_wait_keeps_resource_gate_closed(self):self.data['interrupts'][-1]['ready']=1;self.rejected()
    def test_final_stat_keeps_resource_gate_closed(self):self.data['interrupts'][-2]['ready']=1;self.rejected()
    def test_wrong_native_result_is_compared(self):
        self.values[1][-1]['result']=1
        self.assertEqual(self.compare()[0][0]['category'],'result')


class OutgoingIntegrity(unittest.TestCase):
    def setUp(self):self.values=outro_fixture();self.data=self.values[0];self.gameplay=self.values[1]
    def compare(self):return compare_outro(*self.values,1000)
    def rejected(self):
        with self.assertRaises(ValueError):analyze(self.data,self.gameplay)
    def test_complete_attached_outgoing_fade(self):self.assertEqual(self.compare(),[])
    def test_terminal_owner_required(self):self.gameplay['terminalWait']=False;self.rejected()
    def test_detached_exit_clock(self):self.data['points'][0]['cycles']-=4;self.rejected()
    def test_detached_exit_counter(self):self.data['points'][0]['tick']-=1;self.rejected()
    def test_audio_must_be_running_at_entry(self):self.data['points'][0]['musicEnabled']=0;self.rejected()
    def test_detached_service_number(self):self.data['precedingDisplays']-=1;self.rejected()
    def test_missing_stat(self):self.data['interrupts'].pop(0);self.rejected()
    def test_wrong_stat_work(self):self.data['interrupts'][0]['end']+=4;self.rejected()
    def test_wrong_selector(self):self.data['interrupts'][0]['selector']=5;self.rejected()
    def test_unowned_return(self):self.data['interrupts'][0]['returnAddress']=0x2618;self.rejected()
    def test_busy_upload_gate(self):self.data['interrupts'][1]['ready']=1;self.rejected()
    def test_lost_input_edge(self):self.data['interrupts'][1]['pressed']=1;self.rejected()
    def test_lost_display_counter(self):self.data['points'][4]['tick']-=1;self.rejected()
    def test_missing_sprite_snapshot(self):self.data['interrupts'][1]['oam'].pop();self.rejected()
    def test_native_clock_detached(self):
        self.values[-1][0]['end']+=4
        with self.assertRaises(ValueError):self.compare()
    def test_native_phase_fields_complete(self):
        self.values[2][0].pop('work')
        with self.assertRaises(ValueError):self.compare()
    def test_native_palette_compared(self):
        self.values[2][4]['obp0']^=4
        self.assertEqual(self.compare()[0]['category'],'phase')
    def test_native_vector_compared(self):
        self.values[4][0]['owner']=0
        self.assertEqual(self.compare()[0]['category'],'interrupt')
    def test_native_audio_work_compared(self):
        self.values[3][0]['music']=64
        self.assertEqual(self.compare()[0]['category'],'service')
    def test_native_sprite_compared(self):
        self.values[5][0]['present']=1
        self.assertEqual(self.compare()[0]['category'],'spritePublication')
    def test_native_final_deadline_compared(self):
        self.values[6][0]['nextVBlank']-=70224
        self.assertEqual(self.compare()[0]['category'],'summary')


if __name__=='__main__':unittest.main()
