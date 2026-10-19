"""Read-only post-game-over masked title reset; graphics payload not certified."""
import argparse,contextlib,csv,hashlib,io,json
from pathlib import Path
from air_reference import write_json
from reference_backend import reference_class,require_matching_backend,require_capture_reference

POINTS={0x019c:'begin',0x01a0:'lcdOffReturned',0x01a5:'windowCleared',0x01aa:'backgroundCleared',0x01b0:'objectsCleared',0x01dd:'stateReset',0x01eb:'tilesBank',0x01f7:'upperTilesReady',0x0203:'lowerTilesReady',0x0206:'dataBank'}
STORES={0x01b0:0xff8f,0x01b2:0xff42,0x01b4:0xff43,0x01b6:0xc03e,0x01b9:0xc09c,0x01bc:0xc09d,0x01bf:0xc085,0x01c2:0xc086,0x01c5:0xc087,0x01c8:0xc08d,0x01cb:0xc08e,0x01ce:0xc08f,0x01d1:0xc098,0x01d4:0xc099,0x01d7:0xc082,0x01db:0xff8a}


def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());parent=json.loads((args.parent_out/'return.json').read_text());require_capture_reference(manifest,parent)
    if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or hashlib.sha256(args.rom.read_bytes()).hexdigest()!=manifest['romSha256']:raise ValueError('Changed title-reset control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0);active=False;complete=False;points=[];polls=[];writes=[];vectors=[];board=None
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,board
        if complete:return
        now=p._cycles()
        if pc==0x019c and now==parent['points'][-1]['cycles']:active=True;board=list(p.memory[0xc051:0xc081])
        if not active:return
        if pc in POINTS:
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],lcdc=p.memory[0xff40],bank=p.memory[0xffc5]))
            if pc==0x0206:points[-1].update(scoresUnchanged=list(p.memory[0xc051:0xc081])==board,mapsBlank=not any(p.memory[0x9800:0xa000]),objectsBlank=not any(p.memory[0xc100:0xc200]));complete=True
        if pc==0x2598:polls.append(dict(cycle=now,ly=p.register_file.A))
        if pc in (0x0040,0x0048):vectors.append(dict(pc=pc,cycle=now))
        address=None
        if pc==0x2128:address=p.register_file.D*256+p.register_file.E
        elif pc==0x195d:address=p.register_file.HL
        elif pc in STORES:address=STORES[pc]
        if address is not None:writes.append(dict(cycle=now,address=address,value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,0x2598,0x2128,0x195d,0x0040,0x0048}:p.hook_register(0,pc,hook,pc)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            else:getattr(p,'button_'+e[0])(e[1])
        digest=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete reset or changed full control')
    data=dict(reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,polls=polls,writes=writes,vectors=vectors)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'reset.rejected.json',data);raise
    write_json(args.out/'reset.json',data);print(json.dumps(dict(boundaries=len(points),polls=len(polls),writes=len(writes))))


def analyze(data,parent):
    points=data['points'];end=parent['points'][-1]
    if [p['name'] for p in points]!=list(POINTS.values()) or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('tick','countdown','inputHeld','inputPressed')):raise ValueError('Detached or reordered title reset')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])) or any(p[k]!=points[0][k] for p in points for k in ('tick','countdown')):raise ValueError('Masked reset advanced display state')
    if data['vectors'] or [p['lcdc'] for p in points]!=[0xdb]+[0x5b]*9 or [p['bank'] for p in points]!=[1]*6+[3]*3+[1]:raise ValueError('Unowned title service/LCD/bank transition')
    if any(points[-1].get(k) is not True for k in ('scoresUnchanged','mapsBlank','objectsBlank')):raise ValueError('Reset storage outcome differs')
    if [p['inputHeld'] for p in points]!=[points[0]['inputHeld']]*5+[255]*5 or any(p['inputPressed']!=points[0]['inputPressed'] for p in points):raise ValueError('Title input sentinel changed other edges')
    polls=data['polls'];writes=data['writes']
    if not polls or len(polls)>2200 or polls[-1]['ly']!=145 or any(p['ly']==145 for p in polls[:-1]) or any(b['cycle']-a['cycle']!=32 for a,b in zip(polls,polls[1:])):raise ValueError('Missing equality wait')
    addresses=list(range(0x9c00,0xa000))+list(range(0x9800,0x9c00))+list(range(0xc100,0xc200))+list(STORES.values())
    if [p['address'] for p in writes]!=addresses or [p['value'] for p in writes]!=[0]*(len(addresses)-1)+[255]:raise ValueError('Missing or changed reset stores')
    if any(b['cycle']<=a['cycle'] for a,b in zip(writes,writes[1:])) or not points[0]['cycles']<polls[0]['cycle']<=polls[-1]['cycle']<points[1]['cycles']<writes[0]['cycle']<writes[-1]['cycle']<points[5]['cycles']:raise ValueError('Reset observations escaped their owner')
    return dict(boundaries=len(points),polls=len(polls),writes=len(writes))


def compare(args):
    from air_game_over_return_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.return_base)
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.reset_out/'reset.json').read_text());parent=json.loads((args.return_out/'return.json').read_text());require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed title reset recording')
    scope=analyze(data,parent)
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(json.loads((args.startup/'startup.json').read_text()))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-reset'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');polls=rows('.polls.csv');writes=rows('.writes.csv');summary=rows('.summary.csv')
    if rows('.services.csv') or rows('.interrupts.csv'):raise ValueError('Native reset cannot execute masked services')
    if [len(native),len(polls),len(writes),len(summary)]!=[scope['boundaries'],scope['polls'],scope['writes'],1]:raise ValueError('Incomplete native reset observations')
    differences=[]
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(kind=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered native reset')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in ('tick','countdown','inputHeld','inputPressed','lcdc','bank')}),q)
    for kind,original,observed in [('poll',data['polls'],polls),('write',data['writes'],writes)]:
        for i,(p,q) in enumerate(zip(original,observed)):check(kind,i,{k:v-epoch if k=='cycle' else v for k,v in p.items()},q)
    with Path(str(args.native_base)+'.fifth.game-over-return.summary.csv').open(newline='') as f:prior=next(csv.DictReader(f))
    off=data['polls'][-1]['cycle']+8+8+12+8+12-epoch
    check('summary',0,dict(end=data['points'][-1]['cycles']-epoch,lcdEpoch=int(prior['lcdEpoch']),lcdDisabled=off,pollReads=scope['polls'],pendingRequests=(2 if int(prior['nextStat'])<=off else 0)|(1 if int(prior['nextVBlank'])<=off else 0),tick=int(prior['tick']),countdown=54,displays=546,stats=546,display=0,stat=0,servicesMasked=1),summary[0])
    report=dict(comparedBoundaries=scope['boundaries'],comparedPolls=scope['polls'],comparedWrites=scope['writes'],comparedVectors=0,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Masked post-game-over prefix through fixed title-graphics copy work and bank restoration only. Graphics payload/pixels, first-boot branch, title layout/LCD restart and production timing remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-reset.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native title reset differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--parent-out',type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
