"""Read-only following Air updates and counter waits; never native timing/state input."""
import argparse,csv,hashlib,json
from pathlib import Path
from extract import read_rom
from extract_air import HANDLERS
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_timing import IRQ_PHASES,vblank_work,VBLANK_FIXED,vblank_bookkeeping_work
from air_reference import write_json
from air_following_scope import retry_capture_scope

POINTS={0x03d8:'begin',0x03db:'savedPlayer',0x03de:'entitiesDone',0x03e4:'sprites',0x03e7:'spritesDone',0x03ed:'mapCallback',0x19a2:'placements',0x03fa:'done',0x03c7:'backEdge'}
ORDER=[*POINTS.values(),'end']
TERMINAL_POINTS={0x0400:'terminalWait',0x0403:'terminalEnd'}
TERMINAL_ORDER=ORDER[:8]+list(TERMINAL_POINTS.values())
FIELDS=('tick','secondTicks','seconds','random','ready','map','lastMapCamera','mapScratch','cameraX','cameraY','hudCursor','fadeRemaining','held','pressed','lcdc','display','transfer','remaining','effect','reverse')

def selected_extension(parent,child,events,changed,setup):
    from air_title_actions_reference import event_sha
    tail=[['press','a'],['press','right'],['tick',300,True],['release','a'],['release','right'],['tick',4,True]]
    if child.get('gameplayUpdates')!=320 or child.get('gameplayInput')!='a-right-held' or child['inputCase']!=parent['inputCase'] or child['inputCase'] not in ('full-prompt','skip-held') or changed!=events+tail or child['romSha256']!=parent['romSha256'] or child['parentControlMemorySha256']!=parent['controlMemorySha256'] or child['parentEventsSha256']!=event_sha(events) or child['setupSha256']!=setup or child['controlDifferences'] or child['prefixControlHashes']!=[parent['controlMemorySha256']]*2 or child['unhookedControlHashes']!=[child['controlMemorySha256']]*2:raise ValueError('Detached selected gameplay extension')

def selected_entry_boundary(parent,manifest,accepted=None):
    require_capture_reference(manifest,parent)
    expected=manifest if accepted is None else accepted
    if parent.get('version')!=1 or parent.get('inputCase') not in ('full-prompt','skip-held') or any(parent[k]!=expected[k] for k in ('romSha256','controlMemorySha256','inputCase')) or [g['name'] for g in parent.get('groups',[])]!=['prefix','stage','entry']:raise ValueError('Detached selected-game entry observation')
    from air_following_entry_reference import analyze as analyze_entry
    analyze_entry(parent['groups'][-1]);begin=parent['groups'][-1]['points'][-1]['cycles']
    if type(begin) is not int or begin<=0:raise ValueError('Invalid selected-game entry boundary')
    return begin

