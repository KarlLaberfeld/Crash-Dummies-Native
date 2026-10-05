"""Read-only pending Air startup interrupts; recordings remain local.

Capture uses only the separately authorized, pinned reference. Compare imports
no emulator and never supplies original IRQ times/work to the native process.
The LCD return identifies the comparison epoch, independently of any fitted
display or poll allowance. This does not qualify the first LCD scanline.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from air_reference import write_json
from air_pause_compare import rows
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference

POINTS=(0x25a8,0x25ae,0x03c6,0x0040,0x2484,0x0048,0x2555,0x03c9,0x03cb)


def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['romSha256']!=hashlib.sha256(read_rom(args.rom)).hexdigest() or manifest['controlDifferences']:
        raise ValueError('Requires a matching control-verified original')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    player=Reference(str(args.rom),window='null',sound_volume=0);player.set_emulation_speed(0)
    points=[];started=False;complete=False
    def hook(pc):
        nonlocal started,complete
        if complete or player.memory[0xc098]!=4:return
        if not started:
            if pc!=0x25a8:return
            started=True
        points.append(dict(pc=pc,cycles=player._cycles(),tick=player.memory[0xc00a]+256*player.memory[0xc00b],
            counter=player.memory[0xc009],ready=player.memory[0xffae],interruptFlags=player.memory[0xff0f],
            interruptEnable=player.memory[0xffff],lcd=player.lcd_snapshot()))
        if pc==0x03cb:complete=True
    try:
        with (args.capture/'setup.state').open('rb') as stream:player.load_state(stream)
        for pc in POINTS:player.hook_register(0,pc,hook,pc)
        for event in json.loads((args.capture/'events.json').read_text()):
            if event[0]=='tick':player.tick(event[1],event[2])
            elif event[0] in ('press','release'):getattr(player,'button_'+event[0])(event[1])
            else:raise ValueError('Unknown original control event')
        control=hashlib.sha256(bytes(player.memory[0x8000:0x10000])).hexdigest()
    finally:player.stop(save=False)
    if not complete or control!=manifest['controlMemorySha256']:raise ValueError('Incomplete startup or changed original control memory')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=control,points=points)
    analyze(data);args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'startup.json',data)
    print(json.dumps(dict(startupPoints=len(points),controlDifferences=0,source=analyze(data)),indent=2))


def analyze(data):
    points=data.get('points',[])
    if data.get('version')!=1 or [p['pc'] for p in points]!=list(POINTS):raise ValueError('Incomplete or reordered startup ownership')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Startup time is not increasing')
    by={p['pc']:p for p in points}
    # 25ae RET follows LCD-on's final four-cycle access portion; RET costs 16.
    epoch=by[0x25ae]['cycles']-4
    if by[0x25ae]['cycles']-by[0x25a8]['cycles']!=32 or by[0x03c6]['cycles']-epoch!=20:
        raise ValueError('LCD access/return ownership differs from the source')
    if by[0x03c6]['interruptEnable']&3!=3 or by[0x03c6]['interruptFlags']&3!=3:
        raise ValueError('Startup does not retain both source pending interrupts')
    if by[0x0040]['cycles']-by[0x03c6]['cycles']!=32 or by[0x0048]['cycles']-by[0x2484]['cycles']!=36:
        raise ValueError('Pending interrupt acceptance/order differs')
    if by[0x2555]['cycles']-by[0x0048]['cycles']!=288:
        raise ValueError('Pending STAT body is not source-owned')
    if by[0x03c9]['cycles']-by[0x2555]['cycles']!=16 or by[0x03cb]['cycles']-by[0x03c9]['cycles']!=12:
        raise ValueError('Pending service return/ready store differs')
    if by[0x0040]['tick']!=by[0x03c6]['tick'] or by[0x03cb]['tick']!=(by[0x03c6]['tick']+1)&65535:
        raise ValueError('Pending display counter ownership differs')
    if by[0x03cb]['counter']!=(by[0x03c6]['counter']+1)&255 or by[0x03cb]['ready']!=1:
        raise ValueError('Counter or ready publication differs')
    return dict(epoch=epoch,displayEntry=by[0x0040]['cycles']-epoch,
        displayWork=by[0x2484]['cycles']-by[0x0040]['cycles'],
        statEntry=by[0x0048]['cycles']-epoch,readyStored=by[0x03cb]['cycles']-epoch,
        initialTick=by[0x03c6]['tick'])


def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    data=json.loads((args.out/'startup.json').read_text());require_capture_reference(manifest,data)
    if manifest['controlDifferences'] or any(data.get(k)!=manifest.get(k) for k in ('romSha256','controlMemorySha256')):
        raise ValueError('Mixed startup controls')
    original=analyze(data);native=rows(args.native_csv)
    if not native or native[0]['service']!=0 or native[0]['ready']!=1:raise ValueError('Missing native pending startup service')
    first=native[0];work=1592+first['display']+first['effects']+first['music']
    with Path(str(args.native_csv)+'.startup.csv').open(newline='') as stream:
        boundaries=list(csv.DictReader(stream))
    if [p['boundary'] for p in boundaries]!=['enableReturned','displayEntry','displayReturned','statEntry','statReturned','readyStored']:
        raise ValueError('Missing or reordered actual native startup boundaries')
    times={p['boundary']:int(p['cycle']) for p in boundaries}
    expected=dict(displayEntry=times['displayEntry'],displayWork=work,
        statEntry=times['statEntry'],readyStored=times['readyStored'],initialTick=first['tick'])
    if times['displayEntry']!=first['cycle']+20 or times['displayReturned']-times['displayEntry']!=work+16:
        raise ValueError('Native display boundary logging is inconsistent')
    if times['enableReturned']!=20 or times['statReturned']-times['statEntry']!=288+16:
        raise ValueError('Native source return ownership differs')
    differences={k:[original[k],v] for k,v in expected.items() if original[k]!=v}
    result=dict(comparedStartupPoints=len(POINTS),comparedNativeBoundaries=len(expected),differences=differences,
        productionStartupAccepted=False,evidenceLimit='Pending display/STAT order, source LCD access tail, selected counters, return and ready-store boundaries only. The ordinary first LCD frame, preceding UI setup, arbitrary IRQ latency and production integration remain unqualified.')
    write_json(args.out/'native-comparison.json',result);print(json.dumps(result,indent=2))
    if differences:raise ValueError('Native pending startup differs from the original')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    check=sub.add_parser('compare');check.add_argument('native_csv',type=Path)
    for command in (record,check):
        command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)
