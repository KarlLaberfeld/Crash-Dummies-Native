from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from audio_work import command_cycles, envelope_cycles, music_tail_cycles, note_cycles
from audio_timing import validate_services, VERSION


class MusicWorkTests(unittest.TestCase):
    def service(self):
        voices=[]
        for i in range(6):
            voices.append(dict(index=i, start=dict(cycles=10+i*10, state=dict(active=0,remaining=0)), end=20+i*10, fetch=[]))
        return dict(version=VERSION,services=[dict(enabled=255,start=0,end=100,voices=voices,finalization=70,tail=80)])

    def test_complete_voice_chain_and_disabled_early_return(self):
        validate_services(self.service())
        validate_services(dict(version=VERSION,services=[dict(enabled=0,start=0,end=60,voices=[])]))
        with self.assertRaises(ValueError):validate_services(dict(version=VERSION,services=[]))

    def test_missing_reversed_overlapping_or_unordered_boundaries(self):
        data=self.service()
        variants=[]
        v=deepcopy(data);v['services'][0]['voices'].pop();variants.append(v)
        v=deepcopy(data);v['services'][0]['voices'][0]['end']=21;variants.append(v)
        v=deepcopy(data);v['services'][0]['tail']=60;variants.append(v)
        v=deepcopy(data);v['services'].append(deepcopy(v['services'][0]));variants.append(v)
        v=deepcopy(data);v['services'][0]['enabled']=0;variants.append(v)
        for invalid in variants:
            with self.assertRaises(ValueError):validate_services(invalid)

    def test_active_voice_cannot_hide_missing_fetch_or_continuing_phases(self):
        for remaining in (1,2):
            data=self.service();data['services'][0]['voices'][0]['start']['state']=dict(active=255,remaining=remaining)
            with self.assertRaises(ValueError):validate_services(data)

    def test_phase_order_and_wave_bypass(self):
        data=self.service();v=data['services'][0]['voices'][2]
        v['envelope']=dict(cycles=31)
        with self.assertRaises(ValueError):validate_services(data)
        data=self.service();v=data['services'][0]['voices'][0]
        v['start']['state']=dict(active=255,remaining=2)
        v.update(envelope=dict(cycles=13),output=dict(cycles=12),modulation=dict(cycles=15))
        with self.assertRaises(ValueError):validate_services(data)

    def test_command_validation_and_loop_branches(self):
        self.assertEqual(command_cycles('loop_end',[],1),124)
        self.assertEqual(command_cycles('loop_end',[],2),172)
        self.assertEqual(command_cycles('noise_short',[]),136)
        self.assertEqual(command_cycles('registers',[0,1,2,3,4]),324)
        for operation,args in (('registers',[]),('registers',[0,1]),('stereo_motion',[]),('unknown',[])):
            self.assertEqual(command_cycles(operation,args),-1)

    def test_stereo_tail_source_only_branches(self):
        self.assertEqual([music_tail_cycles(*v) for v in ((0,1,0),(1,2,0),(1,1,0),(1,1,255))],[40,72,256,248])

    def test_square_and_noise_attack_have_different_fallthrough(self):
        state=dict(stage=0,envelopeCounter=0,volume=14,decay=0,sustain=0)
        self.assertEqual(envelope_cycles(0,state),440)
        self.assertEqual(envelope_cycles(3,state),256)

    def test_note_pointer_carry_does_not_depend_on_duration_value(self):
        state=dict(noTranspose=0,portamento=0,fixed=0,vibratoDelay=0,envelopeMode=0,pitchDelay=0)
        self.assertEqual(note_cycles(0,state,[24,3],255)-note_cycles(0,state,[24,3],100),8)
        state['fixed']=3
        self.assertEqual(note_cycles(0,state,[24,3],254),note_cycles(0,state,[24,3],100))


if __name__=='__main__':unittest.main()
