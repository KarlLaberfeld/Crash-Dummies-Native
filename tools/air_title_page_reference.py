"""Read-only closed-window clears, first title page and reopening."""
import argparse,contextlib,csv,hashlib,io,json
from pathlib import Path
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference

POINTS={0x27f9:'clearEntry',0x26ed:'closeReturned',0x26f0:'clearReturned',0x2701:'pageCall',0x29ac:'pageEntry',0x22e4:'rectangleEntry',0x22f6:'rowReady',0x2301:'copyReturned',0x29b9:'pageReturn',0x2704:'pageReturned',0x27d4:'openWait',0x27d7:'openReady',0x27e3:'centerStored',0x2707:'end'}
STORES={0x2506:0xff40,0x250d:0xff42,0x2519:0xff45,0x251e:0xc099,0x2529:0xff42,0x252d:0xff45,0x2532:0xc099,0x2539:0xff40,0x253c:0xff42,0x2540:0xff45,0x2544:0xc099,0x27da:0xff4a,0x27e0:0xc09c}


def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());parent=json.loads((args.parent_out/'close.json').read_text());start=json.loads((args.fade_out/'fade.json').read_text())
    for d in (parent,start):
        require_capture_reference(manifest,d)
        if any(d[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed page capture parent')
    if manifest['controlDifferences'] or hashlib.sha256(args.rom.read_bytes()).hexdigest()!=manifest['romSha256']:raise ValueError('Changed title-page control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0);active=False;complete=False;title_started=False;opened=cleared=rows=0;points=[];writes=[];polls=[];irqs=[];rasters=[];irq=None;buttons=[];maps=None;before_maps=None
    from air_following_scope import FollowingAirCaptureScope
    scope=FollowingAirCaptureScope(True)
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def point(name,now):points.append(dict(name=name,cycles=now,cleared=cleared,rows=rows,opened=opened,center=p.memory[0xc09c],windowY=p.memory[0xff4a],tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],**geometry()))
    def hook(pc):
        nonlocal active,complete,title_started,opened,cleared,rows,irq,maps,before_maps
        if complete:return
        scope.observe(pc,p.memory[0xc098]);now=p._cycles()
        if pc==0x0258 and now==start['points'][0]['cycles']:title_started=True
        if pc==0x2436 and (active or title_started or scope.samples(p.memory[0xc098])):buttons.append(p.memory[0xff8a])
        if pc==0x27f9 and now==parent['points'][-1]['cycles']:active=True;before_maps=p.title_maps_storage();point('begin',now)
        if not active:return
        if pc in POINTS:
            if pc in (0x26ed,0x26f0):cleared+=1
            if pc==0x22f6:rows+=1
            if pc==0x27e3:opened+=1
            point(POINTS[pc],now)
            if pc==0x2707:maps=p.title_maps_storage();complete=True
        elif pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested title-page vector')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
            if pc==0x0048:rasters.append(dict(boundary='begin',cycle=now,**geometry()))
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            irq['phases'][IRQ_PHASES[pc]]=now
            if IRQ_PHASES[pc]=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b])
        elif pc in (0x2484,0x2555) and irq:
            irq['end']=now;irqs.append(irq);irq=None
            if pc==0x2555:rasters.append(dict(boundary='end',cycle=now,**geometry()))
        if pc in (0x2801,0x2123):polls.append(dict(cycle=now,mode=p.register_file.A&3))
        address=STORES.get(pc);value=p.register_file.A
        if pc==0x2805:address=p.register_file.HL
        if pc==0x2128:address=p.register_file.D*256+p.register_file.E
        if pc in (0x251e,0x2532):value=p.memory[0xc099]+1
        if pc==0x27da:value=p.memory[0xff4a]+1
        if address is not None:writes.append(dict(cycle=now,address=address,value=value&255))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,*IRQ_PHASES,0x0258,0x2801,0x2805,0x2123,0x2128,0x0040,0x0048,0x2484,0x2555,0x268b,0x03d8}:p.hook_register(0,pc,hook,pc)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            else:getattr(p,'button_'+e[0])(e[1])
        digest=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete title page or changed full control')
    data=dict(reference=metadata,storageReadOwner='direct-vram-title-v1',romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,writes=writes,polls=polls,interrupts=irqs,rasters=rasters,beforeMaps=before_maps,maps=maps)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'page.rejected.json',data);raise
    write_json(args.out/'page.json',data);(args.out/'buttons.txt').write_text(''.join(str(b)+'\n' for b in buttons));print(json.dumps(dict(boundaries=len(points),polls=len(polls),writes=len(writes),services=sum(p['kind']=='vblank' for p in irqs),vectors=len(irqs))))


