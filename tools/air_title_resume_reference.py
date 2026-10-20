"""Original-only pending instruction services and first background clear."""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference

POINTS={0x02bc:'begin',0x26de:'selectionEntry',0x02c0:'livesTest',0x02c5:'backgroundClear',0x25af:'clearEntry',0x02ca:'backgroundCleared',0x02ce:'end'}
STORES={0x25af:0xc035,0x24a1:0xff42,0x2559:0xff42,0x02cb:0xc095}

def capture(args):
    manifest=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'campaign.json');require_capture_reference(manifest,parent)
    if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Changed instruction resume ancestry/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    active=complete=False;points=[];polls=[];writes=[];irqs=[];irq=None;before=maps=objects=None;objects_unchanged=False;buttons=[]
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,before,maps,objects,objects_unchanged,irq
        if complete:return
        now=p._cycles()
        if pc==0x02bc and now==parent['points'][-1]['cycles']:active=True;before=p.title_maps_storage();objects=list(p.memory[0xc100:0xc200])
        if not active:return
        if pc in POINTS:
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],display=p.memory[0xc098],stat=p.memory[0xc099],pendingRequests=p.memory[0xff0f]&3,lives=p.memory[0xc08a],result=p.memory[0xc095]))
            if pc==0x02ce:maps=p.title_maps_storage();objects_unchanged=objects==list(p.memory[0xc100:0xc200]);complete=True
        if pc==0x2123:polls.append(dict(cycle=now,mode=p.register_file.A&3))
        if pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested instruction resume vector')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            irq['phases'][IRQ_PHASES[pc]]=now
            if pc==0x2436:irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
        elif pc in (0x2484,0x2555) and irq:irq['end']=now;irqs.append(irq);irq=None
        address=STORES.get(pc)
        if pc==0x2128:address=p.register_file.D*256+p.register_file.E
        if address is not None:writes.append(dict(cycle=now,address=address,value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,*IRQ_PHASES,0x2123,0x2128,0x0040,0x0048,0x2484,0x2555}:p.hook_register(0,pc,hook,pc)
        replay(p,read(args.capture/'events.json'));digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete instruction resume or changed full control')
    data=dict(reference=metadata,storageReadOwner='direct-vram-title-v1',romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,polls=polls,writes=writes,interrupts=irqs,beforeMaps=before,maps=maps,objectsUnchanged=objects_unchanged)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'resume.rejected.json',data);raise
    write_json(args.out/'resume.json',data)
    prefix=(args.buttons_from/'buttons.txt').read_text();(args.out/'buttons.txt').write_text(prefix+''.join(str(b)+'\n' for b in buttons))
    print(dict(boundaries=len(points),polls=len(polls),writes=len(writes),vectors=len(irqs)))

def analyze(data,parent):
    points=data['points'];end=parent['points'][-1];irqs=data['interrupts']
    if [p['name'] for p in points]!=list(POINTS.values()) or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('tick','countdown','inputHeld','inputPressed','lcdc','pendingRequests')):raise ValueError('Detached instruction resume')
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data.get('reference',{}).get('titleStorageObserver')!='direct-vram-title-v1' or data['beforeMaps']!=parent['maps']:raise ValueError('Detached direct resume map storage')
    if data.get('objectsUnchanged') is not True or len(data['maps'])!=2048 or any(data['maps']):raise ValueError('Instruction clear lost blank maps/object storage')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])) or len(irqs)!=8 or [p['kind'] for p in irqs]!=['vblank','stat','stat','vblank','stat','vblank','stat','vblank']:raise ValueError('Unowned instruction resume service sequence')
    if irqs[0]['start']!=points[0]['cycles']+4+24+20 or irqs[1]['start']!=irqs[0]['end']+16+20 or points[1]['cycles']!=irqs[1]['end']+16 or any(p['returnAddress']!=0x26de for p in irqs[:2]):raise ValueError('Pending requests lost EI follower/priority')
    previous=end['inputHeld'];services=[];raster=[]
    for i,p in enumerate(irqs):
        if not points[0]['cycles']<p['start']<p['end']+16<=points[-1]['cycles'] or (i and p['start']-20<irqs[i-1]['end']+16):raise ValueError('Escaped/overlapping resume vector')
        if i>=2 and p['returnAddress'] not in (0x2128,0x2129,0x212a,0x25be):raise ValueError('Unowned LCD-safe clear interrupt boundary')
        if p['kind']=='vblank':
            if vblank_work(p)!=dict(prefix=180,dma=704,joypad=280,display=144,bookkeeping=240,effects=64,audioBank=68,music=60,restore=120):raise ValueError('Unowned instruction display/audio work')
            if p['tick']!=(end['tick']+len(services))&65535 or p['countdown']!=end['countdown'] or p['pressed']!=p['held']&~previous or not 0<=p['held']<=255 or p['held']&15==15:raise ValueError('Resume lost input/tick/countdown owner')
            previous=p['held'];services.append(p);raster.append(dict(cycle=p['start']+1284,address=0xff42,value=0))
        else:
            if p['end']-p['start']!=288 or p['phases']:raise ValueError('Unowned instruction raster work')
            raster.append(dict(cycle=p['start']+216,address=0xff42,value=0))
    for i,p in enumerate(points):
        finished=[s for s in services if s['end']+16<=p['cycles']];last=finished[-1] if finished else None
        expected=dict(tick=(end['tick']+len(finished))&65535,countdown=end['countdown'],lcdc=0xd1,scrollY=0,display=5,stat=5,pendingRequests=3 if i==0 else 0,lives=5,result=0 if i==6 else 33,inputHeld=last['held'] if last else end['inputHeld'],inputPressed=last['pressed'] if last else end['inputPressed'])
        if any(p[k]!=v for k,v in expected.items()):raise ValueError('Unowned resume boundary state')
    writes=data['writes'];polls=data['polls'];cells=[p for p in writes if 0x9800<=p['address']<0x9c00]
    if len(polls)!=3567 or len(writes)!=1034 or [(p['address'],p['value']) for p in cells]!=[(0x9800+i,0) for i in range(1024)] or any(b['cycle']<=a['cycle'] for a,b in zip(writes,writes[1:])):raise ValueError('Incomplete clear accesses')
    expected=sorted(raster+[dict(cycle=points[4]['cycles'],address=0xc035,value=0x98),dict(cycle=points[5]['cycles']+4,address=0xc095,value=0)]+cells,key=lambda p:p['cycle'])
    if writes!=expected:raise ValueError('Unowned or missing resume stores')
    # Audit every busy/ready read and the completed mainline work between
    # accesses. Observed interrupts are audit targets only, never native input.
    def elapsed(a,b):
        return b-a-sum(p['end']+16-(p['start']-20) for p in irqs if a<=p['start']-20 and p['end']+16<=b)
    if any(any(p['start']-20<=q['cycle']<p['end']+16 for p in irqs) for q in polls+cells):raise ValueError('Map access escaped into service body')
    index=0;previous_store=None
    for cell in cells:
        group=[]
        while index<len(polls) and polls[index]['cycle']<cell['cycle']:group.append(polls[index]);index+=1
        if not group or any(p['mode'] not in (2,3) for p in group[:-1]) or group[-1]['mode'] not in (0,1):raise ValueError('Clear store lacks its independent ready poll')
        origin=previous_store if previous_store is not None else points[4]['cycles'];cost=116 if previous_store is not None else 108
        if elapsed(origin,group[0]['cycle'])!=cost or any(elapsed(a['cycle'],b['cycle'])!=32 for a,b in zip(group,group[1:])) or elapsed(group[-1]['cycle'],cell['cycle'])!=28:raise ValueError('Detached busy/read/store work')
        previous_store=cell['cycle']
    if index!=len(polls) or elapsed(cells[-1]['cycle'],points[5]['cycles'])!=72 or points[-1]['cycles']!=points[5]['cycles']+20 or points[2]['cycles']-points[1]['cycles']!=64 or points[3]['cycles']-points[2]['cycles']!=24 or points[4]['cycles']-points[3]['cycles']!=32:raise ValueError('Detached native life selection/clear return')
    return services

