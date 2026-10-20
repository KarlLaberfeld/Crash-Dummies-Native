"""Complete post-feedback title/password return and first music-test screen."""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from password_feedback_reference import prepare as prepare_extension,attachment as attach_extension,logical_voice_projection
from air_title_picture_reference import voice_states,compare_voices
from air_title_menu_reference import STORES
from air_timing import IRQ_PHASES,vblank_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
TAIL=[['tick',100,True]]
POINTS={0x2bdc:'begin',0x2d65:'begin',0x2be6:'titleWait',0x2be9:'titleWaitReturned',0x2bee:'titleMusicReady',0x26ea:'closeCall',0x2b50:'closeCall',0x27e6:'closeWait',0x27e9:'closeReady',0x27f5:'centerStored',0x27f9:'clearEntry',0x26ed:'closeReturned',0x2b53:'closeReturned',0x2d68:'closeReturned',0x26f0:'clearReturned',0x2b56:'clearReturned',0x2d6b:'clearReturned',0x2701:'pageCall',0x29ac:'pageEntry',0x22e4:'rectangleEntry',0x22f6:'rowReady',0x2301:'copyReturned',0x29b9:'pageReturn',0x2704:'pageReturned',0x2b81:'textReturned',0x2da0:'textReturned',0x2b84:'passwordWaitReturned',0x2b89:'passwordMusicReady',0x27d4:'openWait',0x27d7:'openReady',0x27e3:'openStored',0x2b8c:'openReturned',0x2da3:'openReturned',0x2707:'end',0x2ba7:'end',0x2dab:'end'}
MOTION={0x27ec:0xff4a,0x27f2:0xc09c,0x27da:0xff4a,0x27e0:0xc09c}
RAM_STORES={0x2be3:0xc03e,0x2b8d:0xff9b,**{0x2b8f+3*i:0xc0a0+i for i in range(8)},0x2da4:0xff9b,0x2da6:0xff9c,0x2da9:0xff9d}

def attachment(parent,child,events,changed,setup):return attach_extension(parent,child,events,changed,setup,TAIL)
def prepare(args):return prepare_extension(args,TAIL)

