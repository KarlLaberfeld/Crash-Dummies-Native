"""Read-only original result-cleared instruction header through its first wait.

Only capture uses the separately authorized pinned reference emulator. The
native replay inherits its own campaign, time and publication state.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work,VBLANK_FIXED,vblank_bookkeeping_work,elapsed_work
from air_loop_timing import stat_cycles
from air_following_scope import FollowingAirCaptureScope

POINTS={0x02ce:'begin',0x02e4:'playerLabelReady',0x02e7:'livesReady',0x02ee:'livesClamped',0x02f2:'livesPrinted',
    0x02fb:'stageLabelReady',0x02fe:'stageReady',0x0302:'stagePrinted',0x0312:'difficultyLabelReady',
    0x0315:'difficultyReady',0x0319:'difficultyPrinted',0x031c:'end'}

def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or hashlib.sha256(read_rom(args.rom)).hexdigest()!=manifest['romSha256']:raise ValueError('Changed original control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0)
    scope=FollowingAirCaptureScope(getattr(args,'following',False))
    active=False;complete=False;points=[];irqs=[];opened=None;polls=[];writes=[];buttons=[]
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,opened
        if complete:return
        scope.observe(pc,p.memory[0xc098],len(buttons))
        if pc==0x2436 and (scope.samples(p.memory[0xc098]) if scope.following else p.memory[0xc098] in (2,10)):buttons.append(p.memory[0xff8a])
        if pc==0x02ce and scope.ready and p.memory[0xc098] in (2,10):active=True
        if not active:return
        now=p._cycles()
        if pc in POINTS:
            player=p.memory[0xc082];points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),
                player=player,stage=p.memory[0xc088+player*8],difficulty=p.memory[0xc089+player*8],lives=p.memory[0xc08a+player*8],
                display=p.memory[0xc098],result=p.memory[0xc095],musicEnabled=p.memory[0xffcf],
                inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b]))
            if pc==0x031c:active=False;complete=True
        elif pc in (0x0040,0x0048):
            if opened:raise ValueError('Nested header interrupt')
            opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],
                returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and opened and opened['kind']=='vblank':
            name=IRQ_PHASES[pc];opened['phases'][name]=now
            if name=='display':opened.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b])
            if name=='bookkeeping':opened.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
            if name=='effects':opened['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if name=='music':opened['musicEnabled']=p.memory[0xffcf]
        elif pc in (0x2484,0x2555) and opened:
            if opened['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Mismatched header return')
            opened['end']=now;irqs.append(opened);opened=None
        elif pc==0x2123:polls.append(dict(cycles=now,mode=p.register_file.A&3))
        elif pc==0x2128:writes.append(dict(cycles=now,address=256*p.register_file.D+p.register_file.E,value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in (*POINTS,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x2123,0x2128,0x268b,0x03d8,0x0462):p.hook_register(0,pc,hook,pc)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            elif e[0] in ('press','release'):getattr(p,'button_'+e[0])(e[1])
            else:raise ValueError('Unknown original event')
        digest=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or opened or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete header or changed control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,
        precedingDisplays=len(buttons)-sum(r['kind']=='vblank' for r in irqs)-scope.display_offset,points=points,interrupts=irqs,polls=polls,writes=writes)
    if scope.following:data['followingResult']=True
    analyze(data);args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'header.json',data)
    (args.out/'buttons.txt').write_text(''.join(str(b)+'\n' for b in buttons))
    print(json.dumps(dict(boundaries=len(points),interrupts=len(irqs),polls=len(polls),writes=len(writes),begin=points[0],end=points[-1],controlDifferences=0),indent=2))

def analyze(data):
    points=data.get('points',[]);irqs=data.get('interrupts',[])
    if data.get('version')!=1 or [p['name'] for p in points]!=list(POINTS.values()) or not isinstance(data.get('precedingDisplays'),int) or data['precedingDisplays']<0:raise ValueError('Incomplete header boundaries')
    first=points[0];perfect=first['display']==2;previous=first['inputHeld'];services=[];last=first['cycles']
    if first['player'] not in (0,1) or not 0<=first['stage']<5 or not 0<=first['difficulty']<4 or not 1<=first['lives']<=255:raise ValueError('Invalid header campaign')
    for p in points:
        if any(p[k]!=first[k] for k in ('player','stage','difficulty','lives','display')) or p['result'] or p['musicEnabled'] or first['display'] not in (2,10):raise ValueError('Unowned header campaign mutation')
        if (p['inputHeld']&15)==15 or p['inputPressed']&~p['inputHeld']:raise ValueError('Unowned header input/reset')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Reordered header boundaries')
    for r in irqs:
        if not last<=r['start']<r['end'] or r['end']+16>points[-1]['cycles']:raise ValueError('Incomplete header IRQ extent')
        last=r['end']+16
        if r['kind']=='stat':
            if r['selector']!=(4 if perfect else 0) or r['end']-r['start']!=stat_cycles(r['selector']):raise ValueError('Unowned header STAT')
        elif r['kind']=='vblank':
            wanted={**VBLANK_FIXED,'display':(228 if r['countdown']==1 else 272)+(68 if perfect else 0),
                'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched']),'effects':64,'music':60}
            if vblank_work(r)!=wanted or r['effectRequest']!=-1 or r['musicEnabled'] or r['pressed']!=r['held']&~previous or (r['held']&15)==15:raise ValueError('Unowned header display/input/audio')
            previous=r['held'];services.append(r)
        else:raise ValueError('Unknown header IRQ')
    if not services or (points[-1]['tick']-first['tick'])%65536!=len(services):raise ValueError('Missing header counter services')
    costs={'playerLabelReady':88,'livesReady':28 if first['lives']<9 else 32,'stageLabelReady':88,'difficultyLabelReady':88}
    for a,b in zip(points,points[1:]):
        if a['name'] in costs and elapsed_work(a['cycles'],b['cycles'],irqs)!=costs[a['name']]:raise ValueError('Header primitive work differs')
    for key in ('polls','writes'):
        rows=data.get(key,[])
        if not rows or any(not first['cycles']<=r['cycles']<points[-1]['cycles'] for r in rows) or any(b['cycles']<=a['cycles'] for a,b in zip(rows,rows[1:])):raise ValueError('Missing/reordered header accesses')
    if any(r['mode'] not in (0,1,2,3) for r in data['polls']) or any(not 0x9800<=r['address']<0x9c00 or not 0<=r['value']<=127 for r in data['writes']):raise ValueError('Invalid header access')
    return services

def compare_header(data,points,services,irqs,polls,writes,summary,epoch):
    expected_services=analyze(data);differences=[]
    if [len(r) for r in (points,services,irqs,polls,writes,summary)]!=[len(data['points']),len(expected_services),len(data['interrupts']),len(data['polls']),len(data['writes']),1]:raise ValueError('Incomplete native header coverage')
    def check(category,index,expected,row):
        delta={k:[v,int(row[k])] for k,v in expected.items() if int(row[k])!=v}
        if delta:differences.append(dict(category=category,index=index,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],points)):
        if q['boundary']!=p['name']:raise ValueError('Reordered native header')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in ('tick','countdown','player','stage','difficulty','inputHeld','inputPressed')}),q)
    for i,(p,q) in enumerate(zip(expected_services,services)):
        w=vblank_work(p);check('service',i,dict(service=data['precedingDisplays']+i,cycle=p['start']-epoch,tick=p['tick'],countdown=max(1,p['countdown']-1),
            display=w['display'],effects=w['effects'],music=w['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
        if i and int(q['service'])!=int(services[i-1]['service'])+1:raise ValueError('Reordered header services')
    for i,(p,q) in enumerate(zip(data['interrupts'],irqs)):
        if q['kind']!=p['kind'] or int(q['owner'])!=(2 if p['returnAddress']==0x261d else 1):raise ValueError('Unowned header IRQ')
        check('interrupt',i,dict(vectorCycle=p['start']-epoch),q)
    for key,rows,fields in [('polls',polls,('mode',)),('writes',writes,('address','value'))]:
        for i,(p,q) in enumerate(zip(data[key],rows)):check(key,i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in fields}),q)
    end=data['points'][-1];check('summary',0,dict(end=end['cycles']-epoch,tick=end['tick'],countdown=end['countdown']),summary[0])
    if int(summary[0]['displays'])!=int(services[-1]['service'])+1:raise ValueError('Header terminal service differs')
    return differences

def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'header.json').read_text())
    startup=json.loads((args.startup/'startup.json').read_text())
    for recording in (data,startup):
        require_capture_reference(manifest,recording)
        if any(recording[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed original header controls')
    if manifest['controlDifferences']:raise ValueError('Changed original control')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    path=args.native_csv;values=[rows(path)]+[rows(path.with_suffix('.'+key+'.csv')) for key in ('services','interrupts','polls','writes','summary')]
    differences=compare_header(data,*values,epoch)
    report=dict(comparedBoundaries=len(values[0]),comparedServices=len(values[1]),comparedInterrupts=len(values[2]),comparedPolls=len(values[3]),
        comparedWrites=len(values[4]),differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,
        evidenceLimit='Native result-cleared player/lives/stage/difficulty header and first wait through 031c. Excludes instruction music/text/fades, next LCD/gameplay setup, full pixels/PCM and production integration.')
    write_json(path.with_suffix('.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native instruction header differs')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--following',action='store_true')
    verify=sub.add_parser('compare');verify.add_argument('native_csv',type=Path);verify.add_argument('--startup',type=Path,required=True)
    for command in (record,verify):command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
