"""Read-only Start fade/stop continuation of accepted input-only controls."""
import argparse,contextlib,csv,io,json,shutil
from pathlib import Path
from air_title_actions_reference import read,sha,event_sha,replay,memory_sha
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference

POINTS={0x0269:'begin',0x20b4:'fadeEntry',0x20b9:'palette',0x20c7:'wait',0x20ca:'tail',0x026c:'fadeReturned',0x026f:'audioStop',0x3707:'stopEntry',0x369f:'resetEntry',0x36b8:'stateCleared',0x36e7:'presetsReady',0x36f6:'waveReady',0x370d:'resetReturned',0x3710:'audioDisabled',0x0272:'end'}
STORES={0x2506:0xff40,0x250d:0xff42,0x2519:0xff45,0x251e:0xc099,0x2529:0xff42,0x252d:0xff45,0x2532:0xc099,0x2539:0xff40,0x253c:0xff42,0x2540:0xff45,0x2544:0xc099,0x20ba:0xff47,0x20be:0xff49,0x20c3:0xff48,0x36a0:0xff26,0x370e:0xffcf}


def attachment(parent,child,events,changed,setup):
    if parent.get('controlDifferences'):raise ValueError('Unaccepted Start parent control')
    if child.get('parentControlMemorySha256')!=parent['controlMemorySha256'] or child.get('parentEventsSha256')!=event_sha(events) or child.get('setupSha256')!=setup or child.get('romSha256')!=parent['romSha256']:raise ValueError('Detached title Start extension')
    if child.get('extensionFrames')!=80 or changed!=events+[['tick',80,True]]:raise ValueError('Title Start extension changed accepted events')
    if child.get('controlDifferences') or child.get('unhookedControlHashes')!=[child['controlMemorySha256']]*2 or child.get('prefixControlHashes')!=[parent['controlMemorySha256']]*2:raise ValueError('Title Start lacks repeated unchanged control prefix')


def prepare(args):
    parent=read(args.capture/'capture-summary.json');accepted=read(args.parent_out/'actions.json');require_capture_reference(parent,accepted)
    if parent.get('inputCase')!='start' or any(accepted[k]!=parent[k] for k in ('romSha256','controlMemorySha256')) or sha(args.rom.read_bytes())!=parent['romSha256']:raise ValueError('Unowned title Start parent')
    Reference,metadata=reference_class('sameboy');require_matching_backend(parent,metadata);events=read(args.capture/'events.json');hashes=[];prefixes=[]
    for _ in range(2):
        p=Reference(str(args.rom),window='null',sound_volume=0)
        try:
            with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
            replay(p,events);prefixes.append(memory_sha(p));p.tick(80,True);hashes.append(memory_sha(p))
        finally:p.stop(save=False)
    if len(set(hashes))!=1 or prefixes!=[parent['controlMemorySha256']]*2:raise ValueError('Unrepeatable title Start extension')
    child=dict(**metadata,romSha256=parent['romSha256'],controlMemorySha256=hashes[0],controlDifferences=[],unhookedControlHashes=hashes,prefixControlHashes=prefixes,parentControlMemorySha256=parent['controlMemorySha256'],parentEventsSha256=event_sha(events),setupSha256=sha((args.capture/'setup.state').read_bytes()),extensionFrames=80,referenceOnly=True)
    changed=events+[['tick',80,True]];attachment(parent,child,events,changed,child['setupSha256']);args.out.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(args.capture/'setup.state',args.out/'setup.state');write_json(args.out/'events.json',changed);write_json(args.out/'capture-summary.json',child);print('Unchanged Start control extended by 80 held-input frames; two unhooked hashes match.')