def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or hashlib.sha256(read_rom(args.rom)).hexdigest()!=manifest['romSha256']:raise ValueError('Changed original control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    selected_entry=getattr(args,'selected_entry',None);attached=None;begin_cycle=None;accepted=None;accepted_events=None
    if selected_entry:
        attached=json.loads(Path(selected_entry).read_text(encoding='utf-8'))
        accepted_folder=getattr(args,'selected_parent_control',None)
        if accepted_folder:
            folder=Path(accepted_folder);accepted=json.loads((folder/'capture-summary.json').read_text());accepted_events=json.loads((folder/'events.json').read_text())
            selected_extension(accepted,manifest,accepted_events,json.loads((args.capture/'events.json').read_text()),hashlib.sha256((args.capture/'setup.state').read_bytes()).hexdigest())
            if (args.capture/'setup.state').read_bytes()!=(folder/'setup.state').read_bytes():raise ValueError('Changed selected gameplay setup')
        begin_cycle=selected_entry_boundary(attached,manifest,accepted)
    extent=getattr(args,'updates',1)
    scope=retry_capture_scope(args)
    outro=getattr(args,'outro',False)
    terminal=outro or getattr(args,'terminal',False)
    from air_exit_timing import POINTS as OUTRO_POINTS,intervals,display_services
    outgoing=False;outro_points=[];outro_irqs=[]
    observed_points={**POINTS,**(TERMINAL_POINTS if terminal else {})}
    if not 1<=extent<=100000:raise ValueError('Invalid following update extent')
    p=Reference(str(args.rom),window='null',sound_volume=0);armed=False;active=False;complete=False;points=[];irqs=[];opened=None;buttons=[];pause_seen=False;updates=0
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal armed,active,complete,opened,pause_seen,updates,outgoing
        if complete:return
        if pc==0x268b and (not scope.following or scope.ready) and p.memory[0xc098] in (2,10):armed=True
        scope.observe(pc,p.memory[0xc098],len(buttons))
        if pc==0x1476 and armed and not active and not attached:pause_seen=True
        if pc==0x2436 and (active if attached else scope.samples(p.memory[0xc098]) if scope.following else (p.memory[0xc098] in (2,10) or armed and p.memory[0xc098] in (1,4,5,6))):buttons.append(p.memory[0xff8a])
        closing=False
        if pc==0x03d8 and armed and (active or begin_cycle is None or p._cycles()==begin_cycle):
            if p.memory[0xc098]!=4:raise ValueError('Following gameplay control is not an Air retry')
            if not active:active=True
            else:
                updates+=1;closing=True;complete=updates==extent
                if terminal and complete:raise ValueError('Requested terminal extent still continues gameplay')
        if not active:return
        now=p._cycles()
        if terminal and not outgoing and pc==0x0403:
            updates+=1
            if updates!=extent:raise ValueError('Terminal update does not match requested extent')
            complete=not outro
        if pc in observed_points and not outgoing:
            seconds=p.memory[0xc084]
            if seconds&15>9 or seconds>>4>9:raise ValueError('Invalid original BCD timer')
            points.append(dict(name='end' if closing else observed_points[pc],cycles=now,tick=word(0xc00a),secondTicks=p.memory[0xc083],seconds=(seconds>>4)*10+(seconds&15),random=word(0xc09e),result=p.memory[0xc095],
                ready=p.memory[0xffae],map=p.memory[0xc00d],lastMapCamera=word(0xff96),mapScratch=word(0xc00c),cameraX=word(0xff92),cameraY=word(0xff94),hudCursor=p.memory[0xc04c],fadeRemaining=p.memory[0xffc9],
                held=p.memory[0xff8a],pressed=p.memory[0xff8b],lcdc=p.memory[0xff40],display=p.memory[0xc098],transfer=p.memory[0xffb6],remaining=p.memory[0xffb5],effect=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6],reverse=int(bool(p.memory[0xff90])),
                transferFrame=p.memory[0xffb9],transferFlags=p.memory[0xffba],
                entities=[dict(frame=p.memory[0xc200+i*16],flags=p.memory[0xc205+i*16],handler=word(0xc206+i*16),x=word(0xc201+i*16),y=word(0xc203+i*16),params=list(p.memory[0xc209+i*16:0xc210+i*16]),state=p.memory[0xc302+i*16],delay=p.memory[0xc303+i*16],period=p.memory[0xc304+i*16]) for i in range(16)]))
            if closing and not complete:points.append(dict(points[-1],name='begin'))
        if outro and pc==0x0403:outgoing=True
        if outgoing and pc in OUTRO_POINTS:
            outro_points.append(dict(name=OUTRO_POINTS[pc],cycles=now,tick=word(0xc00a),counter=p.memory[0xc009],ready=p.memory[0xffae],musicEnabled=p.memory[0xffcf],bgp=p.memory[0xff47],obp0=p.memory[0xff48],obp1=p.memory[0xff49]))
            if pc==0x0409:complete=True
        elif pc in (0x0040,0x0048):
            if opened:raise ValueError('Nested following gameplay IRQ')
            opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],display=p.memory[0xc098],returnAddress=word(p.register_file.SP),tick=word(0xc00a),ready=p.memory[0xffae],phases={})
            if 0x20<=opened['returnAddress']<=0x24:opened['callerAddress']=word(p.register_file.SP+2)
            if pc==0x0040:opened['oam']=list(p.memory[0xc100:0xc1a0])
        elif pc in IRQ_PHASES and opened and opened['kind']=='vblank':
            name=IRQ_PHASES[pc];opened['phases'][name]=now
            if name=='display':opened.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b],displayWorkload=dict(map_pending=p.memory[0xc00d],ready=p.memory[0xffae],chunks=p.memory[0xffb5],cursor=p.memory[0xc04c],tick=word(0xc00a),fade_remaining=p.memory[0xffc9],collected=p.memory[0xc20a],quota=p.memory[0xffab]))
            if name=='bookkeeping':opened.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004],hudBar=list(p.memory[0xc046:0xc04c]))
            if name=='effects':opened['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if name=='music':opened['musicEnabled']=p.memory[0xffcf]
        elif pc in (0x2484,0x2555) and opened:opened['end']=now;(outro_irqs if outgoing else irqs).append(opened);opened=None
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*observed_points,*(OUTRO_POINTS if outro else {}),*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x268b,0x1476,0x0462}:p.hook_register(0,pc,hook,pc)
        for index,event in enumerate(json.loads((args.capture/'events.json').read_text())):
            if event[0]=='tick':p.tick(event[1],event[2])
            elif event[0] in ('press','release'):getattr(p,'button_'+event[0])(event[1])
            else:raise ValueError('Unknown original control event')
            if accepted_events is not None and index==len(accepted_events)-1 and hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()!=accepted['controlMemorySha256']:raise ValueError('Observed selected gameplay extension changed its accepted prefix')
        digest=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or opened or digest!=manifest['controlMemorySha256']:
        args.out.mkdir(parents=True,exist_ok=True)
        write_json(args.out/'gameplay.incomplete.json',dict(accepted=False,requestedUpdates=extent,completedUpdates=updates,
            complete=complete,openInterrupt=opened,controlMemorySha256=digest,controlMatches=digest==manifest['controlMemorySha256'],points=points,interrupts=irqs))
        raise ValueError(f'Incomplete following gameplay extent or changed control: requested={extent}, completed={updates}, controlMatches={digest==manifest["controlMemorySha256"]}')
    data=dict(version=1,updates=extent,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,interrupts=irqs,precedingDisplays=len(buttons)-sum(r['kind']=='vblank' for r in irqs+outro_irqs)-scope.display_offset,entryPauseConsumed=pause_seen,productionSchedulerAccepted=False)
    if attached:
        prefix=(Path(selected_entry).parent/'buttons.txt').read_text();data.update(selectedEntryCycle=begin_cycle,parentControlMemorySha256=attached['controlMemorySha256'],parentInputCase=attached['parentInputCase'],inputCase=attached['inputCase'],players=attached['players'],precedingDisplays=len(prefix.splitlines()))
    if scope.following:data['nextRetry']=True
    if scope.retry!=1:data['afterRetry']=scope.retry
    if getattr(args,'partial_rows',False):data['partialRows']=True
    if terminal:data['terminalWait']=True
    if terminal or getattr(args,'resource_transfers',False) or getattr(args,'busy_scenes',False):
        rom=read_rom(args.rom);data.update(resourceTransfers=True,resourceChunks=list(rom[0xe08f:0xe0bf:4]))
    if terminal or getattr(args,'busy_scenes',False):data['busyScenes']=True
    try:
        if data.get('busyScenes'):
            from air_following_scene_reference import analyze as analyze_scenes
            analyze_scenes(data)
        elif data.get('resourceTransfers'):
            from air_following_resource_reference import analyze as analyze_resources
            analyze_resources(data)
        elif extent==1:analyze(data)
        else:
            from air_following_quiet_reference import analyze as analyze_quiet
            analyze_quiet(data)
    except ValueError:
        args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'gameplay.rejected.json',data)
        raise
    args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'gameplay.json',data)
    if outro:
        outdata=dict(version=2,reference=metadata,romSha256=data['romSha256'],controlMemorySha256=digest,
            fadePalettes=list(read_rom(args.rom)[0x2118:0x2120]),points=outro_points,interrupts=outro_irqs,
            precedingDisplays=data['precedingDisplays']+sum(r['kind']=='vblank' for r in irqs),productionSchedulerAccepted=False)
        if scope.retry!=1:outdata['afterRetry']=scope.retry
        intervals(outdata);display_services(outdata)
        write_json(args.out/'outro.json',outdata)
    (args.out/'buttons.txt').write_text((prefix if attached else '')+''.join(str(b)+'\n' for b in buttons))
    print(json.dumps(dict(boundaries=len(points),services=sum(r['kind']=='vblank' for r in irqs),interrupts=len(irqs),controlDifferences=0),indent=2))

