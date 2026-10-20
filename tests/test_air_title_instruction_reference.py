"""Masked LCD/register-prefix guards without original data."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_title_instruction_reference import analyze,STORES
class InstructionPrefix(unittest.TestCase):
    def setUp(self):
        base=dict(tick=9,countdown=54,inputHeld=0,inputPressed=0,display=0,stat=2,lcdc=0xfb,scrollY=88,lyc=103)
        points=[dict(base,name='begin',cycles=100),dict(base,name='lcdOffReturned',cycles=324),dict(base,name='end',cycles=480)]
        points[1]['lcdc']=0x7b;points[2].update(display=5,stat=5,lcdc=0x51,scrollY=0,lyc=95)
        self.parent=dict(points=[dict(points[0])]);values=[0x7b,5,5,0,0,0,95,0x44,0x51]
        self.data=dict(points=points,polls=[dict(cycle=200,ly=100),dict(cycle=232,ly=145)],writes=[dict(cycle=268 if i==0 else 320+16*i,address=a,value=v) for i,(a,v) in enumerate(zip(STORES.values(),values))],vectors=[],mapsUnchanged=True)
    def reject(self):
        with self.assertRaises(ValueError):analyze(self.data,self.parent)
    def test_complete(self):analyze(self.data,self.parent)
    def test_detached_parent(self):self.parent['points'][0]['cycles']=99;self.reject()
    def test_masked_services(self):self.data['vectors']=[dict(pc=0x40,cycle=210)];self.reject()
    def test_no_map_mutation(self):self.data['mapsUnchanged']=False;self.reject()
    def test_frozen_tick(self):self.data['points'][-1]['tick']=10;self.reject()
    def test_frozen_input(self):self.data['points'][-1]['inputPressed']=8;self.reject()
    def test_correct_registers(self):self.data['points'][-1]['lyc']=103;self.reject()
    def test_first_equality_only(self):self.data['polls'][0]['ly']=145;self.reject()
    def test_final_equality_required(self):self.data['polls'][-1]['ly']=144;self.reject()
    def test_every_read_retained(self):self.data['polls'][-1]['cycle']+=4;self.reject()
    def test_all_register_stores(self):self.data['writes'].pop();self.reject()
    def test_disable_value(self):self.data['writes'][0]['value']=0xfb;self.reject()
    def test_access_inside_scope(self):self.data['writes'][-1]['cycle']=480;self.reject()
if __name__=='__main__':unittest.main()
