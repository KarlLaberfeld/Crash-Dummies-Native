"""Read-only original Air result layouts, music startup and incoming fade.

Only capture uses the separately authorized pinned emulator. Original data and
measurements stay local; none of its returned clocks drive native execution.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from air_reference import write_json
from air_timing import IRQ_PHASES
from air_timing import vblank_work,vblank_bookkeeping_work,VBLANK_FIXED,elapsed_work
from air_loop_timing import stat_cycles,wait_active_cycles
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference

POINTS={0x0462:'playerReady',0x0471:'successTextReady',0x0474:'portraitReady',
        0x0477:'musicReady',0x047a:'enable',0x047b:'enableFollower',0x047e:'fadeReturned',
        0x0575:'failurePortrait',0x0593:'failurePortraitReady',0x059a:'failureTextReady',
        0x059d:'enable',0x059e:'enableFollower',0x05a7:'failureWait',
        0x05aa:'failureWaitReturned',0x05ac:'musicEntry',0x05af:'musicReady',0x05b2:'fadeReturned',
        0x25ae:'lcdWriteReturned',0x20d1:'fadeEntry',0x20d6:'palette',0x20e4:'wait',0x20e7:'tail'}
HOLD_POINTS={0x25cd:'holdWait',0x25d0:'holdTail',0x05ba:'holdReturned',0x05bd:'musicStopped',0x0514:'failureResultReturned'}


def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or manifest['romSha256']!=hashlib.sha256(read_rom(args.rom)).hexdigest():
        raise ValueError('Requires a matching independently controlled original')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    player=Reference(str(args.rom),window='null',sound_volume=0);player.set_emulation_speed(0)
    active=False;complete=False;points=[];interrupts=[];opened=None
    selected={**POINTS,**(HOLD_POINTS if args.failure_hold else {})}
    def word(a):return player.memory[a]+256*player.memory[a+1]
    def hook(pc):
        nonlocal active,complete,opened
        if complete:return
        now=player._cycles()
        if pc==0x0462 and player.memory[0xc098]==10:active=True
        if not active:return
        if pc in selected:
            points.append(dict(name=selected[pc],cycles=now,pc=pc,tick=word(0xc00a),
                result=player.memory[0xc095],countdown=word(0xc0b7),display=player.memory[0xc098],
                musicEnabled=player.memory[0xffcf],song=player.memory[0xffce],
                bgp=player.memory[0xff47],obp0=player.memory[0xff48],obp1=player.memory[0xff49],
                inputHeld=player.memory[0xff8a],inputPressed=player.memory[0xff8b],
                interruptFlags=player.memory[0xff0f],lcd=player.lcd_snapshot()))
            if selected[pc]==('failureResultReturned' if args.failure_hold else 'fadeReturned'):active=False;complete=True
        elif pc in (0x0040,0x0048):
            if opened is not None:raise ValueError('Nested result interrupt')
            opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=player.memory[0xc099],
                returnAddress=word(player.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and opened is not None and opened['kind']=='vblank':
            name=IRQ_PHASES[pc];opened['phases'][name]=now
            if name=='display':opened.update(held=player.memory[0xff8a],pressed=player.memory[0xff8b])
            if name=='bookkeeping':opened.update(resetEnabled=player.memory[0xc005],resetLatched=player.memory[0xc004])
            if name=='effects':opened['effectRequest']=-1 if player.memory[0xffc6]==255 else player.memory[0xffc6]
            if name=='music':opened['musicEnabled']=player.memory[0xffcf]
        elif pc in (0x2484,0x2555) and opened is not None:
            if opened['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Unexpected result interrupt return')
            opened['end']=now;interrupts.append(opened);opened=None
    try:
        with (args.capture/'setup.state').open('rb') as stream:player.load_state(stream)
        for pc in (*selected,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555):player.hook_register(0,pc,hook,pc)
        for event in json.loads((args.capture/'events.json').read_text()):
            if event[0]=='tick':player.tick(event[1],event[2])
            elif event[0] in ('press','release'):getattr(player,'button_'+event[0])(event[1])
            else:raise ValueError('Unknown original event')
        control=hashlib.sha256(bytes(player.memory[0x8000:0x10000])).hexdigest()
    finally:player.stop(save=False)
    if control!=manifest['controlMemorySha256'] or not complete or opened is not None:
        raise ValueError('Incomplete result transition or changed original control')
    data=dict(version=2,failureHold=args.failure_hold,romSha256=manifest['romSha256'],controlMemorySha256=control,
        reference=metadata,points=points,interrupts=interrupts)
    analyze(data);args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'result-transition.json',data)
    (args.out/'buttons.txt').write_text(''.join(str(r['held'])+'\n' for r in interrupts if r['kind']=='vblank'))
    print(json.dumps(dict(points=len(points),interrupts=len(interrupts),controlDifferences=0),indent=2))


def analyze(data):
    if data.get('version') not in (1,2):raise ValueError('Recapture result transition')
    points=data['points'];irqs=data['interrupts']
    hold=data.get('failureHold',False)
    if not points or points[0]['name']!='playerReady' or points[-1]['name']!=('failureResultReturned' if hold else 'fadeReturned'):
        raise ValueError('Incomplete result transition')
    result=points[0]['result'];success=bool(result&2)
    if result&4 or not result&1:raise ValueError('Separate perfect/unfinished result owner required')
    if hold and success:raise ValueError('Successful result accounting is a separate owner')
    prefix=['playerReady','successTextReady','portraitReady','musicReady','lcdWriteReturned','enable','enableFollower','fadeEntry'] if success else [
        'playerReady','failurePortrait','failurePortraitReady','failureTextReady','lcdWriteReturned','enable','enableFollower',
        'failureWait','failureWaitReturned','musicEntry','musicReady','fadeEntry']
    expected=prefix+[name for _ in range(8) for name in ('palette','wait','tail','wait','tail','wait','tail','wait','tail')]+['fadeReturned']
    hold_count=sum(p['name']=='holdWait' for p in points) if hold else 0
    if hold and not (1<=hold_count<=480 and (data['version']==2 or hold_count==480)):raise ValueError('Incomplete result hold')
    if hold:expected+=[name for _ in range(hold_count) for name in ('holdWait','holdTail')]+['holdReturned','musicStopped','failureResultReturned']
    if [p['name'] for p in points]!=expected or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):
        raise ValueError('Missing/reordered result boundaries')
    if any(p['result']!=result or p['display']!=10 for p in points):raise ValueError('Result mode changed inside transition')
    if any(p['lcd']['lcdc']&128 for p in points[:prefix.index('lcdWriteReturned')]):
        raise ValueError('Result layout is not LCD-off')
    if not irqs or [r['kind'] for r in irqs[:2]]!=['vblank','stat']:
        raise ValueError('Missing pending result startup')
    enable=next(p for p in points if p['name']=='enable')
    if enable['interruptFlags']&3!=3 or irqs[0]['start']!=enable['cycles']+4+24+20:
        raise ValueError('Result enable follower/pending service timing differs')
    if irqs[1]['start']!=irqs[0]['end']+16+20:raise ValueError('Result pending service priority differs')
    services=[];previous=points[0]['cycles']
    for r in irqs:
        if not previous<=r['start']<r['end'] or r['end']+16>points[-1]['cycles']:
            raise ValueError('Incomplete/overlapping result IRQ coverage')
        previous=r['end']+16
        if r['kind']=='stat':
            if r['selector']!=0 or r['end']-r['start']!=stat_cycles(0):raise ValueError('Unowned result STAT callback')
        elif r['kind']=='vblank':
            components=vblank_work(r)
            fixed={**VBLANK_FIXED,'display':272,'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched']),'effects':64}
            if any(components[k]!=v for k,v in fixed.items()) or r['effectRequest']!=-1:
                raise ValueError('Unowned result display/bookkeeping/effect work')
            services.append(r)
        else:raise ValueError('Unknown result interrupt')
    if len(services)!=((33 if success else 34)+hold_count) or len(irqs)!=2*len(services):
        raise ValueError('Result display/STAT coverage differs')
    fade_end=next(i for i,p in enumerate(points) if p['name']=='fadeReturned')
    fade=points[len(prefix)-1:fade_end+1];wait_index=0
    for p,q in zip(fade,fade[1:]):
        active=elapsed_work(p['cycles'],q['cycles'],irqs)
        if p['name']=='wait':
            included=[r for r in irqs if p['cycles']<=r['start']-20 and r['end']+16<=q['cycles']]
            if sum(r['kind']=='vblank' for r in included)!=1 or any(r['returnAddress']!=0x261d for r in included):
                raise ValueError('Unowned incoming counter wait')
            idle=active-wait_active_cycles(sum(r['kind']=='stat' for r in included))
            if idle<0 or idle%4:raise ValueError('Incoming wait has invalid source HALT idle')
            wait_index+=1
        else:
            expected_work=20 if p['name']=='fadeEntry' else 76 if p['name']=='palette' else 16 if wait_index%4 else 40 if wait_index==32 else 28
            if active!=expected_work:raise ValueError('Incoming palette/branch work differs from source')
    if wait_index!=32:raise ValueError('Incomplete incoming fade waits')
    if hold:
        held={r['held'] for r in services}
        if data['version']==1 and len(held)!=1:raise ValueError('Legacy hold requires unchanged input')
        wait=0
        for p,q in zip(points[fade_end:],points[fade_end+1:]):
            active=elapsed_work(p['cycles'],q['cycles'],irqs)
            if p['name']=='holdWait':
                included=[r for r in irqs if p['cycles']<=r['start']-20 and r['end']+16<=q['cycles']]
                if sum(r['kind']=='vblank' for r in included)!=1 or any(r['returnAddress']!=0x261d for r in included):raise ValueError('Unowned result hold wait')
                idle=active-wait_active_cycles(sum(r['kind']=='stat' for r in included));wait+=1
                if idle<0 or idle%4:raise ValueError('Invalid hold HALT idle')
            else:
                edge=p.get('inputPressed',0)&11
                if p['name']=='holdTail' and edge and wait!=hold_count:raise ValueError('Result hold failed to return at a fresh action')
                if p['name']=='holdTail' and wait==hold_count and hold_count<480 and not edge:raise ValueError('Truncated hold without fresh action')
                predicted=44 if p['name']=='fadeReturned' else (36 if edge else 52 if wait<480 else 64) if p['name']=='holdTail' else 12384 if p['name']=='holdReturned' else 16
                if active!=predicted:raise ValueError('Result hold branch/stop work differs')
    if data['version']==2:
        previous=points[0]['inputHeld']
        for r in services:
            if r['pressed']!=r['held']&~previous or (r['held']&15)==15:raise ValueError('Result button edge/reset state differs')
            previous=r['held']
    return services


def compare_transition(data,native,services,irqs,summary,epoch):
    original_services=analyze(data)
    if len(native)!=len(data['points']) or len(services)!=len(original_services) or len(irqs)!=len(data['interrupts']) or len(summary)!=1:
        raise ValueError('Incomplete native result transition coverage')
    differences=[]
    for index,(target,row) in enumerate(zip(data['points'],native)):
        if row['boundary']!=target['name']:raise ValueError('Reordered native result boundaries')
        expected={key:target[key] for key in ('tick','countdown','bgp','obp0','obp1','musicEnabled')}
        expected['cycle']=target['cycles']-epoch
        if data['version']==2:expected.update({k:target[k] for k in ('inputHeld','inputPressed')})
        delta={k:[v,int(row[k])] for k,v in expected.items() if int(row[k])!=v}
        if delta:differences.append(dict(boundary=index,fields=delta))
    for index,(target,row) in enumerate(zip(original_services,services)):
        c=vblank_work(target)
        expected=dict(service=index,cycle=target['start']-epoch,tick=target['tick'],countdown=target['countdown']-1,
            display=c['display'],effects=c['effects'],music=c['music'],musicEnabled=target['musicEnabled'],inputHeld=target['held'])
        if data['version']==2:expected['inputPressed']=target['pressed']
        delta={k:[v,int(row[k])] for k,v in expected.items() if int(row[k])!=v}
        if delta:differences.append(dict(service=index,fields=delta))
    for index,(target,row) in enumerate(zip(data['interrupts'],irqs)):
        owner=3 if index<2 else 2 if target['returnAddress']==0x261d else 1
        if row['kind']!=target['kind'] or int(row['owner'])!=owner:raise ValueError('Unowned/reordered native result IRQ')
        if int(row['vectorCycle'])!=target['start']-epoch:differences.append(dict(interrupt=index,expected=target['start']-epoch,native=int(row['vectorCycle'])))
    enable=next(p for p in data['points'] if p['name']=='enable');last=data['points'][-1]
    expected=dict(end=last['cycles']-epoch,lcdEpoch=enable['cycles']-20-epoch,tick=last['tick'],countdown=last['countdown'],
        displays=len(original_services),stats=len(data['interrupts'])-len(original_services))
    if any(int(summary[0][k])!=v for k,v in expected.items()):differences.append(dict(summary=expected,native=summary[0]))
    return differences


def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    data=json.loads((args.out/'result-transition.json').read_text());require_capture_reference(manifest,data)
    startup=json.loads((args.startup/'startup.json').read_text());require_capture_reference(manifest,startup)
    if manifest['controlDifferences'] or any(r.get(k)!=manifest.get(k) for r in (data,startup) for k in ('romSha256','controlMemorySha256')):
        raise ValueError('Mixed result-transition controls')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
    native=rows(args.native_csv);services=rows(args.native_csv.with_suffix('.services.csv'))
    irqs=rows(args.native_csv.with_suffix('.interrupts.csv'));summary=rows(args.native_csv.with_suffix('.summary.csv'))
    differences=compare_transition(data,native,services,irqs,summary,epoch)
    result=dict(comparedBoundaries=len(native),comparedServices=len(services),comparedInterrupts=len(irqs),differences=len(differences),
        firstDifference=differences[0] if differences else None,productionSchedulerAccepted=False,
        failureHoldAccepted=data.get('failureHold',False),
        evidenceLimit='Ordinary Air result text/portrait work, music reset/start, LCD restart, pending services and complete incoming fade; failure-hold captures additionally include the full or input-shortened hold and final music stop. Version 2 compares fresh input state. Excludes final-life/perfect/reset results, pixels/PCM, subsequent setup and Windows integration.')
    write_json(args.native_csv.with_suffix('.comparison.json'),result);print(json.dumps(result,indent=2))
    if differences:raise ValueError('Native result transition differs from original')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    record.add_argument('--failure-hold',action='store_true')
    diff=sub.add_parser('compare');diff.add_argument('native_csv',type=Path);diff.add_argument('--startup',type=Path,required=True)
    for command in (record,diff):
        command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)
