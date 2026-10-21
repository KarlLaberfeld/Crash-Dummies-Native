"""Input-only original title-page carousel, including dynamic high-score formatting."""
import argparse,contextlib,csv,io,shutil
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_title_actions_reference import event_sha
from air_title_menu_reference import POINTS as IDLE,STORES as RASTER_STORES
from air_title_page_reference import POINTS as PAGE,STORES as PAGE_STORES
from air_title_picture_reference import voice_states,compare_voices
from password_feedback_reference import logical_voice_projection
from air_timing import IRQ_PHASES,vblank_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
TAIL=[['tick',4000,True]]
PAGE_POINTS=dict(PAGE)
PAGE_POINTS.update({0x26ea:'begin',0x27e6:'closeWait',0x27e9:'closeReady',0x27f5:'centerStored',0x27e3:'openStored',0x29ba:'pageEntry',0x2a96:'pageEntry',0x2a1a:'pageEntry',0x2add:'pageEntry',0x2a19:'pageReturn',0x2adc:'pageReturn',0x2a95:'pageReturn',0x2b14:'pageReturn',0x2ab1:'scoreRow'})
IDLE_POINTS=dict(IDLE);IDLE_POINTS[0x2733]='wrapStored'
IDLE_STORES={**RASTER_STORES,0x2b2d:0xc0b5,0x2b31:0xc0b6}
DURATIONS=(480,480,960,480,960)

def later_tail(action='automatic'):
    if action=='automatic':return TAIL
    if action not in ('a','b'):raise ValueError('Unowned later carousel action')
    return [['tick',100,True]]+sum(([['press',action],['tick',2,True],['release',action],['tick',100,True]] for _ in range(4)),[])

def idle_extent(group,index,action='automatic'):
    duration=DURATIONS[index];points=group['points'];end=points[-1];names=[p['name'] for p in points];services=[r for r in group['interrupts'] if r['kind']=='vblank'];waits=names.count('wait')
    fresh=action!='automatic'
    if action not in ('automatic','a','b') or not 0<waits<=duration or names.count('ready')!=waits or names.count('timerStored')!=waits-int(fresh) or len(services)!=waits or end['remaining']!=(duration-waits+1 if fresh else 0) or end['waits']!=waits or end['index']!=(index+1)%5 or end['route']!=1 or any(p['pattern'] for p in points):raise ValueError('Incomplete carousel duration/action/wrap')
    if fresh:
        mask=1 if action=='a' else 2
        if waits>=duration or services[-1]['pressed']!=mask or end['inputPressed']!=mask or any(r['pressed'] for r in services[:-1]):raise ValueError('Missing fresh later-page action')
        if [(w['address'],w['value']) for w in group['writes'] if w['address'] in (0xc0b5,0xc0b6)]!=[(0xc0b5,0x15),(0xc0b6,0x2b)]:raise ValueError('Missing later-page unlock mismatch stores')
    elif waits!=duration:raise ValueError('Incomplete automatic carousel duration')

def attachment(parent,child,events,changed,setup):
    if child['inputCase']!='carousel' or changed!=events+later_tail(child.get('laterAction','automatic')) or child['parentControlMemorySha256']!=parent['controlMemorySha256'] or child['parentEventsSha256']!=event_sha(events) or child['setupSha256']!=setup or child['romSha256']!=parent['romSha256'] or child['controlDifferences'] or child['prefixControlHashes']!=[parent['controlMemorySha256']]*2 or child['unhookedControlHashes']!=[child['controlMemorySha256']]*2:raise ValueError('Detached title carousel controls')

def prepare(args):
    parent=read(args.capture/'capture-summary.json');events=read(args.capture/'events.json');setup=sha((args.capture/'setup.state').read_bytes());action=getattr(args,'action','automatic');tail=later_tail(action)
    if parent['inputCase'] not in ('a','b') or parent['controlDifferences'] or sha(args.rom.read_bytes())!=parent['romSha256']:raise ValueError('Unowned carousel parent/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(parent,metadata);hashes=[];prefixes=[]
    for _ in range(2):
        p=Reference(str(args.rom),window='null',sound_volume=0)
        try:
            with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
            replay(p,events);prefixes.append(memory_sha(p));replay(p,tail);hashes.append(memory_sha(p))
        finally:p.stop(save=False)
    data=dict(**metadata,romSha256=parent['romSha256'],controlMemorySha256=hashes[0],controlDifferences=[],inputCase='carousel',laterAction=action,parentInputCase=parent['inputCase'],parentControlMemorySha256=parent['controlMemorySha256'],parentEventsSha256=event_sha(events),setupSha256=setup,prefixControlHashes=prefixes,unhookedControlHashes=hashes,referenceOnly=True)
    attachment(parent,data,events,events+tail,setup);args.out.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.capture/'setup.state',args.out/'setup.state');write_json(args.out/'events.json',events+tail);write_json(args.out/'capture-summary.json',data);print(parent['inputCase'],action,'two carousel prefix/full hashes match',flush=True)

