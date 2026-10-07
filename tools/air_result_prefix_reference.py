"""Read-only original Air result setup through the common graphics prefix.

Uses the separately authorized reference for capture only. Measurements, ROM
and control states remain local. No observed work drives the native prefix.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from air_reference import write_json
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference

POINTS={0x0409:'begin',0x040d:'lcdOffReturned',0x0413:'objectsCleared',0x0425:'registersReady',
        0x042f:'mapsCleared',0x044d:'flagsReady',0x0450:'tilesBank',0x045c:'tilesReady',0x045f:'dataBank',0x0462:'playerReady'}


def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or manifest['romSha256']!=hashlib.sha256(read_rom(args.rom)).hexdigest():
        raise ValueError('Requires a matching independently controlled original')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    player=Reference(str(args.rom),window='null',sound_volume=0);player.set_emulation_speed(0)
    active=False;complete=False;points=[];polls=[];off=None
    def hook(pc):
        nonlocal active,complete,off
        if complete:return
        if pc==0x0409 and player.memory[0xc098]==4:active=True
        if not active:return
        if pc in POINTS:
            points.append(dict(name=POINTS[pc],cycles=player._cycles(),lcd=player.lcd_snapshot(),
                interruptFlags=player.memory[0xff0f],interruptEnable=player.memory[0xffff],result=player.memory[0xc095]))
            if pc==0x0462:active=False;complete=True
        elif pc==0x2598:polls.append(dict(cycles=player._cycles(),ly=player.register_file.A))
        elif pc==0x25a2:off=dict(cycles=player._cycles(),lcd=player.lcd_snapshot(),interruptFlags=player.memory[0xff0f])
    try:
        with (args.capture/'setup.state').open('rb') as stream:player.load_state(stream)
        for pc in (*POINTS,0x2598,0x25a2):player.hook_register(0,pc,hook,pc)
        for event in json.loads((args.capture/'events.json').read_text()):
            if event[0]=='tick':player.tick(event[1],event[2])
            elif event[0] in ('press','release'):getattr(player,'button_'+event[0])(event[1])
            else:raise ValueError('Unknown original event')
        control=hashlib.sha256(bytes(player.memory[0x8000:0x10000])).hexdigest()
    finally:player.stop(save=False)
    if control!=manifest['controlMemorySha256'] or not complete:raise ValueError('Incomplete result prefix or changed original control')
    data=dict(version=1,romSha256=manifest['romSha256'],controlMemorySha256=control,reference=metadata,points=points,polls=polls,lcdOff=off)
    analyze(data);args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'result-prefix.json',data)
    print(json.dumps(dict(points=len(points),pollReads=len(polls),controlDifferences=0),indent=2))


def analyze(data):
    if data.get('version')!=1 or [point['name'] for point in data['points']]!=list(POINTS.values()):
        raise ValueError('Incomplete/reordered common result prefix')
    if data['points'][0]['result']&4:raise ValueError('Perfect-result celebration needs its separate prefix')
    points=data['points'];polls=data['polls']
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Non-increasing result boundaries')
    if not data.get('lcdOff') or data['lcdOff']['lcd']['lcdc']&128:raise ValueError('Missing LCD-disable completion')
    if not polls or polls[-1]['ly']!=145 or any(p['ly']==145 for p in polls[:-1]):
        raise ValueError('LCD-off must wait for equality with source line 145')
    if any(b['cycles']-a['cycles']!=32 for a,b in zip(polls,polls[1:])):
        raise ValueError('LCD-off poll cadence differs from source')
    if any(p['lcd']['lcdc']&128 for p in points[1:]):raise ValueError('Graphics setup is not LCD-off')
    expected=[4+204+32*(len(polls)-1),6196,96,2*147552,144,68,426056,68,88]
    actual=[b['cycles']-a['cycles'] for a,b in zip(points,points[1:])]
    if actual!=expected:raise ValueError(f'Common result-prefix source work differs: {actual} vs {expected}')
    return expected


def compare_prefix(data,native,polls,summary,epoch):
    analyze(data)
    expected=[dict(boundary=p['name'],cycle=p['cycles']-epoch) for p in data['points']]
    expected.append(dict(boundary='lcdDisabled',cycle=data['lcdOff']['cycles']-epoch))
    if len(native)!=len(expected) or len(polls)!=len(data['polls']) or len(summary)!=1:
        raise ValueError('Incomplete native result-prefix boundaries/polls')
    differences=[]
    for target,row in zip(expected,native):
        if row['boundary']!=target['boundary']:raise ValueError('Reordered native result-prefix boundaries')
        if int(row['cycle'])!=target['cycle']:differences.append(dict(boundary=row['boundary'],expected=target['cycle'],native=int(row['cycle'])))
    for index,(target,row) in enumerate(zip(data['polls'],polls)):
        if int(row['cycle'])!=target['cycles']-epoch or int(row['ly'])!=target['ly']:
            differences.append(dict(poll=index,expected=[target['cycles']-epoch,target['ly']],native=[int(row['cycle']),int(row['ly'])]))
    expected_summary=dict(end=data['points'][-1]['cycles']-epoch,lcdDisabled=data['lcdOff']['cycles']-epoch,
        pollReads=len(data['polls']),pendingRequests=data['lcdOff']['interruptFlags']&3)
    if any(int(summary[0][key])!=value for key,value in expected_summary.items()):
        differences.append(dict(summary=expected_summary,native=summary[0]))
    return differences


def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    data=json.loads((args.out/'result-prefix.json').read_text());require_capture_reference(manifest,data)
    if manifest['controlDifferences'] or any(data.get(k)!=manifest.get(k) for k in ('romSha256','controlMemorySha256')):
        raise ValueError('Mixed original result-prefix control')
    startup=json.loads((args.startup/'startup.json').read_text());require_capture_reference(manifest,startup)
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    if any(startup.get(k)!=manifest.get(k) for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed result startup epoch')
    with args.native_csv.open(encoding='utf-8-sig',newline='') as stream:native=list(csv.DictReader(stream))
    with args.native_csv.with_suffix('.polls.csv').open(encoding='utf-8-sig',newline='') as stream:polls=list(csv.DictReader(stream))
    with args.native_csv.with_suffix('.summary.csv').open(encoding='utf-8-sig',newline='') as stream:summary=list(csv.DictReader(stream))
    differences=compare_prefix(data,native,polls,summary,epoch)
    result=dict(comparedBoundaries=len(native),originalPollReads=len(data['polls']),differences=len(differences),
        firstDifference=differences[0] if differences else None,productionSchedulerAccepted=False,
        evidenceLimit='Common result prefix: LCD-off equality wait, object/register/map reset, fixed graphics copy and player pointer. Excludes perfect celebration, result-specific layout/accounting, music/enable/fade, pixels, PCM and Windows integration.')
    write_json(args.native_csv.with_suffix('.comparison.json'),result);print(json.dumps(result,indent=2))
    if differences:raise ValueError('Native common result prefix differs from original')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    diff=sub.add_parser('compare');diff.add_argument('native_csv',type=Path);diff.add_argument('--startup',type=Path,required=True)
    for command in (record,diff):
        command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)