def analyze(data):
    points=data.get('points',[]);irqs=data.get('interrupts',[])
    if data.get('version')!=1 or data.get('updates',1)!=1 or [p['name'] for p in points]!=ORDER or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Incomplete/reordered following gameplay')
    if len(irqs)!=2 or [r['kind'] for r in irqs]!=['stat','vblank'] or data.get('precedingDisplays',-1)<0:raise ValueError('Incomplete following gameplay vectors')
    first=points[0]
    for i,p in enumerate(points):
        if p['display']!=4 or p['ready'] or p['transfer'] or p['remaining'] or p['effect']!=-1 or p['held']&15==15 or p['pressed']&~p['held'] or (p['pressed']&8 and not (i<9 and data.get('entryPauseConsumed') is True)):raise ValueError('Unowned following gameplay/input/pause state')
        if not 0<=p['secondTicks']<60 or not 0<=p['seconds']<=99 or any(p[k]!=first[k] for k in ('secondTicks','seconds','random','cameraX','cameraY')):raise ValueError('Unowned first following gameplay scalar change')
        if p['tick']!=(first['tick']+(i==9))&65535 or p['hudCursor']!=2+(i==9) or p['fadeRemaining']!=7-(i==9 and not first['tick']&1):raise ValueError('Unowned following counter/HUD/fade continuation')
        if p['lcdc']!=0xe7 or p['map']!=1 or len(p['entities'])!=16:raise ValueError('Unowned following scene extent')
        if any(e['frame']!=255 and (e['handler'] not in HANDLERS or len(e['params'])!=7) for e in p['entities']):raise ValueError('Unidentified following actor')
    if first['entities'][0]['handler']!=0x5fa6 or points[-1]['entities'][0]['handler']!=0x5fae:raise ValueError('Unowned following player intro')
    if points[1]['cycles']-first['cycles']!=96 or points[8]['cycles']-points[7]['cycles']!=32:raise ValueError('Unowned following saved-player/back-edge work')
    for r in irqs:
        if not points[8]['cycles']<r['start']<r['end']<points[-1]['cycles'] or r['selector']!=4 or r['display']!=4 or r['returnAddress']!=0x261d or r['ready']!=1:raise ValueError('Unowned following wait vectors')
    if irqs[0]['end']-irqs[0]['start']!=288 or irqs[0]['end']+16>=irqs[1]['start']:raise ValueError('Unowned following STAT work')
    r=irqs[1];work=vblank_work(r);expected={**VBLANK_FIXED,'display':1508 if first['tick']&1 else 1676,'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched']),'effects':64}
    if r['tick']!=first['tick'] or r['effectRequest']!=-1 or not r['musicEnabled'] or work['music']<60 or any(work[k]!=v for k,v in expected.items()) or r['pressed']!=r['held']&~first['held']:raise ValueError('Unowned following display/input/audio work')
    if points[-1]['cycles']!=r['end']+16+56+48:raise ValueError('Unowned following next input gate')
    return r

