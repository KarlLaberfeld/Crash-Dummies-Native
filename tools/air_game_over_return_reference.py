"""Read-only non-ranking score check and no-survivor return to title-reset entry."""
import argparse,contextlib,csv,hashlib,io,json
from pathlib import Path
from types import SimpleNamespace
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference

POINTS={0x06a2:'begin',0x31b9:'rankEntry',0x31c1:'row',0x31cf:'compareEntry',0x31d5:'compare',0x31da:'compare',0x31df:'compare',0x31c6:'rowDone',
        0x06a5:'rankReturned',0x0514:'resultReturned',0x051d:'fadeCall',0x20b4:'fadeEntry',0x20b9:'palette',0x20c7:'wait',0x20ca:'tail',0x0520:'fadeReturned',0x019c:'titleResetEntry'}


def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());parent=json.loads((args.parent_out/'final-result.json').read_text());require_capture_reference(manifest,parent)
    if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or hashlib.sha256(args.rom.read_bytes()).hexdigest()!=manifest['romSha256']:raise ValueError('Changed game-over return control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0);active=False;complete=False;row=-1;points=[];irqs=[];opened=None;buttons=[];board=None
    from air_following_scope import FollowingAirCaptureScope
    scope=FollowingAirCaptureScope(True)
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,row,opened,board
        if complete:return
        scope.observe(pc,p.memory[0xc098])
        if pc==0x2436 and scope.samples(p.memory[0xc098]):buttons.append(p.memory[0xff8a])
        now=p._cycles()
        if pc==0x06a2 and now==parent['points'][-1]['cycles']:active=True;board=list(p.memory[0xc051:0xc081])
        if not active:return
        if pc==0x31e2:raise ValueError('Qualifying original score needs a separate name-entry owner')
        if pc in POINTS:
            if pc==0x31c1:row+=1
            if pc==0x06a5:row=-1
            byte={0x31d5:0,0x31da:1,0x31df:2}.get(pc,-1)
            amount=p.memory[p.register_file.B*256+p.register_file.C] if byte>=0 else -1
            target=p.memory[p.register_file.HL] if byte>=0 else -1
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),row=row,byte=byte,amount=amount,target=target,carry=int(bool(p.register_file.F&16)) if pc==0x31c6 else -1,
                bgp=p.memory[0xff47],obp0=p.memory[0xff48],obp1=p.memory[0xff49],musicEnabled=p.memory[0xffcf],lives0=p.memory[0xc08a],lives1=p.memory[0xc092],inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b]))
            if pc==0x019c:points[-1]['scoresUnchanged']=list(p.memory[0xc051:0xc081])==board;complete=True
        elif pc in (0x0040,0x0048):
            if opened:raise ValueError('Nested game-over return vector')
            opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and opened and opened['kind']=='vblank':
            opened['phases'][IRQ_PHASES[pc]]=now
            if IRQ_PHASES[pc]=='display':opened.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b])
        elif pc in (0x2484,0x2555) and opened:opened['end']=now;irqs.append(opened);opened=None
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*IRQ_PHASES,0x268b,0x03d8,0x31e2,0x0040,0x0048,0x2484,0x2555}:p.hook_register(0,pc,hook,pc)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            else:getattr(p,'button_'+e[0])(e[1])
        digest=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or opened or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete return or changed control')
    data=dict(reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,interrupts=irqs,scores=board)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:
        write_json(args.out/'return.rejected.json',data);raise
    write_json(args.out/'return.json',data);(args.out/'buttons.txt').write_text(''.join(str(b)+'\n' for b in buttons))
    print(json.dumps(dict(boundaries=len(points),services=len(irqs)//2,rows=8)))


def analyze(data,parent):
    points=data['points'];names=[p['name'] for p in points];end=parent['points'][-1]
    if names[:2]!=['begin','rankEntry'] or names[-1]!='titleResetEntry' or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('tick','countdown','inputHeld','inputPressed')):raise ValueError('Detached game-over hold/return')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])) or any(p['lives0'] or p['lives1'] or not p['musicEnabled'] for p in points):raise ValueError('Unowned game-over life/audio/clock state')
    rows=[p for p in points if p['name']=='row'];done=[p for p in points if p['name']=='rowDone'];compares=[p for p in points if p['name']=='compare']
    if [p['row'] for p in rows]!=list(range(8)) or [p['row'] for p in done]!=list(range(8)) or any(p['carry']!=1 for p in done):raise ValueError('Missing rejected score rows')
    if len(data['scores'])!=48:raise ValueError('Missing original score table')
    if points[-1].get('scoresUnchanged') is not True:raise ValueError('Rejected score changed the original table')
    for row in range(8):
        samples=[p for p in compares if p['row']==row]
        if not samples or [p['byte'] for p in samples]!=list(range(len(samples))) or len(samples)>3:raise ValueError('Incomplete score byte order')
        if any(p['amount']!=0 or p['target']!=data['scores'][6*row+3+p['byte']] for p in samples) or samples[-1]['target']<=0:raise ValueError('Unowned zero-savings rejection')
        if any(p['target'] for p in samples[:-1]):raise ValueError('Comparison continued after a differing score byte')
    fade=names.index('fadeEntry')
    if names[fade:]!=['fadeEntry']+[n for _ in range(8) for n in ('palette','wait','tail','wait','tail','wait','tail','wait','tail')]+['fadeReturned','titleResetEntry']:raise ValueError('Incomplete title-return fade')
    irqs=data['interrupts'];services=[r for r in irqs if r['kind']=='vblank']
    if len(irqs)!=64 or len(services)!=32 or any(r['returnAddress']!=0x261d or not points[fade]['cycles']<r['start']<r['end']<points[-1]['cycles'] for r in irqs):raise ValueError('Unowned title-return vectors')
    return services


