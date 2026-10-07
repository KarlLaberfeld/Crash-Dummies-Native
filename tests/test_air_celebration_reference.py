import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_celebration_reference import analyze,compare_component


class CelebrationEvidence(unittest.TestCase):
    def setUp(self):
        before=dict(random=257,emitters=[[30+i,143,251,0,2] for i in range(4)])
        after=copy.deepcopy(before)
        for e in after['emitters']:e[4]=1
        self.data=dict(version=1,terminal='nextInstruction',services=[dict(start=100,end=2184,tick=65535,before=before,after=after,prepared=[0]*160)])
        self.native=[dict(service=0,tick=65535,work=2084,random=257,spriteCount=0)]
        for i,e in enumerate(after['emitters']):
            self.native[0].update({f'emitter{i}{key}':v for key,v in zip(('x','y','velocity','radius','delay'),e)})
        self.native[0].update({f'prepared{i}':0 for i in range(160)})
    def compare(self):return compare_component(self.data,self.native)
    def test_complete_component(self):self.assertEqual(self.compare(),[])
    def test_qualified_incoming_scope(self):
        self.data['terminal']='incomingFade';self.assertEqual(self.compare(),[])
    def test_native_work_difference(self):
        self.native[0]['work']+=4;self.assertIn('work',self.compare()[0]['fields'])
    def test_native_random_difference(self):
        self.native[0]['random']+=256;self.assertIn('random',self.compare()[0]['fields'])
    def test_native_emitter_difference(self):
        self.native[0]['emitter3delay']=0;self.assertIn('emitter3delay',self.compare()[0]['fields'])
    def test_native_prepared_byte_difference(self):
        self.native[0]['prepared159']=128;self.assertIn('prepared159',self.compare()[0]['fields'])
    def test_missing_native_field(self):
        del self.native[0]['prepared159']
        with self.assertRaises(ValueError):self.compare()
    def test_truncated_native_scope(self):
        with self.assertRaises(ValueError):compare_component(self.data,[])
    def test_missing_terminal(self):
        self.data['terminal']='partial'
        with self.assertRaises(ValueError):analyze(self.data)
    def test_missing_prepared_tail(self):
        self.data['services'][0]['prepared'].pop()
        with self.assertRaises(ValueError):analyze(self.data)
    def test_dirty_prepared_tail(self):
        self.data['services'][0]['prepared'][0]=9
        with self.assertRaises(ValueError):analyze(self.data)
    def test_incomplete_emitter_group(self):
        self.data['services'][0]['prepared'][3]=128
        with self.assertRaises(ValueError):analyze(self.data)
    def test_changed_random_low_byte(self):
        self.data['services'][0]['after']['random']=258
        with self.assertRaises(ValueError):analyze(self.data)
    def second(self):
        row=copy.deepcopy(self.data['services'][0]);row.update(start=70224,end=72308,tick=0)
        row['before']=copy.deepcopy(row['after'])
        self.data['services'].append(row)
    def test_counter_wrap(self):
        self.second();self.assertEqual(len(analyze(self.data)),2)
    def test_skipped_counter(self):
        self.second();self.data['services'][1]['tick']=1
        with self.assertRaises(ValueError):analyze(self.data)
    def test_unowned_state_gap(self):
        self.second();self.data['services'][1]['before']['emitters'][0][0]+=1
        with self.assertRaises(ValueError):analyze(self.data)
    def test_overlapping_component(self):
        self.second();self.data['services'][1]['start']=100
        with self.assertRaises(ValueError):analyze(self.data)


if __name__=='__main__':unittest.main()
