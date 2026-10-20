"""Original music-test controls, all tunes/effects and return edge."""
import argparse,contextlib,csv,io,shutil
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_title_actions_reference import event_sha,KEYS
from air_title_menu_reference import STORES
from password_feedback_reference import logical_voice_projection
from air_title_picture_reference import voice_states,compare_voices
from air_timing import IRQ_PHASES,vblank_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
CASES=('navigation','stop-restart','tunes','effects','completed')
POINTS={0x2dab:'wait',0x2dae:'ready',0x2db3:'tunePositioned',0x2db9:'tuneRendered',0x2dbe:'effectPositioned',0x2dc4:'numbersReady',0x2dcb:'leftReturned',0x2dd2:'rightReturned',0x2dd9:'downReturned',0x2de0:'upReturned',0x2de7:'bReturned',0x2dee:'aReturned',0x2df2:'exitDecision',0x2bdc:'end',0x2e15:'stopEntry',0x2df5:'playEntry',0x2e08:'effectEntry',0x2e0d:'startEntry'}
RAM_STORES={**{pc:0xff9b for pc in (0x2e20,0x2e25,0x2e2b,0x2e30)},**{pc:0xff9c for pc in (0x2e37,0x2e3c,0x2e42,0x2e47)},0x2e17:0xff9d,0x2e0f:0xff9d,0x3711:0xffc6}

def tail(case):
    if case not in CASES:raise ValueError('Unknown music-test case')
    events=[['release',key] for key in KEYS]+[['tick',2,True]]
    def press(keys,frames=4):events.extend([['press',key] for key in keys]+[['tick',frames,True]]+[['release',key] for key in keys]+[['tick',2,True]])
    if case=='navigation':
        press(['left']);press(['right'])
        for _ in range(14):press(['right'])
        for _ in range(14):press(['left'])
        press(['down']);press(['up'])
        for _ in range(26):press(['up'])
        for _ in range(26):press(['down'])
        press(['left','right']);press(['up','down']);press(['right'],24);press(['up'],24);press(['a','b'])
    elif case=='stop-restart':press(['a']);events.append(['tick',30,True]);press(['b']);press(['a']);press(['a','b']);press(['b'])
    elif case=='tunes':
        for tune in range(14):
            press(['a']);events.append(['tick',90,True])
            if tune<13:press(['right'])
    elif case=='effects':
        press(['right']);press(['a']);events.append(['tick',8,True])
        for effect in range(26):
            press(['a']);events.append(['tick',16,True])
            if effect<25:press(['up'])
    else:press(['left']);press(['a']);events.append(['tick',1200,True]);press(['a']);events.append(['tick',8,True]);press(['b'])
    press(['start']);events.append(['tick',12,True]);return events

def attachment(parent,child,events,changed,setup):
    if child['inputCase'] not in CASES or changed!=events+tail(child['inputCase']) or child['parentControlMemorySha256']!=parent['controlMemorySha256'] or child['parentEventsSha256']!=event_sha(events) or child['setupSha256']!=setup or child['romSha256']!=parent['romSha256']:raise ValueError('Detached music-test controls')
    if child['controlDifferences'] or child['prefixControlHashes']!=[parent['controlMemorySha256']]*2 or child['unhookedControlHashes']!=[child['controlMemorySha256']]*2:raise ValueError('Music-test controls lack repeated prefix/full hashes')

def prepare(args):
    parent=read(args.capture/'capture-summary.json');events=read(args.capture/'events.json');setup=sha((args.capture/'setup.state').read_bytes())
    if parent['controlDifferences'] or sha(args.rom.read_bytes())!=parent['romSha256']:raise ValueError('Changed music-test ROM/control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(parent,metadata)
    for case in CASES:
        prefixes=[];hashes=[]
        for _ in range(2):
            p=Reference(str(args.rom),window='null',sound_volume=0)
            try:
                with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
                replay(p,events);prefixes.append(memory_sha(p));replay(p,tail(case));hashes.append(memory_sha(p))
            finally:p.stop(save=False)
        child=dict(**metadata,inputCase=case,romSha256=parent['romSha256'],parentControlMemorySha256=parent['controlMemorySha256'],parentEventsSha256=event_sha(events),setupSha256=setup,controlMemorySha256=hashes[0],controlDifferences=[],prefixControlHashes=prefixes,unhookedControlHashes=hashes,referenceOnly=True)
        attachment(parent,child,events,events+tail(case),setup);folder=args.out/case;folder.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.capture/'setup.state',folder/'setup.state');write_json(folder/'capture-summary.json',child);write_json(folder/'events.json',events+tail(case));print(case,'two music-test controls match',flush=True)

