from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_pause_access import analyze_accesses


class PauseAccessAuditTests(unittest.TestCase):
    def fixture(self):
        reference=dict(emulator='SameBoy',version='1.0.3',model='DMG-B',sourceRevision='fixture-revision',referenceObserver='execution-callback-v1')
        common=dict(reference=reference,romSha256='fixture-rom',controlMemorySha256='fixture-control',version=1)
        bus=[];branches=[];copies=[];points=[]
        for n,(phase,size,base) in enumerate((('copy0',20,0x9c00),('copy1',128,0x8f80),
                                           ('script',20,0x9c00),('copy2',20,0x9c00),('copy3',128,0x8f80))):
            start=n*50000
            script=phase=='script';prefix,stride=(1244,136) if script else (120,104)
            for i in range(size):
                time=start+prefix+i*stride
                bus.append(dict(phase=phase,cycles=time,kind='read',address=0xff41,data=0xc0,pc=0x2123 if script else 0x2363,
                                lcd=dict(line=0,scx=0,wx=7)))
                branches.append(dict(phase=phase,cycles=time+12,blocked=False,pc=0x2125 if script else 0x2365))
                bus.append(dict(phase=phase,cycles=time+(36 if script else 24 if n==0 else 32),kind='read' if n==0 else 'write',
                                address=base+i,data=i,pc=0x2129 if script else 0x2368 if n==0 else 0x2369,
                                lcd=dict(readBlocked=0)))
            if script:
                points.extend([dict(name='script',cycles=start),dict(name='wait',cycles=start+4396)])
            else:copies.append(dict(size=size,start=start,end=start+196+104*size,destinationWraps=0))
        lcd=dict(**common,pauses=[dict(bus=bus,branches=branches)])
        timing=dict(**common,pauses=[dict(copies=copies,points=points,interrupts=[])])
        return lcd,timing

    def test_complete_byte_owners(self):
        result=analyze_accesses(*self.fixture())
        self.assertEqual(result['sourceMismatches'],[])
        self.assertEqual(result['graphicsBytes'],316)
        self.assertEqual(result['retainedStatusBytes'],20)
        self.assertEqual(result['sourceIntervals'],953)
        self.assertFalse(result['nativePollingAccepted'])

    def test_changed_bus_time_reports_source_difference(self):
        lcd,timing=self.fixture();lcd['pauses'][0]['bus'][1]['cycles']+=4
        result=analyze_accesses(lcd,timing)
        self.assertEqual(result['sourceMismatches'][0]['owner'],'data bus access')
        self.assertEqual(result['sourceMismatches'][0]['measured'],28)

    def test_missing_or_changed_access_owner_rejects(self):
        for change in ('missing','address','pc','kind','status_pc'):
            lcd,timing=self.fixture();events=lcd['pauses'][0]['bus']
            if change=='missing':events.pop(1)
            elif change=='status_pc':events[0]['pc']=0
            elif change=='address':events[1]['address']+=1
            elif change=='kind':events[1]['kind']='write'
            else:events[1]['pc']=0
            with self.assertRaises(ValueError):analyze_accesses(lcd,timing)

    def test_control_and_observer_provenance_required(self):
        for field in ('romSha256','controlMemorySha256','referenceObserver'):
            lcd,timing=self.fixture();timing=deepcopy(timing)
            if field=='referenceObserver':timing['reference'][field]='read-callback-prototype'
            else:timing[field]='another-control'
            with self.assertRaises(ValueError):analyze_accesses(lcd,timing)

    def test_saved_bytes_survive_the_entire_pause(self):
        lcd,timing=self.fixture()
        next(e for e in lcd['pauses'][0]['bus'] if e['phase']=='copy2' and e['kind']=='write')['data']=99
        with self.assertRaisesRegex(ValueError,'retain the saved'):analyze_accesses(lcd,timing)

    def test_missing_pause_or_copy_boundaries_reject(self):
        for missing in ('pause','copy','script','wait'):
            lcd,timing=self.fixture();p=timing['pauses'][0]
            if missing=='pause':timing['pauses']=[]
            elif missing=='copy':p['copies'].pop()
            else:p['points']=[q for q in p['points'] if q['name']!=missing]
            with self.assertRaises(ValueError):analyze_accesses(lcd,timing)

    def test_held_status_sample_is_not_replaced_at_branch(self):
        lcd,timing=self.fixture();bus=lcd['pauses'][0]['bus'];branches=lcd['pauses'][0]['branches']
        first=deepcopy(bus[0]);first['data']=0xc3
        bus.insert(0,first)
        branches.insert(0,dict(phase='copy0',cycles=132,blocked=True,pc=0x2365))
        for event in bus[1:]:
            if event['phase']=='copy0':event['cycles']+=32
        for branch in branches[1:]:
            if branch['phase']=='copy0':branch['cycles']+=32
        timing['pauses'][0]['copies'][0]['end']+=32
        self.assertEqual(analyze_accesses(lcd,timing)['sourceMismatches'],[])
        bus.insert(1,dict(phase='copy0',cycles=140,kind='read',address=0x9c00,data=17,pc=0x2368,lcd=dict(readBlocked=0)))
        with self.assertRaises(ValueError):analyze_accesses(lcd,timing)


if __name__=='__main__':unittest.main()
