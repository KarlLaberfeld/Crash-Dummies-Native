import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_instruction_text_reference import FIELDS,analyze,compare_text

def fixture():
    points=[]
    for name,time,speed,delay,mask,tick in [('begin',1000,0,4,0,5),('textNext',1084,5,1,8,5),('glyphWait',1300,5,1,8,5),
        ('glyphReady',10000,5,1,8,6),('delayExpired',10148,5,0,8,6),('textNext',12000,5,5,8,6),('textFinish',12200,5,5,8,6),('end',12324,0,5,0,6)]:
        points.append(dict(name=name,cycles=time,tick=tick,countdown=1,scroll=0,speed=speed,delay=delay,skipMask=mask,layer=152,column=0,row=17,inputHeld=0,inputPressed=0))
    r=dict(kind='vblank',start=8000,tick=5,countdown=1,display=5,selector=5,held=0,pressed=0,resetEnabled=1,resetLatched=0,effectRequest=-1,musicEnabled=1,returnAddress=0x261d,phases={});time=r['start']
    for name,work in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,144,240,64,68,60)):
        time+=work;r['phases'][name]=time
    r['end']=time+120
    polls=[dict(cycles=11000,mode=0)];writes=[dict(cycles=11028,address=0x9a20,value=2)]
    data=dict(version=1,campaign=dict(stage=2,player=0,difficulty=0),precedingDisplays=858,points=points,interrupts=[r],polls=polls,writes=writes)
    native=[dict(boundary=p['name'],cycle=p['cycles']-1000,**{k:p[k] for k in (*FIELDS,'column','row','delay')}) for p in points]
    services=[dict(service=858,cycle=7000,tick=5,countdown=1,display=144,effects=64,music=60,inputHeld=0,inputPressed=0)]
    return data,native,services,[dict(kind='vblank',vectorCycle=7000,owner=2)],[dict(cycle=10000,mode=0)],[dict(cycle=10028,address=0x9a20,value=2)],[dict(end=11324,tick=6,countdown=1,scroll=0,skipped=0,displays=859)]

class TextIntegrity(unittest.TestCase):
    def setUp(self):self.values=list(fixture());self.data=self.values[0]
    def compare(self):return compare_text(*self.values,1000)
    def test_complete_semantic_storage_fixture(self):self.assertEqual(self.compare(),[])
    def test_missing_terminal_rejects(self):
        self.data['points'].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_missing_native_write_rejects(self):
        self.values[5].clear()
        with self.assertRaises(ValueError):self.compare()
    def test_missing_glyph_wait_rejects(self):
        self.data['points'].pop(2)
        with self.assertRaises(ValueError):self.compare()
    def test_changed_countdown_rejects(self):
        self.data['points'][3]['countdown']=2
        with self.assertRaises(ValueError):self.compare()
    def test_unqualified_irq_rejects(self):
        self.values[3][0]['owner']=0
        with self.assertRaises(ValueError):self.compare()
    def test_wrong_callback_rejects(self):
        self.data['interrupts'][0]['display']=10
        with self.assertRaises(ValueError):self.compare()
    def test_unowned_speed_rejects(self):
        self.data['points'][2]['speed']=4
        with self.assertRaises(ValueError):self.compare()
    def test_source_write_outside_layer_rejects(self):
        self.data['writes'][0]['address']=0x9c00
        with self.assertRaises(ValueError):self.compare()
    def test_native_glyph_difference_reported(self):
        self.values[5][0]['value']=3;self.assertEqual(self.compare()[0]['category'],'writes')
    def test_native_delay_difference_reported(self):
        self.values[1][3]['delay']=3;self.assertEqual(self.compare()[0]['category'],'boundary')
    def test_unused_inherited_delay_excluded(self):
        self.values[1][0]['delay']=0;self.assertEqual(self.compare(),[])
    def test_duplicate_finish_rejects(self):
        self.data['points'][1]['name']='textFinish'
        with self.assertRaises(ValueError):self.compare()

if __name__=='__main__':unittest.main()