def compare(args):
    from air_final_result_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.final_base)
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.return_out/'return.json').read_text());parent=json.loads((args.out/'final-result.json').read_text())
    require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed return recording')
    services=analyze(data,parent)
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(json.loads((args.startup/'startup.json').read_text()))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.game-over-return'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');nservices=rows('.services.csv');nirqs=rows('.interrupts.csv');summary=rows('.summary.csv')
    if [len(native),len(nservices),len(nirqs),len(summary)]!=[len(data['points']),32,64,1]:raise ValueError('Incomplete native return')
    differences=[]
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(kind=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered native return')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in ('tick','countdown','row','byte','amount','target','carry','bgp','obp0','obp1','musicEnabled')}),q)
    for i,(p,q) in enumerate(zip(services,nservices)):
        work=vblank_work(p);check('display',i,dict(service=514+i,cycle=p['start']-epoch,tick=p['tick'],countdown=p['countdown']-1,display=work['display'],effects=work['effects'],music=work['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],nirqs)):
        if p['kind']!=q['kind'] or int(q['owner'])!=2:raise ValueError('Wrong return vector owner')
        check('vector',i,dict(vectorCycle=p['start']-epoch),q)
    final=data['points'][-1];lcd=parent['points'][5]['cycles']-20-epoch
    check('summary',0,dict(end=final['cycles']-epoch,lcdEpoch=lcd,tick=final['tick'],countdown=54,displays=546,stats=546,nextStat=lcd+143*456+545*70224,nextVBlank=lcd+144*456+545*70224,lives0=0,lives1=0,savings=0),summary[0])
    report=dict(comparedBoundaries=len(native),comparedScoreRows=8,comparedScoreBytes=sum(p['name']=='compare' for p in data['points']),comparedServices=32,comparedInterrupts=64,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,
        evidenceLimit='Zero native savings rejected by all eight initial score rows; both players eliminated; complete outgoing fade to title-reset entry only. Qualifying score/name entry, surviving-player routing, reset/title internals, pixels/PCM and production timing remain unqualified.')
    write_json(Path(str(args.native_base)+'.game-over-return.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native game-over return differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--parent-out',type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
