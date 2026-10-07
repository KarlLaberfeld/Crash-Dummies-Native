"""Read-only original successful Air accounting; recordings remain local.

Capture alone uses the separately authorized pinned reference emulator.
The native clock receives no original costs, clocks, polls or ledger values.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from extract import read_rom
from air_timing import IRQ_PHASES,vblank_work,VBLANK_FIXED,vblank_bookkeeping_work,elapsed_work
from air_loop_timing import stat_cycles
from air_reference import write_json


def capture(args):
    folder=args.capture;target=args.out;target.mkdir(parents=True,exist_ok=True)
    rom=args.rom;manifest=json.loads((folder/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or hashlib.sha256(read_rom(rom)).hexdigest()!=manifest['romSha256']:raise ValueError('Original control mismatch')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(rom),window='null',sound_volume=0);p.set_emulation_speed(0)
    POINTS={0x047e:'begin',0x0483:'readyWait',0x0486:'readyReturned',0x048a:'detailSetup',0x048d:'dayReady',
     0x04a9:'savingsLabel',0x04b9:'savingsNumber',0x04bc:'savingsNumberReady',0x04bf:'savingsDelay',0x04c2:'payLabel',
     0x04c5:'payNumber',0x04c8:'payLoop',0x1415:'payTest',0x141e:'savingsIncrement',0x1421:'payDecrement',0x1424:'payUpdated',
     0x1432:'payWait',0x1435:'savingsRefresh',0x1438:'payRefresh',0x143b:'payTail',0x04cb:'payDone',0x04ce:'payTotal',
     0x04d1:'payShowEnded',0x04de:'timeLabel',0x04e1:'timeNumber',0x04e4:'timeLoop',0x13ef:'timeTest',0x13f4:'timeUnit',
     0x13f5:'timeSavingsIncrement',0x13f8:'timeDecrement',0x13fb:'timeResult',0x1409:'timeWait',0x140c:'timeSavingsRefresh',
     0x140f:'timeRefresh',0x1412:'timeTail',0x04e7:'timeDone',0x04ea:'finalSavings',0x04ed:'accountingComplete',
     0x04fa:'timerWait',0x04fd:'finalMusicStop',0x0500:'musicStopped',0x0503:'dayAdvance',0x0514:'end'}
    active=False;complete=False;points=[];irqs=[];opened=None;polls=[];writes=[];result_buttons=[];result_seen=False
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def bcd(a,size):
     value=0
     for b in p.memory[a:a+size]:value=100*value+10*(b>>4)+(b&15)
     return value
    def hook(pc):
     nonlocal active,complete,opened,result_seen
     if complete:return
     if pc==0x2436 and p.memory[0xc098]==10:
      result_seen=True;result_buttons.append(p.memory[0xff8a])
     if pc==0x047e and p.memory[0xc098]==10:active=True
     if not active:return
     now=p._cycles()
     if pc in POINTS:
      points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),pay=bcd(0xff98,3),
       savings=bcd(0xc085+8*p.memory[0xc082],3),seconds=bcd(0xc084,1),stage=p.memory[0xc088+8*p.memory[0xc082]],
       result=p.memory[0xc095],lyc=p.memory[0xff45],display=p.memory[0xc098],musicEnabled=p.memory[0xffcf],
       skip=p.memory[0xc0b4],inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],lcd=p.lcd_snapshot()))
      if pc==0x0514:complete=True;active=False
     elif pc in (0x0040,0x0048):
      if opened:raise ValueError('Nested accounting interrupt')
      opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],returnAddress=word(p.register_file.SP),
       tick=word(0xc00a),countdown=word(0xc0b7),phases={})
     elif pc in IRQ_PHASES and opened and opened['kind']=='vblank':
      name=IRQ_PHASES[pc];opened['phases'][name]=now
      if name=='display':opened.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b])
      if name=='bookkeeping':opened.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
      if name=='effects':opened['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
      if name=='music':opened['musicEnabled']=p.memory[0xffcf]
     elif pc in (0x2484,0x2555) and opened:
      if opened['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Accounting interrupt return mismatch')
      opened['end']=now;irqs.append(opened);opened=None
     elif pc==0x2123:polls.append(dict(cycles=now,mode=p.register_file.A&3))
     elif pc==0x2128:writes.append(dict(cycles=now,address=256*p.register_file.D+p.register_file.E,value=p.register_file.A))
    try:
     with (folder/'setup.state').open('rb') as stream:p.load_state(stream)
     for pc in (*POINTS,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x2123,0x2128):p.hook_register(0,pc,hook,pc)
     for event in json.loads((folder/'events.json').read_text()):
      if event[0]=='tick':p.tick(event[1],event[2])
      elif event[0] in ('press','release'):getattr(p,'button_'+event[0])(event[1])
      else:raise ValueError('Unknown original input event')
     control=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or opened or control!=manifest['controlMemorySha256']:raise ValueError('Incomplete accounting or changed original control')
    data=dict(version=2,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=control,
     points=points,interrupts=irqs,polls=polls,writes=writes)
    analyze(data)
    if not result_seen or len(result_buttons)!=33+len([r for r in irqs if r['kind']=='vblank']):raise ValueError('Incomplete result button input coverage')
    write_json(target/'accounting.json',data)
    (target/'buttons.txt').write_text(''.join(str(held)+'\n' for held in result_buttons))
    print(json.dumps(dict(points=len(points),interrupts=len(irqs),polls=len(polls),writes=len(writes),begin=points[0],end=points[-1],nativeCompared=False),indent=2))


def analyze(data):
    points=data.get('points',[]);irqs=data.get('interrupts',[])
    if data.get('version') not in (1,2) or not points or points[0]['name']!='begin' or points[-1]['name']!='end':
        raise ValueError('Incomplete successful accounting')
    if any(p['result']!=3 or p['display']!=10 for p in points):raise ValueError('Separate special-result owner required')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Accounting boundary order differs')
    begin=points[0];end=points[-1]
    if begin['stage']!=1 or end['stage']!=2 or end['pay'] or end['seconds'] or end['musicEnabled'] or begin['countdown']!=567 or not 1<=end['countdown']<=566:
        raise ValueError('Incomplete ordinary Air stage handoff')
    if end['savings']!=(begin['savings']+begin['pay']+begin['seconds'])%1000000:
        raise ValueError('Ordinary pay/time ledger does not conserve the source amounts')
    expected_counts={'payTest':begin['pay']+1,'savingsIncrement':begin['pay'],'payDecrement':begin['pay'],
        'payUpdated':begin['pay'],'payTail':begin['pay'],
        'timeTest':begin['seconds']+1,'timeUnit':begin['seconds'],'timeSavingsIncrement':begin['seconds'],
        'timeDecrement':begin['seconds'],'timeResult':begin['seconds'],'timeTail':begin['seconds']}
    from collections import Counter
    counts=Counter(p['name'] for p in points)
    if any(counts[k]!=v for k,v in expected_counts.items()):raise ValueError('Incomplete successful counting loops')
    before=['begin','readyWait','readyReturned','detailSetup','dayReady','savingsLabel','savingsNumber','savingsNumberReady','savingsDelay','payLabel','payNumber','payLoop']
    between=['payDone','payTotal','payShowEnded','timeLabel','timeNumber','timeLoop']
    after=['timeDone','finalSavings','accountingComplete','timerWait','finalMusicStop','musicStopped','dayAdvance','end']
    expected_order=before[:]
    for p in (p for p in points if p['name']=='payUpdated'):
        expected_order+=['payTest','savingsIncrement','payDecrement','payUpdated']
        if not p.get('skip',0):expected_order+=['payWait','savingsRefresh','payRefresh']
        expected_order+=['payTail']
    expected_order+=['payTest']+between
    for p in (p for p in points if p['name']=='timeResult'):
        expected_order+=['timeTest','timeUnit','timeSavingsIncrement','timeDecrement','timeResult']
        if not p.get('skip',0):expected_order+=['timeWait','timeSavingsRefresh','timeRefresh']
        expected_order+=['timeTail']
    expected_order+=['timeTest']+after
    if [p['name'] for p in points]!=expected_order:raise ValueError('Accounting stages/loop order differ')
    costs={'savingsIncrement':172,'payDecrement':136,'payUpdated':64,'payTail':24,'timeUnit':16,
        'timeSavingsIncrement':172,'timeDecrement':92,'timeResult':64,'timeTail':24,'finalMusicStop':12384,'musicStopped':88,'dayAdvance':40}
    for p,q in zip(points,points[1:]):
        expected=costs.get(p['name'])
        if p['name']=='payTest':expected=64 if p['pay'] else 60
        if p['name']=='timeTest':expected=28 if p['seconds'] else 40
        if p['name'] in ('payUpdated','timeResult'):expected=68 if p.get('skip',0) else 64
        if expected is not None and elapsed_work(p['cycles'],q['cycles'],irqs)!=expected:
            raise ValueError('Accounting primitive work differs: '+p['name'])
    services=[];previous=begin['cycles']
    for r in irqs:
        if not previous<=r['start']<r['end'] or r['end']+16>end['cycles']:raise ValueError('Accounting IRQ coverage overlaps or crosses its boundary')
        previous=r['end']+16
        if r['kind']=='stat':
            if r['selector']!=0 or r['end']-r['start']!=stat_cycles(0):raise ValueError('Unowned accounting STAT work')
        elif r['kind']=='vblank':
            work=vblank_work(r);expected={**VBLANK_FIXED,'display':272 if r['countdown']>1 else 228,
                'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched']),'effects':64}
            if any(work[k]!=v for k,v in expected.items()) or r['effectRequest']!=-1:raise ValueError('Unowned accounting display service')
            services.append(r)
        else:raise ValueError('Unexpected accounting IRQ')
    if len(services)!=(end['tick']-begin['tick'])%65536 or not services:raise ValueError('Missing accounting counter coverage')
    if data['version']==1 and (len({r['held'] for r in services})!=1 or end['countdown']!=1):
        raise ValueError('Legacy result evidence requires unchanged buttons and a complete timer')
    if data['version']==2:
        if any(not 0<=p['skip']<=255 or p['inputPressed']&~p['inputHeld'] or (p['inputHeld']&15)==15 for p in points):
            raise ValueError('Invalid original result input/latch/reset state')
        previous=begin['inputHeld']
        for r in services:
            if r['pressed']!=r['held']&~previous:raise ValueError('Original fresh button sampling differs')
            previous=r['held']
    if not data.get('polls') or not data.get('writes'):raise ValueError('Missing LCD-on result access evidence')
    for key in ('polls','writes'):
        rows=data[key]
        if not begin['cycles']<=rows[0]['cycles']<rows[-1]['cycles']<=end['cycles'] or any(b['cycles']<=a['cycles'] for a,b in zip(rows,rows[1:])):
            raise ValueError('Unordered result LCD access evidence')
    return services


def compare_accounting(data,native,services,irqs,polls,writes,summary,epoch):
    original_services=analyze(data)
    if [len(x) for x in (native,services,irqs,polls,writes,summary)]!=[len(data['points']),len(original_services),len(data['interrupts']),len(data['polls']),len(data['writes']),1]:
        raise ValueError('Incomplete native accounting/access coverage')
    differences=[]
    def check(category,index,target,row):
        delta={k:[v,int(row[k])] for k,v in target.items() if int(row[k])!=v}
        if delta:differences.append(dict(category=category,index=index,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if q['boundary']!=p['name']:raise ValueError('Reordered native accounting boundaries')
        target={k:p[k] for k in ('tick','countdown','pay','savings','seconds','stage','musicEnabled')}
        if data['version']==2:target.update({k:p[k] for k in ('skip','inputHeld','inputPressed')})
        target['cycle']=p['cycles']-epoch;check('boundary',i,target,q)
    for i,(p,q) in enumerate(zip(original_services,services)):
        w=vblank_work(p);target=dict(service=33+i,cycle=p['start']-epoch,tick=p['tick'],countdown=max(1,p['countdown']-1),display=w['display'],
            effects=w['effects'],music=w['music'],musicEnabled=p['musicEnabled'],inputHeld=p['held'])
        if data['version']==2:target['inputPressed']=p['pressed']
        check('service',i,target,q)
    for i,(p,q) in enumerate(zip(data['interrupts'],irqs)):
        owner=2 if p['returnAddress']==0x261d else 1
        if q['kind']!=p['kind'] or int(q['owner'])!=owner:raise ValueError('Unowned/reordered accounting vector')
        check('interrupt',i,dict(vectorCycle=p['start']-epoch),q)
    for name,rows,keys in [('poll',polls,['mode']),('write',writes,['address','value'])]:
        for i,(p,q) in enumerate(zip(data['polls' if name=='poll' else 'writes'],rows)):
            check(name,i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in keys}),q)
    end=data['points'][-1];target={k:end[k] for k in ('tick','countdown','pay','savings','seconds','stage')}
    target.update(end=end['cycles']-epoch,displays=33+len(original_services),stats=33+len(data['interrupts'])-len(original_services));check('summary',0,target,summary[0])
    return differences


def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    data=json.loads((args.out/'accounting.json').read_text());startup=json.loads((args.startup/'startup.json').read_text())
    for item in (data,startup):require_capture_reference(manifest,item)
    if manifest['controlDifferences'] or any(item.get(k)!=manifest.get(k) for item in (data,startup) for k in ('romSha256','controlMemorySha256')):
        raise ValueError('Mixed successful accounting controls')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
    native=rows(args.native_csv);services=rows(args.native_csv.with_suffix('.services.csv'));irqs=rows(args.native_csv.with_suffix('.interrupts.csv'))
    polls=rows(args.native_csv.with_suffix('.polls.csv'));writes=rows(args.native_csv.with_suffix('.writes.csv'));summary=rows(args.native_csv.with_suffix('.summary.csv'))
    differences=compare_accounting(data,native,services,irqs,polls,writes,summary,epoch)
    result=dict(comparedBoundaries=len(native),comparedServices=len(services),comparedInterrupts=len(irqs),comparedPolls=len(polls),comparedWrites=len(writes),
        differences=len(differences),firstDifference=differences[0] if differences else None,productionSchedulerAccepted=False,
        evidenceLimit='Complete ordinary successful Air accounting for the supplied control, including fresh input/skip state when version 2, ledger/timer/stage state, scalar LCD readiness and intended glyph writes. Excludes perfect/final-life/reset results, new gameplay, pixels/PCM, unobserved interruptions and production integration.')
    write_json(args.native_csv.with_suffix('.comparison.json'),result);print(json.dumps(result,indent=2))
    if differences:raise ValueError('Native successful accounting differs from the original')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    diff=sub.add_parser('compare');diff.add_argument('native_csv',type=Path);diff.add_argument('--startup',type=Path,required=True)
    for command in (record,diff):
        command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)
