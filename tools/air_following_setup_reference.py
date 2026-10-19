"""Read-only following instruction-to-stunt LCD-off prefix through 0367.

The complete original control is replayed and hashed. Only the explicit
0355..0367 interval is qualified here; later gameplay setup is not truncated
into an apparent match. Native replay receives buttons and decoded assets only.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
from air_following_scope import FollowingAirCaptureScope

POINTS={0x0355:'begin',0x0359:'lcdOffReturned',0x035f:'objectsCleared',0x0364:'stateReset',0x0367:'stagePointer'}
FIELDS=('tick','countdown','player','stage','difficulty','lives','display','stat','lcdc','lyc','pendingRequests')

def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or hashlib.sha256(read_rom(args.rom)).hexdigest()!=manifest['romSha256']:
        raise ValueError('Changed original control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    player=Reference(str(args.rom),window='null',sound_volume=0)
    scope=FollowingAirCaptureScope(getattr(args,'next_retry',False))
    armed=False;active=False;complete=False;points=[];polls=[];writes=[];interrupts=[]
    def word(address):return player.memory[address]+256*player.memory[address+1]
    def hook(pc):
        nonlocal armed,active,complete
        if complete:return
        scope.observe(pc,player.memory[0xc098])
        if pc==0x268b and player.memory[0xc098] in (2,10):armed=True
        if pc==0x0355 and scope.ready and armed:active=True
        if not active:return
        now=player._cycles()
        if pc in POINTS:
            selected=player.memory[0xc082]
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),player=selected,
                stage=player.memory[0xc088+8*selected],difficulty=player.memory[0xc089+8*selected],
                lives=player.memory[0xc08a+8*selected],display=player.memory[0xc098],stat=player.memory[0xc099],
                lcdc=player.memory[0xff40],lyc=player.memory[0xff45],pendingRequests=player.memory[0xff0f]&3,
                interruptEnable=player.memory[0xffff]&3,musicEnabled=player.memory[0xffcf]))
            if pc==0x0367:active=False;complete=True
        elif pc==0x2598:polls.append(dict(cycles=now,ly=player.register_file.A))
        elif pc==0x195d:writes.append(dict(cycles=now,address=player.register_file.HL,value=player.register_file.A))
        elif pc in (0x0040,0x0048):interrupts.append(dict(cycles=now,kind='vblank' if pc==0x0040 else 'stat'))
    try:
        with (args.capture/'setup.state').open('rb') as stream:player.load_state(stream)
        for pc in (*POINTS,0x268b,0x2598,0x195d,0x0040,0x0048,0x03d8):player.hook_register(0,pc,hook,pc)
        for event in json.loads((args.capture/'events.json').read_text()):
            if event[0]=='tick':player.tick(event[1],event[2])
            elif event[0] in ('press','release'):getattr(player,'button_'+event[0])(event[1])
            else:raise ValueError('Unknown original control event')
        digest=hashlib.sha256(bytes(player.memory[0x8000:0x10000])).hexdigest()
    finally:player.stop(save=False)
    if not complete or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete following prefix or changed original control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,
        points=points,polls=polls,writes=writes,interrupts=interrupts,productionSchedulerAccepted=False)
    if scope.following:data['nextRetry']=True
    analyze(data);args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'prefix.json',data)
    print(json.dumps(dict(boundaries=len(points),polls=len(polls),writes=len(writes),interrupts=len(interrupts),controlDifferences=0),indent=2))

def analyze(data):
    points=data.get('points',[]);polls=data.get('polls',[]);writes=data.get('writes',[])
    if data.get('version')!=1 or [p['name'] for p in points]!=list(POINTS.values()):raise ValueError('Incomplete/reordered following setup prefix')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Reordered prefix time')
    first=points[0]
    if first['stage'] not in (1,2) or first['difficulty'] not in range(4) or first['player'] not in (0,1) or not 1<=first['lives']<=255 or first['lcdc']&130!=128 or first['pendingRequests']:
        raise ValueError('Unowned following setup entry')
    for i,p in enumerate(points):
        if any(p[k]!=first[k] for k in ('tick','countdown','player','stage','difficulty','lives','display','stat','lyc')) or p['display']!=5 or p['stat']!=5 or p['lyc']!=95 or p['musicEnabled'] or p['interruptEnable']!=3:
            raise ValueError('Unowned prefix state/services')
        if p['lcdc']!=(first['lcdc'] if i==0 else first['lcdc']&127) or p['pendingRequests']!=(0 if i==0 else 3):raise ValueError('Unowned LCD/pending request gate')
    if data.get('interrupts')!=[]:raise ValueError('Unexpected masked service')
    if not polls or len(polls)>2200 or polls[-1]['ly']!=145 or any(p['ly']==145 for p in polls[:-1]) or any(not 0<=p['ly']<=153 for p in polls):raise ValueError('Incomplete LCD equality polls')
    if polls[0]['cycles']!=first['cycles']+116 or any(b['cycles']-a['cycles']!=32 for a,b in zip(polls,polls[1:])) or points[1]['cycles']-polls[-1]['cycles']!=92:
        raise ValueError('Unowned LCD-off operations')
    if [b['cycles']-a['cycles'] for a,b in zip(points[1:],points[2:])]!=[6196,6268,88]:raise ValueError('Unowned buffer/selection work')
    expected=[(0xc100+i,0) for i in range(256)]+[(0xc200+i,255) for i in range(256)]
    if [(w['address'],w['value']) for w in writes]!=expected:raise ValueError('Incomplete/reordered buffer stores')
    for start,base in ((0,points[1]['cycles']+40),(256,points[2]['cycles']+80)):
        if any(writes[start+i]['cycles']!=base+24*i for i in range(256)):raise ValueError('Unowned buffer store boundary')
    return dict(boundaries=len(points),polls=len(polls),writes=len(writes),interrupts=0)

def compare_prefix(data,points,polls,writes,summary,epoch):
    analyze(data)
    if [len(r) for r in (points,polls,writes,summary)]!=[5,len(data['polls']),512,1]:raise ValueError('Incomplete native following prefix coverage')
    differences=[]
    def check(category,index,expected,actual):
        delta={k:[v,int(actual[k])] for k,v in expected.items() if int(actual[k])!=v}
        if delta:differences.append(dict(category=category,index=index,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],points)):
        if q['boundary']!=p['name']:raise ValueError('Reordered native following prefix')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in FIELDS}),q)
    for key,rows,fields in [('polls',polls,('ly',)),('writes',writes,('address','value'))]:
        for i,(p,q) in enumerate(zip(data[key],rows)):check(key,i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in fields}),q)
    end=data['points'][-1]
    check('summary',0,dict(end=end['cycles']-epoch,tick=end['tick'],countdown=end['countdown'],pollReads=len(polls),
        lcdDisabled=data['points'][1]['cycles']-44-epoch,pendingRequests=3),summary[0])
    return differences

def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'prefix.json').read_text())
    startup=json.loads((args.startup/'startup.json').read_text())
    for recording in (data,startup):
        require_capture_reference(manifest,recording)
        if any(recording[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed following prefix controls')
    if manifest['controlDifferences']:raise ValueError('Changed original control')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
    path=args.native_csv;values=[rows(path)]+[rows(path.with_suffix('.'+key+'.csv')) for key in ('polls','writes','summary')]
    differences=compare_prefix(data,*values,epoch)
    # The source service gate freezes both diagnostic counters throughout.
    prior=rows(args.exit_summary)
    if len(prior)!=1 or any(int(values[-1][0][k])!=int(prior[0][k]) for k in ('tick','countdown','displays','stats')):
        raise ValueError('Native masked setup changed service counters')
    report=dict(comparedBoundaries=len(values[0]),comparedPolls=len(values[1]),comparedWrites=len(values[2]),comparedInterrupts=0,
        differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,
        evidenceLimit='0355..0367 LCD-off equality-145 polling, masked services, complete 256-byte object/actor clears and campaign selection. Excludes subsequent stunt/resources/HUD/LCD restart, physical bus/pixels/PCM and production Windows scheduling.')
    write_json(path.with_suffix('.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native following setup prefix differs')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--next-retry',action='store_true')
    verify=sub.add_parser('compare');verify.add_argument('native_csv',type=Path);verify.add_argument('--startup',type=Path,required=True);verify.add_argument('--exit-summary',type=Path,required=True)
    for command in (record,verify):command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
