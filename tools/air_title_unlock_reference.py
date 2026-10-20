"""Input-only menu direction sequence controls and original measurements."""
import argparse,contextlib,csv,io,shutil,json
from pathlib import Path
from air_title_actions_reference import read,sha,event_sha,replay,memory_sha,KEYS
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work
from air_title_menu_reference import POINTS as MENU_POINTS,STORES as MENU_STORES
from reference_backend import reference_class,require_matching_backend,require_capture_reference
CASES=('sequence','held','reset','combined')
POINTS={**MENU_POINTS,0x2b4f:'end'}
STORES={**MENU_STORES,0x2b2d:0xc0b5,0x2b31:0xc0b6,0x2b3c:0xc0b5,0x2b40:0xc0b6,0x2b48:0xc0b5,0x2b4c:0xc0b6}
def tail(case):
    result=[['release',k] for k in KEYS]+[['tick',2,True]]
    def press(keys,frames=4):
        result.extend([['press',k] for k in keys]+[['tick',frames,True]]+[['release',k] for k in keys]+[['tick',2,True]])
    if case=='reset':press(['up']);press(['right'])
    if case=='combined':press(['up','left'])
    for key in ('up','down','left','right'):press([key],12 if case=='held' and key=='up' else 4)
    result.append(['tick',10,True]);return result

def attachment(parent,case_manifest,events,changed,setup):
    n=case_manifest['splitFrames'];case=case_manifest['inputCase']
    if case not in CASES or type(n) is not int or events[-1][0]!='tick' or not 0<n<events[-1][1]:raise ValueError('Invalid menu direction fork')
    prefix=events[:-1]+[['tick',n,events[-1][2]]]
    if changed!=prefix+tail(case) or case_manifest['parentControlMemorySha256']!=parent['controlMemorySha256'] or case_manifest['parentEventsSha256']!=event_sha(events) or case_manifest['setupSha256']!=setup or case_manifest['romSha256']!=parent['romSha256']:raise ValueError('Detached menu direction controls')
    if case_manifest['controlDifferences'] or case_manifest['prefixControlHashes']!=[case_manifest['prefixMemorySha256']]*2 or case_manifest['unhookedControlHashes']!=[case_manifest['controlMemorySha256']]*2:raise ValueError('Direction fork needs repeated unhooked control hashes')
    return prefix

def prepare(args):
    parent=read(args.capture/'capture-summary.json');known=read(args.actions_control/'capture-summary.json');page=read(args.page_out/'page.json');require_capture_reference(parent,page)
    events=read(args.capture/'events.json');setup=sha((args.capture/'setup.state').read_bytes());n=known['splitFrames']
    if parent['controlDifferences'] or known['parentControlMemorySha256']!=parent['controlMemorySha256'] or known['parentEventsSha256']!=event_sha(events) or known['setupSha256']!=setup or sha(args.rom.read_bytes())!=parent['romSha256']:raise ValueError('Changed accepted menu fork ancestry')
    if not page['points'][-1]['cycles']<=known['prefixCycle']<page['points'][-1]['cycles']+70224:raise ValueError('Detached menu page fork')
    Reference,metadata=reference_class('sameboy');require_matching_backend(parent,metadata)
    prefix=events[:-1]+[['tick',n,events[-1][2]]]
    for case in CASES:
        hashes=[];prefixes=[];changed=prefix+tail(case)
        for _ in range(2):
            p=Reference(str(args.rom),window='null',sound_volume=0)
            try:
                with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
                replay(p,prefix);prefixes.append(memory_sha(p))
                if p._cycles()!=known['prefixCycle']:raise ValueError('Direction fork changed prefix clock')
                replay(p,tail(case));hashes.append(memory_sha(p))
            finally:p.stop(save=False)
        if prefixes!=[known['prefixMemorySha256']]*2 or len(set(hashes))!=1:raise ValueError('Unrepeatable direction fork')
        manifest=dict(**metadata,romSha256=parent['romSha256'],inputCase=case,splitFrames=n,prefixCycle=known['prefixCycle'],prefixMemorySha256=known['prefixMemorySha256'],prefixControlHashes=prefixes,controlMemorySha256=hashes[0],controlDifferences=[],unhookedControlHashes=hashes,parentControlMemorySha256=parent['controlMemorySha256'],parentEventsSha256=event_sha(events),setupSha256=setup,referenceOnly=True)
        attachment(parent,manifest,events,changed,setup);folder=args.out/case;folder.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(args.capture/'setup.state',folder/'setup.state');write_json(folder/'events.json',changed);write_json(folder/'capture-summary.json',manifest);print(case,'two unhooked controls match',flush=True)


