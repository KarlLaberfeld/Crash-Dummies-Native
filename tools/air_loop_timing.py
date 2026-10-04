"""Local Air STAT and main-loop wait measurements; no runtime dependency.

Only capture imports the user-authorized reference emulator. Original states,
inputs and measurements must remain local. Report uses Python alone.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

from air_reference import write_json
from air_timing import elapsed_work
from extract import read_rom

VERSION=1
BOUNDARIES={0x03c6:'enable',0x03cb:'wait',0x03ce:'resume',0x03d8:'update',0x03fa:'done',0x0400:'finalWait'}


def stat_cycles(selector):
    # 0048 JP + 24e4 DI / four pushes / table dispatch + callback + four pops.
    # The table pointer (24f2 + 2*selector) never crosses a page in this table.
    # 23d6: ADD(4), RST20(16+28), LD(8+8+4), JP HL(4) = 72.
    prefix=16+4+64+12+16+16+72
    if selector==0:return prefix+48 # 2551 pops directly.
    if selector==4:return prefix+8+12+8+12+48 # Two NOPs, disable objects, pops.
    return -1 # Other stunts' scanline callbacks require their own workloads.


def wait_active_cycles(stat_wakes):
    if stat_wakes<0:raise ValueError('Invalid wait wake count')
    # CALL + PUSH BC + counter snapshot + first HALT; unsuccessful wakes
    # compare/rebranch/HALT; final changed counter exits through POP BC / RET.
    return 24+16+16+4+4+stat_wakes*(16+4+12+4)+16+4+8+12+16


def analyze(data):
    if data.get('version')!=VERSION:raise ValueError('Recapture with current loop hooks')
    interrupts=data['interrupts'];points=data['points']
    unknown=[];differences=[];waits=[];prefixes=[];tails=[]
    previous=-1
    for i,q in enumerate(interrupts):
        if not previous<=q['start']<q['end']:raise ValueError('Unordered loop interrupts')
        previous=q['end']+16
        if q['kind']=='stat':
            predicted=stat_cycles(q['selector'])
            if predicted<0:unknown.append(i)
            elif q['end']-q['start']!=predicted:differences.append(dict(interrupt=i,measured=q['end']-q['start'],source=predicted))
    previous=-1
    for i,p in enumerate(points):
        if p['cycles']<=previous:raise ValueError('Unordered main-loop boundaries')
        previous=p['cycles']
        if p['name'] not in ('wait','resume','done','enable'):continue
        if i+1==len(points):continue # Last boundary can await completion.
        following=points[i+1]
        start,end=p['cycles'],following['cycles']
        included=[q for q in interrupts if start<=q['start']-20 and q['end']+16<=end]
        active=elapsed_work(start,end,interrupts)
        if p['name']=='wait':
            if following['name']!='resume':raise ValueError('Wait missing its resume boundary')
            if sum(q['kind']=='vblank' for q in included)!=1:raise ValueError('Wait does not contain exactly one counter-changing service')
            wakes=sum(q['kind']=='stat' for q in included)
            predicted=wait_active_cycles(wakes);idle=active-predicted
            if idle<0 or idle%4:raise ValueError('Invalid HALT idle interval')
            if following['counter']!=(p['counter']+1)&255:raise ValueError('Wait counter does not advance once')
            waits.append(dict(start=start,end=end,statWakes=wakes,activeSource=predicted,idle=idle))
        elif p['name']=='resume':
            if following['name']!='update':raise ValueError('Pause or resume path needs a separate comparison')
            prefixes.append(active)
            if active!=48:differences.append(dict(boundary=i,name='resume',measured=active,source=48))
        elif p['name']=='done':
            if following['name']=='wait':expected=52
            elif following['name']=='finalWait':expected=28
            else:raise ValueError('Unexpected main-loop tail')
            tails.append(active)
            if active!=expected:differences.append(dict(boundary=i,name='tail',measured=active,source=expected))
        else:
            if following['name']!='wait':raise ValueError('Unexpected interrupt-enable sequence')
            if active!=24:differences.append(dict(boundary=i,name='enable',measured=active,source=24))
    return dict(statServices=sum(q['kind']=='stat' for q in interrupts),unknownStatServices=unknown,
        sourceMismatches=differences,waits=len(waits),statWakeCounts=sorted(set(w['statWakes'] for w in waits)),
        idleRange=[min(w['idle'] for w in waits),max(w['idle'] for w in waits)] if waits else [],
        resumePrefixes=len(prefixes),loopTails=len(tails),runtimeSchedulingFixed=False,
        evidenceLimit='Wait active work is source derived. HALT idle is measured elapsed time, not a scheduling allowance or proof of interrupt deadlines.')


def capture(args):
    rom=read_rom(args.rom)
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['romSha256']!=hashlib.sha256(rom).hexdigest() or manifest['controlDifferences']:
        raise ValueError('Requires matching control-verified Air replay')
    if args.reference_lib:sys.path.insert(0,str(args.reference_lib.resolve()))
    if importlib.metadata.version('pyboy')!='2.7.0':raise ValueError('Requires PyBoy 2.7.0')
    from pyboy import PyBoy
    p=PyBoy(str(args.rom),window='null',sound_volume=0);p.set_emulation_speed(0)
    points=[];interrupts=[];opened=None
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(a):
        nonlocal opened
        if p.memory[0xc098]!=4:return
        now=p._cycles()
        if a in (0x0040,0x0048):
            if opened is not None:raise ValueError('Nested loop interrupt')
            opened=dict(kind='vblank' if a==0x0040 else 'stat',start=now,selector=p.memory[0xc099],
                ly=p.memory[0xff44],returnAddress=word(p.register_file.SP))
        elif a in (0x2484,0x2555):
            if opened is None or opened['kind']!=('vblank' if a==0x2484 else 'stat'):
                raise ValueError('Unmatched loop interrupt return')
            opened['end']=now;interrupts.append(opened);opened=None
        else:
            points.append(dict(name=BOUNDARIES[a],cycles=now,tick=word(0xc00a),counter=p.memory[0xc009],
                ready=p.memory[0xffae],cursor=p.memory[0xc04c],ly=p.memory[0xff44],
                interruptFlags=p.memory[0xff0f],interruptEnable=p.memory[0xffff]))
    try:
        with (args.capture/'setup.state').open('rb') as stream:p.load_state(stream)
        for a in (*BOUNDARIES,0x0040,0x0048,0x2484,0x2555):p.hook_register(0,a,hook,a)
        for i,e in enumerate(json.loads((args.capture/'events.json').read_text())):
            if args.progress and i%200==0:print(f'event {i}, loop boundaries {len(points)}',flush=True)
            if e[0]=='tick':p.tick(e[1],e[2])
            elif e[0] in ('press','release'):getattr(p,'button_'+e[0])(e[1])
            else:raise ValueError('Unknown replay event')
        control=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if opened is not None or control!=manifest['controlMemorySha256']:raise ValueError('Unclosed interrupt or changed control memory')
    args.out.mkdir(parents=True,exist_ok=True)
    write_json(args.out/'loop.json',dict(version=VERSION,romSha256=manifest['romSha256'],controlMemorySha256=control,
        emulator='PyBoy 2.7.0',points=points,interrupts=interrupts))
    report(args)


def report(args):
    result=analyze(json.loads((args.out/'loop.json').read_text()))
    write_json(args.out/'summary.json',result);print(json.dumps(result,indent=2))
    if result['sourceMismatches'] or result['unknownStatServices']:raise ValueError('Uncertified loop source work')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    rec=sub.add_parser('capture');rec.add_argument('rom',type=Path);rec.add_argument('--reference-lib',type=Path)
    rec.add_argument('--capture',type=Path,default=Path('local/original-air-verified'));rec.add_argument('--progress',action='store_true')
    for q in (rec,sub.add_parser('report')):q.add_argument('--out',type=Path,default=Path('local/air-loop-timing'))
    args=parser.parse_args();{'capture':capture,'report':report}[args.mode](args)
