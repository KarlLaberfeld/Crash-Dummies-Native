"""Independent bounded instruction typing/scrolling/skip comparison through 032b."""
import argparse,csv,hashlib,json
from pathlib import Path
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work,VBLANK_FIXED,vblank_bookkeeping_work,elapsed_work
from air_following_scope import FollowingAirCaptureScope

POINTS={0x0a0a:'begin',0x0c7a:'begin',0x032b:'end',0x214f:'textNext',0x2166:'glyphWait',0x2169:'glyphReady',0x217f:'delayExpired',
    0x2186:'skip',0x2219:'scrollBegin',0x2223:'scrollWait',0x2229:'scrollReady',0x222d:'scrollStored',0x2230:'scrollEnd',0x21c0:'textFinish'}
FIELDS=('tick','countdown','scroll','speed','skipMask','layer','inputHeld','inputPressed')

def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or hashlib.sha256(read_rom(args.rom)).hexdigest()!=manifest['romSha256']:raise ValueError('Changed original control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0)
    scope=FollowingAirCaptureScope(getattr(args,'following',False))
    active=False;armed=False;complete=False;points=[];irqs=[];opened=None;polls=[];writes=[];buttons=[];campaign=None
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,armed,complete,opened,campaign
        if complete:return
        scope.observe(pc,p.memory[0xc098],len(buttons))
        if pc==0x268b and p.memory[0xc098] in (2,10):armed=True
        if pc==0x2436 and (scope.samples(p.memory[0xc098]) if scope.following else (p.memory[0xc098] in (2,10) or armed and p.memory[0xc098]==5)):buttons.append(p.memory[0xff8a])
        if pc in (0x0a0a,0x0c7a) and scope.ready and armed and p.memory[0xc098]==5:
            active=True;player=p.memory[0xc082];campaign=dict(player=player,stage=p.memory[0xc088+8*player],difficulty=p.memory[0xc089+8*player])
        if not active:return
        now=p._cycles()
        if pc in POINTS:
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),scroll=p.memory[0xc09c],speed=p.memory[0xc03a],
                delay=p.memory[0xc039],skipMask=p.memory[0xc03b],layer=p.memory[0xc035],column=p.register_file.C,row=p.register_file.B,
                inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b]))
            if pc==0x2186:
                pointer=p.register_file.HL;player=campaign['player'];level=campaign['difficulty']
                points[-1]['skipContext']=1 if 0x2272+6*player<=pointer<=0x2276+6*player else 2 if 0x2297+3*level<=pointer<=0x2298+3*level else 0
            if pc==0x032b:active=False;complete=True
        elif pc in (0x0040,0x0048):
            if opened:raise ValueError('Nested text interrupt')
            opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],display=p.memory[0xc098],returnAddress=word(p.register_file.SP),
                tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and opened and opened['kind']=='vblank':
            name=IRQ_PHASES[pc];opened['phases'][name]=now
            if name=='display':opened.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b])
            if name=='bookkeeping':opened.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
            if name=='effects':opened['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if name=='music':opened['musicEnabled']=p.memory[0xffcf]
        elif pc in (0x2484,0x2555) and opened:
            if opened['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Mismatched text interrupt')
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
    if not complete or opened or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete text or changed control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,campaign=campaign,
        precedingDisplays=len(buttons)-sum(r['kind']=='vblank' for r in irqs)-scope.display_offset,points=points,interrupts=irqs,polls=polls,writes=writes)
    if scope.following:data['followingResult']=True
    analyze(data);args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'text.json',data)
    (args.out/'buttons.txt').write_text(''.join(str(b)+'\n' for b in buttons))
    print(json.dumps(dict(boundaries=len(points),interrupts=len(irqs),polls=len(polls),writes=len(writes),controlDifferences=0),indent=2))

