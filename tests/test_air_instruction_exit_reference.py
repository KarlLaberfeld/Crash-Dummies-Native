import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_instruction_exit_reference import FIELDS,analyze,compare_exit

def fixture():
    points=[];irqs=[];tick=5;bgp=228;obp0=196;obp1=224;time=1000
    def point(name):points.append(dict(name=name,cycles=time,tick=tick,countdown=1,scroll=64,bgp=bgp,obp0=obp0,obp1=obp1,musicEnabled=int(name!='end'),inputHeld=8,inputPressed=0))
    def wait():
        nonlocal time,tick
        r=dict(kind='vblank',start=time+1000,tick=tick,countdown=1,display=5,selector=5,held=8,pressed=0,resetEnabled=1,resetLatched=0,effectRequest=-1,musicEnabled=1,returnAddress=0x261d,phases={});stamp=r['start']
        for name,cost in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,144,240,64,68,60)):
            stamp+=cost;r['phases'][name]=stamp
        r['end']=stamp+120;irqs.append(r);time+=20000;tick+=1
    point('begin');time+=32;point('fadeCall');time+=44
    for segment in range(8):
        point('fadePalette');time+=20;bgp=0 if segment==7 else 228;point('bgpReady');time+=56
        obp0=bgp&207;obp1=bgp&243
        for i in range(4):point('fadeWait');wait();point('fadeReady');time+=16
    point('fadeReturned');wait();point('audioStop');time+=12384;point('end')
    data=dict(version=1,precedingDisplays=865,points=points,interrupts=irqs,polls=[],writes=[])
    native=[dict(boundary=p['name'],cycle=p['cycles']-1000,**{k:p[k] for k in FIELDS}) for p in points]
    services=[dict(service=865+i,cycle=r['start']-1000,tick=r['tick'],countdown=1,display=144,effects=64,music=60,inputHeld=8,inputPressed=0) for i,r in enumerate(irqs)]
    native_irqs=[dict(kind='vblank',vectorCycle=r['start']-1000,owner=2) for r in irqs]
    return data,native,services,native_irqs,[],[],[dict(end=time-1000,tick=tick,countdown=1,displays=898)]

class ExitIntegrity(unittest.TestCase):
    def setUp(self):self.values=list(fixture());self.data=self.values[0]
    def compare(self):return compare_exit(*self.values,1000)
    def test_complete_semantic_storage_fixture(self):self.assertEqual(self.compare(),[])
    def test_missing_fade_step_rejects(self):
        self.data['points'].pop(5)
        with self.assertRaises(ValueError):self.compare()
    def test_missing_native_irq_rejects(self):
        self.values[3].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_missing_final_wait_rejects(self):
        self.data['interrupts'].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_interrupted_sound_reset_rejects(self):
        self.data['points'][-1]['cycles']+=4
        with self.assertRaises(ValueError):self.compare()
    def test_incomplete_palette_rejects(self):
        self.data['points'][-1]['bgp']=228
        with self.assertRaises(ValueError):self.compare()
    def test_changed_countdown_rejects(self):
        self.data['points'][4]['countdown']=2
        with self.assertRaises(ValueError):self.compare()
    def test_wrong_stat_selector_rejects(self):
        self.data['interrupts'][0]['selector']=4
        with self.assertRaises(ValueError):self.compare()
    def test_held_start_cannot_borrow_prompt_branch(self):
        self.data['points'][0]['inputHeld']=0
        with self.assertRaises(ValueError):self.compare()
    def test_native_palette_difference_reported(self):
        self.values[1][3]['bgp']=0;self.assertEqual(self.compare()[0]['category'],'boundary')
    def test_native_audio_work_difference_reported(self):
        self.values[2][0]['music']=64;self.assertEqual(self.compare()[0]['category'],'service')
    def test_unowned_vector_rejects(self):
        self.values[3][0]['owner']=0
        with self.assertRaises(ValueError):self.compare()

if __name__=='__main__':unittest.main()
