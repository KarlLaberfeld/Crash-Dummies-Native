"""Read-only interrupted title music start and forty center-closing waits."""
import argparse,contextlib,csv,hashlib,io,json
from pathlib import Path
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference

POINTS={0x025f:'begin',0x362a:'musicEntry',0x369f:'resetEntry',0x36b8:'stateCleared',0x36e7:'presetsReady',0x36f6:'waveReady',0x3633:'resetReturned',0x366b:'rootsReady',0x3677:'hardwareReady',0x0264:'musicReturned',0x26ea:'menuEntry',0x27e6:'closeWait',0x27e9:'closeReady',0x27f5:'centerStored',0x27f9:'end'}
STORES={0x2506:0xff40,0x250d:0xff42,0x2519:0xff45,0x251e:0xc099,0x2529:0xff42,0x252d:0xff45,0x2532:0xc099,0x2539:0xff40,0x253c:0xff42,0x2540:0xff45,0x2544:0xc099,0x27ec:0xff4a,0x27f2:0xc09c}


def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());parent=json.loads((args.parent_out/'fade.json').read_text());require_capture_reference(manifest,parent)
    if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or hashlib.sha256(args.rom.read_bytes()).hexdigest()!=manifest['romSha256']:raise ValueError('Changed title-close control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0);active=False;complete=False;points=[];writes=[];irqs=[];rasters=[];opened=None;buttons=[]
    from air_following_scope import FollowingAirCaptureScope
    scope=FollowingAirCaptureScope(True);title_started=False
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def hook(pc):
        nonlocal active,complete,opened,title_started
        if complete:return
        scope.observe(pc,p.memory[0xc098]);now=p._cycles()
        if pc==0x0258 and now==parent['points'][0]['cycles']:title_started=True
        if pc==0x025f and now==parent['points'][-1]['cycles']:active=True
        if pc==0x2436 and (active or title_started or scope.samples(p.memory[0xc098])):buttons.append(p.memory[0xff8a])
        if not active:return
        if pc in POINTS:
            center=p.memory[0xc09c]
            points.append(dict(name=POINTS[pc],cycles=now,center=center,steps=((256-center)&255)//2,windowY=p.memory[0xff4a],tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],sourceSong=p.memory[0xffce],**geometry()))
            if pc==0x27f9:complete=True
        elif pc in (0x0040,0x0048):
            if opened:raise ValueError('Nested title-close vector')
            opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
            if pc==0x0048:rasters.append(dict(boundary='begin',cycle=now,center=p.memory[0xc09c],**geometry()))
        elif pc in IRQ_PHASES and opened and opened['kind']=='vblank':
            opened['phases'][IRQ_PHASES[pc]]=now
            if IRQ_PHASES[pc]=='display':opened.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b])
        elif pc in (0x2484,0x2555) and opened:
            opened['end']=now;irqs.append(opened);opened=None
            if pc==0x2555:rasters.append(dict(boundary='end',cycle=now,center=p.memory[0xc09c],**geometry()))
        if pc in STORES:
            address=STORES[pc];value=p.register_file.A
            if pc in (0x251e,0x2532):value=p.memory[0xc099]+1
            if pc==0x27ec:value=p.memory[0xff4a]-1
            writes.append(dict(cycle=now,address=address,value=value&255))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,*IRQ_PHASES,0x0258,0x0040,0x0048,0x2484,0x2555,0x268b,0x03d8}:p.hook_register(0,pc,hook,pc)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            else:getattr(p,'button_'+e[0])(e[1])
        digest=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or opened or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete title closing or changed full control')
    data=dict(reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,writes=writes,interrupts=irqs,rasters=rasters)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'close.rejected.json',data);raise
    write_json(args.out/'close.json',data);(args.out/'buttons.txt').write_text(''.join(str(b)+'\n' for b in buttons));print(json.dumps(dict(boundaries=len(points),writes=len(writes),services=sum(p['kind']=='vblank' for p in irqs),vectors=len(irqs))))