def compare(args):
    from air_title_campaign_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.campaign_base)
    data=read(args.resume_out/'resume.json');parent=read(args.campaign_out/'campaign.json');manifest=read(args.start_control/'capture-summary.json');require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed resume recording/control')
    services=analyze(data,parent)
    prefix=(args.title_start_out/'buttons.txt').read_text()
    if (args.resume_out/'buttons.txt').read_text()!=prefix+''.join(str(p['held'])+'\n' for p in services):raise ValueError('Detached resume input-only extension')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-resume'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');polls=rows('.polls.csv');writes=rows('.writes.csv');maps=rows('.maps.csv');summary=rows('.summary.csv')
    if [len(native),len(ns),len(ni),len(polls),len(writes),len(maps),len(summary)]!=[7,4,8,3567,1034,2048,1]:raise ValueError('Incomplete native instruction resume')
    differences=[]
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(kind=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered resume boundary')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:v for k,v in p.items() if k not in ('name','cycles')}),q)
    for i,(p,q) in enumerate(zip(services,ns)):
        work=vblank_work(p);check('display',i,dict(service=698+i,cycle=p['start']-epoch,tick=p['tick'],countdown=p['countdown'],display=work['display'],effects=work['effects'],music=work['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],ni)):
        if p['kind']!=q['kind']:raise ValueError('Reordered resume vector')
        check('vector',i,dict(vectorCycle=p['start']-epoch,owner=3 if i<2 else 1),q)
    for kind,original,observed in [('poll',data['polls'],polls),('write',data['writes'],writes)]:
        for i,(p,q) in enumerate(zip(original,observed)):check(kind,i,{k:v-epoch if k=='cycle' else v for k,v in p.items()},q)
    for i,(value,q) in enumerate(zip(data['maps'],maps)):check('map',i,dict(address=0x9800+i,value=value),q)
    lcd=parent['writes'][-1]['cycle']+8-epoch;end=data['points'][-1]['cycles']-epoch
    def deadline(line):
        value=lcd+(end-lcd)//70224*70224+line*456
        return value+70224 if value<=end else value
    check('summary',0,dict(end=end,lcdEpoch=lcd,nextStat=deadline(95),nextVBlank=deadline(144),displays=702,stats=931,pendingRequests=0,servicesMasked=0,result=0),summary[0])
    report=dict(comparedBoundaries=7,comparedServices=4,comparedVectors=8,comparedPolls=3567,comparedWrites=1034,comparedMapBytes=2048,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Post-Start single-player Air/easy pending services, native life selection and complete first LCD-on background clear through 02ce. Instruction content, pixels/PCM, other routes and production timing remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-resume.comparison.json'),report);print(report)
    if differences:raise ValueError('Native instruction resume differs')

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    for k in ('parent-out','buttons-from'):record.add_argument('--'+k,type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','actions-out','actions-base','start-control','title-start-out','instruction-out','title-start-base','campaign-out','instruction-prefix-base','resume-out','campaign-base'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)

if __name__=='__main__':main()
