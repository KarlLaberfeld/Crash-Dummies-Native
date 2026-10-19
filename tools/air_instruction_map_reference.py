"""Independent subsequent instruction map-transition capture and full comparison."""
import argparse,csv,hashlib,json
from pathlib import Path
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work,VBLANK_FIXED,vblank_bookkeeping_work,elapsed_work
from air_following_scope import FollowingAirCaptureScope

NAMES=['begin','lineWait','objectsDisabled','scrollCleared','callbacksReady','enabled','compareReady','mapJump','mapBegin']
NAMES+=['stepWait','stepReady','mapWrite','stepComplete']*64+['mapReturn','end']
FIELDS=('tick','countdown','lcdc','lyc','scroll','alternate','display','stat','inputHeld','inputPressed')

def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or hashlib.sha256(read_rom(args.rom)).hexdigest()!=manifest['romSha256']:raise ValueError('Changed original control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0)
    scope=FollowingAirCaptureScope(getattr(args,'following',False))
    active=False;complete=False;points=[];irqs=[];opened=None;polls=[];buttons=[]
    names={0x268b:'begin',0x2691:'lineWait',0x2699:'objectsDisabled',0x269e:'scrollCleared',0x26a3:'callbacksReady',
        0x26a7:'enabled',0x26ab:'compareReady',0x26af:'mapJump',0x16c1:'mapBegin',0x16d2:'stepWait',0x16d5:'stepReady',
        0x16da:'mapWrite',0x16dc:'stepComplete',0x16e2:'mapReturn',0x0a0a:'end',0x0c7a:'end'}
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,opened
        if complete:return
        scope.observe(pc,p.memory[0xc098],len(buttons))
        if pc==0x2436 and (scope.samples(p.memory[0xc098]) if scope.following else (p.memory[0xc098] in (2,10) or active and p.memory[0xc098]==5)):buttons.append(p.memory[0xff8a])
        if pc==0x268b and scope.ready and p.memory[0xc098] in (2,10):active=True
        if not active:return
        now=p._cycles();stage=p.memory[0xc088+8*p.memory[0xc082]]
        if pc in names and (pc not in (0x0a0a,0x0c7a) or stage==(1 if pc==0x0a0a else 2)):
            points.append(dict(name=names[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),lcdc=p.memory[0xff40],lyc=p.memory[0xff45],
                scroll=p.memory[0xc09c],alternate=p.memory[0xc09d],display=p.memory[0xc098],stat=p.memory[0xc099],
                inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b]))
            if names[pc]=='end':active=False;complete=True
        elif pc in (0x0040,0x0048):
            if opened:raise ValueError('Nested map interrupt')
            opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],display=p.memory[0xc098],
                returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and opened and opened['kind']=='vblank':
            name=IRQ_PHASES[pc];opened['phases'][name]=now
            if name=='display':opened.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b])
            if name=='bookkeeping':opened.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
            if name=='effects':opened['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if name=='music':opened['musicEnabled']=p.memory[0xffcf]
        elif pc in (0x2484,0x2555) and opened:
            if opened['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Mismatched map interrupt')
            opened['end']=now;irqs.append(opened);opened=None
        elif pc==0x2627:polls.append(dict(cycles=now,ly=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in (*names,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x2627,0x03d8,0x0462):p.hook_register(0,pc,hook,pc)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            elif e[0] in ('press','release'):getattr(p,'button_'+e[0])(e[1])
            else:raise ValueError('Unknown original event')
        digest=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or opened or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete map or changed control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,
        precedingDisplays=len(buttons)-sum(r['kind']=='vblank' for r in irqs)-scope.display_offset,points=points,interrupts=irqs,polls=polls)
    if scope.following:data['followingResult']=True
    analyze(data);args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'transition.json',data)
    (args.out/'buttons.txt').write_text(''.join(str(b)+'\n' for b in buttons))
    print(json.dumps(dict(boundaries=len(points),interrupts=len(irqs),polls=len(polls),mapWrites=64,controlDifferences=0),indent=2))

def analyze(data):
    points=data.get('points',[]);irqs=data.get('interrupts',[]);polls=data.get('polls',[])
    if data.get('version')!=1 or [p['name'] for p in points]!=NAMES or not isinstance(data.get('precedingDisplays'),int) or data['precedingDisplays']<0:raise ValueError('Incomplete map boundaries')
    first=points[0];perfect=first['display']==2;previous=first['inputHeld'];services=[];last=first['cycles']
    if first['display'] not in (2,10) or first['stat']!=(4 if perfect else 0) or first['alternate']!=1 or first['lyc'] not in (120,143):raise ValueError('Unowned map entry')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Reordered map boundaries')
    for i,p in enumerate(points):
        inherited_scroll=first['scroll'] if data.get('followingResult') is True and i<3 else 0
        if not 0<=p['scroll']<=255 or p['scroll']!=inherited_scroll or p['alternate']!=1 or (p['inputHeld']&15)==15 or p['inputPressed']&~p['inputHeld']:raise ValueError('Unowned map mutation/reset')
        if p['display']!=(5 if i>=4 else first['display']) or p['stat']!=(5 if i>=5 else first['stat']) or p['lyc']!=(95 if i>=6 else first['lyc']):raise ValueError('Unowned map callback transition')
        if i>=2 and p['lcdc']&2:raise ValueError('Objects remain enabled during map transition')
        if i>=4 and p['countdown']!=points[4]['countdown']:raise ValueError('Instruction countdown changed after callback replacement')
    immediate=[]
    for r in irqs:
        if not last<=r['start']<r['end'] or r['end']+16>points[-1]['cycles']:raise ValueError('Incomplete map IRQ extent')
        last=r['end']+16
        if points[2]['cycles']<r['start']<points[6]['cycles']:raise ValueError('Unowned callback critical crossing')
        if r['kind']=='stat':
            if r['selector']!=(5 if r['start']>points[5]['cycles'] else first['stat']):raise ValueError('Unowned map STAT selector')
            cost=248 if r['selector']==0 else 288 if r['selector'] in (4,5) else -1
            if r['end']-r['start']!=cost:raise ValueError('Unowned map STAT')
            if points[6]['cycles']<r['start']<points[7]['cycles']:immediate.append(r)
        elif r['kind']=='vblank':
            display=(228 if r['countdown']==1 else 272)+(68 if perfect else 0) if r['display']==first['display'] else 144 if r['display']==5 else -1
            wanted={**VBLANK_FIXED,'display':display,'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched']),'effects':64}
            w=vblank_work(r)
            if any(w[k]!=v for k,v in wanted.items()) or w['music']<60 or r['effectRequest']!=-1 or not r['musicEnabled'] or r['pressed']!=r['held']&~previous or (r['held']&15)==15:raise ValueError('Unowned map display/input/audio')
            previous=r['held'];services.append(r)
        else:raise ValueError('Unknown map IRQ')
    if len(immediate)!=1 or immediate[0]['selector']!=5 or immediate[0]['start']!=points[6]['cycles']+40:raise ValueError('Missing identified STAT-write request')
    if not services or (points[-1]['tick']-first['tick'])%65536!=len(services):raise ValueError('Missing map counter services')
    for index,cost in ((0,28),(2,24),(3,24),(4,20),(5,20),(6,20),(7,16)):
        if elapsed_work(points[index]['cycles'],points[index+1]['cycles'],irqs)!=cost:raise ValueError('Map primitive differs')
    if not polls or any(b['cycles']<=a['cycles'] for a,b in zip(polls,polls[1:])) or any(not points[1]['cycles']<p['cycles']<points[2]['cycles'] or not 0<=p['ly']<=153 for p in polls) or polls[-1]['ly']!=144 or any(p['ly']==144 for p in polls[:-1]):raise ValueError('Incomplete map LY equality wait')
    for i in range(64):
        wait=points[9+4*i]
        ready,before,after=points[10+4*i:13+4*i]
        if sum(wait['cycles']<r['start']<ready['cycles'] for r in services)!=1:raise ValueError('Missing map-step display wait')
        if elapsed_work(ready['cycles'],before['cycles'],irqs)!=24 or elapsed_work(before['cycles'],after['cycles'],irqs)!=12 or after['lcdc']&~8!=before['lcdc']&~8:raise ValueError('Map write primitive differs')
    return services

