from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from air_exit_timing import intervals,stop_work,VERSION,display_services,compare_service_rows
from air_timing import display_cycles,IRQ_PHASES,VBLANK_FIXED


class AirExitTests(unittest.TestCase):
    def data(self):
        points=[];interrupts=[];now=0;tick=65530;palette=228;enabled=1
        palettes=[228,228,224,208,192,128,64,0]
        def point(name):
            points.append(dict(name=name,cycles=now,tick=tick,ready=0,musicEnabled=enabled,
                               bgp=palette,obp0=palette&0xcf,obp1=palette&0xf3))
        point('audioStop');now+=stop_work();enabled=0;point('fadeEntry');now+=44
        for segment in range(8):
            point('palette');now+=76;palette=palettes[segment]
            for wait in range(4):
                point('wait')
                interrupts.append(dict(kind='vblank',start=now+100,end=now+160,returnAddress=0x261d))
                now+=216;tick=(tick+1)&65535;point('tail')
                now+=16 if wait<3 else 28 if segment<7 else 40
        point('end')
        return dict(version=VERSION,points=points,interrupts=interrupts,fadePalettes=palettes)

    def test_bounded_stop_and_complete_palette_wait_sequence(self):
        rows=intervals(self.data())
        self.assertEqual(len(rows),74)
        self.assertEqual(rows[0]['work'],12384)
        self.assertEqual(sum(r['phase']=='wait' for r in rows),32)
        self.assertTrue(all(r['activeSource']==120 and r['idle']==0 for r in rows if r['phase']=='wait'))
        self.assertEqual(rows[-1]['tickAfter'],26)

    def test_missing_final_wait_or_palette_write_is_rejected(self):
        data=self.data();data['points'].pop()
        with self.assertRaises(ValueError):intervals(data)
        data=self.data();data['points'][3]['obp0']^=4
        with self.assertRaises(ValueError):intervals(data)

    def test_source_work_error_cannot_be_absorbed_into_idle(self):
        data=self.data();data['points'][1]['cycles']+=4
        with self.assertRaises(ValueError):intervals(data)

    def test_resource_gate_and_music_remain_disabled(self):
        for name in ('ready','musicEnabled'):
            data=self.data();data['points'][4][name]=1
            with self.assertRaises(ValueError):intervals(data)

    def test_unknown_irq_ownership_and_counterless_wait_are_rejected(self):
        data=self.data();data['interrupts'][0]['returnAddress']=0x2618
        with self.assertRaises(ValueError):intervals(data)
        data=self.data();data['interrupts'].pop(0)
        with self.assertRaises(ValueError):intervals(data)

    def services(self):
        data=self.data();native=[]
        for index,q in enumerate(data['interrupts']):
            workload=dict(map_pending=0,ready=0,chunks=8,cursor=index%13,tick=5+index,fade_remaining=0,collected=0,quota=14)
            work={**VBLANK_FIXED,'display':sum(display_cycles(**workload).values()),'bookkeeping':240,'effects':64,'music':60}
            now=q['start']+work['prefix'];phases={}
            for name in IRQ_PHASES.values():phases[name]=now;now+=work[name]
            q.update(end=now,phases=phases,ready=0,tick=5+index,held=0,resetEnabled=1,resetLatched=0,
                     effectRequest=-1,musicEnabled=0,displayWorkload=workload,hudBar=[0]*6)
            native.append(dict(tick=q['tick'],ready=0,display=work['display'],effects=64,music=60,cursor=(index+1)%13,pending=-1,inputHeld=0,**{'bar'+str(i):0 for i in range(6)}))
        return data,native

    def test_service_components_prevent_halt_idle_from_hiding_cost_errors(self):
        data,native=self.services()
        self.assertEqual(len(display_services(data)),32)
        self.assertEqual(compare_service_rows(data,native),[])
        native[0]['music']=64
        self.assertEqual(compare_service_rows(data,native)[0]['fields'],{'music':[60,64]})
        data['interrupts'][0]['phases']['restore']+=4
        with self.assertRaises(ValueError):display_services(data)

    def test_pending_effect_and_short_service_coverage_are_rejected(self):
        data,native=self.services();data['interrupts'][0]['effectRequest']=0
        with self.assertRaises(ValueError):display_services(data)
        data,native=self.services()
        with self.assertRaises(ValueError):compare_service_rows(data,native[:-1])


if __name__=='__main__':unittest.main()