def compare_gameplay(data,points,entities,services,irqs,summary,entry,epoch):
    r=analyze(data)
    if [len(rows) for rows in (points,entities,services,irqs,summary,entry)]!=[10,160,1,2,1,1]:raise ValueError('Incomplete native following gameplay coverage')
    differences=[]
    def check(category,index,wanted,actual):
        delta={k:[v,int(actual[k])] for k,v in wanted.items() if int(actual[k])!=v}
        if delta:differences.append(dict(category=category,index=index,fields=delta))
    occupied=0
    for i,(p,q) in enumerate(zip(data['points'],points)):
        if q['boundary']!=p['name']:raise ValueError('Reordered native following gameplay boundary')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in FIELDS}),q)
        for slot,e in enumerate(p['entities']):
            native=entities[16*i+slot]
            if native['boundary']!=p['name'] or int(native['slot'])!=slot:raise ValueError('Reordered native following actors')
            values=dict(alive=int(e['frame']!=255),frame=e['frame'])
            if e['frame']!=255:
                occupied+=1;values.update(flags=e['flags'],handler=HANDLERS[e['handler']],x=e['x'],y=e['y'],done=int(bool(e['state']&128)),waiting=int(bool(e['state']&64)),delay=e['delay'],period=e['period'],**{f'param{j}':v for j,v in enumerate(e['params'])})
            check('actor',16*i+slot,values,native)
    work=vblank_work(r);check('service',0,dict(service=data['precedingDisplays'],cycle=r['start']-epoch,tick=r['tick'],display=work['display'],effects=work['effects'],music=work['music'],inputHeld=r['held'],inputPressed=r['pressed']),services[0])
    for i,(p,q) in enumerate(zip(data['interrupts'],irqs)):
        if q['kind']!=p['kind'] or int(q['owner'])!=2:raise ValueError('Unowned native following counter-wait vector')
        check('interrupt',i,dict(vectorCycle=p['start']-epoch),q)
    first=data['points'][0];end=data['points'][-1]
    if int(entry[0]['end'])!=first['cycles']-epoch or int(entry[0]['tick'])!=first['tick'] or int(entry[0]['randomState'])!=first['random'] or int(entry[0]['displays'])!=data['precedingDisplays']:raise ValueError('Following gameplay is detached from native entry')
    if int(entry[0].get('entryPauseComplete',0))!=int(data.get('entryPauseConsumed',False)):raise ValueError('Following first-update Start consumption lacks its native pause return')
    if any(int(entry[0][key])+epoch+20!=p['start'] for key,p in zip(('nextStat','nextVBlank'),data['interrupts'])):raise ValueError('Following wait lost its inherited deadlines')
    check('summary',0,dict(end=end['cycles']-epoch,tick=end['tick'],countdown=int(entry[0]['countdown']),displays=int(entry[0]['displays'])+1,stats=int(entry[0]['stats'])+1,lcdEpoch=int(entry[0]['lcdEpoch']),nextStat=int(entry[0]['nextStat'])+70224,nextVBlank=int(entry[0]['nextVBlank'])+70224),summary[0])
    return differences,occupied

