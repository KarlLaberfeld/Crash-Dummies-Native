"""Original password validation and feedback, before return/test presentation."""
import argparse,contextlib,csv,io,shutil,copy
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_title_actions_reference import event_sha
from air_title_menu_reference import STORES
from air_title_picture_reference import voice_states,compare_voices
from air_timing import IRQ_PHASES,vblank_work,elapsed_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
TAIL=[['tick',200,True]]
POINTS={0x2bcf:'begin',0x2bd0:'finalWait',0x2bd3:'waitReturned',0x2bd6:'audioStopped',0x2bd9:'objectsCleared',0x2c64:'validate',0x2c67:'check',0x2c72:'compareReturned',0x2c78:'rejected',0x2c9e:'accepted',0x27e6:'closeWait',0x27e9:'closeReady',0x27f5:'centerStored',0x27f9:'clearEntry',0x2c7b:'closeReturned',0x2ca2:'closeReturned',0x2c7e:'clearReturned',0x2ca5:'clearReturned',0x2c95:'textReturned',0x2cbc:'textReturned',0x27d4:'openWait',0x27d7:'openReady',0x27e3:'openStored',0x2c98:'opened',0x2cbf:'opened',0x25c4:'holdWait',0x25c7:'holdReady',0x2cc5:'handlerDispatch',0x2bdc:'end',0x2d65:'end',**{0x2d2f+6*i:'actionEntry' for i in range(9)}}
MOTION={0x27ec:0xff4a,0x27f2:0xc09c,0x27da:0xff4a,0x27e0:0xc09c}
ACTION_STORES={0x2d31+6*i:0xc006 if i<5 else 0xc007 for i in range(9)}

def attachment(parent,child,events,changed,setup,extension=TAIL):
    if changed!=events+extension or child['inputCase']!=parent['inputCase'] or child['parentControlMemorySha256']!=parent['controlMemorySha256'] or child['parentEventsSha256']!=event_sha(events) or child['setupSha256']!=setup or child['romSha256']!=parent['romSha256']:raise ValueError('Detached feedback controls')
    if child['controlDifferences'] or child['prefixControlHashes']!=[parent['controlMemorySha256']]*2 or child['unhookedControlHashes']!=[child['controlMemorySha256']]*2:raise ValueError('Feedback controls lack repeated unobserved prefix/full hashes')

def prepare(args,extension=TAIL):
    parent=read(args.capture/'capture-summary.json');events=read(args.capture/'events.json');setup=sha((args.capture/'setup.state').read_bytes())
    if parent['controlDifferences'] or sha(args.rom.read_bytes())!=parent['romSha256']:raise ValueError('Changed feedback ROM/control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(parent,metadata);prefixes=[];hashes=[]
    for _ in range(2):
        p=Reference(str(args.rom),window='null',sound_volume=0)
        try:
            with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
            replay(p,events);prefixes.append(memory_sha(p));replay(p,extension);hashes.append(memory_sha(p))
        finally:p.stop(save=False)
    child=dict(**metadata,inputCase=parent['inputCase'],romSha256=parent['romSha256'],parentControlMemorySha256=parent['controlMemorySha256'],parentEventsSha256=event_sha(events),setupSha256=setup,controlMemorySha256=hashes[0],controlDifferences=[],prefixControlHashes=prefixes,unhookedControlHashes=hashes,referenceOnly=True)
    attachment(parent,child,events,events+extension,setup,extension);args.out.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.capture/'setup.state',args.out/'setup.state');write_json(args.out/'capture-summary.json',child);write_json(args.out/'events.json',events+extension)

