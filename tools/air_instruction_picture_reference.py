"""Independent original 031c..268b music/tile/picture prefix; local capture only."""
import argparse,csv,hashlib,json
from pathlib import Path
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work,VBLANK_FIXED,vblank_bookkeeping_work,elapsed_work
from air_loop_timing import stat_cycles
from air_following_scope import instruction_capture_scope

NAMES=['begin','musicReady','stageReady','tableDispatch','resourceEntry','copyCall','copyReturned','rectangleReady','end']

def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or hashlib.sha256(read_rom(args.rom)).hexdigest()!=manifest['romSha256']:raise ValueError('Changed original control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0)
    scope=instruction_capture_scope(args)
    active=False;complete=False;points=[];irqs=[];opened=None;polls=[];writes=[];buttons=[]
    entries={0x09ee:('resourceEntry',1),0x0c5e:('resourceEntry',2),0x09f9:('copyCall',1),0x0c69:('copyCall',2),
        0x09fc:('copyReturned',1),0x0c6c:('copyReturned',2),0x0a07:('rectangleReady',1),0x0c77:('rectangleReady',2)}
    common={0x031c:'begin',0x0321:'musicReady',0x0324:'stageReady',0x0328:'tableDispatch',0x268b:'end'}
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,opened
        if complete:return
        scope.observe(pc,p.memory[0xc098],len(buttons))
        if pc==0x2436 and (scope.samples(p.memory[0xc098]) if scope.following else p.memory[0xc098] in (2,10)):buttons.append(p.memory[0xff8a])
        if pc==0x031c and scope.ready and p.memory[0xc098] in (2,10):active=True
        if not active:return
        now=p._cycles();stage=p.memory[0xc088+8*p.memory[0xc082]]
        if pc in common or (pc in entries and entries[pc][1]==stage):
            name=common[pc] if pc in common else entries[pc][0]
            points.append(dict(name=name,cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),stage=stage,
                display=p.memory[0xc098],result=p.memory[0xc095],musicEnabled=p.memory[0xffcf],
                inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b]))
            if pc==0x268b:active=False;complete=True
        elif pc in (0x0040,0x0048):
            if opened:raise ValueError('Nested picture interrupt')
            opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],returnAddress=word(p.register_file.SP),
                tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and opened and opened['kind']=='vblank':
            name=IRQ_PHASES[pc];opened['phases'][name]=now
            if name=='display':opened.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b])
            if name=='bookkeeping':opened.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
            if name=='effects':opened['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if name=='music':opened['musicEnabled']=p.memory[0xffcf]
        elif pc in (0x2484,0x2555) and opened:
            if opened['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Mismatched picture return')
            opened['end']=now;irqs.append(opened);opened=None
        elif pc in (0x2363,0x2123):polls.append(dict(cycles=now,mode=p.register_file.A&3,lcd=p.lcd_snapshot()))
        elif pc in (0x2368,0x2128):writes.append(dict(kind='tile' if pc==0x2368 else 'map',cycles=now,
            address=256*p.register_file.D+p.register_file.E,value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in (*common,*entries,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x2363,0x2123,0x2368,0x2128,0x03d8,0x0462):p.hook_register(0,pc,hook,pc)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            elif e[0] in ('press','release'):getattr(p,'button_'+e[0])(e[1])
            else:raise ValueError('Unknown original event')
        digest=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or opened or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete picture or changed control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,
        precedingDisplays=len(buttons)-sum(r['kind']=='vblank' for r in irqs)-scope.display_offset,points=points,interrupts=irqs,polls=polls,writes=writes)
    if scope.following:data['followingResult']=True
    if scope.following and scope.retry==2:data['afterRetry']=2
    analyze(data);args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'picture.json',data)
    (args.out/'buttons.txt').write_text(''.join(str(b)+'\n' for b in buttons))
    print(json.dumps(dict(boundaries=len(points),interrupts=len(irqs),polls=len(polls),writes=len(writes),begin=points[0],end=points[-1],controlDifferences=0),indent=2))

def analyze(data):
    points=data.get('points',[]);irqs=data.get('interrupts',[])
    if data.get('version')!=1 or [p['name'] for p in points]!=NAMES or not isinstance(data.get('precedingDisplays'),int) or data['precedingDisplays']<0:raise ValueError('Incomplete picture boundaries')
    first=points[0];perfect=first['display']==2;previous=first['inputHeld'];services=[];last=first['cycles']
    if first['stage'] not in (1,2) or first['display'] not in (2,10):raise ValueError('Unowned picture campaign')
    for i,p in enumerate(points):
        if p['stage']!=first['stage'] or p['display']!=first['display'] or p['result'] or bool(p['musicEnabled'])!=bool(i):raise ValueError('Unowned picture campaign/audio mutation')
        if (p['inputHeld']&15)==15 or p['inputPressed']&~p['inputHeld']:raise ValueError('Unowned picture input/reset')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Reordered picture boundaries')
    if any(r['start']<points[1]['cycles'] for r in irqs):raise ValueError('Interrupted music reset requires a separate owner')
    for r in irqs:
        if not last<=r['start']<r['end'] or r['end']+16>points[-1]['cycles']:raise ValueError('Incomplete picture IRQ extent')
        last=r['end']+16
        if r['kind']=='stat':
            if r['selector']!=(4 if perfect else 0) or r['end']-r['start']!=stat_cycles(r['selector']):raise ValueError('Unowned picture STAT')
        elif r['kind']=='vblank':
            wanted={**VBLANK_FIXED,'display':(228 if r['countdown']==1 else 272)+(68 if perfect else 0),
                'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched']),'effects':64}
            w=vblank_work(r)
            if any(w[k]!=v for k,v in wanted.items()) or w['music']<60 or r['effectRequest']!=-1 or not r['musicEnabled'] or r['pressed']!=r['held']&~previous or (r['held']&15)==15:raise ValueError('Unowned picture display/input/audio')
            previous=r['held'];services.append(r)
        else:raise ValueError('Unknown picture IRQ')
    if not services or (points[-1]['tick']-first['tick'])%65536!=len(services):raise ValueError('Missing picture counter services')
    costs={'musicReady':88,'stageReady':20,'tableDispatch':96,'resourceEntry':44,'rectangleReady':24}
    for a,b in zip(points,points[1:]):
        if a['name'] in costs and elapsed_work(a['cycles'],b['cycles'],irqs)!=costs[a['name']]:raise ValueError('Picture primitive work differs: '+a['name'])
    for key in ('polls','writes'):
        rows=data.get(key,[])
        if not rows or any(not first['cycles']<=r['cycles']<points[-1]['cycles'] for r in rows) or any(b['cycles']<=a['cycles'] for a,b in zip(rows,rows[1:])):raise ValueError('Missing/reordered picture accesses')
    tiles=[r for r in data['writes'] if r['kind']=='tile'];maps=[r for r in data['writes'] if r['kind']=='map']
    if len(tiles)!=1024 or any(r['address']!=0x8340+i for i,r in enumerate(tiles)) or len(maps)!=90 or any(r['address']!=0x9800+(3+i//10)*32+5+i%10 for i,r in enumerate(maps)):raise ValueError('Missing picture destinations')
    if any(r['mode'] not in (0,1,2,3) for r in data['polls']) or any(not 0<=r['value']<=255 for r in data['writes']):raise ValueError('Invalid picture access')
    return services

def compare_picture(data,points,services,irqs,polls,writes,summary,epoch):
    expected_services=analyze(data);differences=[]
    if [len(r) for r in (points,services,irqs,polls,writes,summary)]!=[len(data['points']),len(expected_services),len(data['interrupts']),len(data['polls']),len(data['writes']),1]:raise ValueError('Incomplete native picture coverage')
    def check(category,index,expected,row):
        delta={k:[v,int(row[k])] for k,v in expected.items() if int(row[k])!=v}
        if delta:differences.append(dict(category=category,index=index,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],points)):
        if q['boundary']!=p['name']:raise ValueError('Reordered native picture')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in ('tick','countdown','musicEnabled','inputHeld','inputPressed')}),q)
    for i,(p,q) in enumerate(zip(expected_services,services)):
        w=vblank_work(p);check('service',i,dict(service=data['precedingDisplays']+i,cycle=p['start']-epoch,tick=p['tick'],countdown=max(1,p['countdown']-1),
            display=w['display'],effects=w['effects'],music=w['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],irqs)):
        if q['kind']!=p['kind'] or int(q['owner'])!=1:raise ValueError('Unowned picture IRQ')
        check('interrupt',i,dict(vectorCycle=p['start']-epoch),q)
    for key,rows,fields in [('polls',polls,('mode',)),('writes',writes,('address','value'))]:
        for i,(p,q) in enumerate(zip(data[key],rows)):
            if key=='writes' and p['kind']!=q['kind']:raise ValueError('Reordered native picture destination')
            check(key,i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in fields}),q)
    end=data['points'][-1];check('summary',0,dict(end=end['cycles']-epoch,tick=end['tick'],countdown=end['countdown']),summary[0])
    if int(summary[0]['displays'])!=int(services[-1]['service'])+1:raise ValueError('Picture terminal service differs')
    return differences

def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'picture.json').read_text());startup=json.loads((args.startup/'startup.json').read_text())
    for recording in (data,startup):
        require_capture_reference(manifest,recording)
        if any(recording[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed original picture controls')
    if manifest['controlDifferences']:raise ValueError('Changed original control')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    path=args.native_csv;values=[rows(path)]+[rows(path.with_suffix('.'+key+'.csv')) for key in ('services','interrupts','polls','writes','summary')]
    differences=compare_picture(data,*values,epoch)
    report=dict(comparedBoundaries=len(values[0]),comparedServices=len(values[1]),comparedInterrupts=len(values[2]),comparedPolls=len(values[3]),
        comparedWrites=len(values[4]),differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,
        evidenceLimit='Native instruction music, 1024 tile bytes and 90 picture-map glyphs through transition entry 268b. Excludes bus acceptance/full pictures/PCM, map transition, timed text/exit, next gameplay setup and production integration.')
    write_json(path.with_suffix('.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native instruction picture differs')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--following',action='store_true')
    record.add_argument('--after-retry',type=int,choices=(1,2),default=1)
    verify=sub.add_parser('compare');verify.add_argument('native_csv',type=Path);verify.add_argument('--startup',type=Path,required=True)
    for command in (record,verify):command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
