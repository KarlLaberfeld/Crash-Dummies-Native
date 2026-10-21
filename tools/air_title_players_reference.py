"""Select-page presentation, player toggles and outgoing clear entry."""
import argparse,contextlib,csv,io,shutil
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_title_actions_reference import event_sha,KEYS
from air_title_menu_reference import STORES
from air_title_picture_reference import voice_states,compare_voices
from air_timing import IRQ_PHASES,vblank_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
CASES=('one-start','two-start','back-a','back-b','held-select','combined-toggle-start','combined-a-start','blink')
POINTS={0x2749:'begin',0x27e6:'closeWait',0x27e9:'closeReady',0x27f5:'centerStored',0x27f9:'clearEntry',0x274c:'closeReturned',0x274f:'clearReturned',0x2786:'textReturned',0x27d4:'openWait',0x27d7:'openReady',0x27e3:'openStored',0x2789:'wait',0x278c:'ready',0x27aa:'cursorEntry',0x278f:'cursorReturned',0x27cb:'toggleEntry',0x2796:'toggleReturned',0x1b2f:'end'}
MOTION={0x27ec:0xff4a,0x27f2:0xc09c,0x27da:0xff4a,0x27e0:0xc09c}
RAM_STORES={0x27b1:0xc100,0x27b6:0xc101,0x27c2:0xc102,0x27c7:0xc103,0x27d0:0xc081}

def later_select_parent(data):
    target=data.get('targetPage',0);groups=data.get('groups',[])
    if data.get('version')!=1 or data.get('inputCase')!='carousel' or data.get('laterAction')!='select' or type(target) is not int or not 1<=target<=4 or len(groups)!=2*target or groups[-1]['name']!=str(target-1)+'.idle':raise ValueError('Players lack their later-title Select parent')
    group=groups[-1];end=group['points'][-1]
    if end['name']!='end' or end['route']!=3 or end['index']!=target or end['pattern'] or end['inputPressed']!=4 or group['objects']!=[0]*256 or len(group['maps'])!=2048:raise ValueError('Unowned later Select decision/storage')
    return dict(data,origin='later-title-select',points=[end],maps=group['maps'],objects=group['objects'])


def observation_start(events,later=False):
    # The accepted later decision is inside this exact fresh-Select suffix.
    # Delay only installing read-only hooks; replay every input event unchanged.
    # The exact begin cycle, endpoint hash and all outputs remain mandatory.
    if not later:return 0
    suffix=[['press','select'],['tick',4,True],['release','select'],['tick',2,True],['tick',100,True]]
    if events[-5:]!=suffix:raise ValueError('Unknown later Select observation suffix')
    return len(events)-5


def tail(case):
    if case not in CASES:raise ValueError('Unknown player-selection case')
    events=[['release',key] for key in KEYS]+[['tick',100,True]]
    def press(keys,frames=4):events.extend([['press',key] for key in keys]+[['tick',frames,True]]+[['release',key] for key in keys]+[['tick',2,True]])
    if case in ('two-start','held-select'):press(['select'],24 if case=='held-select' else 4)
    if case=='combined-toggle-start':press(['up','down','select','start'])
    elif case=='combined-a-start':press(['a','start'])
    elif case=='back-a':press(['a'])
    elif case=='back-b':press(['b'])
    else:
        if case=='blink':events.append(['tick',64,True])
        press(['start'])
    events.append(['tick',10,True]);return events

def continuation_observation_start(events,case,extension=()):
    suffix=tail(case)+list(extension)
    if events[-len(suffix):]!=suffix:raise ValueError('Detached later player continuation observation suffix')
    return len(events)-len(suffix)


def attachment(parent,child,events,changed,setup):
    if child['inputCase'] not in CASES or (parent['inputCase']!='select' and not (parent['inputCase']=='carousel' and parent.get('laterAction')=='select' and child.get('origin')=='later-title-select')) or changed!=events+tail(child['inputCase']) or child['parentControlMemorySha256']!=parent['controlMemorySha256'] or child['parentEventsSha256']!=event_sha(events) or child['setupSha256']!=setup or child['romSha256']!=parent['romSha256']:raise ValueError('Detached player-selection controls')
    if child['controlDifferences'] or child['prefixControlHashes']!=[parent['controlMemorySha256']]*2 or child['unhookedControlHashes']!=[child['controlMemorySha256']]*2:raise ValueError('Player-selection controls lack repeated hashes')

