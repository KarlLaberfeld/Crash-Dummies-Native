"""Input-only first password presentation; separate from native execution."""
import argparse,contextlib,csv,io,shutil
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_title_actions_reference import event_sha
from air_title_menu_reference import STORES as RASTER_STORES
from air_timing import IRQ_PHASES,vblank_work
from air_title_picture_reference import voice_states,compare_voices
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
POINTS={0x2b4f:'begin',0x2b50:'closeCall',0x27e6:'closeWait',0x27e9:'closeReady',0x27f5:'centerStored',0x27f9:'clearEntry',0x2b53:'closeReturned',0x2b56:'clearReturned',0x2b81:'textReturned',0x2b84:'musicWaitReturned',0x2b89:'musicReady',0x27d4:'openWait',0x27d7:'openReady',0x27e3:'openStored',0x2b8c:'openReturned',0x2ba7:'end'}
STORES={**RASTER_STORES,0x27ec:0xff4a,0x27f2:0xc09c,0x27da:0xff4a,0x27e0:0xc09c}
TAIL=[['tick',100,True]]

def attachment(parent,child,events,changed,setup):
    if child.get('inputCase')!='first-password' or changed!=events+TAIL or child['parentControlMemorySha256']!=parent['controlMemorySha256'] or child['parentEventsSha256']!=event_sha(events) or child['setupSha256']!=setup or child['romSha256']!=parent['romSha256']:raise ValueError('Detached password controls')
    if child['controlDifferences'] or child['prefixControlHashes']!=[parent['controlMemorySha256']]*2 or child['unhookedControlHashes']!=[child['controlMemorySha256']]*2:raise ValueError('Password controls lack repeated unobserved prefix/full hashes')

def prepare(args):
    parent=read(args.capture/'capture-summary.json');events=read(args.capture/'events.json');setup=sha((args.capture/'setup.state').read_bytes())
    if parent['controlDifferences'] or sha(args.rom.read_bytes())!=parent['romSha256']:raise ValueError('Changed password control/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(parent,metadata);prefixes=[];hashes=[]
    for _ in range(2):
        p=Reference(str(args.rom),window='null',sound_volume=0)
        try:
            with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
            replay(p,events);prefixes.append(memory_sha(p));replay(p,TAIL);hashes.append(memory_sha(p))
        finally:p.stop(save=False)
    child=dict(**metadata,inputCase='first-password',romSha256=parent['romSha256'],parentControlMemorySha256=parent['controlMemorySha256'],parentEventsSha256=event_sha(events),setupSha256=setup,controlMemorySha256=hashes[0],controlDifferences=[],prefixControlHashes=prefixes,unhookedControlHashes=hashes,referenceOnly=True)
    attachment(parent,child,events,events+TAIL,setup);args.out.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.capture/'setup.state',args.out/'setup.state');write_json(args.out/'capture-summary.json',child);write_json(args.out/'events.json',events+TAIL);print('Two password controls match',flush=True)

