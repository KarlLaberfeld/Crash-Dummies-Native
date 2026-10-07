import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_instruction_header_reference import POINTS,analyze,compare_header

def fixture():
    points=[]
    for name,time in zip(POINTS.values(),(1000,5000,5088,5116,6000,10000,10088,14000,18000,18088,22000,28000)):
        points.append(dict(name=name,cycles=time,tick=6 if name=='end' else 5,countdown=85 if name=='end' else 86,
            player=0,stage=2,difficulty=0,lives=5,display=10,result=0,musicEnabled=0,inputHeld=0,inputPressed=0))
    r=dict(kind='vblank',start=23000,tick=5,countdown=86,held=0,pressed=0,resetEnabled=1,resetLatched=0,
        effectRequest=-1,musicEnabled=0,returnAddress=0x261d,phases={})
    time=r['start']
    for name,work in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,272,240,64,68,60)):
        time+=work;r['phases'][name]=time
    r['end']=time+120
    data=dict(version=1,precedingDisplays=663,points=points,interrupts=[r],polls=[dict(cycles=2000,mode=0)],writes=[dict(cycles=2028,address=0x9800,value=1)])
    native=[dict(boundary=p['name'],cycle=p['cycles']-1000,**{k:p[k] for k in ('tick','countdown','player','stage','difficulty','inputHeld','inputPressed')}) for p in points]
    services=[dict(service=663,cycle=22000,tick=5,countdown=85,display=272,effects=64,music=60,inputHeld=0,inputPressed=0)]
    return data,native,services,[dict(kind='vblank',vectorCycle=22000,owner=2)],[dict(cycle=1000,mode=0)],

class HeaderIntegrity(unittest.TestCase):
    def setUp(self):
        self.values=list(fixture())+[ [dict(cycle=1028,address=0x9800,value=1)], [dict(end=27000,tick=6,countdown=85,displays=664,stats=0)] ]
        self.data=self.values[0]
    def compare(self):return compare_header(*self.values,1000)
    def test_complete_source_shaped_storage_fixture(self):self.assertEqual(self.compare(),[])
    def test_missing_terminal_rejects(self):
        self.data['points'].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_unowned_campaign_mutation_rejects(self):
        self.data['points'][3]['stage']=1
        with self.assertRaises(ValueError):self.compare()
    def test_unowned_music_rejects(self):
        self.data['points'][0]['musicEnabled']=1
        with self.assertRaises(ValueError):self.compare()
    def test_life_clamp_branch_work_rejects(self):
        self.data['points'][3]['cycles']+=4
        with self.assertRaises(ValueError):self.compare()
    def test_missing_poll_rejects(self):
        self.values[4].clear()
        with self.assertRaises(ValueError):self.compare()
    def test_native_glyph_difference_reported(self):
        self.values[5][0]['value']=2;self.assertEqual(self.compare()[0]['category'],'writes')
    def test_unqualified_irq_rejects(self):
        self.values[3][0]['owner']=0
        with self.assertRaises(ValueError):self.compare()
    def test_terminal_service_mismatch_rejects(self):
        self.values[6][0]['displays']=663
        with self.assertRaises(ValueError):self.compare()
    def test_perfect_cleared_result_service(self):
        for p in self.data['points']:p['display']=2
        r=self.data['interrupts'][0]
        for name in ('bookkeeping','effects','audioBank','music','restore'):r['phases'][name]+=68
        r['end']+=68;self.values[2][0]['display']+=68
        self.assertEqual(self.compare(),[])
    def test_partial_capture_cannot_have_extra_native_glyphs(self):
        self.values[5].append(dict(cycle=1100,address=0x9801,value=2))
        with self.assertRaises(ValueError):self.compare()
    def test_wrong_global_service_index_reported(self):
        self.values[2][0]['service']=0;self.values[6][0]['displays']=1
        self.assertEqual(self.compare()[0]['category'],'service')

if __name__=='__main__':unittest.main()