def capture(args):
    original=read(args.capture/'capture-summary.json');manifest=read(args.start_control/'capture-summary.json');parent=read(args.parent_out/'actions.json');require_capture_reference(original,parent)
    if parent['inputCase']!='start' or any(parent[k]!=original[k] for k in ('romSha256','controlMemorySha256')) or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Mixed title Start ancestry/ROM')
    events=read(args.start_control/'events.json');old=read(args.capture/'events.json');attachment(original,manifest,old,events,sha((args.start_control/'setup.state').read_bytes()))
    if manifest['setupSha256']!=sha((args.capture/'setup.state').read_bytes()):raise ValueError('Title Start setup changed')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);require_matching_backend(original,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0);active=complete=False;palettes=waits=0;points=[];writes=[];irqs=[];rasters=[];irq=None;buttons=[];before=maps=None
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def hook(pc):
        nonlocal active,complete,palettes,waits,irq,before,maps
        if complete:return
        now=p._cycles()
        if pc==0x0269 and now==parent['points'][-1]['cycles']:active=True;before=p.title_maps_storage()
        if not active:return
        if pc==0x2436:buttons.append(p.memory[0xff8a])
        if pc in POINTS:
            if pc==0x20b9:palettes+=1
            if pc==0x20ca:waits+=1
            points.append(dict(name=POINTS[pc],cycles=now,palettes=palettes,waits=waits,tick=word(0xc00a),countdown=word(0xc0b7),bgp=p.memory[0xff47],obp0=p.memory[0xff48],obp1=p.memory[0xff49],musicEnabled=p.memory[0xffcf],inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],**geometry()))
            if pc==0x0272:maps=p.title_maps_storage();complete=True
        elif pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested title Start vector')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
            if pc==0x0048:rasters.append(dict(boundary='begin',cycle=now,**geometry()))
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            irq['phases'][IRQ_PHASES[pc]]=now
            if IRQ_PHASES[pc]=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b])
        elif pc in (0x2484,0x2555) and irq:
            irq['end']=now;irqs.append(irq);irq=None
            if pc==0x2555:rasters.append(dict(boundary='end',cycle=now,**geometry()))
        address=STORES.get(pc);value=p.register_file.A
        if pc in (0x251e,0x2532):value=p.memory[0xc099]+1
        if address is not None:writes.append(dict(cycle=now,address=address,value=value&255))
    try:
        with (args.start_control/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555}:p.hook_register(0,pc,hook,pc)
        for i,e in enumerate(events):
            replay(p,[e])
            if i==len(old)-1 and memory_sha(p)!=original['controlMemorySha256']:raise ValueError('Hooked Start changed its accepted control prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete title Start or changed full control')
    data=dict(reference=metadata,storageReadOwner='direct-vram-title-v1',romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=original['controlMemorySha256'],points=points,writes=writes,interrupts=irqs,rasters=rasters,beforeMaps=before,maps=maps)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'start.rejected.json',data);raise
    write_json(args.out/'start.json',data);prefix=(args.parent_out/'buttons.txt').read_text();(args.out/'buttons.txt').write_text(prefix+''.join(str(b)+'\n' for b in buttons));print(json.dumps(dict(boundaries=len(points),services=len(buttons),vectors=len(irqs),writes=len(writes))))


def analyze(data,parent):
    points=data['points'];end=parent['points'][-1]
    if parent['inputCase']!='start' or end['route']!=2 or data.get('parentControlMemorySha256')!=parent['controlMemorySha256'] or data.get('storageReadOwner')!='direct-vram-title-v1' or data.get('reference',{}).get('titleStorageObserver')!='direct-vram-title-v1':raise ValueError('Detached Start route/storage owner')
    names=['begin','fadeEntry']+['palette','wait','tail','wait','tail','wait','tail','wait','tail']*8+['fadeReturned','audioStop','stopEntry','resetEntry','stateCleared','presetsReady','waveReady','resetReturned','audioDisabled','end']
    if [p['name'] for p in points]!=names or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('tick','countdown','stat','lcdc','scrollY','lyc','inputHeld','inputPressed')) or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Incomplete/detached title Start boundaries')
    palettes=waits=0
    for p in points:
        if p['name']=='palette':palettes+=1
        if p['name']=='tail':waits+=1
        if p['palettes']!=palettes or p['waits']!=waits or p['countdown']!=54 or p['musicEnabled']!=int(p['name'] not in ('audioDisabled','end')):raise ValueError('Changed Start palette/wait/audio progression')
    if (points[0]['bgp'],points[0]['obp0'],points[0]['obp1'])!=(0xe4,0xc4,0xe0) or any(points[-1][k] for k in ('bgp','obp0','obp1')):raise ValueError('Unowned outgoing palette endpoints')
    if len(data['maps'])!=2048 or data['beforeMaps']!=parent['maps'] or data['maps']!=data['beforeMaps']:raise ValueError('Start changed/detached map storage')
    irqs=data['interrupts'];services=[p for p in irqs if p['kind']=='vblank'];stats=[p for p in irqs if p['kind']=='stat']
    reset=next(p['cycles'] for p in points if p['name']=='audioStop')
    if len(services)!=33 or len(stats)!=67 or len(data['rasters'])!=134 or [p['kind'] for p in irqs]!=['stat','stat','vblank']*33+['stat'] or any(p['start']>=reset for p in services):raise ValueError('Unowned Start services/partial-reset display observation')
    previous=end['inputHeld']
    for i,p in enumerate(services):
        if p['tick']!=(end['tick']+i)&65535 or p['countdown']!=54 or p['pressed']!=p['held']&~previous or p['held']&15==15:raise ValueError('Changed Start input/tick/countdown')
        previous=p['held'];vblank_work(p)
    for p in points:
        finished=[s for s in services if s['end']+16<=p['cycles']];last=finished[-1] if finished else None
        if p['tick']!=(end['tick']+len(finished))&65535 or (p['inputHeld'],p['inputPressed'])!=((last['held'],last['pressed']) if last else (end['inputHeld'],end['inputPressed'])):raise ValueError('Start boundary lost its actual display/input owner')
    if any(not points[0]['cycles']<p['start']<p['end']<points[-1]['cycles'] for p in irqs) or any(b['start']<=a['end'] for a,b in zip(irqs,irqs[1:])):raise ValueError('Escaped/overlapping Start vector')
    stores=data['writes'];colors=[p for p in stores if p['address'] in (0xff47,0xff48,0xff49)]
    if [p['address'] for p in colors]!=[0xff47,0xff49,0xff48]*8 or any(colors[3*i+1]['value']!=colors[3*i]['value']&0xf3 or colors[3*i+2]['value']!=colors[3*i]['value']&0xcf for i in range(8)):raise ValueError('Incomplete outgoing palette stores')
    if [(p['address'],p['value']) for p in stores if p['address'] in (0xff26,0xffcf)]!=[(0xff26,0),(0xffcf,0)] or any(b['cycle']<=a['cycle'] for a,b in zip(stores,stores[1:])):raise ValueError('Incomplete/reordered Start reset stores')
    raster=[(0xff40,0xfb),(0xff42,88),(0xff42,88),(0xff45,103),(0xc099,2),(0xff40,0xc3),(0xff42,0),(0xff45,23),(0xc099,1)]
    if [(p['address'],p['value']) for p in stores if p['address'] in (0xff40,0xff42,0xff45,0xc099)]!=raster*33+raster[:5] or len(stores)!=328:raise ValueError('Incomplete/unknown Start raster stores')
    return services