def analyze(data,parent):
    points=data['points'];end=parent['points'][-1];names=[p['name'] for p in points]
    if names!=list(POINTS.values())[:11]+['closeWait','closeReady','centerStored']*40+['end'] or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('tick','countdown','inputHeld','inputPressed','lcdc','stat','lyc','scrollY')):raise ValueError('Detached or incomplete title music/close owner')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])) or any(p['countdown']!=54 for p in points):raise ValueError('Title closing changed retained timer/order')
    for p in points:
        if not 0<=p['steps']<=40 or p['center']!=(-2*p['steps'])&255 or p['windowY']!=112-p['steps']:raise ValueError('Unowned closing center/window position')
    done=[p for p in points if p['name']=='centerStored']
    if [p['steps'] for p in done]!=list(range(1,41)) or points[-1]['center']!=176:raise ValueError('Missing closing steps')
    music=points[9]['cycles'];irqs=data['interrupts'];services=[p for p in irqs if p['kind']=='vblank'];stats=[p for p in irqs if p['kind']=='stat'];raster=data['rasters']
    if len(services)!=40 or len(stats)!=119 or len(raster)!=238 or irqs[0]['kind']!='stat' or not points[1]['cycles']<irqs[0]['start']<irqs[0]['end']<music:raise ValueError('Unowned interrupted title music reset')
    if any(p['start']<music or p['tick']!=(end['tick']+i)&65535 or p['countdown']!=54 for i,p in enumerate(services)) or points[-1]['tick']!=(end['tick']+40)&65535:raise ValueError('Display observed partial reset or changed title tick')
    for p in services:vblank_work(p)
    if any(p['sourceSong']!=1 for p in points[9:]):raise ValueError('Title song did not remain selected')
    if irqs[0]['returnAddress']!=0x23af or any(not points[0]['cycles']<p['start']<p['end']<points[-1]['cycles'] for p in irqs) or any(p['returnAddress']!=0x261d for p in irqs[1:]):raise ValueError('Unowned title-close vector return')
    contexts=[(0,1),(0,2)]+[(center,phase) for center in range(254,177,-2) for phase in (1,2,3)]
    for i,p in enumerate(stats):
        a,b=raster[2*i:2*i+2];center=a['center'];phase=a['stat']
        if (center,phase)!=contexts[i] or tuple(a[k] for k in ('lcdc','scrollY','lyc'))!=(0xc3 if phase==1 else 0xfb,0 if phase==1 else (center+88)&255 if phase==2 else 88,23 if phase==1 else ((23-center)&255 if center else 103) if phase==2 else 103):raise ValueError('Unowned title-close raster sequence')
        if a['boundary']!='begin' or b['boundary']!='end' or a['cycle']!=p['start'] or b['cycle']!=p['end'] or b['center']!=center or center not in [0,*range(178,255,2)]:raise ValueError('Incomplete title-close raster context')
        if phase==1:expected=(2,0xfb,(center+88)&255 if center else 88,(23-center)&255 if center else 103)
        elif phase==2 and a['lyc']!=103:expected=(3,0xfb,88,103)
        elif phase in (2,3):expected=(1,0xc3,0,23)
        else:raise ValueError('Unknown title closing raster phase')
        if tuple(b[k] for k in ('stat','lcdc','scrollY','lyc'))!=expected:raise ValueError('Wrong title closing raster result')
    if len(data['writes'])!=518 or any(b['cycle']<=a['cycle'] for a,b in zip(data['writes'],data['writes'][1:])):raise ValueError('Incomplete title-close stores')
    for i,p in enumerate(stats):
        a=raster[2*i];center=a['center'];phase=a['stat'];selected=[w for w in data['writes'] if p['start']<w['cycle']<p['end']]
        if phase==1 and center==0:expected=list(zip((0xff40,0xff42,0xff42,0xff45,0xc099),(0xfb,88,88,103,2)))
        elif phase==1:expected=list(zip((0xff40,0xff42,0xff45,0xc099),(0xfb,(center+88)&255,(23-center)&255,2)))
        elif phase==2 and a['lyc']!=103:expected=list(zip((0xff42,0xff45,0xc099),(88,103,3)))
        else:expected=list(zip((0xff40,0xff42,0xff45,0xc099),(0xc3,0,23,1)))
        if [(w['address'],w['value']) for w in selected]!=expected:raise ValueError('Missing title-close raster stores')
    motion=[w for w in data['writes'] if w['address'] in (0xff4a,0xc09c)]
    if [(w['address'],w['value']) for w in motion]!=[(address,value) for step in range(1,41) for address,value in ((0xff4a,112-step),(0xc09c,(-2*step)&255))]:raise ValueError('Incomplete window/center motion stores')
    return services


def compare(args):
    from air_title_fade_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.fade_base)
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.close_out/'close.json').read_text());parent=json.loads((args.fade_out/'fade.json').read_text());require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed title close recording')
    services=analyze(data,parent)
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(json.loads((args.startup/'startup.json').read_text()))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-close'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');nr=rows('.raster.csv');nw=rows('.writes.csv');summary=rows('.summary.csv')
    if [len(native),len(ns),len(ni),len(nr),len(nw),len(summary)]!=[132,40,159,238,518,1]:raise ValueError('Incomplete native title closing')
    differences=[]
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(kind=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered native title closing')
        wanted=dict(cycle=p['cycles']-epoch,**{k:p[k] for k in ('center','steps','windowY','tick','countdown','stat','lcdc','scrollY','lyc','inputHeld','inputPressed')})
        if i>=9:wanted['song']=1
        check('boundary',i,wanted,q)
    for i,(p,q) in enumerate(zip(services,ns)):
        work=vblank_work(p);check('display',i,dict(service=580+i,cycle=p['start']-epoch,tick=p['tick'],countdown=54,display=work['display'],effects=work['effects'],music=work['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],ni)):
        if p['kind']!=q['kind'] or int(q['owner'])!=(1 if i==0 else 2):raise ValueError('Wrong title-close vector owner')
        check('vector',i,dict(vectorCycle=p['start']-epoch),q)
    for i,(p,q) in enumerate(zip(data['rasters'],nr)):
        if p['boundary']!=q['boundary']:raise ValueError('Reordered title-close raster')
        check('raster',i,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k not in ('boundary','center')},q)
    for i,(p,q) in enumerate(zip(data['writes'],nw)):check('write',i,{k:v-epoch if k=='cycle' else v for k,v in p.items()},q)
    with Path(str(args.native_base)+'.fifth.title-fade.summary.csv').open(newline='') as f:prior=next(csv.DictReader(f))
    lcd=int(prior['lcdEpoch']);final=data['points'][-1]
    check('summary',0,dict(end=final['cycles']-epoch,lcdEpoch=lcd,tick=final['tick'],countdown=54,displays=620,stats=731,nextStat=lcd+73*70224+23*456,nextVBlank=lcd+73*70224+144*456,center=176,steps=40,windowY=72,song=1),summary[0])
    report=dict(comparedBoundaries=132,comparedServices=40,comparedVectors=159,comparedRasterBoundaries=238,comparedWrites=518,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Title song start with STAT-only interruption and forty center-closing waits, through entry before window clear/page installation. Partial audio-reset RAM/register state is not certified; no VBlank observes it. Page clear/install/open/menu, graphics/pixels/PCM and production timing remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-close.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native title closing differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--parent-out',type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
