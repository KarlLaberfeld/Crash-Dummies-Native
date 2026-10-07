import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_result_prefix_reference import POINTS,analyze,compare_prefix


class ResultPrefixEvidence(unittest.TestCase):
    def setUp(self):
        costs=[208,6196,96,295104,144,68,426056,68,88];cycle=500;points=[]
        for index,name in enumerate(POINTS.values()):
            points.append(dict(name=name,cycles=cycle,result=3,lcd=dict(lcdc=128 if not index else 0)))
            if index<len(costs):cycle+=costs[index]
        self.data=dict(version=1,points=points,polls=[dict(cycles=616,ly=145)],
                       lcdOff=dict(cycles=664,lcd=dict(lcdc=0),interruptFlags=227))
        self.native=[dict(boundary=p['name'],cycle=p['cycles']-500) for p in points]+[dict(boundary='lcdDisabled',cycle=164)]
        self.polls=[dict(cycle=116,ly=145)]
        self.summary=[dict(end=cycle-500,lcdDisabled=164,pollReads=1,pendingRequests=3)]

    def compare(self):return compare_prefix(self.data,self.native,self.polls,self.summary,500)

    def test_complete_source_prefix(self):self.assertEqual(self.compare(),[])

    def test_corrupt_copy_work_rejects(self):
        self.data['points'][-3]['cycles']+=4
        with self.assertRaises(ValueError):analyze(self.data)

    def test_native_boundary_delay_is_reported(self):
        self.native[1]['cycle']+=4;self.assertEqual(self.compare()[0]['boundary'],'lcdOffReturned')

    def test_lcd_off_requires_equality(self):
        self.data['polls'][-1]['ly']=146
        with self.assertRaises(ValueError):analyze(self.data)

    def test_earlier_equal_poll_cannot_continue(self):
        self.data['polls'].append(dict(cycles=648,ly=145))
        with self.assertRaises(ValueError):analyze(self.data)

    def test_non_source_poll_stride_rejects(self):
        self.data['polls']=[dict(cycles=580,ly=144),dict(cycles=616,ly=145)]
        with self.assertRaises(ValueError):analyze(self.data)

    def test_perfect_celebration_rejects(self):
        self.data['points'][0]['result']=7
        with self.assertRaises(ValueError):self.compare()

    def test_missing_original_lcd_disable_rejects(self):
        self.data['lcdOff']=None
        with self.assertRaises(ValueError):self.compare()

    def test_copy_with_lcd_enabled_rejects(self):
        self.data['points'][4]['lcd']['lcdc']=128
        with self.assertRaises(ValueError):self.compare()

    def test_missing_native_poll_rejects(self):
        self.polls=[]
        with self.assertRaises(ValueError):self.compare()

    def test_native_readback_difference_is_reported(self):
        self.polls[0]['ly']=144;self.assertEqual(self.compare()[0]['poll'],0)

    def test_pending_requests_difference_is_reported(self):
        self.summary[0]['pendingRequests']=0;self.assertIn('summary',self.compare()[0])

    def test_missing_native_summary_rejects(self):
        self.summary=[]
        with self.assertRaises(ValueError):self.compare()

    def test_missing_native_boundary_rejects(self):
        self.native=self.native[:-1]
        with self.assertRaises(ValueError):self.compare()


if __name__=='__main__':unittest.main()
