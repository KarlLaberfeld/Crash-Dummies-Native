import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_instruction_map_reference import FIELDS,analyze,compare_map
from air_timing import vblank_work

def fixture():
    points=[];irqs=[];tick=5;countdown=100;lcdc=219;display=10;stat=0;lyc=120
    def point(name,time):points.append(dict(name=name,cycles=time,tick=tick,countdown=countdown,lcdc=lcdc,lyc=lyc,scroll=0,alternate=1,display=display,stat=stat,inputHeld=0,inputPressed=0))
    def service(time,work,return_address):
        r=dict(kind='vblank',start=time,tick=tick,countdown=countdown,display=display,held=0,pressed=0,resetEnabled=1,resetLatched=0,effectRequest=-1,musicEnabled=1,returnAddress=return_address,phases={})
        for name,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,work,240,64,68,60)):
            time+=cost;r['phases'][name]=time
        r['end']=time+120;irqs.append(r)
    point('begin',1000);point('lineWait',1028);service(2000,272,0x2629);tick+=1;countdown-=1;lcdc=217
    point('objectsDisabled',10000);point('scrollCleared',10024);display=5;point('callbacksReady',10048)
    stat=5;point('enabled',10068);lyc=95;point('compareReady',10088)
    irqs.append(dict(kind='stat',start=10128,end=10416,selector=5,returnAddress=0x26af))
    point('mapJump',10432);point('mapBegin',10448);time=10524
    for i in range(64):
        point('stepWait',time);service(time+1000,144,0x261d);tick+=1;point('stepReady',time+20000)
        point('mapWrite',time+20024);lcdc=(lcdc&~8)|(8 if i%2 else 0);point('stepComplete',time+20036);time+=20100
    point('mapReturn',points[-1]['cycles']+24);point('end',points[-1]['cycles']+16)
    polls=[dict(cycles=1064,ly=144)]
    data=dict(version=1,precedingDisplays=788,points=points,interrupts=irqs,polls=polls)
    native=[dict(boundary=p['name'],cycle=p['cycles']-1000,**{k:p[k] for k in FIELDS}) for p in points]
    services=[dict(service=788+i,cycle=p['start']-1000,tick=p['tick'],countdown=p['countdown']-(p['display']!=5),display=vblank_work(p)['display'],effects=64,music=60,inputHeld=0,inputPressed=0) for i,p in enumerate(irqs) if p['kind']=='vblank']
    # STAT is excluded from the display-service index.
    for i,r in enumerate(services):r['service']=788+i
    native_irqs=[dict(kind=p['kind'],vectorCycle=p['start']-1000,owner=2 if p['returnAddress']==0x261d else 1) for p in irqs]
    return data,native,services,native_irqs,[dict(cycle=64,ly=144)],[dict(end=points[-1]['cycles']-1000,tick=tick,countdown=countdown,displays=788+len(services))]

class MapIntegrity(unittest.TestCase):
    def setUp(self):self.values=list(fixture());self.data=self.values[0]
    def compare(self):return compare_map(*self.values,1000)
    def test_complete_semantic_fixture(self):self.assertEqual(self.compare(),[])
    def test_missing_native_step_rejects(self):
        self.values[1].pop(12)
        with self.assertRaises(ValueError):self.compare()
    def test_missing_source_step_rejects(self):
        self.data['points'].pop(12)
        with self.assertRaises(ValueError):self.compare()
    def test_missing_stat_write_request_rejects(self):
        self.data['interrupts'].pop(1)
        with self.assertRaises(ValueError):self.compare()
    def test_countdown_decrement_after_swap_rejects(self):
        self.data['points'][12]['countdown']-=1
        with self.assertRaises(ValueError):self.compare()
    def test_early_compare_change_rejects(self):
        self.data['points'][4]['lyc']=95
        with self.assertRaises(ValueError):self.compare()
    def test_missing_step_service_rejects(self):
        self.data['interrupts'].pop(2)
        with self.assertRaises(ValueError):self.compare()
    def test_unowned_initial_transition_rejects(self):
        self.data['points'][0]['alternate']=0
        with self.assertRaises(ValueError):self.compare()
    def test_incomplete_ly_wait_rejects(self):
        self.data['polls'][-1]['ly']=143
        with self.assertRaises(ValueError):self.compare()
    def test_changed_map_bit_reported(self):
        self.values[1][12]['lcdc']^=8;self.assertEqual(self.compare()[0]['category'],'boundary')
    def test_shifted_irq_reported(self):
        self.values[3][2]['vectorCycle']+=4;self.assertEqual(self.compare()[0]['category'],'interrupt')
    def test_reset_chord_rejects(self):
        self.data['points'][4]['inputHeld']=15
        with self.assertRaises(ValueError):self.compare()
    def inherited_scroll(self):
        self.data['followingResult']=True
        for p in self.data['points'][:3]:p['scroll']=64
        for p in self.values[1][:3]:p['scroll']=64
    def test_following_map_retains_scroll_until_clear(self):
        self.inherited_scroll();self.assertEqual(self.compare(),[])
    def test_inherited_scroll_requires_following_scope(self):
        self.inherited_scroll();self.data.pop('followingResult')
        with self.assertRaises(ValueError):self.compare()
    def test_inherited_scroll_cannot_clear_early(self):
        self.inherited_scroll();self.data['points'][2]['scroll']=0
        with self.assertRaises(ValueError):self.compare()
    def test_inherited_scroll_must_clear_at_store(self):
        self.inherited_scroll();self.data['points'][3]['scroll']=64
        with self.assertRaises(ValueError):self.compare()
    def test_native_inherited_scroll_compared(self):
        self.inherited_scroll();self.values[1][0]['scroll']=0
        self.assertEqual(self.compare()[0]['category'],'boundary')

if __name__=='__main__':unittest.main()
