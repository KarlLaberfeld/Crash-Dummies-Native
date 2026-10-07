"""Compare every complete Air IRQ vector in an independently bounded replay.

Original cycles/returns are read only after native execution. Pause/exit
recordings fill explicitly recorded intervals; truncating to a common prefix
is never accepted. This does not qualify other inputs or production scheduling.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

from air_reference import write_json
from reference_backend import require_capture_reference


def merge_interrupts(*recordings):
    combined = {}
    for recording in recordings:
        previous = -1
        for row in recording:
            if row['kind'] not in ('stat','vblank') or not previous < row['start'] < row['end']:
                raise ValueError('Invalid original IRQ order/return coverage')
            previous = row['end'] + 15
            if row['start'] in combined:
                old = combined[row['start']]
                if any(old[key] != row[key] for key in ('kind','end','returnAddress')):
                    raise ValueError('Overlapping original IRQ recordings disagree')
            else:combined[row['start']] = row
    result = sorted(combined.values(),key=lambda row:row['start'])
    if any(a['end']+16 > b['start']-20 for a,b in zip(result,result[1:])):
        raise ValueError('Original IRQ services overlap')
    return result


def interval_targets(interrupts,epoch,end):
    if end <= 52 or not interrupts:raise ValueError('Incomplete original replay interval')
    first = interrupts[0]
    if first['kind'] != 'vblank' or first['returnAddress'] != 0x03c9 or first['start']-epoch != 52:
        raise ValueError('Unqualified pending-startup epoch')
    targets = [];excluded = 0
    for row in interrupts:
        start = row['start']-epoch;returned = row['end']+16-epoch
        if start >= end:
            if start-20 < end:raise ValueError('Terminal IRQ entry crosses the comparison boundary')
            excluded += 1;continue
        if start < 0 or returned > end:raise ValueError('Incomplete IRQ return inside the comparison interval')
        targets.append(dict(kind=row['kind'],vectorCycle=start))
    return targets,excluded


def compare_vectors(expected,rows,end):
    if not expected or not rows:raise ValueError('Empty IRQ evidence')
    if len(rows) != len(expected):raise ValueError('Incomplete full IRQ coverage; common-prefix comparisons are forbidden')
    previous = -1;differences = []
    for index,(target,row) in enumerate(zip(expected,rows)):
        if row['kind'] not in ('stat','vblank') or not previous < row['vectorCycle'] < end:
            raise ValueError('Invalid native IRQ ordering or terminal coverage')
        previous = row['vectorCycle']
        if row['owner'] not in (1,2,3):raise ValueError('Unqualified aggregate/protected IRQ owner')
        if row['phase'] in (2,3,4,5,6) and row['owner'] != 1:
            raise ValueError('Scene/placement/result IRQ lacks a source completion owner')
        delta = {key:[value,row[key]] for key,value in target.items() if row[key] != value}
        if delta:differences.append(dict(index=index,fields=delta))
    return differences


def compare(args):
    manifest = json.loads((args.capture/'capture-summary.json').read_text())
    timing = json.loads((args.timing/'timing.json').read_text())
    if timing.get('version') != 9 or manifest.get('controlDifferences') or not timing['updates']:
        raise ValueError('Requires complete control-verified source timing')
    def provenance(data):
        require_capture_reference(manifest,data)
        if any(data.get(key) != manifest.get(key) for key in ('romSha256','controlMemorySha256')):
            raise ValueError('Mixed original IRQ controls')
    provenance(timing)
    reference = timing['reference']
    if reference.get('emulator') != 'SameBoy' or reference.get('model') != 'DMG-B' or reference.get('referenceObserver') != 'execution-callback-v1':
        raise ValueError('Requires the independently qualified vector convention')
    epoch = timing['interrupts'][0]['start']-52
    with args.boundary_csv.open(encoding='utf-8-sig',newline='') as stream:boundaries = list(csv.DictReader(stream))
    if len(boundaries) != 1:raise ValueError('Missing native completion boundary')
    boundary = boundaries[0]
    if int(boundary['updates']) != len(timing['updates']) or not int(boundary['result']):
        raise ValueError('Incomplete native game completion')
    sources = [timing['interrupts']]
    if args.pause:
        from air_pause_timing import analyze
        pause = json.loads((args.pause/'pause.json').read_text());provenance(pause)
        if analyze(pause)['sourceMismatches'] or len(pause['pauses']) != 1:
            raise ValueError('Incomplete original pause coverage')
        sources.append(pause['pauses'][0]['interrupts'])
    if args.exit:
        from air_exit_timing import intervals
        outro = json.loads((args.exit/'exit.json').read_text());provenance(outro)
        intervals(outro)  # Require all 32 independently observed fade waits.
        sources.append(outro['interrupts'])
        end = outro['points'][-1]['cycles']-epoch;name = 'resultSetup'
    else:
        # The completed native result test consumes 16+4+8, through 0400.
        end = timing['updates'][-1]['done']['cycles']-epoch+28;name = 'gameExitTest'
    if boundary['boundary'] != name or int(boundary['cycle']) != end:
        raise ValueError('Native absolute terminal boundary differs from original')
    expected,excluded = interval_targets(merge_interrupts(*sources),epoch,end)
    with args.native_csv.open(encoding='utf-8-sig',newline='') as stream:
        native = [{key:value if key == 'kind' else int(value) for key,value in row.items()} for row in csv.DictReader(stream)]
    differences = compare_vectors(expected,native,end)
    result = dict(comparedInterrupts=len(expected),statInterrupts=sum(row['kind']=='stat' for row in expected),
        vblankInterrupts=sum(row['kind']=='vblank' for row in expected),boundary=name,boundaryCycle=end,
        excludedOriginalInterruptsAfterBoundary=excluded,owners=dict(Counter(str(row['owner']) for row in native)),
        differences=len(differences),firstDifference=differences[0] if differences else None,
        productionSchedulerAccepted=False,
        evidenceLimit='All complete IRQ vectors in this control, from the source-owned pending startup through the explicit terminal boundary. No common-prefix truncation, captured runtime clocks or fitted return-address corrections. Other inputs, interrupted entity/resource/row-publication paths, first LCD frame, protected crossings, result setup, hardware and Windows scheduling remain unqualified.')
    write_json(args.native_csv.with_suffix('.all-comparison.json'),result);print(json.dumps(result,indent=2))
    if differences:raise ValueError('Native absolute IRQ vectors differ from original')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('native_csv',type=Path)
    for name in ('capture','timing','boundary-csv'):parser.add_argument('--'+name,type=Path,required=True)
    for name in ('pause','exit'):parser.add_argument('--'+name,type=Path)
    compare(parser.parse_args())