def capture(args):
    manifest=read(args.control/'capture-summary.json');accepted=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'unlock.json');require_capture_reference(accepted,parent)
    events=read(args.control/'events.json');old=read(args.capture/'events.json');attachment(accepted,manifest,old,events,sha((args.control/'setup.state').read_bytes()))
    if (args.capture/'setup.state').read_bytes()!=(args.control/'setup.state').read_bytes() or sha(args.rom.read_bytes())!=manifest['romSha256'] or parent['controlMemorySha256']!=accepted['controlMemorySha256']:raise ValueError('Changed password entry ancestry')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    points=[];irqs=[];writes=[];polls=[];glyphs=[];rasters=[];buttons=[];irq=None;active=complete=False;before=maps=objects=None;objects_unchanged=False;digits=cursor=None
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def hook(pc):
        nonlocal irq,active,complete,before,maps,objects,objects_unchanged,digits,cursor
        if complete:return
        now=p._cycles()
        if pc==0x2b4f and now==parent['points'][-1]['cycles']:active=True;before=p.title_maps_storage();objects=list(p.memory[0xc100:0xc200])
        if not active:return
        if pc in POINTS:
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),center=p.memory[0xc09c],windowY=p.memory[0xff4a],display=p.memory[0xc098],held=p.memory[0xff8a],pressed=p.memory[0xff8b],song=p.memory[0xffce],musicEnabled=p.memory[0xffcf],**geometry()))
            if pc==0x2ba7:maps=p.title_maps_storage();objects_unchanged=objects==list(p.memory[0xc100:0xc200]);digits=list(p.memory[0xc0a0:0xc0a8]);cursor=p.memory[0xff9b];complete=True
        elif pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested password IRQ')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
            if pc==0x0048:rasters.append(dict(boundary='begin',cycle=now,**geometry()))
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            phase=IRQ_PHASES[pc];irq['phases'][phase]=now
            if phase=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if phase=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:
            if irq['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Mismatched password IRQ')
            irq['end']=now;irqs.append(irq);irq=None
            if pc==0x2555:rasters.append(dict(boundary='end',cycle=now,**geometry()))
        if pc in STORES:
            value=p.register_file.A
            if pc in (0x251e,0x2532):value=p.memory[0xc099]+1
            if pc==0x27ec:value=p.memory[0xff4a]-1
            if pc==0x27da:value=p.memory[0xff4a]+1
            writes.append(dict(cycle=now,address=STORES[pc],value=value&255))
        if pc in (0x2123,0x2801):polls.append(dict(cycle=now,mode=p.register_file.A&3))
        if pc==0x2128:glyphs.append(dict(cycle=now,address=p.register_file.D*256+p.register_file.E,value=p.register_file.A))
        if pc==0x2805:glyphs.append(dict(cycle=now,address=p.register_file.HL,value=p.register_file.A))
    try:
        with (args.control/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x2123,0x2128,0x2801,0x2805}:p.hook_register(0,pc,hook,pc)
        for i,e in enumerate(events):
            replay(p,[e])
            if i==len(old)-1 and memory_sha(p)!=accepted['controlMemorySha256']:raise ValueError('Password observer changed accepted prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete password presentation or changed full control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=accepted['controlMemorySha256'],storageReadOwner='direct-vram-title-v1',points=points,interrupts=irqs,writes=writes,polls=polls,glyphs=glyphs,rasters=rasters,beforeMaps=before,maps=maps,objectsUnchanged=objects_unchanged,digits=digits,cursor=cursor)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'password.rejected.json',data);raise
    write_json(args.out/'password.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons));print(dict(boundaries=len(points),services=len(buttons),vectors=len(irqs),glyphs=len(glyphs),polls=len(polls),stores=len(writes)),flush=True)

def analyze(data,parent):
    points=data['points'];first=points[0];end=parent['points'][-1];irqs=data['interrupts'];services=[r for r in irqs if r['kind']=='vblank']
    names=['begin','closeCall']+['closeWait','closeReady','centerStored']*40+['clearEntry','closeReturned','clearEntry','clearReturned','textReturned','musicWaitReturned','musicReady']+['openWait','openReady','openStored']*40+['openReturned','end']
    if data.get('version')!=1 or data['parentControlMemorySha256']!=parent['controlMemorySha256'] or [p['name'] for p in points]!=names or first['cycles']!=end['cycles'] or any(first[k]!=end[k] for k in ('tick','countdown','stat','lcdc','scrollY','lyc')) or first['held']!=end['inputHeld'] or first['pressed']!=end['inputPressed']:raise ValueError('Detached password unlock state/sequence')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])) or any(p['countdown']!=54 or p['display']!=0 or not p['musicEnabled'] for p in points):raise ValueError('Unowned password order/callback/countdown')
    for label,centers,ys in [('centerStored',list(range(254,175,-2)),list(range(111,71,-1))),('openStored',list(range(178,255,2))+[0],list(range(73,113)))]:
        selected=[p for p in points if p['name']==label]
        if [p['center'] for p in selected]!=centers or [p['windowY'] for p in selected]!=ys:raise ValueError('Incomplete password window motion')
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data['reference'].get('titleStorageObserver')!='direct-vram-title-v1' or data['beforeMaps']!=parent['maps'] or len(data['maps'])!=2048 or data.get('objectsUnchanged') is not True or data['digits']!=[0]*8 or data['cursor']!=0:raise ValueError('Detached password storage/reset')
    expected=list(data['beforeMaps'])
    if len(data['glyphs'])!=672:raise ValueError('Incomplete password clear/text stores')
    for w in data['glyphs']:
        if not 0x9dc0<=w['address']<0x9f00 or not 0<=w['value']<128:raise ValueError('Unowned password glyph')
        expected[w['address']-0x9800]=w['value']
    if expected!=data['maps'] or [(p['address'],p['value']) for p in data['glyphs'][:640]]!=[(0x9dc0+i,0) for _ in range(2) for i in range(320)]:raise ValueError('Password clear/publication incomplete')
    if [p['address'] for p in data['glyphs'][640:]]!=[0x9c00+32*row+column+i for column,row,count in ((5,16,10),(3,19,14),(6,21,8)) for i in range(count)]:raise ValueError('Incomplete password text rows')
    for rows,timekey in ((data['glyphs'],'cycle'),(data['writes'],'cycle'),(data['polls'],'cycle')):
        if any(not first['cycles']<r[timekey]<points[-1]['cycles'] for r in rows) or any(b[timekey]<=a[timekey] for a,b in zip(rows,rows[1:])):raise ValueError('Reordered password stores/polls')
    if len(data['polls'])<len(data['glyphs']) or any(p['mode'] not in (0,1,2,3) for p in data['polls']):raise ValueError('Incomplete password readiness observations')
    motion=[(p['address'],p['value']) for p in data['writes'] if p['address'] in (0xff4a,0xc09c)]
    wanted=[(address,value) for i in range(1,41) for address,value in ((0xff4a,112-i),(0xc09c,(-2*i)&255))]+[(address,value) for i in range(1,41) for address,value in ((0xff4a,72+i),(0xc09c,(176+2*i)&255))]
    if motion!=wanted:raise ValueError('Password actual window/center stores incomplete')
    previous=first['held'];last=first['cycles'];switch=next(p['cycles'] for p in points if p['name']=='musicReady')
    if len(services)!=82 or len(data['rasters'])!=2*sum(r['kind']=='stat' for r in irqs):raise ValueError('Incomplete password services/rasters')
    if sum(r['kind']=='stat' for r in irqs)!=242:raise ValueError('Incomplete retained password raster extent')
    for p in irqs:
        if not last<=p['start']<p['end'] or p['end']+16>points[-1]['cycles']:raise ValueError('Reordered password vectors')
        last=p['end']+16
        if p['kind']=='vblank':
            w=vblank_work(p);i=services.index(p)
            if p['tick']!=(first['tick']+i)&65535 or p['countdown']!=54 or p['pressed']!=p['held']&~previous or len(p.get('voiceStates',[]))!=6 or w['display']!=116 or w['effects']!=64:raise ValueError('Unowned password display/input/audio')
            previous=p['held']
        elif p['kind']!='stat':raise ValueError('Unknown password vector')
    for p in points:
        if p['song']!=(7 if p['cycles']>=switch else 1) or p['tick']!=(first['tick']+sum(r['end']+16<=p['cycles'] for r in services))&65535:raise ValueError('Password music/tick boundary lost')
    reset=next(p['cycles'] for p in points if p['name']=='musicWaitReturned')
    if any(reset<r['start']<switch for r in services):raise ValueError('Display observed a partial password music reset')
    for i,p in enumerate([r for r in irqs if r['kind']=='stat']):
        a,b=data['rasters'][2*i:2*i+2]
        if a['boundary']!='begin' or b['boundary']!='end' or a['cycle']!=p['start'] or b['cycle']!=p['end']:raise ValueError('Detached password raster boundaries')
    return services