def capture(args):
    original=read(args.capture/'capture-summary.json');manifest=read(args.case_control/'capture-summary.json');parent=read(args.parent_out/'page.json');start=read(args.fade_out/'fade.json')
    for d in (parent,start):
        require_capture_reference(original,d)
        if any(d[k]!=original[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed accepted menu ancestry')
    events=read(args.case_control/'events.json');prefix=attachment(original,manifest,read(args.capture/'events.json'),events,sha((args.case_control/'setup.state').read_bytes()))
    if manifest['setupSha256']!=sha((args.capture/'setup.state').read_bytes()) or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Changed action setup/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0);active=complete=title_started=False;waits=0;points=[];writes=[];irqs=[];rasters=[];irq=None;buttons=[];before=maps=None
    from air_following_scope import FollowingAirCaptureScope
    scope=FollowingAirCaptureScope(True)
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def hook(pc):
        nonlocal active,complete,title_started,waits,irq,before,maps
        if complete:return
        scope.observe(pc,p.memory[0xc098]);now=p._cycles()
        if pc==0x0258 and now==start['points'][0]['cycles']:title_started=True
        if pc==0x2436 and (active or title_started or scope.samples(p.memory[0xc098])):buttons.append(p.memory[0xff8a])
        if pc==0x2707 and now==parent['points'][-1]['cycles']:active=True;before=p.title_maps_storage()
        if not active:return
        if pc in POINTS:
            if pc==0x270b:waits+=1
            name=POINTS[pc];route=0 if name!='end' else {0x26ea:1,0x2b4f:4}[pc]
            points.append(dict(name=name,cycles=now,remaining=480 if name=='begin' else p.register_file.B*256+p.register_file.C,waits=waits,index=p.memory[0xc03e],pattern=word(0xc0b5)-0x2b15,route=route,tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],**geometry()))
            if name=='end':maps=p.title_maps_storage();complete=True
        elif pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested action vector')
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
        with (args.case_control/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,*IRQ_PHASES,0x0258,0x0040,0x0048,0x2484,0x2555,0x268b,0x03d8}:p.hook_register(0,pc,hook,pc)
        for i,e in enumerate(events):
            replay(p,[e])
            if i==len(prefix)-1 and (p._cycles()!=manifest['prefixCycle'] or memory_sha(p)!=manifest['prefixMemorySha256']):raise ValueError('Hooked action fork changed the original prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete action capture or changed full control')
    data=dict(reference=metadata,storageReadOwner='direct-vram-title-v1',inputCase=manifest['inputCase'],romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=original['controlMemorySha256'],points=points,writes=writes,interrupts=irqs,rasters=rasters,beforeMaps=before,maps=maps)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'unlock.rejected.json',data);raise
    write_json(args.out/'unlock.json',data);(args.out/'buttons.txt').write_text(''.join(str(b)+'\n' for b in buttons))
    print(json.dumps(dict(case=data['inputCase'],boundaries=len(points),services=waits,vectors=len(irqs),writes=len(writes))))

def analyze(data,parent):
    points=data['points'];end=parent['points'][-1];irqs=data['interrupts'];services=[p for p in irqs if p['kind']=='vblank'];count=len(services)
    if data['inputCase'] not in CASES or data.get('parentControlMemorySha256')!=parent['controlMemorySha256'] or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('tick','countdown','stat','lcdc','scrollY','lyc','inputHeld','inputPressed')):raise ValueError('Detached original unlock/page state')
    if not count or count>80 or [p['kind'] for p in irqs]!=['stat','stat','vblank']*count or len(data['rasters'])!=4*count:raise ValueError('Incomplete unlock services/rasters')
    names=['begin']+['wait','ready','unlockEntry','unlockReturned','startDecision','selectDecision','actionDecision','timer','timerStored']*(count-1)+['wait','ready','unlockEntry','end']
    if [p['name'] for p in points]!=names or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Incomplete unlock decisions/endpoint')
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data['reference'].get('titleStorageObserver')!='direct-vram-title-v1' or data['beforeMaps']!=parent['maps'] or len(data['maps'])!=2048 or data['maps']!=data['beforeMaps']:raise ValueError('Unlock changed/detached map storage')
    progression=[];progress=0;previous=end['inputHeld'];selector_stores=[]
    for i,p in enumerate(services):
        if p['pressed']!=p['held']&~previous or p['tick']!=(end['tick']+i)&65535 or p['countdown']!=54 or p['held']&15 or not 0<=p['held']<=255:raise ValueError('Unowned unlock fresh/held input/counters')
        previous=p['held'];pressed=p['pressed'];complete=False
        if pressed:
            if pressed==(64,128,32,16)[progress]:progress+=1;complete=progress==4
            else:progress=0
            if complete:progress=0
            selector_stores += [(0xc0b5,0x15+progress),(0xc0b6,0x2b)]
        progression.append(progress)
        if complete!=(i==count-1):raise ValueError('Sequence completed early or failed to complete')
        vblank_work(p)
    if services[0]['held']&~end['inputHeld'] or services[0]['pressed'] or services[1]['held'] or services[1]['pressed']:raise ValueError('Direction fork lost two release samples')
    waits=0;remaining=480;progress=0
    for p in points:
        if p['name']=='ready':waits+=1
        if p['name'] in ('unlockReturned','end'):progress=progression[waits-1]
        if p['name']=='timerStored':remaining-=1
        last=services[waits-1] if waits else None
        wanted=dict(waits=waits,remaining=remaining,index=0,pattern=progress,countdown=54,tick=(end['tick']+waits)&65535,inputHeld=last['held'] if last else end['inputHeld'],inputPressed=last['pressed'] if last else end['inputPressed'],route=4 if p['name']=='end' else 0)
        if any(p[k]!=v for k,v in wanted.items()):raise ValueError('Changed native sequence/page/timer progression')
    writes=data['writes'];raster=[(0xff40,0xfb),(0xff42,88),(0xff42,88),(0xff45,103),(0xc099,2),(0xff40,0xc3),(0xff42,0),(0xff45,23),(0xc099,1)]*count
    if [(p['address'],p['value']) for p in writes if p['address'] not in (0xc0b5,0xc0b6)]!=raster or [(p['address'],p['value']) for p in writes if p['address'] in (0xc0b5,0xc0b6)]!=selector_stores:raise ValueError('Incomplete unlock pointer/raster stores')
    if any(b['cycle']<=a['cycle'] for a,b in zip(writes,writes[1:])) or any(not points[0]['cycles']<p['start']<p['end']<points[-1]['cycles'] for p in irqs) or any(b['start']<=a['end'] for a,b in zip(irqs,irqs[1:])):raise ValueError('Escaped/overlapping unlock work')
    return services