def analyze(data,parent):
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data.get('reference',{}).get('titleStorageObserver')!='direct-vram-title-v1':raise ValueError('Title storage requires explicit direct-read provenance')
    points=data['points'];end=parent['points'][-1]
    names=['begin','clearEntry','closeReturned','clearEntry','clearReturned','pageCall','pageEntry','rectangleEntry']+['rowReady']*10+['copyReturned','pageReturn','pageReturned']+['openWait','openReady','centerStored']*40+['end']
    if [p['name'] for p in points]!=names or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('center','windowY','tick','countdown','stat','lcdc','scrollY','lyc','inputHeld','inputPressed')):raise ValueError('Detached or incomplete title page')
    if points[0]['cycles']!=points[1]['cycles'] or any(b['cycles']<=a['cycles'] for a,b in zip(points[1:],points[2:])) or any(p['countdown']!=54 for p in points):raise ValueError('Unowned title-page boundary order/timer')
    for p in points:
        if p['center']!=(176+2*p['opened'])&255 or p['windowY']!=72+p['opened']:raise ValueError('Unowned reopening motion')
    if [p['rows'] for p in points if p['name']=='rowReady']!=list(range(1,11)) or [p['opened'] for p in points if p['name']=='centerStored']!=list(range(1,41)) or points[-1]['cleared']!=2:raise ValueError('Missing clears/rows/opening steps')
    if [p['cleared'] for p in points]!=[0,0,1,1,2]+[2]*(len(points)-5) or [p['rows'] for p in points]!=[0]*8+list(range(1,11))+[10]*(len(points)-18):raise ValueError('Unowned clear/rectangle progression')
    if any([p['opened'] for p in points if p['name']==name]!=list(range(40)) for name in ('openWait','openReady')):raise ValueError('Missing reopening wait/ready state')
    stores=[p for p in data['writes'] if 0x9800<=p['address']<0xa000]
    addresses=list(range(0x9dc0,0x9f00))*2+[0x9dc0+32*r+c for r in range(10) for c in range(20)]
    if [p['address'] for p in stores]!=addresses or any(p['value'] for p in stores[:640]):raise ValueError('Incomplete title-page map stores')
    if len(data['maps'])!=2048 or len(data.get('beforeMaps',[]))!=2048 or not data['polls'] or any(p['mode'] not in (0,1,2,3) for p in data['polls']):raise ValueError('Incomplete title page graphics observations')
    painted=list(data['beforeMaps'])
    for p in stores:painted[p['address']-0x9800]=p['value']
    if painted!=data['maps']:raise ValueError('Title maps changed outside identified clear/rectangle stores')
    for stream in (data['polls'],data['writes']):
        if any(b['cycle']<=a['cycle'] for a,b in zip(stream,stream[1:])):raise ValueError('Reordered title-page access observations')
    irqs=data['interrupts'];services=[p for p in irqs if p['kind']=='vblank'];stats=[p for p in irqs if p['kind']=='stat']
    if len(data['rasters'])!=2*len(stats) or len(stats)<117 or len(services)<40 or any(p['tick']!=(end['tick']+i)&65535 or p['countdown']!=54 for i,p in enumerate(services)) or points[-1]['tick']!=(end['tick']+len(services))&65535:raise ValueError('Incomplete title page services')
    for p in services:vblank_work(p)
    if any(not points[0]['cycles']<p['start']<p['end']<points[-1]['cycles'] for p in irqs):raise ValueError('Title-page vectors escaped owner')
    return services


def compare(args):
    from air_title_close_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.close_base)
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.page_out/'page.json').read_text());parent=json.loads((args.close_out/'close.json').read_text());require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed title page recording')
    services=analyze(data,parent)
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(json.loads((args.startup/'startup.json').read_text()))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-page'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');nr=rows('.raster.csv');nw=rows('.writes.csv');np=rows('.polls.csv');maps=rows('.maps.csv');summary=rows('.summary.csv')
    if [len(native),len(ns),len(ni),len(nr),len(nw),len(np),len(maps),len(summary)]!=[len(data['points']),len(services),len(data['interrupts']),len(data['rasters']),len(data['writes']),len(data['polls']),2048,1]:raise ValueError('Incomplete native title-page observations')
    differences=[]
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(kind=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered native title-page boundaries')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in ('cleared','rows','opened','center','windowY','tick','countdown','stat','lcdc','scrollY','lyc','inputHeld','inputPressed')}),q)
    for i,(p,q) in enumerate(zip(services,ns)):
        work=vblank_work(p);check('display',i,dict(service=620+i,cycle=p['start']-epoch,tick=p['tick'],countdown=54,display=work['display'],effects=work['effects'],music=work['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],ni)):
        if p['kind']!=q['kind']:raise ValueError('Reordered title-page vector')
        owner=2 if p['returnAddress']==0x261d else 1
        check('vector',i,dict(vectorCycle=p['start']-epoch,owner=owner),q)
    for kind,source,target in [('raster',data['rasters'],nr),('write',data['writes'],nw),('poll',data['polls'],np)]:
        for i,(p,q) in enumerate(zip(source,target)):
            if 'boundary' in p and p['boundary']!=q['boundary']:raise ValueError('Reordered native raster')
            check(kind,i,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k!='boundary'},q)
    for i,(value,q) in enumerate(zip(data['maps'],maps)):check('map',i,dict(address=0x9800+i,value=value),q)
    with Path(str(args.native_base)+'.fifth.title-close.summary.csv').open(newline='') as f:prior=next(csv.DictReader(f))
    lcd=int(prior['lcdEpoch']);frame=(services[-1]['start']-epoch-lcd)//70224;final=data['points'][-1]
    check('summary',0,dict(end=final['cycles']-epoch,lcdEpoch=lcd,tick=final['tick'],countdown=54,displays=620+len(services),stats=731+sum(p['kind']=='stat' for p in data['interrupts']),nextStat=lcd+(frame+1)*70224+23*456,nextVBlank=lcd+(frame+1)*70224+144*456,center=0,cleared=2,rows=10,opened=40,windowY=112,song=1),summary[0])
    report=dict(comparedBoundaries=len(native),comparedServices=len(ns),comparedVectors=len(ni),comparedRasterBoundaries=len(nr),comparedWrites=len(nw),comparedPolls=len(np),comparedMapBytes=2048,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='First post-campaign title page: two clears, rectangle installation and forty reopening waits through return before menu input. WX=166 readiness is bounded to empty eight-pixel OAM/no horizontal scroll; pixels/hardware edge glitches, later menu pages/input, PCM and production timing remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-page.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native first title page differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--parent-out',type=Path,required=True);record.add_argument('--fade-out',type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