def analyze(data):
    points=data.get('points',[]);irqs=data.get('interrupts',[]);polls=data.get('polls',[]);writes=data.get('writes',[])
    campaign=data.get('campaign',{})
    if data.get('version')!=1 or campaign.get('stage') not in (1,2) or campaign.get('difficulty') not in range(4) or campaign.get('player') not in (0,1):raise ValueError('Unowned text campaign')
    if not isinstance(data.get('precedingDisplays'),int) or data['precedingDisplays']<0 or len(points)<3 or points[0]['name']!='begin' or points[-2]['name']!='textFinish' or points[-1]['name']!='end':raise ValueError('Incomplete text boundaries')
    if any(p['name'] not in POINTS.values() for p in points) or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])) or any(sum(p['name']==name for p in points)!=1 for name in ('begin','textFinish','end')):raise ValueError('Reordered/unknown text boundaries')
    first=points[0];last=first['cycles'];previous=first['inputHeld'];services=[];skip=False
    for p in points:
        if p['countdown']!=first['countdown'] or p['layer']!=152 or p['speed'] not in (0,5) or p['skipMask'] not in (0,8) or (p['inputHeld']&15)==15 or p['inputPressed']&~p['inputHeld']:raise ValueError('Unowned text mutation/reset')
        if p['name']=='skip':
            if skip or not p['inputPressed']&8 or p.get('skipContext') not in (0,1,2):raise ValueError('Unowned text skip')
            skip=True
    if points[-1]['speed'] or points[-1]['skipMask']:raise ValueError('Text termination did not clear speed/skip mask')
    for r in irqs:
        if not last<=r['start']<r['end'] or r['end']+16>points[-1]['cycles']:raise ValueError('Incomplete text IRQ extent')
        last=r['end']+16
        if r['selector']!=5:raise ValueError('Unowned text STAT selector')
        if r['kind']=='stat':
            if r['end']-r['start']!=288:raise ValueError('Unowned text STAT work')
        elif r['kind']=='vblank':
            w=vblank_work(r);wanted={**VBLANK_FIXED,'display':144,'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched']),'effects':64}
            if r['display']!=5 or r['countdown']!=first['countdown'] or any(w[k]!=v for k,v in wanted.items()) or w['music']<60 or r['effectRequest']!=-1 or not r['musicEnabled'] or r['pressed']!=r['held']&~previous or (r['held']&15)==15:raise ValueError('Unowned text display/input/audio')
            previous=r['held'];services.append(r)
        else:raise ValueError('Unknown text IRQ')
    if (points[-1]['tick']-first['tick'])%65536!=len(services):raise ValueError('Missing text counter services')
    for i,p in enumerate(points):
        if p['name'] in ('glyphWait','scrollWait'):
            expected='glyphReady' if p['name']=='glyphWait' else 'scrollReady';count=1 if expected=='glyphReady' else 2
            if i+1>=len(points) or points[i+1]['name']!=expected or sum(p['cycles']<r['start']<points[i+1]['cycles'] for r in services)!=count:raise ValueError('Incomplete glyph/scroll wait')
        if p['name'] in ('glyphReady','scrollReady') and (not i or points[i-1]['name']!=('glyphWait' if p['name']=='glyphReady' else 'scrollWait')):raise ValueError('Orphaned text wait completion')
        if p['name']=='scrollStored':
            if i<1 or points[i-1]['name']!='scrollReady' or elapsed_work(points[i-1]['cycles'],p['cycles'],irqs)!=32:raise ValueError('Unowned scroll store')
    scrolls=[i for i,p in enumerate(points) if p['name']=='scrollBegin']
    for begin in scrolls:
        sequence=points[begin+1:begin+17]
        if [p['name'] for p in sequence]!=['scrollWait','scrollReady','scrollStored']*5+['scrollEnd']:raise ValueError('Incomplete five-part scroll')
        before=points[begin]['scroll']
        for p,increment in zip(sequence[2:15:3],(1,2,3,1,1)):
            before=(before+increment)%256
            if p['scroll']!=before:raise ValueError('Unowned scroll increment')
    for key,rows in (('polls',polls),('writes',writes)):
        if any(not first['cycles']<r['cycles']<points[-1]['cycles'] for r in rows) or any(b['cycles']<=a['cycles'] for a,b in zip(rows,rows[1:])):raise ValueError('Reordered text accesses')
    if any(r['mode'] not in (0,1,2,3) for r in polls) or any(not 0x9800<=r['address']<0x9c00 or not 0<=r['value']<128 for r in writes):raise ValueError('Invalid text access')
    return services