def compare(args):
    from air_title_page_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.page_base)
    manifest=read(args.case_control/'capture-summary.json');original=read(args.capture/'capture-summary.json');data=read(args.unlock_out/'unlock.json');parent=read(args.page_out/'page.json')
    attachment(original,manifest,read(args.capture/'events.json'),read(args.case_control/'events.json'),sha((args.case_control/'setup.state').read_bytes()))
    require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase')) or manifest['setupSha256']!=sha((args.capture/'setup.state').read_bytes()) or not parent['points'][-1]['cycles']<=manifest['prefixCycle']<parent['points'][-1]['cycles']+70224:raise ValueError('Mixed action control/recording or detached fork')
    services=analyze(data,parent)
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-unlock'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');nr=rows('.raster.csv');nw=rows('.writes.csv');maps=rows('.maps.csv');summary=rows('.summary.csv')
    if [len(native),len(ns),len(ni),len(nr),len(nw),len(maps),len(summary)]!=[len(data['points']),len(services),len(data['interrupts']),len(data['rasters']),len(data['writes']),2048,1]:raise ValueError('Incomplete native action outputs')
    differences=[]
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(kind=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered native action boundaries')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in ('remaining','waits','index','tick','countdown','stat','lcdc','scrollY','lyc','inputHeld','inputPressed','route','pattern')}),q)
    for i,(p,q) in enumerate(zip(services,ns)):
        work=vblank_work(p);check('display',i,dict(service=662+i,cycle=p['start']-epoch,tick=p['tick'],countdown=54,display=work['display'],effects=work['effects'],music=work['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],ni)):
        if p['kind']!=q['kind']:raise ValueError('Reordered action vector')
        check('vector',i,dict(vectorCycle=p['start']-epoch,owner=2 if p['returnAddress']==0x261d else 1),q)
    for kind,source,target in [('raster',data['rasters'],nr),('write',data['writes'],nw)]:
        for i,(p,q) in enumerate(zip(source,target)):
            if 'boundary' in p and p['boundary']!=q['boundary']:raise ValueError('Reordered action raster')
            check(kind,i,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k!='boundary'},q)
    for i,(value,q) in enumerate(zip(data['maps'],maps)):check('map',i,dict(address=0x9800+i,value=value),q)
    from air_title_menu_reference import inherited_title_epoch
    lcd=inherited_title_epoch(args.native_base);frame=(services[-1]['start']-epoch-lcd)//70224;final=data['points'][-1]
    check('summary',0,dict(end=final['cycles']-epoch,lcdEpoch=lcd,tick=final['tick'],countdown=54,displays=662+len(services),stats=854+2*len(services),nextStat=lcd+(frame+1)*70224+23*456,nextVBlank=lcd+(frame+1)*70224+144*456,remaining=481-len(services),waits=len(services),index=final['index'],song=1),summary[0])
    report=dict(inputCase=data['inputCase'],comparedBoundaries=len(native),comparedServices=len(ns),comparedVectors=len(ni),comparedRasterBoundaries=len(nr),comparedWrites=len(nw),comparedMapBytes=2048,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='First-page Up/Down/Left/Right sequence, held, wrong and combined-direction cases through 2b4f before password transition. Password presentation/validation, other routes, rendered frames/PCM and production timing remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-unlock.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native title action differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    make=sub.add_parser('prepare');make.add_argument('rom',type=Path);make.add_argument('--page-out',type=Path,required=True);make.add_argument('--actions-control',type=Path,required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    for k in ('parent-out','fade-out','case-control'):record.add_argument('--'+k,type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','unlock-out'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (make,record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();{'prepare':prepare,'capture':capture,'compare':compare}[args.mode](args)
