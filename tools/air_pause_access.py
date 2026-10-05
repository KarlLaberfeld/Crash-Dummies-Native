"""Audit identified pause bus owners against independent original recordings.

Report only: no emulator import or native scheduling input. Observed STAT bytes
choose which source interval to check, never a native readiness allowance.
"""
import argparse
import json
from pathlib import Path

from air_pause_lcd import analyze,VERSION as LCD_VERSION
from air_pause_timing import VERSION as TIMING_VERSION
from air_reference import write_json
from air_timing import elapsed_work
from reference_backend import require_matching_backend


def analyze_accesses(lcd,timing):
    analyze(lcd)  # Status bytes must already own their subsequent branches.
    if lcd.get('version')!=LCD_VERSION or timing.get('version')!=TIMING_VERSION:
        raise ValueError('Requires complete current pause bus/work recordings')
    require_matching_backend(lcd.get('reference',{}),timing.get('reference',{}))
    if lcd['reference'].get('emulator')!='SameBoy' or lcd['reference'].get('referenceObserver')!='execution-callback-v1':
        raise ValueError('Requires the independent instruction-execution observer')
    for field in ('romSha256','controlMemorySha256'):
        if not lcd.get(field) or lcd[field]!=timing.get(field):
            raise ValueError('Pause bus and source intervals belong to different controls')
    if len(lcd['pauses'])!=len(timing.get('pauses',[])):
        raise ValueError('Missing pause work intervals')
    differences=[];intervals=0;bytes_checked=0;restored=0
    def check(pi,phase,owner,start,end,expected,interrupts):
        nonlocal intervals
        actual=elapsed_work(start,end,interrupts);intervals+=1
        if actual!=expected:
            differences.append(dict(pause=pi,phase=phase,owner=owner,measured=actual,source=expected))
    for pi,(bus_pause,work_pause) in enumerate(zip(lcd['pauses'],timing['pauses'])):
        copies=work_pause.get('copies',[]);points=work_pause.get('points',[])
        if len(copies)!=4 or [c['size'] for c in copies]!=[20,128,20,128]:
            raise ValueError('Incomplete identified copies')
        interrupts=work_pause['interrupts'];saved=[];restore=[]
        for phase,size,index,base in (('copy0',20,0,0x9c00),('copy1',128,1,0x8f80),
                                     ('script',20,None,0x9c00),('copy2',20,2,0x9c00),('copy3',128,3,0x8f80)):
            events=[e for e in bus_pause['bus'] if e['phase']==phase]
            polls=[e for e in events if e['kind']=='read' and e['address']==0xff41]
            branches=[e for e in bus_pause['branches'] if e['phase']==phase]
            if any(e.get('pc')!=(0x2123 if phase=='script' else 0x2363) for e in polls):
                raise ValueError('Unexpected status access owner')
            accesses=[e for e in events if 0x8000<=e['address']<0xa000]
            wanted_kind='read' if phase=='copy0' else 'write'
            expected_pc=0x2368 if phase=='copy0' else 0x2129 if phase=='script' else 0x2369
            if len(accesses)!=size or any(e['kind']!=wanted_kind or e['address']!=base+i or e['pc']!=expected_pc
                                         for i,e in enumerate(accesses)):
                raise ValueError('Incomplete, unordered or unexpected pause data accesses')
            if not polls or any(a['cycles']>=b['cycles'] for a,b in zip(events,events[1:])):
                raise ValueError('Unordered pause bus observations')
            if phase=='script':
                starts=[p['cycles'] for p in points if p['name']=='script']
                ends=[p['cycles'] for p in points if p['name']=='wait']
                if len(starts)!=1 or not ends:raise ValueError('Missing identified text boundaries')
                start,end=starts[0],ends[0];prefix,tail,stride,access_delta=1244,568,136,36
            else:
                copy=copies[index];start,end=copy['start'],copy['end']
                if copy.get('destinationWraps')!=0:raise ValueError('Unexpected identified-copy destination wrap')
                prefix,tail,stride,access_delta=120,180,104,24 if phase=='copy0' else 32
            if any(not start<=e['cycles']<end for e in events):
                raise ValueError('Access escapes its identified phase')
            check(pi,phase,'first status sample',start,polls[0]['cycles'],prefix,interrupts)
            ai=0
            for j,(poll,branch) in enumerate(zip(polls,branches)):
                check(pi,phase,'retained status branch',poll['cycles'],branch['cycles'],12,interrupts)
                blocked=bool(poll['data']&2)
                if blocked:
                    if j+1==len(polls):raise ValueError('Copy/text ends in a blocked poll')
                    if ai<size and accesses[ai]['cycles']<polls[j+1]['cycles']:
                        raise ValueError('Data access occurs after a blocked poll')
                    expected=32
                else:
                    if ai>=size:raise ValueError('Status success has no owned data access')
                    access=accesses[ai]
                    if j+1<len(polls) and access['cycles']>=polls[j+1]['cycles']:
                        raise ValueError('Data access is not owned by its successful poll')
                    check(pi,phase,'data bus access',poll['cycles'],access['cycles'],access_delta,interrupts)
                    ai+=1;bytes_checked+=1;expected=stride
                if j+1<len(polls):
                    check(pi,phase,'next status sample',poll['cycles'],polls[j+1]['cycles'],expected,interrupts)
            if ai!=size:raise ValueError('Missing byte owners')
            check(pi,phase,'final return',polls[-1]['cycles'],end,tail,interrupts)
            if phase=='copy0':saved=[e['data'] for e in accesses]
            elif phase=='copy2':restore=[e['data'] for e in accesses]
        if saved!=restore:raise ValueError('Status restoration attempts do not retain the saved bytes')
        restored+=len(saved)
    return dict(pauses=len(lcd['pauses']),sourceIntervals=intervals,graphicsBytes=bytes_checked,
                retainedStatusBytes=restored,sourceMismatches=differences,nativePollingAccepted=False,
                evidenceLimit='Read-only source/access audit. Attempted writes are not certified stores. Native LCD phase, pixels, PCM, pause integration and production scheduler remain unaccepted.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lcd',type=Path,required=True);parser.add_argument('--timing',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    result=analyze_accesses(json.loads(args.lcd.read_text()),json.loads(args.timing.read_text()))
    args.out.mkdir(parents=True,exist_ok=True)
    write_json(args.out/'summary.json',result);print(json.dumps(result,indent=2))
    if result['sourceMismatches']:raise ValueError('Pause access ownership differs from identified source work')