def prepare(args):
    parent=read(args.capture/'capture-summary.json');events=read(args.capture/'events.json');setup=sha((args.capture/'setup.state').read_bytes())
    later=getattr(args,'later_parent',None)
    if later:
        source=later_select_parent(read(later/'cycle.json'))
        require_capture_reference(parent,source)
        if any(source[k]!=parent[k] for k in ('romSha256','controlMemorySha256','inputCase')) or parent.get('laterAction')!='select':raise ValueError('Detached later Select controls')
    if parent['controlDifferences'] or (parent['inputCase']!='select' and not later) or sha(args.rom.read_bytes())!=parent['romSha256']:raise ValueError('Changed select control/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(parent,metadata)
    for case in ([args.case] if getattr(args,'case',None) else CASES):
        prefixes=[];hashes=[]
        for _ in range(2):
            p=Reference(str(args.rom),window='null',sound_volume=0)
            try:
                with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
                replay(p,events);prefixes.append(memory_sha(p));replay(p,tail(case));hashes.append(memory_sha(p))
            finally:p.stop(save=False)
        child=dict(**metadata,inputCase=case,romSha256=parent['romSha256'],parentControlMemorySha256=parent['controlMemorySha256'],parentEventsSha256=event_sha(events),setupSha256=setup,controlMemorySha256=hashes[0],controlDifferences=[],prefixControlHashes=prefixes,unhookedControlHashes=hashes,referenceOnly=True)
        if later:child.update(origin='later-title-select',targetPage=source['targetPage'],parentCycleSha256=sha((later/'cycle.json').read_bytes()))
        attachment(parent,child,events,events+tail(case),setup);folder=args.out/case;folder.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.capture/'setup.state',folder/'setup.state');write_json(folder/'capture-summary.json',child);write_json(folder/'events.json',events+tail(case));print(case,'two select controls match',flush=True)

