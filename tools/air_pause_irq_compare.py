"""Check absolute pause counter-wait interrupt edges against local originals.

Only comparison reads original times. It supplies no clocks or work to the
native replay. Protected/copy crossings need separate original qualification.
"""
import argparse
import csv
import json
from pathlib import Path

from air_reference import write_json
from air_pause_timing import analyze as analyze_pause
from air_startup_reference import analyze as analyze_startup
from reference_backend import require_capture_reference


def compare_pause_waits(expected, rows, begin, end):
    if begin >= end or not expected:raise ValueError('Incomplete pause interrupt interval')
    previous = -1
    for row in rows:
        if row['kind'] not in ('stat','vblank') or row['vectorCycle'] <= previous or row['owner'] not in range(5):
            raise ValueError('Invalid native interrupt ordering/owner')
        previous = row['vectorCycle']
    native = [row for row in rows if begin <= row['vectorCycle'] < end]
    if len(native) != len(expected):raise ValueError('Incomplete pause interrupt coverage')
    differences = []
    for index, (target, row) in enumerate(zip(expected, native)):
        if row['owner'] != 2:raise ValueError('Pause interrupt lacks the qualified counter-wait owner')
        delta = {key:[value,row[key]] for key,value in target.items() if row[key] != value}
        if delta:differences.append(dict(index=index,fields=delta))
    return differences


def compare(args):
    manifest = json.loads((args.capture/'capture-summary.json').read_text())
    if manifest.get('controlDifferences') or not manifest.get('pauseReached'):
        raise ValueError('Requires a control-verified original pause')
    timing = json.loads((args.timing/'pause.json').read_text())
    startup = json.loads((args.startup/'startup.json').read_text())
    for data in (timing,startup):
        require_capture_reference(manifest,data)
        if any(data.get(key) != manifest.get(key) for key in ('romSha256','controlMemorySha256')):
            raise ValueError('Mixed pause interrupt controls')
    reference = startup['reference']
    if reference.get('emulator') != 'SameBoy' or reference.get('model') != 'DMG-B' or reference.get('referenceObserver') != 'execution-callback-v1':
        raise ValueError('Requires the qualified independent startup convention')
    epoch = analyze_startup(startup)['epoch']
    if analyze_pause(timing)['sourceMismatches'] or len(timing['pauses']) != 1:
        raise ValueError('Requires one complete source-verified pause')
    pause = timing['pauses'][0]
    with args.phases_csv.open(encoding='utf-8-sig',newline='') as stream:
        phases = list(csv.DictReader(stream))
    if not phases or phases[0]['phase'] != 'copy0' or phases[-1]['phase'] != 'return':
        raise ValueError('Missing native pause interval boundaries')
    begin = int(phases[0]['start']);end = int(phases[-1]['end'])
    if begin != pause['copies'][0]['start']-epoch or end != pause['points'][-1]['cycles']-epoch:
        raise ValueError('Native absolute pause boundaries differ from the original')
    expected = []
    previous = -1
    for irq in pause['interrupts']:
        if irq['returnAddress'] != 0x261d or not begin <= irq['start']-epoch < irq['end']+16-epoch <= end:
            raise ValueError('Unqualified protected/copy pause interrupt or incomplete return')
        if irq['start'] <= previous:raise ValueError('Unordered original pause interrupts')
        previous = irq['end']+16
        expected.append(dict(kind=irq['kind'],vectorCycle=irq['start']-epoch))
    with args.native_csv.open(encoding='utf-8-sig',newline='') as stream:
        rows = [{key:value if key == 'kind' else int(value) for key,value in row.items()} for row in csv.DictReader(stream)]
    differences = compare_pause_waits(expected,rows,begin,end)
    result = dict(comparedPauseWaitInterrupts=len(expected),statInterrupts=sum(q['kind']=='stat' for q in expected),
        vblankInterrupts=sum(q['kind']=='vblank' for q in expected),differences=len(differences),
        firstDifference=differences[0] if differences else None,productionSchedulerAccepted=False,
        evidenceLimit='Absolute source counter-wait IRQ vectors during one bounded pause, using the independently qualified startup epoch. No pending protected/copy crossings, first LCD frame, arbitrary IRQ latency, hardware or Windows scheduling acceptance.')
    write_json(args.native_csv.with_suffix('.pause-comparison.json'),result)
    print(json.dumps(result,indent=2))
    if differences:raise ValueError('Native pause interrupt vectors differ from the original')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('native_csv',type=Path)
    for name in ('capture','timing','startup','phases-csv'):parser.add_argument('--'+name,type=Path,required=True)
    compare(parser.parse_args())