def compare(args):
    from air_title_unlock_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.unlock_base);parent=read(args.unlock_out/'unlock.json');data=read(args.password_out/'password.json');child=read(args.password_control/'capture-summary.json');accepted=read(args.case_control/'capture-summary.json')
    attachment(accepted,child,read(args.case_control/'events.json'),read(args.password_control/'events.json'),sha((args.password_control/'setup.state').read_bytes()));require_capture_reference(child,data)
    if data['controlMemorySha256']!=child['controlMemorySha256'] or data['romSha256']!=child['romSha256']:raise ValueError('Mixed password control/recording')
    services=analyze(data,parent)
    if (args.password_out/'buttons.txt').read_text()!=(args.unlock_out/'buttons.txt').read_text()+''.join(str(p['held'])+'\n' for p in services):raise ValueError('Detached password raw inputs')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-password'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');nr=rows('.raster.csv');np=rows('.polls.csv');nw=rows('.writes.csv');maps=rows('.maps.csv');summary=rows('.summary.csv');voices=rows('.voices.csv')
    source_writes=sorted(data['glyphs']+data['writes'],key=lambda w:w['cycle'])
    if [len(native),len(ns),len(ni),len(nr),len(np),len(nw),len(maps),len(summary)]!=[len(data['points']),len(services),len(data['interrupts']),len(data['rasters']),len(data['polls']),len(source_writes),2048,1]:raise ValueError('Incomplete native password outputs')
    with Path(str(args.unlock_base)+'.fifth.title-unlock.summary.csv').open(newline='') as f:before=next(csv.DictReader(f))
    preceding=int(before['displays']);differences=compare_voices(services,voices,preceding)
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(category=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered password native boundaries')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:v for k,v in p.items() if k not in ('name','cycles')}),q)
    for i,(p,q) in enumerate(zip(services,ns)):
        w=vblank_work(p);check('service',i,dict(service=preceding+i,cycle=p['start']-epoch,tick=p['tick'],countdown=54,display=w['display'],effects=w['effects'],music=w['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],ni)):
        if p['kind']!=q['kind']:raise ValueError('Reordered password vectors')
        check('vector',i,dict(vectorCycle=p['start']-epoch,owner=2 if p['returnAddress']==0x261d else 1),q)
    for kind,source,target in [('raster',data['rasters'],nr),('poll',data['polls'],np),('write',source_writes,nw)]:
        for i,(p,q) in enumerate(zip(source,target)):
            if 'boundary' in p and p['boundary']!=q['boundary']:raise ValueError('Reordered password raster')
            check(kind,i,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k!='boundary'},q)
    for i,(value,q) in enumerate(zip(data['maps'],maps)):check('map',i,dict(address=0x9800+i,value=value),q)
    lcd=int(before['lcdEpoch']);end=data['points'][-1]['cycles']-epoch
    def deadline(line):
        value=lcd+(end-lcd)//70224*70224+line*456
        return value+70224 if value<=end else value
    check('summary',0,dict(end=end,tick=data['points'][-1]['tick'],countdown=54,displays=preceding+len(services),stats=int(before['stats'])+sum(p['kind']=='stat' for p in data['interrupts']),lcdEpoch=lcd,nextStat=deadline(23),nextVBlank=deadline(144),center=0,closed=40,cleared=2,opened=40,cursor=0,song=7),summary[0])
    report=dict(comparedBoundaries=len(native),comparedServices=len(ns),comparedVectors=len(ni),comparedRasterBoundaries=len(nr),comparedPolls=len(np),comparedWrites=len(nw),comparedMapBytes=len(maps),comparedVoiceRows=len(voices),preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='First password presentation through initial cursor/digit clear at 2ba7. Editing, validation, return, rendered frames/PCM and production scheduling remain unqualified. Active voice projection exclusions match instruction music scope.')
    write_json(Path(str(args.native_base)+'.title-password.comparison.json'),report);print(report)
    if differences:raise ValueError('Native password presentation differs')

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    make=sub.add_parser('prepare');make.add_argument('rom',type=Path)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    for k in ('control','parent-out'):record.add_argument('--'+k,type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','unlock-out','password-out','password-control','unlock-base'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (make,record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();dict(prepare=prepare,capture=capture,compare=compare)[args.mode](args)
if __name__=='__main__':main()
