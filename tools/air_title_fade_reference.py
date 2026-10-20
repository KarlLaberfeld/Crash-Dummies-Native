"""Read-only title pending services, alternating raster callbacks and fade."""
import argparse,contextlib,csv,hashlib,io,json
from pathlib import Path
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference

POINTS={0x0258:'begin',0x20d1:'fadeEntry',0x20d6:'palette',0x20e4:'wait',0x20e7:'tail',0x025c:'fadeReturned',0x025f:'end'}
STORES={0x20d7:0xff47,0x20db:0xff49,0x20e0:0xff48,0x2506:0xff40,0x250d:0xff42,0x2529:0xff42,0x252d:0xff45,0x2532:0xc099,0x2539:0xff40,0x253c:0xff42,0x2540:0xff45,0x2544:0xc099}


def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());parent=json.loads((args.parent_out/'layout.json').read_text());require_capture_reference(manifest,parent)
    if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or hashlib.sha256(args.rom.read_bytes()).hexdigest()!=manifest['romSha256']:raise ValueError('Changed title-fade control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0);active=False;complete=False;points=[];writes=[];irqs=[];rasters=[];opened=None;buttons=[]
    from air_following_scope import FollowingAirCaptureScope
    scope=FollowingAirCaptureScope(True)
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def hook(pc):
        nonlocal active,complete,opened
        if complete:return
        scope.observe(pc,p.memory[0xc098]);now=p._cycles()
        if pc==0x0258 and now==parent['points'][-1]['cycles']:active=True
        if pc==0x2436 and (active or scope.samples(p.memory[0xc098])):buttons.append(p.memory[0xff8a])
        if not active:return
        if pc in POINTS:
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],bgp=p.memory[0xff47],obp0=p.memory[0xff48],obp1=p.memory[0xff49],**geometry()))
            if pc==0x025f:complete=True
        elif pc in (0x0040,0x0048):
            if opened:raise ValueError('Nested title vector')
            opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
            if pc==0x0048:rasters.append(dict(boundary='begin',cycle=now,**geometry()))
        elif pc in IRQ_PHASES and opened and opened['kind']=='vblank':
            opened['phases'][IRQ_PHASES[pc]]=now
            if IRQ_PHASES[pc]=='display':opened.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b])
        elif pc in (0x2484,0x2555) and opened:
            opened['end']=now;irqs.append(opened);opened=None
            if pc==0x2555:rasters.append(dict(boundary='end',cycle=now,**geometry()))
        if pc in STORES:writes.append(dict(cycle=now,address=STORES[pc],value=(p.memory[0xc099]+1)&255 if pc==0x2532 else p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x268b,0x03d8}:p.hook_register(0,pc,hook,pc)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            else:getattr(p,'button_'+e[0])(e[1])
        digest=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or opened or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete title fade or changed full control')
    data=dict(reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,writes=writes,interrupts=irqs,rasters=rasters)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'fade.rejected.json',data);raise
    write_json(args.out/'fade.json',data);(args.out/'buttons.txt').write_text(''.join(str(b)+'\n' for b in buttons));print(json.dumps(dict(boundaries=len(points),writes=len(writes),services=sum(p['kind']=='vblank' for p in irqs),vectors=len(irqs))))