def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'gameplay.json').read_text());startup=json.loads((args.startup/'startup.json').read_text())
    for recording in (data,startup):
        require_capture_reference(manifest,recording)
        if any(recording[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed following gameplay controls')
    if manifest['controlDifferences']:raise ValueError('Changed original control')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
    path=args.native_csv;values=[rows(path)]+[rows(path.with_suffix('.'+key+'.csv')) for key in ('entities','services','interrupts','summary')]+[rows(args.entry_summary)]
    differences,occupied=compare_gameplay(data,*values,epoch)
    report=dict(comparedBoundaries=10,comparedActorSlots=160,comparedOccupiedActors=occupied,comparedServices=1,comparedInterrupts=2,entryPauseConsumed=data.get('entryPauseConsumed',False),differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,
        evidenceLimit='Bounded following Air retry: complete first update and next wait/input gate, live actor fields, native inherited timer/animation block, row/RNG/scene scalars and counter-wait input/audio/vectors. A preceding entry pause is qualified separately and its completed native return must own consumed Start. Excludes raw script pointers, unused vacant actor payloads, full map/sprite bytes, images/PCM, later gameplay, Ski and production Windows scheduling.')
    write_json(path.with_suffix('.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native following gameplay differs')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--updates',type=int,default=1);record.add_argument('--resource-transfers',action='store_true')
    record.add_argument('--busy-scenes',action='store_true')
    record.add_argument('--next-retry',action='store_true')
    record.add_argument('--after-retry',type=int,choices=(1,2,3),default=1)
    record.add_argument('--partial-rows',action='store_true',help='Capture partial-row crossings; comparison additionally requires matching byte-level map evidence')
    record.add_argument('--terminal',action='store_true',help='Include the last update and closed-gate final counter wait')
    record.add_argument('--outro',action='store_true',help='Also include audio stop and all outgoing fade waits, ending before result setup')
    verify=sub.add_parser('compare');verify.add_argument('native_csv',type=Path);verify.add_argument('--startup',type=Path,required=True);verify.add_argument('--entry-summary',type=Path,required=True)
    for command in (record,verify):command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
