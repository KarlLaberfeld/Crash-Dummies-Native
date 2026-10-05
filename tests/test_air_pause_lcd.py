from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_pause_lcd import analyze,VERSION


class PauseBusTests(unittest.TestCase):
    def fixture(self):
        bus=[];branches=[]
        for i,phase in enumerate(('copy0','copy1','script','copy2','copy3')):
            for j,mode in enumerate((2,3,0)):
                start=i*1000+j*32
                bus.append(dict(phase=phase,kind='read',address=0xff41,data=0xc0|mode,cycles=start,
                    lcd=dict(line=10,scx=240,wx=7)))
                branches.append(dict(phase=phase,cycles=start+12,blocked=bool(mode&2)))
        return dict(version=VERSION,pauses=[dict(bus=bus,branches=branches)])

    def test_status_sample_owns_later_branch(self):
        result=analyze(self.fixture())
        self.assertEqual([g['failedPolls'] for g in result['groups']],[2]*5)
        self.assertFalse(result['nativePollingAccepted'])

    def test_changed_decision_or_missing_branch_is_rejected(self):
        for kind in range(3):
            data=deepcopy(self.fixture());pause=data['pauses'][0]
            if kind==0:pause['branches'][0]['blocked']=False
            elif kind==1:pause['branches'].pop()
            else:pause['branches'][0]['cycles']=pause['bus'][0]['cycles']
            with self.assertRaises(ValueError):analyze(data)

    def test_blocked_read_is_not_a_successful_copy_claim(self):
        data=self.fixture();data['pauses'][0]['bus'].append(dict(phase='copy0',kind='read',address=0x9c00,
            data=255,cycles=96,lcd=dict(readBlocked=1)))
        result=analyze(data)
        self.assertEqual(result['groups'][0]['blockedVramReads'],1)
        self.assertFalse(result['nativePollingAccepted'])


if __name__=='__main__':unittest.main()