def capture(args):
    accepted=read(args.accepted_control/'capture-summary.json');manifest=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'actions.json');old=read(args.accepted_control/'events.json');events=read(args.capture/'events.json')
    attachment(accepted,manifest,old,events,sha((args.capture/'setup.state').read_bytes()));require_capture_reference(accepted,parent)
    if parent['inputCase'] not in ('a','b') or parent['inputCase']!=manifest['parentInputCase'] or parent['controlMemorySha256']!=accepted['controlMemorySha256'] or manifest['romSha256']!=sha(args.rom.read_bytes()) or (args.capture/'setup.state').read_bytes()!=(args.accepted_control/'setup.state').read_bytes():raise ValueError('Detached carousel ancestry/ROM/setup')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    groups=[];active=complete=False;is_page=True;page_number=0;group=None;irq=None;buttons=[];closed=cleared=opened=rows=waits=0
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def begin(now):
        nonlocal group,closed,cleared,opened,rows,waits
        closed=cleared=opened=rows=waits=0;group=dict(name=str(page_number)+('.page' if is_page else '.idle'),page=p.memory[0xc03e],points=[],interrupts=[],polls=[],writes=[],rasters=[],beforeMaps=p.title_maps_storage(),beforeObjects=list(p.memory[0xc100:0xc200]));groups.append(group)
    def hook(pc):
        nonlocal active,complete,is_page,page_number,irq,closed,cleared,opened,rows,waits
        if complete:return
        now=p._cycles()
        if not active:
            if pc!=0x26ea or now!=parent['points'][-1]['cycles']:return
            active=True;begin(now)
        while True:
            table=PAGE_POINTS if is_page else IDLE_POINTS
            if pc not in table:break
            name=table[pc]
            if is_page:
                closed+=name=='centerStored';cleared+=name in ('closeReturned','clearReturned');opened+=name=='openStored';rows+=name=='rowReady'
                values=dict(center=p.memory[0xc09c],closed=closed,cleared=cleared,opened=opened,rows=rows,windowY=p.memory[0xff4a])
            else:
                waits+=name=='ready';values=dict(remaining=DURATIONS[group['page']] if name=='begin' else 256*p.register_file.B+p.register_file.C,waits=waits,pattern=word(0xc0b5)-0x2b15,route=1 if name=='end' else 0)
            group['points'].append(dict(name=name,cycles=now,index=p.memory[0xc03e],tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],**geometry(),**values))
            if name!='end':break
            if irq:raise ValueError('Carousel segment ended inside vector')
            group.update(maps=p.title_maps_storage(),objects=list(p.memory[0xc100:0xc200]))
            if is_page and page_number==4:complete=True;return
            if not is_page:page_number+=1
            is_page=not is_page;begin(now)
        if pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested carousel vector')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
            if pc==0x0048:group['rasters'].append(dict(boundary='begin',cycle=now,**geometry()))
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            phase=IRQ_PHASES[pc];irq['phases'][phase]=now
            if phase=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if phase=='music':irq['musicEnabled']=p.memory[0xffcf]
            if phase=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:
            irq['end']=now;group['interrupts'].append(irq);irq=None
            if pc==0x2555:group['rasters'].append(dict(boundary='end',cycle=now,**geometry()))
        if pc in (0x2123,0x2801) and is_page:group['polls'].append(dict(cycle=now,mode=p.register_file.A&3))
        address=(PAGE_STORES if is_page else IDLE_STORES).get(pc);value=p.register_file.A
        if pc==0x27ec and is_page:address=0xff4a
        if pc==0x27f2 and is_page:address=0xc09c
        if pc==0x2128 and is_page:address=256*p.register_file.D+p.register_file.E
        if pc==0x2805 and is_page:address=p.register_file.HL
        if pc==0x27da and is_page:value=(p.memory[0xff4a]+1)&255
        if pc==0x27ec and is_page:value=(p.memory[0xff4a]-1)&255
        if pc in (0x251e,0x2532):value=(p.memory[0xc099]+1)&255
        if pc==0x2730 and not is_page:address=0xc03e
        if address is not None:group['writes'].append(dict(cycle=now,address=address,value=value))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in set(PAGE_POINTS)|set(IDLE_POINTS)|set(PAGE_STORES)|set(IDLE_STORES)|set(IRQ_PHASES)|{0x0040,0x0048,0x2484,0x2555,0x2123,0x2128,0x2801,0x2805,0x27ec,0x27f2,0x2730}:p.hook_register(0,pc,hook,pc)
        for n,event in enumerate(events):
            replay(p,[event])
            if n==len(old)-1 and memory_sha(p)!=accepted['controlMemorySha256']:raise ValueError('Carousel observation changed accepted prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete carousel or changed original control')
    data=dict(version=1,reference=metadata,storageReadOwner='direct-vram-title-v1',romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=parent['controlMemorySha256'],inputCase='carousel',laterAction=manifest.get('laterAction','automatic'),parentInputCase=parent['inputCase'],groups=groups)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'cycle.rejected.json',data);raise
    write_json(args.out/'cycle.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons));print(dict(parent=data['parentInputCase'],boundaries=sum(len(g['points']) for g in groups),services=len(buttons)),flush=True)

def analyze(data,parent):
    if data.get('version')!=1 or data['inputCase']!='carousel' or data['parentInputCase'] not in ('a','b') or data['parentInputCase']!=parent['inputCase'] or parent['points'][-1]['route']!=1 or parent['points'][-1]['index']!=1 or data['parentControlMemorySha256']!=parent['controlMemorySha256'] or data.get('storageReadOwner')!='direct-vram-title-v1' or data['reference'].get('titleStorageObserver')!='direct-vram-title-v1' or [g['name'] for g in data['groups']]!=[str(n)+suffix for n in range(5) for suffix in (('.page',) if n==4 else ('.page','.idle'))]:raise ValueError('Detached carousel provenance/segments')
    previous=parent['points'][-1];maps=parent['maps'];held=previous['inputHeld'];tick=previous['tick'];all_services=[]
    for group in data['groups']:
        points=group['points'];first=points[0];end=points[-1];irqs=group['interrupts'];services=[p for p in irqs if p['kind']=='vblank'];page=group['name'].endswith('.page');index=(int(group['name'][0])+1)%5
        if group['page']!=index or first['cycles']!=previous['cycles'] or first['index']!=previous['index'] or any(first[k]!=previous[k] for k in ('tick','countdown','stat','lcdc','scrollY','lyc','inputHeld','inputPressed')) or group['beforeMaps']!=maps or len(group['maps'])!=2048 or group['beforeObjects']!=[0]*256 or group['objects']!=group['beforeObjects'] or points[0]['name']!='begin' or end['name']!='end' or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Detached carousel state/storage extent')
        if page:
            names=[p['name'] for p in points]
            for name,count in [('closeWait',40),('closeReady',40),('centerStored',40),('clearEntry',2),('closeReturned',1),('clearReturned',1),('pageCall',1),('pageEntry',1),('pageReturn',1),('pageReturned',1),('openWait',40),('openReady',40),('openStored',40),('rowReady',10 if index==0 else 0),('scoreRow',8 if index==2 else 0)]:
                if names.count(name)!=count:raise ValueError('Incomplete carousel composition/motion')
            if (end['center'],end['closed'],end['cleared'],end['opened'],end['rows'],end['windowY'])!=(0,40,2,40,10 if index==0 else 0,112) or len(services)<80:raise ValueError('Incomplete carousel reopening')
            stores=[w for w in group['writes'] if 0x9c00<=w['address']<0xa000]
            if len(stores)<640 or any(w['address']!=0x9dc0+n%320 or w['value'] for n,w in enumerate(stores[:640])):raise ValueError('Incomplete carousel two-pass clear')
        else:
            idle_extent(group,index,data.get('laterAction','automatic'))
            selector=[w['value'] for w in group['writes'] if w['address']==0xc03e]
            if selector!=([5,0] if index==4 else [index+1]):raise ValueError('Unowned carousel page-selector stores')
        last=first['cycles']
        for irq in irqs:
            if not last<=irq['start']<irq['end'] or irq['end']+16>end['cycles']:raise ValueError('Incomplete carousel vector extent')
            last=irq['end']+16
            if irq['kind']=='vblank':
                work=vblank_work(irq)
                if work['display']!=116 or irq['tick']!=tick or irq['countdown']!=54 or irq['pressed']!=irq['held']&~held or irq['musicEnabled']!=1 or len(irq.get('voiceStates',[]))!=6:raise ValueError('Unowned carousel audio/input/counters')
                held=irq['held'];tick=(tick+1)&65535
            elif irq['kind']!='stat':raise ValueError('Unknown carousel vector')
        for point in points:
            finished=[r for r in services if r['end']+16<=point['cycles']];owner=finished[-1] if finished else dict(held=first['inputHeld'],pressed=first['inputPressed'])
            if point['tick']!=(first['tick']+len(finished))&65535 or point['countdown']!=54 or (point['inputHeld'],point['inputPressed'])!=(owner['held'],owner['pressed']):raise ValueError('Detached carousel semantic counters/input')
        maps=list(maps)
        for w in group['writes']:
            if 0x9800<=w['address']<0xa000:maps[w['address']-0x9800]=w['value']
        if maps!=group['maps'] or any(b['cycle']<=a['cycle'] for a,b in zip(group['writes'],group['writes'][1:])):raise ValueError('Incomplete carousel map/store publication')
        previous=end;all_services+=services
    return all_services

def compare(args,_parent_qualified=False):
    if not _parent_qualified:
        from air_title_actions_reference import compare as qualify
        with contextlib.redirect_stdout(io.StringIO()):qualify(argparse.Namespace(**dict(vars(args),native_base=args.actions_base)))
    from air_fourth_entry_reference import preserved_native_prefix
    from air_startup_reference import analyze as startup_epoch
    accepted=read(args.case_control/'capture-summary.json');manifest=read(args.cycle_control/'capture-summary.json');data=read(args.cycle_out/'cycle.json');parent=read(args.actions_out/'actions.json')
    attachment(accepted,manifest,read(args.case_control/'events.json'),read(args.cycle_control/'events.json'),sha((args.cycle_control/'setup.state').read_bytes()));require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase','parentControlMemorySha256','parentInputCase')) or data.get('laterAction','automatic')!=manifest.get('laterAction','automatic'):raise ValueError('Mixed carousel controls/recording')
    services=analyze(data,parent)
    if (args.cycle_out/'buttons.txt').read_text()!=(args.actions_out/'buttons.txt').read_text()+''.join(str(p['held'])+'\n' for p in services):raise ValueError('Detached carousel raw inputs')
    retained=preserved_native_prefix(args.native_base,args.actions_base);epoch=startup_epoch(read(args.startup/'startup.json'))['epoch'];differences=[];totals=dict(boundaries=0,services=0,vectors=0,rasterBoundaries=0,polls=0,writes=0,mapBytes=0,voiceRows=0)
    def rows(stem,suffix):
        with Path(stem+suffix).open(newline='') as f:return list(csv.DictReader(f))
    prior=rows(str(args.actions_base)+'.fifth.title-actions','.summary.csv')[0];preceding=int(prior['displays']);stats=int(prior['stats']);lcd=int(prior['lcdEpoch'])
    def check(kind,n,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(category=kind,index=n,fields=delta))
    for group in data['groups']:
        name=group['name'];stem=str(args.native_base)+'.fifth.title-cycle.'+name;points=group['points'];irqs=group['interrupts'];displays=[p for p in irqs if p['kind']=='vblank']
        native,ns,ni,np,nw,nr,summary,maps,voices=[rows(stem,s) for s in ('.csv','.services.csv','.interrupts.csv','.polls.csv','.writes.csv','.raster.csv','.summary.csv','.maps.csv','.voices.csv')]
        if [len(native),len(ns),len(ni),len(np),len(nw),len(nr),len(summary),len(maps),len(voices)]!=[len(points),len(displays),len(irqs),len(group['polls']),len(group['writes']),len(group['rasters']),1,2048,6*len(displays)]:raise ValueError('Incomplete carousel '+name+' outputs')
        for n,(p,q) in enumerate(zip(points,native)):
            if p['name']!=q['boundary']:raise ValueError('Reordered carousel boundaries')
            check(name+' boundary',n,dict(cycle=p['cycles']-epoch,**{k:v for k,v in p.items() if k not in ('name','cycles')}),q)
        for n,(p,q) in enumerate(zip(displays,ns)):
            work=vblank_work(p);check(name+' service',n,dict(service=preceding+n,cycle=p['start']-epoch,tick=p['tick'],countdown=54,display=work['display'],effects=work['effects'],music=work['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
        for n,(p,q) in enumerate(zip(irqs,ni)):
            if p['kind']!=q['kind']:raise ValueError('Reordered carousel vectors')
            check(name+' vector',n,dict(vectorCycle=p['start']-epoch,owner=2 if p['returnAddress']==0x261d else 1),q)
        for kind,source,target in [('poll',group['polls'],np),('store',group['writes'],nw),('raster',group['rasters'],nr)]:
            for n,(p,q) in enumerate(zip(source,target)):
                if 'boundary' in p and p['boundary']!=q['boundary']:raise ValueError('Reordered carousel raster')
                check(name+' '+kind,n,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k!='boundary'},q)
        differences+=compare_voices(logical_voice_projection(displays),voices,preceding)
        for n,(value,q) in enumerate(zip(group['maps'],maps)):check(name+' map',n,dict(address=0x9800+n,value=value),q)
        preceding+=len(displays);stats+=sum(p['kind']=='stat' for p in irqs);last=points[-1];end=last['cycles']-epoch
        def deadline(line):
            value=lcd+(end-lcd)//70224*70224+line*456
            return value+70224 if value<=end else value
        page=name.endswith('.page');index=group['page'];wanted=dict(end=end,lcdEpoch=lcd,tick=last['tick'],countdown=54,displays=preceding,stats=stats,nextStat=deadline(23),nextVBlank=deadline(144),index=last['index'],remaining=DURATIONS[index] if page else last['remaining'],route=0 if page else 1,song=1)
        if set(wanted)!=set(summary[0]):raise ValueError('Unqualified carousel summary')
        check(name+' summary',0,wanted,summary[0])
        for key,number in [('boundaries',len(points)),('services',len(ns)),('vectors',len(ni)),('rasterBoundaries',len(nr)),('polls',len(np)),('writes',len(nw)),('mapBytes',2048),('voiceRows',len(voices))]:totals[key]+=number
    report=dict(parentInputCase=data['parentInputCase'],laterAction=data.get('laterAction','automatic'),**{'compared'+k[0].upper()+k[1:]:v for k,v in totals.items()},preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Five-page original title carousel after first-page A/B: composition, retained initial high scores/BCD formatting, wrap, access/raster timing/maps and active music. Automatic cases require complete 480/960 durations; fresh A/B cases independently require each of the four later pages to exit on its fresh edge with the correct retained timer. Other fresh routes, modified high scores, frames/PCM and production scheduling remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-cycle.comparison.json'),report);print(report)
    if differences:raise ValueError('Native title carousel differs from the original')

def compare_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid carousel batch')
    ignored={'native_base','actions_base','case_control','actions_out','cycle_out','cycle_control'};common={k:v for k,v in vars(cases[0]).items() if k not in ignored}
    if any({k:v for k,v in vars(c).items() if k not in ignored}!=common for c in cases[1:]):raise ValueError('Mixed carousel ancestry')
    # Requalify the shared first-page chain once, then independently check each
    # complete action/child prefix. No earlier CSV is silently omitted.
    from air_title_page_reference import compare as qualify_page
    from air_title_actions_reference import compare as qualify
    with contextlib.redirect_stdout(io.StringIO()):qualify_page(argparse.Namespace(**dict(vars(cases[0]),native_base=cases[0].actions_base)))
    for case in cases:
        with contextlib.redirect_stdout(io.StringIO()):qualify(argparse.Namespace(**{k:v for k,v in dict(vars(case),native_base=case.actions_base).items() if k not in ('actions_base','cycle_out','cycle_control')}),_parent_qualified=True)
        compare(case,_parent_qualified=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    for mode in ('prepare','capture'):
        p=sub.add_parser(mode);p.add_argument('rom',type=Path)
        if mode=='prepare':p.add_argument('--action',choices=('automatic','a','b'),default='automatic')
        for key in ('capture','out')+(('accepted-control','parent-out') if mode=='capture' else ()):p.add_argument('--'+key,type=Path,required=True)
    p=sub.add_parser('compare-batch');p.add_argument('manifest',type=Path);args=parser.parse_args()
    if args.mode=='compare-batch':compare_many([argparse.Namespace(**{k:Path(v) for k,v in c.items()}) for c in read(args.manifest)])
    else:dict(prepare=prepare,capture=capture)[args.mode](args)
if __name__=='__main__':main()