def analyze(data,parent):
    points=data['points'];end=parent['points'][-1];names=[p['name'] for p in points]
    if names!=['begin','fadeEntry']+[n for _ in range(8) for n in ('palette','wait','tail','wait','tail','wait','tail','wait','tail')]+['fadeReturned','end'] or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('tick','countdown','inputHeld','inputPressed','lcdc','stat')):raise ValueError('Detached or incomplete title fade')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])) or any(p['countdown']!=54 for p in points):raise ValueError('Title fade changed retained countdown/order')
    irqs=data['interrupts'];displays=[p for p in irqs if p['kind']=='vblank'];stats=[p for p in irqs if p['kind']=='stat'];rasters=data['rasters']
    if len(displays)!=34 or len(stats)!=66 or len(rasters)!=132 or [r['kind'] for r in irqs[:2]]!=['vblank','stat']:raise ValueError('Incomplete pending/periodic title services')
    if any(p['returnAddress']!=(0x20d1 if i<2 else 0x261d) or not points[0]['cycles']<p['start']<p['end']<points[-1]['cycles'] for i,p in enumerate(irqs)):raise ValueError('Unowned title interrupt return')
    for i,p in enumerate(displays):
        if p['tick']!=(end['tick']+i)&65535 or p['countdown']!=54:raise ValueError('Title display resampled bookkeeping incorrectly')
        vblank_work(p)
    if points[-1]['tick']!=(end['tick']+34)&65535:raise ValueError('Missing title display ticks')
    for i,p in enumerate(stats):
        begin,done=rasters[2*i:2*i+2];top=i%2==0
        if [begin[k] for k in ('boundary','cycle','stat','lcdc','scrollY','lyc')]!=['begin',p['start'],1 if top else 2,0xc3 if top else 0xfb,0 if top else 88,23 if top else 103] or [done[k] for k in ('boundary','cycle','stat','lcdc','scrollY','lyc')]!=['end',p['end'],2 if top else 1,0xfb if top else 0xc3,88 if top else 0,103 if top else 23]:raise ValueError('Unowned title raster branch/order')
    writes=data['writes']
    if len(writes)!=321 or any(b['cycle']<=a['cycle'] for a,b in zip(writes,writes[1:])):raise ValueError('Incomplete title palette/raster stores')
    for i,p in enumerate(stats):
        top=i%2==0;selected=[w for w in writes if p['start']<w['cycle']<p['end']]
        expected=list(zip((0xff40,0xff42,0xff42,0xff45,0xc099),(0xfb,88,88,103,2))) if top else list(zip((0xff40,0xff42,0xff45,0xc099),(0xc3,0,23,1)))
        if [(w['address'],w['value']) for w in selected]!=expected:raise ValueError('Incomplete title raster stores')
    palettes=[w for w in writes if w['address'] in (0xff47,0xff48,0xff49)]
    if len(palettes)!=24:raise ValueError('Missing title palette writes')
    for i in range(8):
        triple=palettes[3*i:3*i+3];value=triple[0]['value']
        if [w['address'] for w in triple]!=[0xff47,0xff49,0xff48] or [w['value'] for w in triple]!=[value,value&0xf3,value&0xcf]:raise ValueError('Unowned title palette masks/order')
    return displays


def compare(args):
    from air_title_layout_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.layout_base)
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.fade_out/'fade.json').read_text());parent=json.loads((args.layout_out/'layout.json').read_text());require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed title fade recording')
    services=analyze(data,parent)
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(json.loads((args.startup/'startup.json').read_text()))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-fade'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');nservices=rows('.services.csv');nirqs=rows('.interrupts.csv');rasters=rows('.raster.csv');writes=rows('.writes.csv');summary=rows('.summary.csv')
    if [len(native),len(nservices),len(nirqs),len(rasters),len(writes),len(summary)]!=[76,34,100,132,321,1]:raise ValueError('Incomplete native title fade')
    differences=[]
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(kind=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered native title fade')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in ('tick','countdown','lcdc','stat','lyc','scrollY','bgp','obp0','obp1','inputHeld','inputPressed')}),q)
    for i,(p,q) in enumerate(zip(services,nservices)):
        work=vblank_work(p);check('display',i,dict(service=546+i,cycle=p['start']-epoch,tick=p['tick'],countdown=54,display=work['display'],effects=work['effects'],music=work['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],nirqs)):
        if p['kind']!=q['kind'] or int(q['owner'])!=(3 if i<2 else 2):raise ValueError('Wrong title interrupt owner')
        check('vector',i,dict(vectorCycle=p['start']-epoch),q)
    for i,(p,q) in enumerate(zip(data['rasters'],rasters)):
        if p['boundary']!=q['boundary']:raise ValueError('Reordered native raster')
        check('raster',i,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k!='boundary'},q)
    for i,(p,q) in enumerate(zip(data['writes'],writes)):check('write',i,{k:v-epoch if k=='cycle' else v for k,v in p.items()},q)
    final=data['points'][-1];lcd=parent['points'][-2]['cycles']-4-epoch
    check('summary',0,dict(end=final['cycles']-epoch,lcdEpoch=lcd,tick=final['tick'],countdown=54,displays=580,stats=612,nextStat=lcd+33*70224+23*456,nextVBlank=lcd+33*70224+144*456,servicesMasked=0,pendingRequests=0),summary[0])
    report=dict(comparedBoundaries=76,comparedServices=34,comparedVectors=100,comparedRasterBoundaries=132,comparedWrites=321,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Post-campaign blank-center title: initial pending services, alternating zero-scroll raster branches, complete incoming fade and one final wait only. Later music selection/center motion/page/menu, pixels/PCM and production timing remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-fade.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native title fade differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--parent-out',type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
