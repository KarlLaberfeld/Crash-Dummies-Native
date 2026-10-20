"""Read-only first title-menu idle timeout, attached to accepted reopening."""
import argparse,contextlib,csv,hashlib,io,json
from pathlib import Path
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference

POINTS={0x2707:'begin',0x2708:'wait',0x270b:'ready',0x2b1a:'unlockEntry',0x270e:'unlockReturned',0x2712:'startDecision',0x2717:'selectDecision',0x271e:'actionDecision',0x2720:'timer',0x2721:'timerStored',0x2725:'advance',0x272c:'pageStored',0x26ea:'end'}
STORES={0x2506:0xff40,0x250d:0xff42,0x2519:0xff45,0x251e:0xc099,0x2529:0xff42,0x252d:0xff45,0x2532:0xc099,0x2539:0xff40,0x253c:0xff42,0x2540:0xff45,0x2544:0xc099,0x2729:0xc03e}


def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());parent=json.loads((args.parent_out/'page.json').read_text());start=json.loads((args.fade_out/'fade.json').read_text())
    for d in (parent,start):
        require_capture_reference(manifest,d)
        if any(d[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed page capture parent')
    if manifest['controlDifferences'] or hashlib.sha256(args.rom.read_bytes()).hexdigest()!=manifest['romSha256']:raise ValueError('Changed title-menu control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0);active=False;complete=False;title_started=False;waits=0;points=[];writes=[];irqs=[];rasters=[];irq=None;buttons=[];maps=None;before_maps=None
    from air_following_scope import FollowingAirCaptureScope
    scope=FollowingAirCaptureScope(True)
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def point(name,now):points.append(dict(name=name,cycles=now,remaining=480 if name=='begin' else p.register_file.B*256+p.register_file.C,waits=waits,index=p.memory[0xc03e],pattern=word(0xc0b5)-0x2b15,tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],**geometry()))
    def hook(pc):
        nonlocal active,complete,title_started,waits,irq,maps,before_maps
        if complete:return
        scope.observe(pc,p.memory[0xc098]);now=p._cycles()
        if pc==0x0258 and now==start['points'][0]['cycles']:title_started=True
        if pc==0x2436 and (active or title_started or scope.samples(p.memory[0xc098])):buttons.append(p.memory[0xff8a])
        if pc==0x2707 and now==parent['points'][-1]['cycles']:active=True;before_maps=p.title_maps_storage();
        if not active:return
        if pc in POINTS:
            if pc==0x270b:waits+=1
            point(POINTS[pc],now)
            if pc==0x26ea:maps=p.title_maps_storage();complete=True
        elif pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested title-menu vector')
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
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,*IRQ_PHASES,0x0258,0x0040,0x0048,0x2484,0x2555,0x268b,0x03d8}:p.hook_register(0,pc,hook,pc)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            else:getattr(p,'button_'+e[0])(e[1])
        digest=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete title menu or changed full control')
    data=dict(reference=metadata,storageReadOwner='direct-vram-title-v1',romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,writes=writes,interrupts=irqs,rasters=rasters,beforeMaps=before_maps,maps=maps)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'menu.rejected.json',data);raise
    write_json(args.out/'menu.json',data);(args.out/'buttons.txt').write_text(''.join(str(b)+'\n' for b in buttons));print(json.dumps(dict(boundaries=len(points),writes=len(writes),services=sum(p['kind']=='vblank' for p in irqs),vectors=len(irqs))))


