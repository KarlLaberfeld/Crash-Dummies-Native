"""Synthetic third-attempt prefix and timer qualification guards."""
import copy,sys,unittest
from uuid import uuid4
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_third_gameplay_reference import first_update,native_prefix,timer_rollovers
from air_next_retry_reference import preserved_prefix
from test_air_next_retry_reference import controls


class ThirdControlIntegrity(unittest.TestCase):
    def setUp(self):
        self.parent,self.child,self.events,self.extended=controls();self.extended=self.events+[['tick',1800,True]]
    def check(self):preserved_prefix(self.parent,self.child,self.events,self.extended,[['tick',1800,True]])
    def test_longer_released_interval(self):self.check()
    def test_changed_prefix_rejects(self):
        self.extended[0]=['tick',4199,True]
        with self.assertRaises(ValueError):self.check()
    def test_fresh_input_in_extension_rejects(self):
        self.extended.insert(-1,['press','a'])
        with self.assertRaises(ValueError):self.check()
    def test_wrong_parent_ram_rejects(self):
        self.child['parentPrefixHashes'][1]='wrong'
        with self.assertRaises(ValueError):self.check()


class FirstUpdateIntegrity(unittest.TestCase):
    def setUp(self):
        self.first=dict(nextRetry=True,updates=1,points=[dict(index=i) for i in range(10)],interrupts=[dict(index=i) for i in range(2)],precedingDisplays=2348)
        self.long=copy.deepcopy(self.first);self.long['updates']=1000;self.long['points']+=[dict(index=10)];self.long['interrupts']+=[dict(index=2)]
    def test_retained_first_update(self):first_update(self.first,self.long)
    def test_changed_first_timer_rejects(self):
        self.long['points'][3]['secondTicks']=0
        with self.assertRaises(ValueError):first_update(self.first,self.long)
    def test_changed_first_irq_rejects(self):
        self.long['interrupts'][1]['cycle']=100
        with self.assertRaises(ValueError):first_update(self.first,self.long)
    def test_wrong_service_origin_rejects(self):
        self.long['precedingDisplays']=0
        with self.assertRaises(ValueError):first_update(self.first,self.long)
    def test_wrong_retry_scope_rejects(self):
        self.long['nextRetry']=False
        with self.assertRaises(ValueError):first_update(self.first,self.long)


def timer_fixture():
    points=[];phase=58;seconds=40
    for update in range(3):
        for i in range(10):
            if i==2:
                phase+=1
                if phase==60:phase=0;seconds-=1
            points.append(dict(secondTicks=phase,seconds=seconds))
    return dict(updates=3,points=points)


class TimerIntegrity(unittest.TestCase):
    def setUp(self):self.data=timer_fixture()
    def test_rollover_preserves_phase(self):
        self.assertEqual(timer_rollovers(self.data),dict(inheritedSecondTicks=58,timerIncrements=3,timerRollovers=1,firstRolloverUpdate=1))
    def test_reset_phase_rejects(self):
        for p in self.data['points'][2:10]:p['secondTicks']=0
        with self.assertRaises(ValueError):timer_rollovers(self.data)
    def test_rollover_without_second_decrement_rejects(self):
        for p in self.data['points'][12:20]:p['seconds']=40
        with self.assertRaises(ValueError):timer_rollovers(self.data)
    def test_timer_in_display_rejects(self):
        self.data['points'][9]['secondTicks']=0
        with self.assertRaises(ValueError):timer_rollovers(self.data)
    def test_timer_before_actor_rejects(self):
        self.data['points'][1]['secondTicks']=59
        with self.assertRaises(ValueError):timer_rollovers(self.data)
    def test_no_rollover_is_not_coverage(self):
        self.data['updates']=1;self.data['points']=self.data['points'][:10]
        with self.assertRaises(ValueError):timer_rollovers(self.data)
    def test_initial_zero_is_not_inheritance_coverage(self):
        self.data['points'][0]['secondTicks']=0
        with self.assertRaises(ValueError):timer_rollovers(self.data)


class NativePrefixIntegrity(unittest.TestCase):
    def setUp(self):
        # Inherit workspace permissions; Windows sandbox temp ACLs can deny
        # files in tempfile's mode-0700 directories.
        parent=(Path(__file__).resolve().parents[1]/'build'/'test-temp').resolve();parent.mkdir(parents=True,exist_ok=True)
        self.root=(parent/str(uuid4())).resolve();assert self.root.parent==parent;self.root.mkdir()
        self.first=self.root/'first.csv';self.long=self.root/'long.csv'
        self.suffixes=['.next-gameplay.csv','.next-gameplay.entities.csv','.next-gameplay.services.csv','.next-gameplay.interrupts.csv','.next-gameplay.sprites.csv','.next-entry.summary.csv','.next-text.csv']
        for suffix in self.suffixes:
            Path(str(self.first)+suffix).write_bytes(b'header\r\nfirst\r\n')
            Path(str(self.long)+suffix).write_bytes(b'header\nfirst\n'+(b'next\n' if suffix.startswith('.next-gameplay') else b''))
    def tearDown(self):
        for base in (self.first,self.long):
            for suffix in self.suffixes:Path(str(base)+suffix).unlink(missing_ok=True)
        self.root.rmdir()
    def test_normalized_prefix(self):self.assertEqual(len(native_prefix(self.first,self.long)),7)
    def test_different_native_entry_rejects(self):
        Path(str(self.long)+'.next-entry.summary.csv').write_text('different')
        with self.assertRaises(ValueError):native_prefix(self.first,self.long)
    def test_different_first_native_update_rejects(self):
        Path(str(self.long)+'.next-gameplay.csv').write_text('different')
        with self.assertRaises(ValueError):native_prefix(self.first,self.long)
    def test_missing_accepted_native_scope_rejects(self):
        Path(str(self.first)+'.next-gameplay.sprites.csv').unlink()
        with self.assertRaises(ValueError):native_prefix(self.first,self.long)


if __name__=='__main__':unittest.main()