def capture(args):
    manifest=read(args.control/'capture-summary.json');accepted=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'edit.json');require_capture_reference(accepted,parent)
    old=read(args.capture/'events.json');events=read(args.control/'events.json');attachment(accepted,manifest,old,events,sha((args.control/'setup.state').read_bytes()))
    if (args.capture/'setup.state').read_bytes()!=(args.control/'setup.state').read_bytes() or sha(args.rom.read_bytes())!=manifest['romSha256'] or parent['controlMemorySha256']!=accepted['controlMemorySha256']:raise ValueError('Changed feedback ancestry')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    active=complete=holding=False;candidate=action=-1;points=[];irqs=[];irq=None;writes=[];polls=[];rasters=[];buttons=[];before=maps=before_objects=objects=None
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def hook(pc):
        nonlocal active,complete,irq,before,maps,before_objects,objects,candidate,action,holding
        if complete:return
        now=p._cycles()
        if pc==0x2bcf and now==parent['points'][-1]['cycles']:active=True;before=p.title_maps_storage();before_objects=list(p.memory[0xc100:0xc200])
        if not active:return
        if pc in POINTS:
            if pc==0x2c67:candidate+=1
            if pc==0x2c9e:action=candidate
            if pc==0x25c4:holding=True
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),center=p.memory[0xc09c],windowY=p.memory[0xff4a],candidate=candidate,action=action,remaining=p.register_file.B*256+p.register_file.C if holding else 60,day=p.memory[0xc006],difficulty=p.memory[0xc007],musicEnabled=p.memory[0xffcf],held=p.memory[0xff8a],pressed=p.memory[0xff8b],**geometry()))
            if POINTS[pc]=='end':maps=p.title_maps_storage();objects=list(p.memory[0xc100:0xc200]);complete=True
        elif pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested feedback interrupt')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
            if pc==0x0048:rasters.append(dict(boundary='begin',cycle=now,**geometry()))
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            phase=IRQ_PHASES[pc];irq['phases'][phase]=now
            if phase=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if phase=='music':irq['musicEnabled']=p.memory[0xffcf]
            if phase=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:
            if irq['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Mismatched feedback vector')
            irq['end']=now;irqs.append(irq);irq=None
            if pc==0x2555:rasters.append(dict(boundary='end',cycle=now,**geometry()))
        if pc in STORES:
            value=p.memory[0xc099]+1 if pc in (0x251e,0x2532) else p.register_file.A;writes.append(dict(cycle=now,address=STORES[pc],value=value&255))
        if pc in MOTION:
            value=p.memory[0xff4a]+(-1 if pc==0x27ec else 1) if pc in (0x27ec,0x27da) else p.register_file.A;writes.append(dict(cycle=now,address=MOTION[pc],value=value&255))
        if pc in ACTION_STORES:writes.append(dict(cycle=now,address=ACTION_STORES[pc],value=p.register_file.A))
        if 0x1b33<=pc<=0x1bd2 or pc==0x2805:writes.append(dict(cycle=now,address=p.register_file.HL,value=p.register_file.A))
        if pc in (0x2801,0x2123):polls.append(dict(cycle=now,mode=p.register_file.A&3))
        if pc==0x2128:writes.append(dict(cycle=now,address=p.register_file.D*256+p.register_file.E,value=p.register_file.A))
    try:
        with (args.control/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,*MOTION,*ACTION_STORES,*IRQ_PHASES,*range(0x1b33,0x1bd3),0x0040,0x0048,0x2484,0x2555,0x2801,0x2805,0x2123,0x2128}:p.hook_register(0,pc,hook,pc)
        for i,e in enumerate(events):
            replay(p,[e])
            if i==len(old)-1 and memory_sha(p)!=accepted['controlMemorySha256']:raise ValueError('Feedback observer changed accepted prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete feedback or changed control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=accepted['controlMemorySha256'],inputCase=manifest['inputCase'],storageReadOwner='direct-vram-title-v1',points=points,interrupts=irqs,writes=writes,polls=polls,rasters=rasters,beforeMaps=before,maps=maps,beforeObjects=before_objects,objects=objects)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'feedback.rejected.json',data);raise
    write_json(args.out/'feedback.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons));print(dict(case=manifest['inputCase'],boundaries=len(points),services=len(buttons),vectors=len(irqs),polls=len(polls),stores=len(writes),action=action),flush=True)

def analyze(data,parent):
    points=data['points'];first=points[0];end=parent['points'][-1];action=points[-1]['action'];irqs=data['interrupts'];services=[r for r in irqs if r['kind']=='vblank']
    if data.get('version')!=1 or data['inputCase']!=parent['inputCase'] or data['parentControlMemorySha256']!=parent['controlMemorySha256'] or first['name']!='begin' or first['cycles']!=end['cycles'] or any(first[k]!=end[k] for k in ('tick','countdown','held','pressed')):raise ValueError('Detached feedback submission')
    wanted=int(data['inputCase'][6:]) if data['inputCase'].startswith('valid-') else -1
    if action!=wanted or not -1<=action<=9:raise ValueError('Original feedback did not resolve its intended password')
    candidates=list(range(11 if action<0 else action+1))
    names=['begin','finalWait','waitReturned','audioStopped','objectsCleared','validate']+[name for i in candidates for name in (('check',) if i==10 else ('check','compareReturned'))]+['rejected' if action<0 else 'accepted']+['closeWait','closeReady','centerStored']*40+['clearEntry','closeReturned','clearEntry','clearReturned','textReturned']+['openWait','openReady','openStored']*40+['opened']+['holdWait','holdReady']*60+(['handlerDispatch'] if action>=0 else [])+(['actionEntry'] if 0<=action<9 else [])+['end']
    if [p['name'] for p in points]!=names or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])) or any(p['countdown']!=54 for p in points) or [p['candidate'] for p in points if p['name']=='check']!=candidates:raise ValueError('Incomplete feedback validation/window/hold sequence')
    stop=next(p['cycles'] for p in points if p['name']=='audioStopped');wait=next(p['cycles'] for p in points if p['name']=='waitReturned')
    if elapsed_work(wait,stop,irqs)!=12384 or any(wait<r['start']<stop for r in services) or any(bool(p['musicEnabled'])!=(p['cycles']<stop) for p in points):raise ValueError('Unowned feedback music stop')
    if [p['remaining'] for p in points if p['name']=='holdWait']!=list(range(60,0,-1)) or points[-1]['remaining']:raise ValueError('Feedback hold did not retain all sixty waits')
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data['reference'].get('titleStorageObserver')!='direct-vram-title-v1' or data['beforeMaps']!=parent['maps'] or data['beforeObjects']!=parent['objects'] or len(data['maps'])!=2048 or len(data['objects'])!=256:raise ValueError('Detached feedback storage')
    maps=list(data['beforeMaps']);objects=list(data['beforeObjects'])
    for w in data['writes']:
        if 0x9800<=w['address']<0xa000:maps[w['address']-0x9800]=w['value']
        if 0xc100<=w['address']<0xc200:objects[w['address']-0xc100]=w['value']
    if maps!=data['maps'] or objects!=data['objects'] or any(objects[:160]):raise ValueError('Feedback map/object publication incomplete')
    glyphs=[w for w in data['writes'] if 0x9800<=w['address']<0xa000]
    if [(w['address'],w['value']) for w in glyphs[:640]]!=[(0x9dc0+i,0) for _ in range(2) for i in range(320)] or [w['address'] for w in glyphs[640:]]!=list(range(0x9e61,0x9e73)):raise ValueError('Incomplete feedback clears/text')
    if [(w['address'],w['value']) for w in data['writes'] if 0xc100<=w['address']<0xc200]!=[(0xc100+i,0) for i in range(160)]:raise ValueError('Incomplete feedback cursor-object clear')
    for label,centers,ys in [('centerStored',list(range(254,175,-2)),list(range(111,71,-1))),('openStored',list(range(178,255,2))+[0],list(range(73,113)))]:
        selected=[p for p in points if p['name']==label]
        if [p['center'] for p in selected]!=centers or [p['windowY'] for p in selected]!=ys:raise ValueError('Feedback window motion lost its forty steps')
    for rows in (data['writes'],data['polls']):
        if any(not first['cycles']<r['cycle']<points[-1]['cycles'] for r in rows) or any(b['cycle']<=a['cycle'] for a,b in zip(rows,rows[1:])):raise ValueError('Reordered feedback stores/accesses')
    if len(data['polls'])<len(glyphs) or any(p['mode'] not in (0,1,2,3) for p in data['polls']):raise ValueError('Incomplete feedback readiness observations')
    if (points[-1]['day'],points[-1]['difficulty'])!=((action if 0<=action<5 else 1),(action-5 if 5<=action<9 else 0)):raise ValueError('Wrong native-selection target in original handler')
    previous=first['held']
    for i,p in enumerate(services):
        work=vblank_work(p)
        if p['tick']!=(first['tick']+i)&65535 or p['pressed']!=p['held']&~previous or p['countdown']!=54 or work['display']!=116 or work['effects']!=64 or len(p.get('voiceStates',[]))!=6 or bool(p['musicEnabled'])!=(p['start']<stop) or (not p['musicEnabled'] and work['music']!=60):raise ValueError('Unowned feedback counter/input/music projection')
        previous=p['held']
    for p in points:
        if p['tick']!=(first['tick']+sum(r['end']+16<=p['cycles'] for r in services))&65535:raise ValueError('Feedback boundary counter lost a service')
    if len(data['rasters'])!=2*sum(r['kind']=='stat' for r in irqs):raise ValueError('Incomplete feedback rasters')
    return services

