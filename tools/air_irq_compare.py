"""Compare source-owned placement interrupt boundaries with local originals.

Reads observations only after native execution. No captured cycles, return
addresses or outcomes drive the native clock. Other phases remain unqualified.
"""
import argparse
from bisect import bisect_left
import csv
import json
from pathlib import Path

from air_reference import write_json
from reference_backend import require_capture_reference


def placement_targets(timing):
    interrupts=timing['interrupts'];updates=timing['updates']
    if not interrupts or not updates:raise ValueError('Incomplete original interrupt coverage')
    first=interrupts[0]
    if first['kind']!='vblank' or first['returnAddress']!=0x03c9:
        raise ValueError('Unowned pending-startup epoch')
    # The already identified LCD access/return, EI + following load, and
    # interrupt entry own vector +52. This is not a fitted later IRQ shift.
    epoch=first['start']-52
    starts=[q['start']-20 for q in interrupts]
    if any(starts[i]>=starts[i+1] for i in range(len(starts)-1)):
        raise ValueError('Unordered original interrupts')
    result=[]
    for index,update in enumerate(updates):
        begin=update['placements']['cycles'];end=update['done']['cycles']
        if begin>=end:raise ValueError('Invalid original placement interval')
        for irq in interrupts[bisect_left(starts,begin):bisect_left(starts,end)]:
            if irq['end']+16>end:raise ValueError('Incomplete placement interrupt return')
            result.append(dict(update=index,kind=irq['kind'],vectorCycle=irq['start']-epoch))
    return result


def compare_placements(expected,rows):
    previous=-1
    for row in rows:
        if row['kind'] not in ('stat','vblank') or row['vectorCycle']<=previous or row['owner'] not in range(5):
            raise ValueError('Invalid native interrupt ordering/owner')
        previous=row['vectorCycle']
    native=[r for r in rows if r['phase']==5]
    if len(native)!=len(expected):raise ValueError('Incomplete native placement interrupt coverage')
    differences=[]
    for index,(target,row) in enumerate(zip(expected,native)):
        if row['owner']!=1:raise ValueError('Placement interrupt lacks a source completion owner')
        delta={k:[value,row[k]] for k,value in target.items() if value!=row[k]}
        if delta:differences.append(dict(index=index,fields=delta))
    return differences


def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    timing=json.loads((args.timing/'timing.json').read_text())
    require_capture_reference(manifest,timing)
    if manifest['controlDifferences'] or any(manifest[k]!=timing[k] for k in ('romSha256','controlMemorySha256')):
        raise ValueError('Mixed or unverified original interrupt control')
    reference=manifest.get('reference',manifest)
    if reference.get('emulator')!='SameBoy' or reference.get('model')!='DMG-B' or reference.get('referenceObserver')!='execution-callback-v1':
        raise ValueError('Requires the qualified independent pending-startup convention')
    with args.native_csv.open(encoding='utf-8-sig',newline='') as stream:
        native=[{k:v if k=='kind' else int(v) for k,v in row.items()} for row in csv.DictReader(stream)]
    expected=placement_targets(timing);differences=compare_placements(expected,native)
    result=dict(comparedPlacementInterrupts=len(expected),placementEdgesCompared=bool(expected),statInterrupts=sum(q['kind']=='stat' for q in expected),
        vblankInterrupts=sum(q['kind']=='vblank' for q in expected),differences=len(differences),
        firstDifference=differences[0] if differences else None,productionSchedulerAccepted=False,
        evidenceLimit='Identified eight-record Air placement scan and allocation completion boundaries, on the pinned independent reference. Other gameplay phases, masked/pending IRQ paths, initial LCD access, result setup, hardware and Windows scheduling remain unqualified.')
    write_json(args.native_csv.with_suffix('.comparison.json'),result);print(json.dumps(result,indent=2))
    if differences:raise ValueError('Native source-owned placement interrupt edges differ')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('native_csv',type=Path);parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--timing',type=Path,required=True)
    compare(parser.parse_args())
