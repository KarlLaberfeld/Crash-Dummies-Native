import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_result_transition_reference import analyze,compare_transition


def synthetic_transition(failure=False,short_hold=False):
    """Small source-shaped fixture; no cartridge bytes/reference capture."""
    points=[];irqs=[];tick=1000;countdown=600;bgp=0
    def point(name,cycle,lcd=128):
        points.append(dict(name=name,cycles=cycle,tick=tick,countdown=countdown,result=1 if failure else 3,display=10,
            bgp=bgp,obp0=bgp&0xcf,obp1=bgp&0xf3,musicEnabled=1,interruptFlags=3,inputHeld=held,inputPressed=pressed,lcd=dict(lcdc=lcd)))
    def vb(cycle,address):
        nonlocal tick,countdown
        costs=[180,704,280,272,240,64,68,60,120];names=['dma','joypad','display','bookkeeping','effects','audioBank','music','restore']
        time=cycle;phases={}
        for name,cost in zip(names,costs):time+=cost;phases[name]=time
        time+=costs[-1]
        irqs.append(dict(kind='vblank',start=cycle,end=time,selector=0,returnAddress=address,tick=tick,
            countdown=countdown,phases=phases,held=held,pressed=pressed,musicEnabled=1,effectRequest=-1,resetEnabled=1,resetLatched=0))
        tick+=1;countdown-=1
    def stat(cycle,address):irqs.append(dict(kind='stat',start=cycle,end=cycle+248,selector=0,returnAddress=address))
    held=pressed=0
    for name,cycle in zip(['playerReady','failurePortrait','failurePortraitReady','failureTextReady'] if failure else
                          ['playerReady','successTextReady','portraitReady','musicReady'],[100,200,300,400]):point(name,cycle,0)
    point('lcdWriteReturned',900);point('enable',1000);point('enableFollower',1004)
    vb(1048,0x20d1);stat(irqs[-1]['end']+36,0x20d1)
    now=irqs[-1]['end']+16
    if failure:
        point('failureWait',now);stat(now+100,0x261d);vb(now+1000,0x261d);now=irqs[-1]['end']+72
        point('failureWaitReturned',now);now+=8;point('musicEntry',now);now+=14052;point('musicReady',now);now+=24
    point('fadeEntry',now);now+=20
    for segment in range(8):
        point('palette',now);bgp=(0,0x50,0x50,0x90,0xa4,0xe4,0xe4,0xe4)[segment];now+=76
        for wait in range(4):
            point('wait',now);stat(now+100,0x261d);vb(now+1000,0x261d);now=irqs[-1]['end']+16+56
            point('tail',now);now+=16 if wait<3 else 40 if segment==7 else 28
    point('fadeReturned',now)
    if short_hold:
        now+=44
        for index in range(2):
            point('holdWait',now);stat(now+100,0x261d)
            held=pressed=2 if index else 0;vb(now+1000,0x261d);now=irqs[-1]['end']+72
            point('holdTail',now);now+=36 if index else 52
        point('holdReturned',now);now+=12384;point('musicStopped',now);points[-1]['musicEnabled']=0
        now+=16;point('failureResultReturned',now);points[-1]['musicEnabled']=0
    data=dict(version=2 if short_hold else 1,failureHold=short_hold,points=points,interrupts=irqs)
    native=[dict(boundary=p['name'],cycle=p['cycles']-100,**{k:p[k] for k in ('tick','countdown','bgp','obp0','obp1','musicEnabled','inputHeld','inputPressed')}) for p in points]
    services=[dict(service=i,cycle=r['start']-100,tick=r['tick'],countdown=r['countdown']-1,display=272,effects=64,music=60,musicEnabled=1,inputHeld=r['held'],inputPressed=r['pressed'])
        for i,r in enumerate(r for r in irqs if r['kind']=='vblank')]
    native_irqs=[dict(kind=r['kind'],vectorCycle=r['start']-100,owner=3 if i<2 else 2) for i,r in enumerate(irqs)]
    summary=[dict(end=now-100,lcdEpoch=880,tick=tick,countdown=countdown,displays=len(services),stats=len(services))]
    return data,native,services,native_irqs,summary


