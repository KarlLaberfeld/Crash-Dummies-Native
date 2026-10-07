import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_instruction_picture_reference import NAMES,analyze,compare_picture

def fixture():
    points=[]
    for name,time in zip(NAMES,(1000,15060,15148,15168,15264,15308,200000,230000,230024)):
        points.append(dict(name=name,cycles=time,tick=6 if time>=200000 else 5,countdown=99 if time>=200000 else 100,
            stage=2,display=10,result=0,musicEnabled=int(name!='begin'),inputHeld=0,inputPressed=0))
    r=dict(kind='vblank',start=100000,tick=5,countdown=100,held=0,pressed=0,resetEnabled=1,resetLatched=0,
        effectRequest=-1,musicEnabled=1,returnAddress=0x2361,phases={});time=r['start']
    for name,work in zip(('dma','joypad','display','bookkeeping','effects','audioBank','music','restore'),(180,704,280,272,240,64,68,60)):
        time+=work;r['phases'][name]=time
    r['end']=time+120
    writes=[dict(kind='tile',cycles=20000+144*i,address=0x8340+i,value=i%256) for i in range(1024)]
    writes += [dict(kind='map',cycles=210000+144*i,address=0x9800+(3+i//10)*32+5+i%10,value=37) for i in range(90)]
    polls=[dict(cycles=w['cycles']-28,mode=0) for w in writes]
    data=dict(version=1,precedingDisplays=788,points=points,interrupts=[r],polls=polls,writes=writes)
    native=[dict(boundary=p['name'],cycle=p['cycles']-1000,**{k:p[k] for k in ('tick','countdown','musicEnabled','inputHeld','inputPressed')}) for p in points]
    services=[dict(service=788,cycle=99000,tick=5,countdown=99,display=272,effects=64,music=60,inputHeld=0,inputPressed=0)]
    native_polls=[dict(cycle=p['cycles']-1000,mode=p['mode']) for p in polls]
    native_writes=[dict(cycle=w['cycles']-1000,**{k:w[k] for k in ('kind','address','value')}) for w in writes]
    return data,native,services,[dict(kind='vblank',vectorCycle=99000,owner=1)],native_polls,native_writes,[dict(end=229024,tick=6,countdown=99,displays=789)]

class PictureIntegrity(unittest.TestCase):
    def setUp(self):self.values=list(fixture());self.data=self.values[0]
    def compare(self):return compare_picture(*self.values,1000)
    def test_complete_source_shaped_storage_fixture(self):self.assertEqual(self.compare(),[])
    def test_missing_native_tile_rejects(self):
        self.values[5].pop(12)
        with self.assertRaises(ValueError):self.compare()
    def test_missing_source_tile_rejects(self):
        self.data['writes'].pop(12)
        with self.assertRaises(ValueError):self.compare()
    def test_wrong_map_pitch_rejects(self):
        self.data['writes'][1034]['address']+=1
        with self.assertRaises(ValueError):self.compare()
    def test_interrupted_reset_rejects(self):
        self.data['interrupts'][0]['start']=14000
        with self.assertRaises(ValueError):self.compare()
    def test_unowned_result_rejects(self):
        self.data['points'][2]['result']=7
        with self.assertRaises(ValueError):self.compare()
    def test_shifted_dispatch_rejects(self):
        self.data['points'][4]['cycles']+=4
        with self.assertRaises(ValueError):self.compare()
    def test_missing_terminal_rejects(self):
        self.data['points'].pop()
        with self.assertRaises(ValueError):self.compare()
    def test_native_byte_difference_reported(self):
        self.values[5][100]['value']+=1;self.assertEqual(self.compare()[0]['category'],'writes')
    def test_native_poll_difference_reported(self):
        self.values[4][100]['mode']=3;self.assertEqual(self.compare()[0]['category'],'polls')
    def test_unqualified_irq_rejects(self):
        self.values[3][0]['owner']=0
        with self.assertRaises(ValueError):self.compare()
    def test_wrong_service_index_reported(self):
        self.values[2][0]['service']=0;self.values[6][0]['displays']=1;self.assertEqual(self.compare()[0]['category'],'service')

if __name__=='__main__':unittest.main()