def analyze(data,parent):
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data.get('reference',{}).get('titleStorageObserver')!='direct-vram-title-v1':raise ValueError('Title maps require direct storage provenance')
    points=data['points'];end=parent['points'][-1]
    names=['begin']+['wait','ready','unlockEntry','unlockReturned','startDecision','selectDecision','actionDecision','timer','timerStored']*480+['advance','pageStored','end']
    if [p['name'] for p in points]!=names or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('tick','countdown','stat','lcdc','scrollY','lyc','inputHeld','inputPressed')):raise ValueError('Detached or incomplete first menu timeout')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Reordered menu boundaries')
    if any(p['countdown']!=54 or p['pattern'] or p['inputPressed'] for p in points):raise ValueError('Unowned menu input/pattern/countdown branch')
    for i,p in enumerate(points):
        if i==0:remaining,waits,index=480,0,0
        elif i<=4320:
            loop,phase=divmod(i-1,9);waits=loop+(phase>0);remaining=480-loop-(phase==8);index=0
        else:remaining,waits,index=0,480,int(i>4321)
        if any(p[k]!=v for k,v in dict(remaining=remaining,waits=waits,index=index,tick=(end['tick']+waits)&65535,inputHeld=end['inputHeld']).items()):raise ValueError('Unowned menu duration/page/input progression')
    if len(data['beforeMaps'])!=2048 or data['beforeMaps']!=parent['maps'] or data['beforeMaps']!=data['maps']:raise ValueError('Idle menu changed or detached graphics storage')
    stores=[p for p in data['writes'] if p['address']==0xc03e]
    if len(stores)!=1 or stores[0]['value']!=1 or not points[-3]['cycles']<stores[0]['cycle']<points[-2]['cycles']:raise ValueError('Missing native page advance store')
    if any(p['address'] not in (0xff40,0xff42,0xff45,0xc099,0xc03e) for p in data['writes']):raise ValueError('Unowned idle menu store')
    expected=[(0xff40,0xfb),(0xff42,88),(0xff42,88),(0xff45,103),(0xc099,2),(0xff40,0xc3),(0xff42,0),(0xff45,23),(0xc099,1)]*480+[(0xc03e,1)]
    if [(p['address'],p['value']) for p in data['writes']]!=expected:raise ValueError('Incomplete idle raster/page stores')
    if any(b['cycle']<=a['cycle'] for a,b in zip(data['writes'],data['writes'][1:])):raise ValueError('Reordered menu stores')
    irqs=data['interrupts'];services=[p for p in irqs if p['kind']=='vblank'];stats=[p for p in irqs if p['kind']=='stat']
    if len(services)!=480 or len(stats)!=960 or len(data['rasters'])!=1920 or any(p['tick']!=(end['tick']+i)&65535 or p['countdown']!=54 for i,p in enumerate(services)):raise ValueError('Incomplete idle menu services')
    if [p['kind'] for p in irqs]!=['stat','stat','vblank']*480 or any(b['start']<=a['end'] for a,b in zip(irqs,irqs[1:])):raise ValueError('Reordered/overlapping idle menu vectors')
    for p in services:vblank_work(p)
    if any(not points[0]['cycles']<p['start']<p['end']<points[-1]['cycles'] for p in irqs):raise ValueError('Menu vector escaped owner')
    return services


def compare(args):
    from air_title_page_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.page_base)
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.menu_out/'menu.json').read_text());parent=json.loads((args.page_out/'page.json').read_text());require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed title menu recording')
    services=analyze(data,parent)
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(json.loads((args.startup/'startup.json').read_text()))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-menu'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');nr=rows('.raster.csv');nw=rows('.writes.csv');maps=rows('.maps.csv');summary=rows('.summary.csv')
    if [len(native),len(ns),len(ni),len(nr),len(nw),len(maps),len(summary)]!=[len(data['points']),len(services),len(data['interrupts']),len(data['rasters']),len(data['writes']),2048,1]:raise ValueError('Incomplete native title-menu observations')
    differences=[]
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(kind=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered native title-menu boundaries')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in ('remaining','waits','index','tick','countdown','stat','lcdc','scrollY','lyc','inputHeld','inputPressed')}),q)
    for i,(p,q) in enumerate(zip(services,ns)):
        work=vblank_work(p);check('display',i,dict(service=662+i,cycle=p['start']-epoch,tick=p['tick'],countdown=54,display=work['display'],effects=work['effects'],music=work['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],ni)):
        if p['kind']!=q['kind']:raise ValueError('Reordered title-menu vector')
        owner=2 if p['returnAddress']==0x261d else 1
        check('vector',i,dict(vectorCycle=p['start']-epoch,owner=owner),q)
    for kind,source,target in [('raster',data['rasters'],nr),('write',data['writes'],nw)]:
        for i,(p,q) in enumerate(zip(source,target)):
            if 'boundary' in p and p['boundary']!=q['boundary']:raise ValueError('Reordered native raster')
            check(kind,i,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k!='boundary'},q)
    for i,(value,q) in enumerate(zip(data['maps'],maps)):check('map',i,dict(address=0x9800+i,value=value),q)
    with Path(str(args.native_base)+'.fifth.title-menu.summary.csv').open(newline='') as f:prior=next(csv.DictReader(f))
    lcd=int(prior['lcdEpoch']);frame=(services[-1]['start']-epoch-lcd)//70224;final=data['points'][-1]
    check('summary',0,dict(end=final['cycles']-epoch,lcdEpoch=lcd,tick=final['tick'],countdown=54,displays=662+len(services),stats=854+sum(p['kind']=='stat' for p in data['interrupts']),nextStat=lcd+(frame+1)*70224+23*456,nextVBlank=lcd+(frame+1)*70224+144*456,remaining=0,waits=480,index=1,song=1),summary[0])
    report=dict(comparedBoundaries=len(native),comparedServices=len(ns),comparedVectors=len(ni),comparedRasterBoundaries=len(nr),comparedWrites=len(nw),unchangedMapBytes=2048,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Complete first-page idle timeout: 480 waits with unchanged held input, empty unlock sequence and automatic index advance to page one. Fresh action/direction/reset branches, page-one composition, pixels/PCM and production timing remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-menu.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native first title menu differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--parent-out',type=Path,required=True);record.add_argument('--fade-out',type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','menu-out'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