def capture(args):
    manifest=read(args.control/'capture-summary.json');accepted=read(args.capture/'capture-summary.json');later=getattr(args,'later_parent',None);parent=read(args.parent_out/('cycle.json' if later else 'actions.json'));require_capture_reference(accepted,parent)
    if later:
        if args.parent_out!=later or manifest.get('origin')!='later-title-select' or manifest.get('parentCycleSha256')!=sha((later/'cycle.json').read_bytes()) or manifest.get('targetPage')!=parent.get('targetPage'):raise ValueError('Detached later Select capture')
        parent=later_select_parent(parent)
    old=read(args.capture/'events.json');events=read(args.control/'events.json');attachment(accepted,manifest,old,events,sha((args.control/'setup.state').read_bytes()))
    if parent['points'][-1]['route']!=3 or parent['controlMemorySha256']!=accepted['controlMemorySha256'] or (args.capture/'setup.state').read_bytes()!=(args.control/'setup.state').read_bytes() or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Changed select ancestry')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    active=complete=False;points=[];irqs=[];irq=None;writes=[];polls=[];rasters=[];buttons=[];before=maps=before_objects=objects=None;closed=cleared=opened=waits=0
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def hook(pc):
        nonlocal active,complete,irq,before,maps,before_objects,objects,closed,cleared,opened,waits
        if complete:return
        now=p._cycles()
        if pc==0x2749 and now==parent['points'][-1]['cycles']:active=True;before=p.title_maps_storage();before_objects=list(p.memory[0xc100:0xc200])
        if not active:return
        if pc in POINTS:
            name=POINTS[pc]
            if name=='centerStored':closed+=1
            if name in ('closeReturned','clearReturned'):cleared+=1
            if name=='openStored':opened+=1
            if name=='ready':waits+=1
            points.append(dict(name=name,cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),center=p.memory[0xc09c],windowY=p.memory[0xff4a],closed=closed,cleared=cleared,opened=opened,waits=waits,players=p.memory[0xc081],route=(2 if p.memory[0xff8b]&8 else 1) if name=='end' else 0,song=p.memory[0xffce],musicEnabled=p.memory[0xffcf],held=p.memory[0xff8a],pressed=p.memory[0xff8b],**geometry()))
            if name=='end':maps=p.title_maps_storage();objects=list(p.memory[0xc100:0xc200]);complete=True
        elif pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested player-selection vector')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
            if pc==0x0048:rasters.append(dict(boundary='begin',cycle=now,**geometry()))
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            phase=IRQ_PHASES[pc];irq['phases'][phase]=now
            if phase=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if phase=='music':irq['musicEnabled']=p.memory[0xffcf]
            if phase=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:
            if irq['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Mismatched player-selection vector')
            irq['end']=now;irqs.append(irq);irq=None
            if pc==0x2555:rasters.append(dict(boundary='end',cycle=now,**geometry()))
        if pc in STORES:
            value=p.memory[0xc099]+1 if pc in (0x251e,0x2532) else p.register_file.A;writes.append(dict(cycle=now,address=STORES[pc],value=value&255))
        if pc in MOTION:
            value=p.memory[0xff4a]+(-1 if pc==0x27ec else 1) if pc in (0x27ec,0x27da) else p.register_file.A;writes.append(dict(cycle=now,address=MOTION[pc],value=value&255))
        if pc in RAM_STORES:writes.append(dict(cycle=now,address=RAM_STORES[pc],value=p.register_file.A))
        if pc in (0x2801,0x2123):polls.append(dict(cycle=now,mode=p.register_file.A&3))
        if pc in (0x2805,0x2128):writes.append(dict(cycle=now,address=p.register_file.HL if pc==0x2805 else p.register_file.D*256+p.register_file.E,value=p.register_file.A))
    try:
        with (args.control/'setup.state').open('rb') as f:p.load_state(f)
        watch_at=observation_start(old,bool(later))
        for i,e in enumerate(events):
            if i==watch_at:
                for pc in {*POINTS,*STORES,*MOTION,*RAM_STORES,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x2801,0x2805,0x2123,0x2128}:p.hook_register(0,pc,hook,pc)
            replay(p,[e])
            if i==len(old)-1 and memory_sha(p)!=accepted['controlMemorySha256']:raise ValueError('Player-selection observer changed prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete player selection or changed full control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=accepted['controlMemorySha256'],inputCase=manifest['inputCase'],storageReadOwner='direct-vram-title-v1',points=points,interrupts=irqs,writes=writes,polls=polls,rasters=rasters,beforeMaps=before,maps=maps,beforeObjects=before_objects,objects=objects)
    if later:data.update(origin='later-title-select',targetPage=parent['targetPage'],parentCycleSha256=sha((later/'cycle.json').read_bytes()))
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'players.rejected.json',data);raise
    write_json(args.out/'players.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons));print(dict(case=manifest['inputCase'],boundaries=len(points),services=len(buttons)),flush=True)

def analyze(data,parent):
    later=data.get('origin')=='later-title-select'
    if 'groups' in parent and not later:raise ValueError('Missing later Select origin')
    if later:
        parent=later_select_parent(parent) if 'groups' in parent else parent
        if parent.get('origin')!='later-title-select' or data.get('targetPage')!=parent['targetPage']:raise ValueError('Mixed later Select page')
    points=data['points'];first=points[0];end=parent['points'][-1];irqs=data['interrupts'];services=[p for p in irqs if p['kind']=='vblank'];case=data['inputCase']
    if data.get('version')!=1 or case not in CASES or (parent['inputCase']!='select' and not later) or end['route']!=3 or data['parentControlMemorySha256']!=parent['controlMemorySha256'] or first['cycles']!=end['cycles'] or any(first[k]!=end[k] for k in ('tick','countdown','stat','lcdc','scrollY','lyc')) or (first['held'],first['pressed'])!=(end['inputHeld'],end['inputPressed']):raise ValueError('Detached player-selection entry')
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data['reference'].get('titleStorageObserver')!='direct-vram-title-v1' or data['beforeMaps']!=parent['maps'] or len(data['maps'])!=2048 or data['beforeObjects']!=[0]*256 or len(data['objects'])!=256:raise ValueError('Detached player-selection maps/objects')
    names=['begin']+['closeWait','closeReady','centerStored']*40+['clearEntry','closeReturned','clearEntry','clearReturned','textReturned']+['openWait','openReady','openStored']*40
    loop_start=len(names);groups=[];i=loop_start
    if len(points)<loop_start+6:raise ValueError('Missing player-selection loop')
    while i<len(points)-1:
        group=['wait','ready','cursorEntry','cursorReturned'];j=i+4
        if j>=len(points)-1:raise ValueError('Truncated player-selection loop')
        if points[j]['name']=='toggleEntry':group.append('toggleEntry');j+=1
        if j>=len(points)-1:raise ValueError('Truncated player-selection toggle')
        group.append('toggleReturned');j+=1;names+=group;groups.append(points[i:j]);i=j
    names+=['end']
    if [p['name'] for p in points]!=names or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])) or len(services)!=81+len(groups):raise ValueError('Incomplete player-selection presentation/loop')
    previous=first['held']
    for i,p in enumerate(services):
        w=vblank_work(p)
        if p['tick']!=(first['tick']+i)&65535 or p['countdown']!=54 or p['pressed']!=p['held']&~previous or w['display']!=116 or p['musicEnabled']!=1 or len(p.get('voiceStates',[]))!=6:raise ValueError('Unowned player-selection service')
        previous=p['held']
    closed=cleared=opened=waits=players=0
    for p in points:
        name=p['name']
        if name=='centerStored':closed+=1
        if name in ('closeReturned','clearReturned'):cleared+=1
        if name=='openStored':opened+=1
        if name=='ready':waits+=1
        if name=='toggleReturned' and p['pressed']&196:players^=1
        route=(2 if p['pressed']&8 else 1) if name=='end' else 0
        wanted=dict(closed=closed,cleared=cleared,opened=opened,waits=waits,players=players,route=route,countdown=54,song=1,musicEnabled=1,tick=(first['tick']+sum(r['end']+16<=p['cycles'] for r in services))&65535)
        if any(p[k]!=v for k,v in wanted.items()):raise ValueError('Player-selection state escaped its owner')
    if (closed,cleared,opened)!=(40,2,40) or players!=int(case in ('two-start','held-select','combined-toggle-start')) or points[-1]['route']!=(1 if case in ('back-a','back-b') else 2):raise ValueError('Player-selection final route/choice incomplete')
    for group in groups:
        pressed=group[1]['pressed'];toggle=any(p['name']=='toggleEntry' for p in group)
        if toggle!=bool(pressed&196) or any(p['pressed']!=pressed for p in group[1:]):raise ValueError('Player toggle did not follow fresh masked input')
    for label,centers,ys in [('centerStored',list(range(254,175,-2)),list(range(111,71,-1))),('openStored',list(range(178,255,2))+[0],list(range(73,113)))]:
        selected=[p for p in points if p['name']==label]
        if [p['center'] for p in selected]!=centers or [p['windowY'] for p in selected]!=ys:raise ValueError('Incomplete player-selection window motion')
    glyphs=[w for w in data['writes'] if 0x9800<=w['address']<0xa000]
    addresses=[0x9dc0+i for _ in range(2) for i in range(320)]+[0x9c00+32*y+x+i for x,y,n in ((3,15,14),(3,18,15),(3,20,15)) for i in range(n)]
    if [w['address'] for w in glyphs]!=addresses or any(w['value'] for w in glyphs[:640]):raise ValueError('Incomplete player-selection clears/text')
    maps=list(data['beforeMaps']);objects=list(data['beforeObjects'])
    for w in data['writes']:
        if 0x9800<=w['address']<0xa000:maps[w['address']-0x9800]=w['value']
        if 0xc100<=w['address']<0xc200:objects[w['address']-0xc100]=w['value']
    if maps!=data['maps'] or objects!=data['objects']:raise ValueError('Player-selection image/cursor writes incomplete')
    cursor=[w for w in data['writes'] if 0xc100<=w['address']<=0xc103]
    expected=[(a,v) for g in groups for a,v in zip(range(0xc100,0xc104),(72+16*g[1]['players'],24,254+((g[1]['tick']&16)>>4),128))]
    if [(w['address'],w['value']) for w in cursor]!=expected or len(data['rasters'])!=2*sum(p['kind']=='stat' for p in irqs):raise ValueError('Incomplete player cursor/blink/raster')
    return services