def capture(args):
    manifest=read(args.control/'capture-summary.json');accepted=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'feedback.json');require_capture_reference(accepted,parent)
    old=read(args.capture/'events.json');events=read(args.control/'events.json');attachment(accepted,manifest,old,events,sha((args.control/'setup.state').read_bytes()))
    if (args.capture/'setup.state').read_bytes()!=(args.control/'setup.state').read_bytes() or sha(args.rom.read_bytes())!=manifest['romSha256'] or parent['controlMemorySha256']!=accepted['controlMemorySha256']:raise ValueError('Changed password-return ancestry')
    target=3 if parent['points'][-1]['action']==9 else 2 if manifest['inputCase'] in ('submit-a','submit-b') else 1
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    active=complete=False;points=[];raw_songs=[];irqs=[];irq=None;writes=[];polls=[];rasters=[];buttons=[];before=maps=before_objects=objects=None;rows=0;end_tune=end_effect=end_last=None
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def point(name,now):
        enabled=p.memory[0xffcf];points.append(dict(name=name,cycles=now,target=target,tick=word(0xc00a),countdown=word(0xc0b7),center=p.memory[0xc09c],windowY=p.memory[0xff4a],rows=rows,day=p.memory[0xc006],difficulty=p.memory[0xc007],musicEnabled=enabled,song=p.memory[0xffce] if enabled else -1,held=p.memory[0xff8a],pressed=p.memory[0xff8b],cursor=p.memory[0xff9b],**{'digit'+str(i):p.memory[0xc0a0+i] for i in range(8)},**geometry()));raw_songs.append(p.memory[0xffce])
    def hook(pc):
        nonlocal active,complete,irq,before,maps,before_objects,objects,rows,end_tune,end_effect,end_last
        if complete:return
        now=p._cycles()
        if pc in (0x2bdc,0x2d65) and now==parent['points'][-1]['cycles']:active=True;before=p.title_maps_storage();before_objects=list(p.memory[0xc100:0xc200])
        if not active:return
        if pc in POINTS:
            if pc==0x22f6:rows+=1
            point(POINTS[pc],now)
            if pc==0x2d65:point('closeCall',now)
            if POINTS[pc]=='end':maps=p.title_maps_storage();objects=list(p.memory[0xc100:0xc200]);end_tune=p.memory[0xff9b];end_effect=p.memory[0xff9c];end_last=p.memory[0xff9d];complete=True
        elif pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested return vector')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
            if pc==0x0048:rasters.append(dict(boundary='begin',cycle=now,**geometry()))
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            phase=IRQ_PHASES[pc];irq['phases'][phase]=now
            if phase=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if phase=='music':irq['musicEnabled']=p.memory[0xffcf]
            if phase=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:
            if irq['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Mismatched return vector')
            irq['end']=now;irqs.append(irq);irq=None
            if pc==0x2555:rasters.append(dict(boundary='end',cycle=now,**geometry()))
        if pc in STORES:
            value=p.memory[0xc099]+1 if pc in (0x251e,0x2532) else p.register_file.A;writes.append(dict(cycle=now,address=STORES[pc],value=value&255))
        if pc in MOTION:
            value=p.memory[0xff4a]+(-1 if pc==0x27ec else 1) if pc in (0x27ec,0x27da) else p.register_file.A;writes.append(dict(cycle=now,address=MOTION[pc],value=value&255))
        if pc in RAM_STORES:writes.append(dict(cycle=now,address=RAM_STORES[pc],value=p.register_file.A))
        if pc in (0x2801,0x2123):polls.append(dict(cycle=now,mode=p.register_file.A&3))
        if pc==0x2805:writes.append(dict(cycle=now,address=p.register_file.HL,value=p.register_file.A))
        if pc==0x2128:writes.append(dict(cycle=now,address=p.register_file.D*256+p.register_file.E,value=p.register_file.A))
    try:
        with (args.control/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,*MOTION,*RAM_STORES,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x2801,0x2805,0x2123,0x2128}:p.hook_register(0,pc,hook,pc)
        for i,e in enumerate(events):
            replay(p,[e])
            if i==len(old)-1 and memory_sha(p)!=accepted['controlMemorySha256']:raise ValueError('Return observer changed accepted prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete password return or changed full control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=accepted['controlMemorySha256'],inputCase=manifest['inputCase'],storageReadOwner='direct-vram-title-v1',target=target,points=points,rawSongs=raw_songs,interrupts=irqs,writes=writes,polls=polls,rasters=rasters,beforeMaps=before,maps=maps,beforeObjects=before_objects,objects=objects,endTestTune=end_tune,endTestEffect=end_effect,endTestLast=end_last)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'return.rejected.json',data);raise
    write_json(args.out/'return.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons));print(dict(case=manifest['inputCase'],target=target,boundaries=len(points),services=len(buttons),vectors=len(irqs),polls=len(polls),stores=len(writes)),flush=True)

def analyze(data,parent):
    points=data['points'];first=points[0];end=parent['points'][-1];target=data['target'];irqs=data['interrupts'];services=[r for r in irqs if r['kind']=='vblank']
    wanted=3 if end['action']==9 else 2 if data['inputCase'] in ('submit-a','submit-b') else 1
    if data.get('version')!=1 or target!=wanted or data['inputCase']!=parent['inputCase'] or data['parentControlMemorySha256']!=parent['controlMemorySha256'] or first['name']!='begin' or first['cycles']!=end['cycles'] or any(first[k]!=end[k] for k in ('tick','countdown','center','windowY','day','difficulty','musicEnabled','held','pressed','stat','lcdc','scrollY','lyc')):raise ValueError('Detached return/feedback state')
    prefix=['begin']+(['titleWait','titleWaitReturned','titleMusicReady'] if target==1 else [])+['closeCall']+['closeWait','closeReady','centerStored']*40+['clearEntry','closeReturned','clearEntry','clearReturned']
    if target==1:middle=['pageCall','pageEntry','rectangleEntry']+['rowReady']*10+['copyReturned','pageReturn','pageReturned']
    else:middle=['textReturned']+(['passwordWaitReturned','passwordMusicReady'] if target==2 else [])
    names=prefix+middle+['openWait','openReady','openStored']*40+([] if target==1 else ['openReturned'])+['end']
    if [p['name'] for p in points]!=names or any(b['cycles']<=a['cycles'] for i,(a,b) in enumerate(zip(points,points[1:])) if not(target==3 and i==0)) or any(p['countdown']!=54 or p['target']!=target or p['day']!=end['day'] or p['difficulty']!=end['difficulty'] for p in points):raise ValueError('Incomplete return presentation sequence')
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data['reference'].get('titleStorageObserver')!='direct-vram-title-v1' or data['beforeMaps']!=parent['maps'] or data['beforeObjects']!=parent['objects'] or len(data['maps'])!=2048 or data['objects']!=data['beforeObjects']:raise ValueError('Detached return image/object storage')
    maps=list(data['beforeMaps'])
    for w in data['writes']:
        if 0x9800<=w['address']<0xa000:maps[w['address']-0x9800]=w['value']
    if maps!=data['maps']:raise ValueError('Return maps did not publish observed native glyphs')
    glyphs=[w for w in data['writes'] if 0x9800<=w['address']<0xa000]
    if len(glyphs)!=(840 if target==1 else 672 if target==2 else 682) or [(w['address'],w['value']) for w in glyphs[:640]]!=[(0x9dc0+i,0) for _ in range(2) for i in range(320)]:raise ValueError('Incomplete return clears/glyph publication')
    if len(services)!=(83 if target==1 else 82 if target==2 else 81):raise ValueError('Incomplete retained return service extent')
    for label,centers,ys in [('centerStored',list(range(254,175,-2)),list(range(111,71,-1))),('openStored',list(range(178,255,2))+[0],list(range(73,113)))]:
        selected=[p for p in points if p['name']==label]
        if [p['center'] for p in selected]!=centers or [p['windowY'] for p in selected]!=ys:raise ValueError('Return window motion did not retain forty independent steps')
    previous=first['held']
    if len(data['rawSongs'])!=len(points):raise ValueError('Incomplete raw return song observations')
    for i,p in enumerate(services):
        w=vblank_work(p)
        if p['tick']!=(first['tick']+i)&65535 or p['countdown']!=54 or p['pressed']!=p['held']&~previous or w['display']!=116 or w['effects']!=64 or len(p.get('voiceStates',[]))!=6 or p['musicEnabled'] not in (0,1):raise ValueError('Unowned return input/music/counter')
        previous=p['held']
    for p,raw in zip(points,data['rawSongs']):
        if p['tick']!=(first['tick']+sum(r['end']+16<=p['cycles'] for r in services))&65535 or p['song']!=(raw if p['musicEnabled'] else -1):raise ValueError('Return counter/active-song projection lost its owner')
    final=points[-1]
    if (final['center'],final['windowY'],final['rows'])!=(0,112,10 if target==1 else 0) or (final['musicEnabled'],final['song'])!=((1,1) if target==1 else (1,7) if target==2 else (0,-1)):raise ValueError('Return did not reach its final presentation')
    if target==2 and (final['cursor'] or any(final['digit'+str(i)] for i in range(8))):raise ValueError('Returned password input did not reset')
    if target==3 and (data['endTestTune'],data['endTestEffect'],data['endTestLast'])!=(0,0,255):raise ValueError('Music test numbers/last-tune state not initialized')
    if len(data['rasters'])!=2*sum(r['kind']=='stat' for r in irqs):raise ValueError('Incomplete return raster coverage')
    return services

def boundary_projection(data):
    """Preserve raw observations; exclude only the inactive formatter alias."""
    title_scratch=False;result=[]
    for p in data['points']:
        if data['target']==1 and p['name']=='rectangleEntry':title_scratch=True
        excluded=('name','cycles','cursor') if title_scratch else ('name','cycles')
        result.append({k:v for k,v in p.items() if k not in excluded})
    return result

def compare(args,_parent_qualified=False):
    from password_feedback_reference import compare as prior_compare
    if not _parent_qualified:
        with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.feedback_base);data=read(args.return_screen_out/'return.json');parent=read(args.feedback_out/'feedback.json');accepted=read(args.feedback_control/'capture-summary.json');child=read(args.return_screen_control/'capture-summary.json')
    attachment(accepted,child,read(args.feedback_control/'events.json'),read(args.return_screen_control/'events.json'),sha((args.return_screen_control/'setup.state').read_bytes()));require_capture_reference(child,data)
    if any(data[k]!=child[k] for k in ('romSha256','controlMemorySha256','inputCase')):raise ValueError('Mixed return controls')
    services=analyze(data,parent)
    if (args.return_screen_out/'buttons.txt').read_text()!=(args.feedback_out/'buttons.txt').read_text()+''.join(str(r['held'])+'\n' for r in services):raise ValueError('Detached return raw input stream')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.password-return'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');nr=rows('.raster.csv');np=rows('.polls.csv');nw=rows('.writes.csv');maps=rows('.maps.csv');objects=rows('.objects.csv');summary=rows('.summary.csv');voices=rows('.voices.csv')
    if [len(native),len(ns),len(ni),len(nr),len(np),len(nw),len(maps),len(objects),len(summary)]!=[len(data['points']),len(services),len(data['interrupts']),len(data['rasters']),len(data['polls']),len(data['writes']),2048,256,1]:raise ValueError('Incomplete native return outputs')
    with Path(str(args.feedback_base)+'.fifth.password-feedback.summary.csv').open(newline='') as f:before=next(csv.DictReader(f))
    preceding=int(before['displays']);differences=compare_voices(logical_voice_projection(services),voices,preceding)
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(category=kind,index=i,fields=delta))
    projected=boundary_projection(data)
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered native return phase')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**projected[i]),q)
    for i,(p,q) in enumerate(zip(services,ns)):
        w=vblank_work(p);check('service',i,dict(service=preceding+i,cycle=p['start']-epoch,tick=p['tick'],countdown=54,display=w['display'],effects=w['effects'],music=w['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],ni)):
        if p['kind']!=q['kind']:raise ValueError('Reordered return vector')
        check('vector',i,dict(vectorCycle=p['start']-epoch,owner=2 if p['returnAddress']==0x261d else 1),q)
    for kind,source,target in [('raster',data['rasters'],nr),('poll',data['polls'],np),('write',data['writes'],nw)]:
        for i,(p,q) in enumerate(zip(source,target)):
            if 'boundary' in p and p['boundary']!=q['boundary']:raise ValueError('Reordered return raster')
            check(kind,i,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k!='boundary'},q)
    for kind,source,target,base in [('map',data['maps'],maps,0x9800),('object',data['objects'],objects,0xc100)]:
        for i,(value,q) in enumerate(zip(source,target)):check(kind,i,dict(address=base+i,value=value),q)
    lcd=int(before['lcdEpoch']);end=data['points'][-1]['cycles']-epoch;final=data['points'][-1];target=data['target']
    def deadline(line):
        value=lcd+(end-lcd)//70224*70224+line*456
        return value+70224 if value<=end else value
    wanted=dict(end=end,tick=final['tick'],countdown=54,displays=preceding+len(services),stats=int(before['stats'])+sum(p['kind']=='stat' for p in data['interrupts']),lcdEpoch=lcd,nextStat=deadline(23),nextVBlank=deadline(144),target=target,center=0,closed=40,cleared=2,opened=40,rows=final['rows'],day=final['day'],difficulty=final['difficulty'],musicEnabled=final['musicEnabled'],song=final['song'])
    if target!=1:wanted['cursor']=final['cursor']
    if target==3:wanted.update(tune=0,effect=0,lastTune=255)
    check('summary',0,wanted,summary[0])
    report=dict(inputCase=data['inputCase'],target=target,comparedBoundaries=len(native),comparedServices=len(ns),comparedVectors=len(ni),comparedRasterBoundaries=len(nr),comparedPolls=len(np),comparedWrites=len(nw),comparedMapBytes=2048,comparedObjectBytes=256,comparedVoiceRows=len(voices),preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],stoppedDriverPayloadCompared=False,titleFormatterScratchCursorExcluded=target==1,productionSchedulerAccepted=False,evidenceLimit='Complete feedback return to page zero/password input or first music-test screen. Disabled driver song/presets use explicit logical projection. The inactive password cursor byte is formatter scratch from title rectangle entry and excluded there; raw source observations remain recorded. Subsequent menu/test operations, frames/PCM and production scheduling remain unqualified.')
    write_json(Path(str(args.native_base)+'.password-return.comparison.json'),report);print(report)
    if differences:raise ValueError('Native password return differs')

def compare_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid return batch')
    ignored={'native_base','edit_out','edit_control','edit_base','feedback_out','feedback_control','feedback_base','return_screen_out','return_screen_control'}
    common={k:v for k,v in vars(cases[0]).items() if k not in ignored}
    if any({k:v for k,v in vars(c).items() if k not in ignored}!=common for c in cases[1:]):raise ValueError('Return batch mixes distinct parent chains')
    from password_feedback_reference import compare_many as qualify_feedback
    parents=[]
    for case in cases:
        values={k:v for k,v in vars(case).items() if k not in ('return_screen_out','return_screen_control','feedback_base')};values['native_base']=case.feedback_base;parents.append(argparse.Namespace(**values))
    with contextlib.redirect_stdout(io.StringIO()):qualify_feedback(parents)
    for case in cases:compare(case,_parent_qualified=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    make=sub.add_parser('prepare');make.add_argument('rom',type=Path)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    for k in ('control','parent-out'):record.add_argument('--'+k,type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    batch=sub.add_parser('compare-batch');batch.add_argument('manifest',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','unlock-out','password-out','password-control','unlock-base','edit-out','edit-control','password-base','feedback-out','feedback-control','edit-base','return-screen-out','return-screen-control','feedback-base'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (make,record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args()
    if args.mode=='compare-batch':compare_many([argparse.Namespace(**{k:Path(v) for k,v in c.items()}) for c in read(args.manifest)])
    else:dict(prepare=prepare,capture=capture,compare=compare)[args.mode](args)
if __name__=='__main__':main()