def compare_text(data,points,services,irqs,polls,writes,summary,epoch):
    expected_services=analyze(data);differences=[]
    if [len(r) for r in (points,services,irqs,polls,writes,summary)]!=[len(data['points']),len(expected_services),len(data['interrupts']),len(data['polls']),len(data['writes']),1]:raise ValueError('Incomplete native text coverage')
    def check(category,index,expected,row):
        delta={k:[v,int(row[k])] for k,v in expected.items() if int(row[k])!=v}
        if delta:differences.append(dict(category=category,index=index,fields=delta))
    delay_owned=False;position_owned=False
    for i,(p,q) in enumerate(zip(data['points'],points)):
        if q['boundary']!=p['name']:raise ValueError('Reordered native text')
        delay_owned|=bool(p['speed']);position_owned|=p['name']=='textNext' and p['row']==17
        fields=list(FIELDS)
        # The layout overwrites the inherited unused delay and cursor before
        # any timed glyph. No CPU/scratch register parity is implied by this
        # semantic comparison. Scroll's B is a loop counter, not text row.
        if delay_owned:fields.append('delay')
        if position_owned and p['name'] in ('textNext','textFinish','end'):fields+=['column','row']
        if p['name']=='skip':fields.append('skipContext')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in fields}),q)
    for i,(p,q) in enumerate(zip(expected_services,services)):
        w=vblank_work(p);check('service',i,dict(service=data['precedingDisplays']+i,cycle=p['start']-epoch,tick=p['tick'],countdown=p['countdown'],
            display=w['display'],effects=w['effects'],music=w['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],irqs)):
        owner=2 if p['returnAddress']==0x261d else 1
        if q['kind']!=p['kind'] or int(q['owner'])!=owner:raise ValueError('Unowned text IRQ')
        check('interrupt',i,dict(vectorCycle=p['start']-epoch),q)
    for key,rows,fields in [('polls',polls,('mode',)),('writes',writes,('address','value'))]:
        for i,(p,q) in enumerate(zip(data[key],rows)):check(key,i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in fields}),q)
    end=data['points'][-1];check('summary',0,dict(end=end['cycles']-epoch,tick=end['tick'],countdown=end['countdown'],scroll=end['scroll'],skipped=int(any(p['name']=='skip' for p in data['points']))),summary[0])
    if services and int(summary[0]['displays'])!=int(services[-1]['service'])+1:raise ValueError('Text terminal service differs')
    return differences

def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'text.json').read_text());startup=json.loads((args.startup/'startup.json').read_text())
    for recording in (data,startup):
        require_capture_reference(manifest,recording)
        if any(recording[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed text controls')
    if manifest['controlDifferences']:raise ValueError('Changed original control')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    path=args.native_csv;values=[rows(path)]+[rows(path.with_suffix('.'+key+'.csv')) for key in ('services','interrupts','polls','writes','summary')]
    differences=compare_text(data,*values,epoch)
    report=dict(comparedBoundaries=len(values[0]),comparedServices=len(values[1]),comparedInterrupts=len(values[2]),comparedPolls=len(values[3]),comparedWrites=len(values[4]),
        differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,
        evidenceLimit='Instruction typing, scroll, semantic substitutions and observed Start skip through 032b. Unused inherited delay/cursor and CPU scratch registers are excluded. Excludes pixels/PCM/hardware, prompt/exit, next gameplay and production scheduling.')
    write_json(path.with_suffix('.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native instruction text differs')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--following',action='store_true')
    verify=sub.add_parser('compare');verify.add_argument('native_csv',type=Path);verify.add_argument('--startup',type=Path,required=True)
    for command in (record,verify):command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