def capture(args):
    manifest=read(args.control/'capture-summary.json');accepted=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'return.json');require_capture_reference(accepted,parent)
    old=read(args.capture/'events.json');events=read(args.control/'events.json');attachment(accepted,manifest,old,events,sha((args.control/'setup.state').read_bytes()))
    if (args.capture/'setup.state').read_bytes()!=(args.control/'setup.state').read_bytes() or sha(args.rom.read_bytes())!=manifest['romSha256'] or parent['controlMemorySha256']!=accepted['controlMemorySha256'] or parent['target']!=3:raise ValueError('Changed test presentation ancestry')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    active=complete=False;points=[];raw_songs=[];raw_flags=[];raw_pending=[];irqs=[];irq=None;writes=[];polls=[];rasters=[];buttons=[];before=maps=before_objects=objects=None
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def hook(pc):
        nonlocal active,complete,irq,before,maps,before_objects,objects
        if complete:return
        now=p._cycles()
        if pc==0x2dab and now==parent['points'][-1]['cycles']:active=True;before=p.title_maps_storage();before_objects=list(p.memory[0xc100:0xc200])
        if not active:return
        if pc in POINTS:
            enabled=p.memory[0xffcf];flags=list(p.memory[0xdea9:0xdead]);pending=p.memory[0xffc6]
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),tune=p.memory[0xff9b],effect=p.memory[0xff9c],lastTune=p.memory[0xff9d],musicEnabled=enabled,song=p.memory[0xffce] if enabled else -1,musicActive=int(bool(enabled and any(flags))),pending=-1 if pending==255 else pending,held=p.memory[0xff8a],pressed=p.memory[0xff8b],day=p.memory[0xc006],difficulty=p.memory[0xc007],center=p.memory[0xc09c],windowY=p.memory[0xff4a],**geometry()));raw_songs.append(p.memory[0xffce]);raw_flags.append(flags);raw_pending.append(pending)
            if pc==0x2bdc:maps=p.title_maps_storage();objects=list(p.memory[0xc100:0xc200]);complete=True
        elif pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested music-test vector')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
            if pc==0x0048:rasters.append(dict(boundary='begin',cycle=now,**geometry()))
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            phase=IRQ_PHASES[pc];irq['phases'][phase]=now
            if phase=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if phase=='music':irq['musicEnabled']=p.memory[0xffcf]
            if phase=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:
            if irq['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Mismatched music-test vector')
            irq['end']=now;irqs.append(irq);irq=None
            if pc==0x2555:rasters.append(dict(boundary='end',cycle=now,**geometry()))
        if pc in STORES:
            value=p.memory[0xc099]+1 if pc in (0x251e,0x2532) else p.register_file.A;writes.append(dict(cycle=now,address=STORES[pc],value=value&255))
        if pc in RAM_STORES:writes.append(dict(cycle=now,address=RAM_STORES[pc],value=p.register_file.A))
        if pc==0x2123:polls.append(dict(cycle=now,mode=p.register_file.A&3))
        if pc==0x2128:writes.append(dict(cycle=now,address=p.register_file.D*256+p.register_file.E,value=p.register_file.A))
    try:
        with (args.control/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,*RAM_STORES,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x2123,0x2128}:p.hook_register(0,pc,hook,pc)
        for i,e in enumerate(events):
            replay(p,[e])
            if i==len(old)-1 and memory_sha(p)!=accepted['controlMemorySha256']:raise ValueError('Music-test observer changed accepted prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete music test or changed full control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=accepted['controlMemorySha256'],inputCase=manifest['inputCase'],storageReadOwner='direct-vram-title-v1',points=points,rawSongs=raw_songs,rawMusicFlags=raw_flags,rawPending=raw_pending,interrupts=irqs,writes=writes,polls=polls,rasters=rasters,beforeMaps=before,maps=maps,beforeObjects=before_objects,objects=objects)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'test.rejected.json',data);raise
    write_json(args.out/'test.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons));print(dict(case=manifest['inputCase'],boundaries=len(points),services=len(buttons),vectors=len(irqs),polls=len(polls),stores=len(writes)),flush=True)

def analyze(data,parent):
    points=data['points'];first=points[0];end=parent['points'][-1];irqs=data['interrupts'];services=[r for r in irqs if r['kind']=='vblank']
    if data.get('version')!=1 or data['inputCase'] not in CASES or data['parentControlMemorySha256']!=parent['controlMemorySha256'] or first['name']!='wait' or first['cycles']!=end['cycles'] or any(first[k]!=end[k] for k in ('tick','countdown','musicEnabled','song','held','pressed','day','difficulty','center','windowY','stat','lcdc','scrollY','lyc')) or (first['tune'],first['effect'],first['lastTune'])!=(0,0,255):raise ValueError('Detached music-test presentation')
    if points[-1]['name']!='end' or len(data['rawSongs'])!=len(points) or len(data['rawMusicFlags'])!=len(points) or len(data['rawPending'])!=len(points) or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Incomplete music-test boundaries/raw observations')
    previous=first['held']
    for i,p in enumerate(services):
        w=vblank_work(p)
        if p['tick']!=(first['tick']+i)&65535 or p['countdown']!=54 or p['pressed']!=p['held']&~previous or w['display']!=116 or len(p.get('voiceStates',[]))!=6 or p['musicEnabled'] not in (0,1):raise ValueError('Unowned music-test input/counter/audio')
        previous=p['held']
    for p,song,flags,pending in zip(points,data['rawSongs'],data['rawMusicFlags'],data['rawPending']):
        if p['countdown']!=54 or not 0<=p['tune']<14 or not 0<=p['effect']<26 or p['lastTune'] not in (*range(14),255) or p['center'] or p['windowY']!=112 or p['day']!=end['day'] or p['difficulty']!=end['difficulty']:raise ValueError('Unowned music-test state mutation')
        if p['tick']!=(first['tick']+sum(r['end']+16<=p['cycles'] for r in services))&65535 or p['song']!=(song if p['musicEnabled'] else -1) or p['musicActive']!=int(bool(p['musicEnabled'] and any(flags))) or p['pending']!=(-1 if pending==255 else pending):raise ValueError('Music-test logical/raw projection incomplete')
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data['reference'].get('titleStorageObserver')!='direct-vram-title-v1' or data['beforeMaps']!=parent['maps'] or len(data['maps'])!=2048 or data['beforeObjects']!=parent['objects'] or data['objects']!=data['beforeObjects']:raise ValueError('Detached music-test image/object storage')
    maps=list(data['beforeMaps'])
    glyphs=[p for p in data['writes'] if 0x9800<=p['address']<0xa000]
    for p in glyphs:maps[p['address']-0x9800]=p['value']
    if maps!=data['maps'] or len(glyphs)!=4*len(services) or [p['address'] for p in glyphs]!=[a for _ in services for a in (0x9e70,0x9e71,0x9eb0,0x9eb1)]:raise ValueError('Music-test hexadecimal displays incomplete')
    names=[p['name'] for p in points]
    if names.count('wait')!=len(services) or names.count('numbersReady')!=len(services) or names.count('exitDecision')!=len(services) or not points[-1]['pressed']&8:raise ValueError('Music-test wait/exit extent incomplete')
    starts=[i for i,p in enumerate(points) if p['name']=='wait'];tune=effect=0;last_tune=255;expected_glyphs=[]
    for index,begin in enumerate(starts):
        group=points[begin:starts[index+1] if index+1<len(starts) else len(points)];pressed=services[index]['pressed']
        expected_glyphs.extend(((0x9e70,(tune>>4)+1),(0x9e71,(tune&15)+1),(0x9eb0,(effect>>4)+1),(0x9eb1,(effect&15)+1)))
        wanted=['wait','ready','tunePositioned','tuneRendered','effectPositioned','numbersReady','leftReturned','rightReturned','downReturned','upReturned']
        if pressed&2:wanted.append('stopEntry')
        wanted.append('bReturned')
        if pressed&1:
            entry=next((p for p in group if p['name']=='playEntry'),None)
            if entry is None:raise ValueError('Missing music-test A decision')
            wanted+=['playEntry','effectEntry' if entry['lastTune']==entry['tune'] and entry['musicActive'] else 'startEntry']
        wanted+=['aReturned','exitDecision']+(['end'] if index==len(starts)-1 else [])
        if [p['name'] for p in group]!=wanted or bool(pressed&8)!=(index==len(starts)-1):raise ValueError('Music-test decisions do not follow fresh input order')
        for p in group:
            name=p['name']
            if name=='leftReturned' and pressed&32:tune=(tune-1)%14
            if name=='rightReturned' and pressed&16:tune=(tune+1)%14
            if name=='downReturned' and pressed&128:effect=(effect-1)%26
            if name=='upReturned' and pressed&64:effect=(effect+1)%26
            if name=='bReturned' and pressed&2:last_tune=255
            if name=='aReturned' and any(q['name']=='startEntry' for q in group):last_tune=tune
            if (p['tune'],p['effect'],p['lastTune'])!=(tune,effect,last_tune):raise ValueError('Music-test selection/last-tune state escaped its owner')
        if group[-2 if index==len(starts)-1 else -1]['pressed']!=pressed:raise ValueError('Music-test input changed before exit decision')
    if [(p['address'],p['value']) for p in glyphs]!=expected_glyphs:raise ValueError('Music-test numbers were not rendered before input')
    if data['inputCase']=='tunes' and set(p['tune'] for p in points if p['name']=='startEntry')!=set(range(14)):raise ValueError('Not all fourteen tunes were started')
    if data['inputCase']=='effects' and set(p['effect'] for p in points if p['name']=='effectEntry')!=set(range(26)):raise ValueError('Not all twenty-six effects were queued')
    if data['inputCase']=='completed' and not any(p['name']=='playEntry' and p['tune']==p['lastTune'] and not p['musicActive'] for p in points):raise ValueError('Completed tune did not exercise restart')
    if len(data['rasters'])!=2*sum(r['kind']=='stat' for r in irqs):raise ValueError('Incomplete music-test raster observations')
    return services

def compare(args,_parent_qualified=False):
    from password_return_reference import compare as prior_compare
    if not _parent_qualified:
        with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.return_screen_base);data=read(args.test_out/'test.json');parent=read(args.return_screen_out/'return.json');accepted=read(args.return_screen_control/'capture-summary.json');child=read(args.test_control/'capture-summary.json')
    attachment(accepted,child,read(args.return_screen_control/'events.json'),read(args.test_control/'events.json'),sha((args.test_control/'setup.state').read_bytes()));require_capture_reference(child,data)
    if any(data[k]!=child[k] for k in ('romSha256','controlMemorySha256','inputCase')):raise ValueError('Mixed music-test controls')
    services=analyze(data,parent)
    if (args.test_out/'buttons.txt').read_text()!=(args.return_screen_out/'buttons.txt').read_text()+''.join(str(p['held'])+'\n' for p in services):raise ValueError('Detached music-test raw inputs')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.music-test'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');nr=rows('.raster.csv');np=rows('.polls.csv');nw=rows('.writes.csv');maps=rows('.maps.csv');objects=rows('.objects.csv');summary=rows('.summary.csv');voices=rows('.voices.csv')
    if [len(native),len(ns),len(ni),len(nr),len(np),len(nw),len(maps),len(objects),len(summary)]!=[len(data['points']),len(services),len(data['interrupts']),len(data['rasters']),len(data['polls']),len(data['writes']),2048,256,1]:raise ValueError('Incomplete native music-test outputs')
    with Path(str(args.return_screen_base)+'.fifth.password-return.summary.csv').open(newline='') as f:before=next(csv.DictReader(f))
    preceding=int(before['displays']);differences=compare_voices(logical_voice_projection(services),voices,preceding)
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(category=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered native music-test boundary')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:v for k,v in p.items() if k not in ('name','cycles')}),q)
    for i,(p,q) in enumerate(zip(services,ns)):
        w=vblank_work(p);check('service',i,dict(service=preceding+i,cycle=p['start']-epoch,tick=p['tick'],countdown=54,display=w['display'],effects=w['effects'],music=w['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],ni)):
        if p['kind']!=q['kind']:raise ValueError('Reordered music-test vector')
        check('vector',i,dict(vectorCycle=p['start']-epoch,owner=2 if p['returnAddress']==0x261d else 1),q)
    for kind,source,target in [('raster',data['rasters'],nr),('poll',data['polls'],np),('write',data['writes'],nw)]:
        for i,(p,q) in enumerate(zip(source,target)):
            if 'boundary' in p and p['boundary']!=q['boundary']:raise ValueError('Reordered music-test raster')
            check(kind,i,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k!='boundary'},q)
    for kind,source,target,base in [('map',data['maps'],maps,0x9800),('object',data['objects'],objects,0xc100)]:
        for i,(value,q) in enumerate(zip(source,target)):check(kind,i,dict(address=base+i,value=value),q)
    lcd=int(before['lcdEpoch']);end=data['points'][-1]['cycles']-epoch;last=data['points'][-1]
    def deadline(line):
        value=lcd+(end-lcd)//70224*70224+line*456
        return value+70224 if value<=end else value
    check('summary',0,dict(end=end,tick=last['tick'],countdown=54,displays=preceding+len(services),stats=int(before['stats'])+sum(p['kind']=='stat' for p in data['interrupts']),lcdEpoch=lcd,nextStat=deadline(23),nextVBlank=deadline(144),waits=len(services),**{k:last[k] for k in ('tune','effect','lastTune','musicEnabled','song','musicActive','pending')},plays=sum(p['name']=='startEntry' for p in data['points']),effects=sum(p['name']=='effectEntry' for p in data['points']),stops=sum(p['name']=='stopEntry' for p in data['points']),exited=1),summary[0])
    report=dict(inputCase=data['inputCase'],comparedBoundaries=len(native),comparedServices=len(ns),comparedVectors=len(ni),comparedRasterBoundaries=len(nr),comparedPolls=len(np),comparedWrites=len(nw),comparedMapBytes=2048,comparedObjectBytes=256,comparedVoiceRows=len(voices),preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],startedTunes=sorted(set(p['tune'] for p in data['points'] if p['name']=='startEntry')),queuedEffects=sorted(set(p['effect'] for p in data['points'] if p['name']=='effectEntry')),stoppedDriverPayloadCompared=False,productionSchedulerAccepted=False,evidenceLimit='Music-test input, hexadecimal display, play/stop/restart/effects and RET through 2bdc. Disabled driver fields use explicit logical projection; raw observations retained. Post-test menu return, frames/PCM and production scheduler remain unqualified.')
    write_json(Path(str(args.native_base)+'.music-test.comparison.json'),report);print(report)
    if differences:raise ValueError('Native music-test loop differs')

def compare_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid music-test batch')
    ignored={'native_base','test_out','test_control'};common={k:v for k,v in vars(cases[0]).items() if k not in ignored}
    if any({k:v for k,v in vars(c).items() if k not in ignored}!=common for c in cases[1:]):raise ValueError('Music-test batch mixes parent chains')
    from password_return_reference import compare as prior_compare
    parent=argparse.Namespace(**{k:v for k,v in vars(cases[0]).items() if k not in ('test_out','test_control','return_screen_base')});parent.native_base=cases[0].return_screen_base
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(parent)
    for case in cases:compare(case,_parent_qualified=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    make=sub.add_parser('prepare');make.add_argument('rom',type=Path)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    for k in ('control','parent-out'):record.add_argument('--'+k,type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    batch=sub.add_parser('compare-batch');batch.add_argument('manifest',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','unlock-out','password-out','password-control','unlock-base','edit-out','edit-control','password-base','feedback-out','feedback-control','edit-base','return-screen-out','return-screen-control','feedback-base','test-out','test-control','return-screen-base'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (make,record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args()
    if args.mode=='compare-batch':compare_many([argparse.Namespace(**{k:Path(v) for k,v in c.items()}) for c in read(args.manifest)])
    else:dict(prepare=prepare,capture=capture,compare=compare)[args.mode](args)
if __name__=='__main__':main()
