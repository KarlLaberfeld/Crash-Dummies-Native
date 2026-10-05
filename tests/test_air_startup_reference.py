from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_startup_reference import analyze,POINTS


class StartupEvidenceTests(unittest.TestCase):
    def fixture(self):
        # Independent synthetic boundary fixture, including wrapped counters.
        times=(972,1004,1020,1052,13388,13424,13712,13728,13740)
        points=[dict(pc=pc,cycles=time,tick=65535,counter=255,ready=1,
            interruptFlags=243,interruptEnable=3) for pc,time in zip(POINTS,times)]
        points[-1].update(tick=0,counter=0)
        return dict(version=1,points=points)

    def test_pending_startup_has_owned_tail_and_counter_wrap(self):
        result=analyze(self.fixture())
        self.assertEqual(result['epoch'],1000)
        self.assertEqual(result['readyStored'],12740)
        self.assertEqual(result['initialTick'],65535)

    def test_partial_reordered_or_shifted_tail_cannot_be_accepted(self):
        for change in range(4):
            data=self.fixture()
            if change==0:data['points'].pop()
            elif change==1:data['points'][3],data['points'][5]=data['points'][5],data['points'][3]
            elif change==2:data['points'][1]['cycles']-=4
            else:data['points'][2]['cycles']-=4
            with self.subTest(change=change),self.assertRaises(ValueError):analyze(data)

    def test_missing_pending_service_or_wrong_publication_rejects(self):
        data=self.fixture()
        for index,field,value in ((2,'interruptFlags',241),(2,'interruptEnable',1),
            (8,'tick',65535),(8,'counter',255),(8,'ready',0),(5,'cycles',13420)):
            changed=deepcopy(data);changed['points'][index][field]=value
            with self.subTest(index=index,field=field),self.assertRaises(ValueError):analyze(changed)


if __name__=='__main__':unittest.main()