def logical_voice_projection(services):
    """Keep recorded raw presets; only compare logical voices if disabled."""
    projected=copy.deepcopy(services)
    for p in projected:
        if p['musicEnabled'] not in (0,1):raise ValueError('Unknown feedback driver state')
        if not p['musicEnabled']:
            if vblank_work(p)['music']!=60:raise ValueError('Disabled feedback driver performed active music work')
            for voice in p['voiceStates']:voice['active']=0
    return projected

def compare(args,_parent_qualified=False):
    from password_edit_reference import compare as prior_compare
    if not _parent_qualified:
        with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.edit_base);data=read(args.feedback_out/'feedback.json');parent=read(args.edit_out/'edit.json');accepted=read(args.edit_control/'capture-summary.json');child=read(args.feedback_control/'capture-summary.json')
    attachment(accepted,child,read(args.edit_control/'events.json'),read(args.feedback_control/'events.json'),sha((args.feedback_control/'setup.state').read_bytes()));require_capture_reference(child,data)
    if any(data[k]!=child[k] for k in ('romSha256','controlMemorySha256','inputCase')):raise ValueError('Mixed feedback controls')
    services=analyze(data,parent)
    if (args.feedback_out/'buttons.txt').read_text()!=(args.edit_out/'buttons.txt').read_text()+''.join(str(r['held'])+'\n' for r in services):raise ValueError('Detached feedback input stream')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.password-feedback'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');nr=rows('.raster.csv');np=rows('.polls.csv');nw=rows('.writes.csv');maps=rows('.maps.csv');objects=rows('.objects.csv');summary=rows('.summary.csv');voices=rows('.voices.csv')
    if [len(native),len(ns),len(ni),len(nr),len(np),len(nw),len(maps),len(objects),len(summary)]!=[len(data['points']),len(services),len(data['interrupts']),len(data['rasters']),len(data['polls']),len(data['writes']),2048,256,1]:raise ValueError('Incomplete native feedback outputs')
    with Path(str(args.edit_base)+'.fifth.password-edit.summary.csv').open(newline='') as f:before=next(csv.DictReader(f))
    preceding=int(before['displays']);differences=compare_voices(logical_voice_projection(services),voices,preceding)
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(category=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered native feedback phases')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:v for k,v in p.items() if k not in ('name','cycles')}),q)
    for i,(p,q) in enumerate(zip(services,ns)):
        w=vblank_work(p);check('service',i,dict(service=preceding+i,cycle=p['start']-epoch,tick=p['tick'],countdown=54,display=w['display'],effects=w['effects'],music=w['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],ni)):
        if p['kind']!=q['kind']:raise ValueError('Reordered feedback vector')
        check('vector',i,dict(vectorCycle=p['start']-epoch,owner=2 if p['returnAddress']==0x261d else 1),q)
    for kind,source,target in [('raster',data['rasters'],nr),('poll',data['polls'],np),('write',data['writes'],nw)]:
        for i,(p,q) in enumerate(zip(source,target)):
            if 'boundary' in p and p['boundary']!=q['boundary']:raise ValueError('Reordered feedback raster')
            check(kind,i,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k!='boundary'},q)
    for kind,source,target,base in [('map',data['maps'],maps,0x9800),('object',data['objects'],objects,0xc100)]:
        for i,(value,q) in enumerate(zip(source,target)):check(kind,i,dict(address=base+i,value=value),q)
    lcd=int(before['lcdEpoch']);end=data['points'][-1]['cycles']-epoch
    def deadline(line):
        value=lcd+(end-lcd)//70224*70224+line*456
        return value+70224 if value<=end else value
    final=data['points'][-1];check('summary',0,dict(end=end,tick=final['tick'],countdown=54,displays=preceding+len(services),stats=int(before['stats'])+sum(p['kind']=='stat' for p in data['interrupts']),lcdEpoch=lcd,nextStat=deadline(23),nextVBlank=deadline(144),action=final['action'],day=final['day'],difficulty=final['difficulty'],musicTest=int(final['action']==9),musicEnabled=0,remaining=0),summary[0])
    raw_counts=sorted(set(sum(bool(v['active']&128) for v in p['voiceStates']) for p in services if not p['musicEnabled']))
    report=dict(inputCase=data['inputCase'],comparedBoundaries=len(native),comparedServices=len(ns),comparedVectors=len(ni),comparedRasterBoundaries=len(nr),comparedPolls=len(np),comparedWrites=len(nw),comparedMapBytes=2048,comparedObjectBytes=256,comparedVoiceRows=len(voices),preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],stoppedDriverRawFlagCounts=raw_counts,stoppedDriverPayloadCompared=False,productionSchedulerAccepted=False,evidenceLimit='Validation, accepted/rejected feedback, full hold and simple selection handlers through 2bdc; music-test action stops at 2d65. Raw stopped-driver presets, return/test presentation, frames/PCM and production scheduling remain unqualified.')
    write_json(Path(str(args.native_base)+'.password-feedback.comparison.json'),report);print(report)
    if differences:raise ValueError('Native password feedback differs')

def compare_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid feedback comparison batch')
    ignored={'native_base','edit_out','edit_control','edit_base','feedback_out','feedback_control'}
    common={k:v for k,v in vars(cases[0]).items() if k not in ignored}
    if any({k:v for k,v in vars(c).items() if k not in ignored}!=common for c in cases[1:]):raise ValueError('Feedback batch mixes distinct parent chains')
    from password_edit_reference import compare_many as qualify_edits
    parents=[]
    for case in cases:
        values={k:v for k,v in vars(case).items() if k not in ('feedback_out','feedback_control','edit_base')};values['native_base']=case.edit_base;parents.append(argparse.Namespace(**values))
    with contextlib.redirect_stdout(io.StringIO()):qualify_edits(parents)
    for case in cases:compare(case,_parent_qualified=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    make=sub.add_parser('prepare');make.add_argument('rom',type=Path)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    for k in ('control','parent-out'):record.add_argument('--'+k,type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    batch=sub.add_parser('compare-batch');batch.add_argument('manifest',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','unlock-out','password-out','password-control','unlock-base','edit-out','edit-control','password-base','feedback-out','feedback-control','edit-base'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (make,record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args()
    if args.mode=='compare-batch':compare_many([argparse.Namespace(**{k:Path(v) for k,v in c.items()}) for c in read(args.manifest)])
    else:dict(prepare=prepare,capture=capture,compare=compare)[args.mode](args)
if __name__=='__main__':main()