def compare(args):
    from air_title_actions_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.actions_base)
    manifest=read(args.start_control/'capture-summary.json');original=read(args.case_control/'capture-summary.json');data=read(args.title_start_out/'start.json');parent=read(args.actions_out/'actions.json')
    attachment(original,manifest,read(args.case_control/'events.json'),read(args.start_control/'events.json'),sha((args.start_control/'setup.state').read_bytes()));require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or manifest['setupSha256']!=sha((args.case_control/'setup.state').read_bytes()):raise ValueError('Mixed title Start control/recording')
    services=analyze(data,parent)
    from air_startup_reference import analyze as startup_epoch
    from air_title_menu_reference import inherited_title_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch'];lcd=inherited_title_epoch(args.native_base)
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-start'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');nr=rows('.raster.csv');nw=rows('.writes.csv');maps=rows('.maps.csv');summary=rows('.summary.csv')
    if [len(native),len(ns),len(ni),len(nr),len(nw),len(maps),len(summary)]!=[len(data['points']),33,len(data['interrupts']),len(data['rasters']),len(data['writes']),2048,1]:raise ValueError('Incomplete native Start outputs')
    differences=[]
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(kind=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered native Start boundaries')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:v for k,v in p.items() if k not in ('name','cycles')}),q)
    for i,(p,q) in enumerate(zip(services,ns)):
        work=vblank_work(p);check('display',i,dict(service=665+i,cycle=p['start']-epoch,tick=p['tick'],countdown=54,display=work['display'],effects=work['effects'],music=work['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],ni)):
        if p['kind']!=q['kind']:raise ValueError('Reordered Start vector')
        check('vector',i,dict(vectorCycle=p['start']-epoch,owner=2 if p['returnAddress']==0x261d else 1),q)
    for kind,source,target in [('raster',data['rasters'],nr),('write',data['writes'],nw)]:
        for i,(p,q) in enumerate(zip(source,target)):
            if 'boundary' in p and p['boundary']!=q['boundary']:raise ValueError('Reordered Start raster')
            check(kind,i,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k!='boundary'},q)
    for i,(value,q) in enumerate(zip(data['maps'],maps)):check('map',i,dict(address=0x9800+i,value=value),q)
    final=data['points'][-1];cycle=final['cycles']-epoch;frame=(cycle-lcd)//70224
    def deadline(line):
        result=lcd+frame*70224+line*456
        return result+70224 if result<=cycle else result
    check('summary',0,dict(end=cycle,lcdEpoch=lcd,tick=final['tick'],countdown=54,displays=698,stats=860+sum(p['kind']=='stat' for p in data['interrupts']),nextStat=deadline(final['lyc']),nextVBlank=deadline(144),musicEnabled=0),summary[0])
    report=dict(comparedBoundaries=len(native),comparedServices=33,comparedVectors=len(ni),comparedRasterBoundaries=len(nr),comparedWrites=len(nw),comparedMapBytes=2048,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Start outgoing fade, final wait and fixed audio stop with STAT-only reset interruption, before DI/instruction preparation. Intermediate reset voice RAM/PCM, later instruction work, other paths, pixels and production timing remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-start.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native title Start transition differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    make=sub.add_parser('prepare');make.add_argument('rom',type=Path);make.add_argument('--parent-out',type=Path,required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    for k in ('parent-out','start-control'):record.add_argument('--'+k,type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','actions-out','actions-base','start-control','title-start-out'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (make,record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();{'prepare':prepare,'capture':capture,'compare':compare}[args.mode](args)