class ResultTransitionEvidence(unittest.TestCase):
    def setUp(self):self.data,self.native,self.services,self.irqs,self.summary=synthetic_transition()
    def compare(self):return compare_transition(self.data,self.native,self.services,self.irqs,self.summary,100)
    def test_complete_source_shaped_fixture(self):self.assertEqual(self.compare(),[])
    def test_missing_boundary_rejects(self):
        self.native.pop()
        with self.assertRaises(ValueError):self.compare()
    def test_service_truncation_rejects(self):
        self.services.pop()
        with self.assertRaises(ValueError):self.compare()
    def test_irq_truncation_rejects(self):
        self.irqs.pop()
        with self.assertRaises(ValueError):self.compare()
    def test_reordered_boundary_rejects(self):
        self.native[3],self.native[4]=self.native[4],self.native[3]
        with self.assertRaises(ValueError):self.compare()
    def test_unqualified_vector_rejects(self):
        self.irqs[2]['owner']=0
        with self.assertRaises(ValueError):self.compare()
    def test_wrong_pending_owner_rejects(self):
        self.irqs[0]['owner']=2
        with self.assertRaises(ValueError):self.compare()
    def test_native_boundary_delay_reported(self):
        self.native[1]['cycle']+=4;self.assertIn('boundary',self.compare()[0])
    def test_native_music_service_difference_reported(self):
        self.services[1]['music']+=4;self.assertIn('service',self.compare()[0])
    def test_native_irq_delay_reported(self):
        self.irqs[3]['vectorCycle']+=4;self.assertIn('interrupt',self.compare()[0])
    def test_native_epoch_difference_reported(self):
        self.summary[0]['lcdEpoch']+=4;self.assertIn('summary',self.compare()[0])
    def test_missing_summary_rejects(self):
        self.summary=[]
        with self.assertRaises(ValueError):self.compare()
    def test_original_pending_follower_delay_rejects(self):
        self.data['interrupts'][0]['start']+=4
        with self.assertRaises(ValueError):analyze(self.data)
    def test_original_stat_selector_rejects(self):
        self.data['interrupts'][1]['selector']=4
        with self.assertRaises(ValueError):analyze(self.data)
    def test_original_palette_work_rejects(self):
        self.data['points'][9]['cycles']+=4
        with self.assertRaises(ValueError):analyze(self.data)
    def test_perfect_celebration_rejects(self):
        self.data['points'][0]['result']=7
        with self.assertRaises(ValueError):analyze(self.data)
    def test_missing_complete_hold_cannot_pass_as_incoming_only(self):
        self.data['failureHold']=True
        with self.assertRaises(ValueError):analyze(self.data)
    def shortened_hold(self):
        self.data,self.native,self.services,self.irqs,self.summary=synthetic_transition(True,True)
    def test_full_shortened_hold_requires_the_source_fresh_action(self):
        self.shortened_hold();self.assertEqual(self.compare(),[])
    def test_hold_cannot_truncate_without_action(self):
        self.shortened_hold();next(p for p in reversed(self.data['points']) if p['name']=='holdTail')['inputPressed']=0
        with self.assertRaises(ValueError):analyze(self.data)
    def test_wrong_shortened_return_work_rejects(self):
        self.shortened_hold();next(p for p in self.data['points'] if p['name']=='holdReturned')['cycles']+=4
        with self.assertRaises(ValueError):analyze(self.data)
    def test_shortened_hold_button_edge_rejects(self):
        self.shortened_hold();self.data['interrupts'][-1]['pressed']=0
        with self.assertRaises(ValueError):analyze(self.data)
    def test_shortened_hold_native_fresh_edge_is_compared(self):
        self.shortened_hold();self.services[-1]['inputPressed']=0;self.assertIn('service',self.compare()[0])


if __name__=='__main__':unittest.main()