def later_arguments(args):
    return argparse.Namespace(**dict({k:v for k,v in vars(args).items() if k not in ('players_out','players_control','later_out','later_base','later_control')},native_base=args.later_base,cycle_out=args.later_out,cycle_control=args.later_control))

def compare_later_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid later player batch')
    from title_cycle_reference import compare_many as qualify
    unique={tuple(sorted((k,str(v)) for k,v in vars(later_arguments(c)).items())):later_arguments(c) for c in cases}
    with contextlib.redirect_stdout(io.StringIO()):qualify(list(unique.values()))
    for case in cases:compare(case,_parent_qualified=True)

def compare(args,_parent_qualified=False):
    later=getattr(args,'later_out',None)
    if not _parent_qualified and later:
        from title_cycle_reference import compare as qualify
        with contextlib.redirect_stdout(io.StringIO()):qualify(later_arguments(args))
    elif not _parent_qualified:
        from air_title_actions_reference import compare as prior_compare
        with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.later_base if later else args.actions_base);data=read(args.players_out/'players.json');parent=read((later/'cycle.json') if later else args.actions_out/'actions.json');accepted=read((args.later_control if later else args.case_control)/'capture-summary.json');child=read(args.players_control/'capture-summary.json')
    if later and (data.get('origin')!='later-title-select' or data.get('targetPage')!=parent['targetPage'] or data.get('parentCycleSha256')!=sha((later/'cycle.json').read_bytes()) or any(data.get(k)!=child.get(k) for k in ('origin','targetPage','parentCycleSha256'))):raise ValueError('Detached later player recording/control')
    attachment(accepted,child,read((args.later_control if later else args.case_control)/'events.json'),read(args.players_control/'events.json'),sha((args.players_control/'setup.state').read_bytes()));require_capture_reference(child,data)
    if any(data[k]!=child[k] for k in ('romSha256','controlMemorySha256','inputCase')):raise ValueError('Mixed player-selection controls')
    services=analyze(data,parent)
    if (args.players_out/'buttons.txt').read_text()!=((later if later else args.actions_out)/'buttons.txt').read_text()+''.join(str(p['held'])+'\n' for p in services):raise ValueError('Detached player-selection buttons')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+('.fifth.later.title-players' if later else '.fifth.title-players')+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');nr=rows('.raster.csv');np=rows('.polls.csv');nw=rows('.writes.csv');maps=rows('.maps.csv');objects=rows('.objects.csv');summary=rows('.summary.csv');voices=rows('.voices.csv')
    if [len(native),len(ns),len(ni),len(nr),len(np),len(nw),len(maps),len(objects),len(summary)]!=[len(data['points']),len(services),len(irqs:=data['interrupts']),len(data['rasters']),len(data['polls']),len(data['writes']),2048,256,1]:raise ValueError('Incomplete native player-selection outputs')
    prior=str(args.later_base)+'.fifth.title-cycle.'+str(parent['targetPage']-1)+'.idle.summary.csv' if later else str(args.actions_base)+'.fifth.title-actions.summary.csv'
    with Path(prior).open(newline='') as f:before=next(csv.DictReader(f))
    preceding=int(before['displays']);differences=compare_voices(services,voices,preceding)
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(category=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered player-selection boundary')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:v for k,v in p.items() if k not in ('name','cycles')}),q)
    for i,(p,q) in enumerate(zip(services,ns)):
        w=vblank_work(p);check('service',i,dict(service=preceding+i,cycle=p['start']-epoch,tick=p['tick'],countdown=54,display=w['display'],effects=w['effects'],music=w['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(irqs,ni)):
        if p['kind']!=q['kind']:raise ValueError('Reordered player-selection interrupt')
        check('vector',i,dict(vectorCycle=p['start']-epoch,owner=2 if p['returnAddress']==0x261d else 1),q)
    for kind,source,target in [('raster',data['rasters'],nr),('poll',data['polls'],np),('write',data['writes'],nw)]:
        for i,(p,q) in enumerate(zip(source,target)):
            if 'boundary' in p and p['boundary']!=q['boundary']:raise ValueError('Reordered player-selection raster')
            check(kind,i,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k!='boundary'},q)
    for kind,source,target,base in [('map',data['maps'],maps,0x9800),('object',data['objects'],objects,0xc100)]:
        for i,(value,q) in enumerate(zip(source,target)):check(kind,i,dict(address=base+i,value=value),q)
    lcd=int(before['lcdEpoch']);end=data['points'][-1]['cycles']-epoch;last=data['points'][-1]
    def deadline(line):
        value=lcd+(end-lcd)//70224*70224+line*456
        return value+70224 if value<=end else value
    check('summary',0,dict(end=end,tick=last['tick'],countdown=54,displays=preceding+len(services),stats=int(before['stats'])+sum(p['kind']=='stat' for p in irqs),lcdEpoch=lcd,nextStat=deadline(23),nextVBlank=deadline(144),**{k:last[k] for k in ('center','closed','cleared','opened','waits','players','route','song','musicEnabled')}),summary[0])
    report=dict(inputCase=data['inputCase'],comparedBoundaries=len(native),comparedServices=len(ns),comparedVectors=len(ni),comparedRasterBoundaries=len(nr),comparedPolls=len(np),comparedWrites=len(nw),comparedMapBytes=2048,comparedObjectBytes=256,comparedVoiceRows=len(voices),preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Select page close/clear/text/open, cursor blinking, fresh toggles and Start/A/B outgoing clear entry. Subsequent clear/menu or campaign continuation, other game paths, frames/PCM and production scheduler remain unqualified.')
    if data.get('origin'):report.update(origin=data['origin'],targetPage=data['targetPage'])
    write_json(Path(str(args.native_base)+'.title-players.comparison.json'),report);print(report)
    if differences:raise ValueError('Native player selection differs')

def compare_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid player-selection batch')
    ignored={'native_base','players_out','players_control'};common={k:v for k,v in vars(cases[0]).items() if k not in ignored}
    if any({k:v for k,v in vars(c).items() if k not in ignored}!=common for c in cases[1:]):raise ValueError('Mixed player-selection parent chain')
    from air_title_actions_reference import compare as qualify
    parent=argparse.Namespace(**vars(cases[0]));parent.native_base=cases[0].actions_base
    with contextlib.redirect_stdout(io.StringIO()):qualify(parent)
    for case in cases:compare(case,_parent_qualified=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    for mode in ('prepare','capture'):
        p=sub.add_parser(mode);p.add_argument('rom',type=Path)
        for name in ('capture','out')+(('control','parent-out') if mode=='capture' else ()):p.add_argument('--'+name,type=Path,required=True)
        p.add_argument('--later-parent',type=Path)
        if mode=='prepare':p.add_argument('--case',choices=CASES)
    for mode in ('compare-batch','compare-later-batch'):
        p=sub.add_parser(mode);p.add_argument('manifest',type=Path)
    args=parser.parse_args()
    if args.mode in ('compare-batch','compare-later-batch'):(compare_later_many if args.mode=='compare-later-batch' else compare_many)([argparse.Namespace(**{k:Path(v) for k,v in c.items()}) for c in read(args.manifest)])
    else:dict(prepare=prepare,capture=capture)[args.mode](args)
if __name__=='__main__':main()
