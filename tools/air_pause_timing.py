"""Control-verified original Air pause measurements, separate from the port.

Only capture imports the authorized reference emulator. Report reconstructs
semantic work from the source and observed LCD poll/wake counts; it does not
certify a native scheduler. Original inputs, state and recordings stay local.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

from air_reference import write_json
from air_loop_timing import stat_cycles, wait_active_cycles
from air_timing import elapsed_work, VBLANK_FIXED, vblank_bookkeeping_work
from extract import read_rom

VERSION=1
POINTS={0x1476:'enter',0x1492:'copyEntry',0x14ac:'script',0x14b9:'wait',
        0x14bc:'wake',0x14c2:'restore',0x14dc:'restoreAudio',0x14f1:'return',0x03d8:'update'}
PHASES={0x2430:'dma',0x2433:'joypad',0x2436:'display',0x2455:'bookkeeping',
        0x2475:'effects',0x2478:'audioBank',0x247b:'music',0x247e:'restore'}


def copy_cycles(size, failed_polls, destination_wraps=0):
    if size<=0 or failed_polls<0 or not 0<=destination_wraps<=size:
        raise ValueError('Invalid pause copy workload')
    # 2359 prefix (112); successful LCD poll (28), copy and destination
    # test (48), count/branch (28, last 24); bank restore and return (88).
    return 196+104*size+32*failed_polls+4*destination_wraps


def script_cycles(failed_polls):
    if failed_polls<0:raise ValueError('Invalid pause text LCD polling')
    # RST10 entry (84); high-command dispatch (168 each) and handlers:
    # window layer (68), position (184), 20x1 rectangle (216+3064), end (108).
    # Each blocked 2121/2123/2125 poll adds 32; successful stores are included.
    return 84+4*168+68+184+216+3064+108+32*failed_polls


def analyze(data):
    if data.get('version')!=VERSION or not data.get('pauses'):
        raise ValueError('Requires complete current pause capture')
    differences=[];copies=0;waits=0;services=0;idle=[];frozen=0
    def compare(pause,phase,actual,source):
        if actual!=source:differences.append(dict(pause=pause,phase=phase,measured=actual,source=source))
    for pi,pause in enumerate(data['pauses']):
        pts=pause['points'];irq=pause['interrupts'];cs=pause['copies']
        if len(cs)!=4 or [c['size'] for c in cs]!=[20,128,20,128]:raise ValueError('Incomplete pause restoration copies')
        if [p['name'] for p in pts[:3]]!=['enter','copyEntry','script'] or [p['name'] for p in pts[-4:]]!=['restore','restoreAudio','return','update']:
            raise ValueError('Incomplete pause boundaries')
        if pts[0]['selector']!=4 or pts[1]['selector']!=1 or pts[-1]['selector']!=4:
            raise ValueError('Unexpected pause display selector')
        if any(p['audioEnabled'] for p in pts[1:-3]) or not pts[-1]['audioEnabled']:
            raise ValueError('Unexpected music suspension/restoration')
        for c in cs:
            compare(pi,'copy',elapsed_work(c['start'],c['end'],irq),copy_cycles(c['size'],c['failedPolls'],c['destinationWraps']))
            copies+=1
        for i,p in enumerate(pts[:-1]):
            q=pts[i+1];active=elapsed_work(p['cycles'],q['cycles'],irq)
            name=p['name']
            if name=='enter':source=192
            elif name in ('copyEntry','restore'):
                selected=cs[:2] if name=='copyEntry' else cs[2:]
                source=128+sum(copy_cycles(c['size'],c['failedPolls'],c['destinationWraps']) for c in selected)
            elif name=='script':source=script_cycles(pause['scriptFailedPolls'])
            elif name=='restoreAudio':source=140
            elif name=='return':source=16
            elif name=='wake':source=32 if q['name']=='wait' else 28
            elif name=='wait':
                if q['name']!='wake':raise ValueError('Pause wait misses wake')
                included=[r for r in irq if p['cycles']<=r['start']-20 and r['end']+16<=q['cycles']]
                if sum(r['kind']=='vblank' for r in included)!=1 or q['counter']!=(p['counter']+1)&255:
                    raise ValueError('Pause wait must advance the service counter exactly once')
                source=wait_active_cycles(sum(r['kind']=='stat' for r in included))
                residual=active-source
                if residual<0 or residual%4:raise ValueError('Invalid pause HALT idle')
                idle.append(residual);waits+=1;continue
            else:raise ValueError('Unknown pause interval')
            compare(pi,name,active,source)
        previous=-1;prior_frozen=None
        for r in irq:
            if not previous<=r['start']<r['end']:raise ValueError('Unordered pause IRQ')
            previous=r['end']+16
            if r['kind']=='stat':compare(pi,'STAT',r['end']-r['start'],stat_cycles(r['selector']))
            else:
                if set(r.get('phases',{}))!=set(PHASES.values()):raise ValueError('Incomplete pause display phases')
                if r['displaySelector']!=1 or r['audioEnabled']:raise ValueError('Pause callback/music ownership changed')
                if r['effectRequest']!=-1:raise ValueError('Pending paused effect needs its own setup workload')
                b=r['phases'];fixed={**VBLANK_FIXED,'display':160,
                    'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched']),
                    'effects':64,'music':60}
                names=list(PHASES.values())
                intervals={'prefix':b['dma']-r['start']}
                intervals.update({a:b[z]-b[a] for a,z in zip(names,names[1:])})
                intervals['restore']=r['end']-b['restore']
                if any(cost<=0 for cost in intervals.values()):raise ValueError('Unordered pause display phases')
                for name,cost in intervals.items():compare(pi,'VBlank '+name,cost,fixed[name])
                if prior_frozen is not None:
                    if r['world']!=prior_frozen['world']:raise ValueError('Gameplay changed inside pause')
                    if r['tick']!=(prior_frozen['tick']+1)&65535:raise ValueError('Pause global counter did not continue')
                    frozen+=1
                prior_frozen=r;services+=1
    if not waits or not services:raise ValueError('Empty pause wait/service evidence')
    return dict(pauses=len(data['pauses']),copies=copies,waits=waits,pausedDisplayServices=services,
        frozenGameplayIntervals=frozen,sourceMismatches=differences,
        haltIdleRange=[min(idle),max(idle)] if idle else [],runtimeSchedulingFixed=False,
        evidenceLimit='Source work uses observed LCD-poll and STAT-wake counts. HALT idle is measured, never a fitted allowance. No native input, presentation, PCM or Windows scheduler parity is claimed.')


def capture(args):
    rom=read_rom(args.rom);manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['romSha256']!=hashlib.sha256(rom).hexdigest() or manifest['controlDifferences'] or not manifest.get('pauseSamples'):
        raise ValueError('Requires matching control-verified pause replay')
    if args.reference_lib:sys.path.insert(0,str(args.reference_lib.resolve()))
    if importlib.metadata.version('pyboy')!='2.7.0':raise ValueError('Requires PyBoy 2.7.0')
    from pyboy import PyBoy
    p=PyBoy(str(args.rom),window='null',sound_volume=0);p.set_emulation_speed(0)
    pauses=[];current=opened=copy=None;in_script=False
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(a):
        nonlocal current,opened,copy,in_script
        if a==0x1476 and p.memory[0xc098]==4:
            if current is not None:raise ValueError('Nested pause')
            current=dict(points=[],interrupts=[],copies=[],scriptFailedPolls=0);pauses.append(current)
        if current is None:return
        now=p._cycles()
        if a in (0x0040,0x0048):
            if opened is not None:raise ValueError('Nested pause interrupt')
            opened=dict(kind='vblank' if a==0x0040 else 'stat',start=now,selector=p.memory[0xc099],
                displaySelector=p.memory[0xc098],audioEnabled=p.memory[0xffcf],tick=word(0xc00a),
                resetEnabled=p.memory[0xc005],held=p.memory[0xff8a],resetLatched=p.memory[0xc004],
                returnAddress=word(p.register_file.SP),phases={},
                world=list(p.memory[0xc200:0xc310])+list(p.memory[0xff92:0xff98])+list(p.memory[0xffa4:0xffa8])+list(p.memory[0xffb5:0xffb7])+list(p.memory[0xc083:0xc085])+list(p.memory[0xc09e:0xc0a0]))
        elif a in (0x2484,0x2555):
            if opened is None or opened['kind']!=('vblank' if a==0x2484 else 'stat'):raise ValueError('Unmatched pause interrupt')
            opened['end']=now;current['interrupts'].append(opened);opened=None
        elif a in PHASES:
            if opened is None or opened['kind']!='vblank':raise ValueError('Pause display phase outside service')
            opened['phases'][PHASES[a]]=now
            if a==0x2455:opened.update(resetEnabled=p.memory[0xc005],held=p.memory[0xff8a],resetLatched=p.memory[0xc004])
            if a==0x2475:opened['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
        elif a==0x2359:
            if copy is not None:raise ValueError('Nested pause copy')
            copy=dict(start=now,size=p.register_file.B*256+p.register_file.C,failedPolls=0,destinationWraps=0)
        elif a==0x2378:
            if copy is None:raise ValueError('Unmatched pause copy')
            copy['end']=now+16;current['copies'].append(copy);copy=None
        elif a==0x2365:
            # The source BIT's Z flag owns this branch. STAT can change between
            # the earlier LDH read and the branch; a second register read here
            # would incorrectly count the failed polls at LCD mode boundaries.
            if copy is not None and not p.register_file.F&128:copy['failedPolls']+=1
        elif a==0x236d:
            if copy is not None and p.register_file.D==0x98:copy['destinationWraps']+=1
        elif a==0x2125:
            if in_script and not p.register_file.F&128:current['scriptFailedPolls']+=1
        elif a in POINTS:
            current['points'].append(dict(name=POINTS[a],cycles=now,selector=p.memory[0xc098],audioEnabled=p.memory[0xffcf],
                tick=word(0xc00a),counter=p.memory[0xc009],held=p.memory[0xff8a],pressed=p.memory[0xff8b]))
            if a==0x14ac:in_script=True
            elif a==0x14b9:in_script=False
            elif a==0x03d8:
                if opened is not None or copy is not None:raise ValueError('Pause ended during work')
                current=None
    try:
        with (args.capture/'setup.state').open('rb') as stream:p.load_state(stream)
        for a in (*POINTS,*PHASES,0x0040,0x0048,0x2484,0x2555,0x2359,0x2378,0x2365,0x236d,0x2125):p.hook_register(0,a,hook,a)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            elif e[0] in ('press','release'):getattr(p,'button_'+e[0])(e[1])
            else:raise ValueError('Unknown replay event')
        control=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if current is not None or control!=manifest['controlMemorySha256']:raise ValueError('Incomplete pause or changed control memory')
    args.out.mkdir(parents=True,exist_ok=True)
    write_json(args.out/'pause.json',dict(version=VERSION,romSha256=manifest['romSha256'],controlMemorySha256=control,pauses=pauses))
    report(args)


def report(args):
    result=analyze(json.loads((args.out/'pause.json').read_text()))
    write_json(args.out/'summary.json',result);print(json.dumps(result,indent=2))
    if result['sourceMismatches']:raise ValueError('Pause source work mismatch')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    rec=sub.add_parser('capture');rec.add_argument('rom',type=Path);rec.add_argument('--reference-lib',type=Path)
    rec.add_argument('--capture',type=Path,default=Path('local/original-air-pause'))
    for q in (rec,sub.add_parser('report')):q.add_argument('--out',type=Path,default=Path('local/air-pause-timing'))
    args=parser.parse_args();{'capture':capture,'report':report}[args.mode](args)