def compare_map(data,points,services,irqs,polls,summary,epoch):
    expected_services=analyze(data);differences=[]
    if [len(r) for r in (points,services,irqs,polls,summary)]!=[len(data['points']),len(expected_services),len(data['interrupts']),len(data['polls']),1]:raise ValueError('Incomplete native map coverage')
    def check(category,index,expected,row):
        delta={k:[v,int(row[k])] for k,v in expected.items() if int(row[k])!=v}
        if delta:differences.append(dict(category=category,index=index,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],points)):
        if q['boundary']!=p['name']:raise ValueError('Reordered native map')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in FIELDS}),q)
    for i,(p,q) in enumerate(zip(expected_services,services)):
        w=vblank_work(p);check('service',i,dict(service=data['precedingDisplays']+i,cycle=p['start']-epoch,tick=p['tick'],
            countdown=p['countdown'] if p['display']==5 else max(1,p['countdown']-1),display=w['display'],effects=w['effects'],music=w['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],irqs)):
        owner=2 if p['returnAddress']==0x261d else 1
        if q['kind']!=p['kind'] or int(q['owner'])!=owner:raise ValueError('Unowned map IRQ')
        check('interrupt',i,dict(vectorCycle=p['start']-epoch),q)
    for i,(p,q) in enumerate(zip(data['polls'],polls)):check('poll',i,dict(cycle=p['cycles']-epoch,ly=p['ly']),q)
    end=data['points'][-1];check('summary',0,dict(end=end['cycles']-epoch,tick=end['tick'],countdown=end['countdown']),summary[0])
    if int(summary[0]['displays'])!=int(services[-1]['service'])+1:raise ValueError('Map terminal service differs')
    return differences

def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'transition.json').read_text());startup=json.loads((args.startup/'startup.json').read_text())
    for recording in (data,startup):
        require_capture_reference(manifest,recording)
        if any(recording[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed map controls')
    if manifest['controlDifferences']:raise ValueError('Changed original control')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    path=args.native_csv;values=[rows(path)]+[rows(path.with_suffix('.'+key+'.csv')) for key in ('services','interrupts','polls','summary')]
    differences=compare_map(data,*values,epoch)
    report=dict(comparedBoundaries=len(values[0]),comparedServices=len(values[1]),comparedInterrupts=len(values[2]),comparedPolls=len(values[3]),
        mapWrites=64,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,
        evidenceLimit='Subsequent instruction callback/LYC/STAT-write transition and all 64 map selections, through timed-text entry. Excludes full pixels/hardware, timed text/exit, initial instruction and production scheduling.')
    write_json(path.with_suffix('.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native instruction map differs')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--following',action='store_true')
    verify=sub.add_parser('compare');verify.add_argument('native_csv',type=Path);verify.add_argument('--startup',type=Path,required=True)
    for command in (record,verify):command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
