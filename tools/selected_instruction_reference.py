"""One input-only source observation from player selection through instruction picture."""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha,POINTS as START,STORES as START_STORES
from air_title_instruction_reference import POINTS as INSTRUCTION,STORES as INSTRUCTION_STORES
from air_title_campaign_reference import POINTS as CAMPAIGN,STORES as CAMPAIGN_STORES
from air_title_resume_reference import POINTS as RESUME,STORES as RESUME_STORES
from air_instruction_header_reference import POINTS as HEADER
from air_title_picture_reference import POINTS as PICTURE,voice_states,compare_voices
from air_title_players_reference import CASES as PLAYER_CASES
from password_feedback_reference import logical_voice_projection
from air_timing import IRQ_PHASES,vblank_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
CASES=tuple(case for case in PLAYER_CASES if case not in ('back-a','back-b'))
GROUPS=('start','instruction','campaign','resume','header','picture')
TABLES=(START,INSTRUCTION,CAMPAIGN,RESUME,HEADER,PICTURE)
STORES=(START_STORES,INSTRUCTION_STORES,CAMPAIGN_STORES,RESUME_STORES,{}, {})

def later_start_parent(data):
    target=data.get('targetPage',0);groups=data.get('groups',[])
    if data.get('version')!=1 or data.get('inputCase')!='carousel' or data.get('laterAction')!='start' or type(target) is not int or not 1<=target<=4 or len(groups)!=2*target or groups[-1]['name']!=str(target-1)+'.idle':raise ValueError('Instruction lacks its later-title Start parent')
    group=groups[-1];end=group['points'][-1]
    if end['name']!='end' or end['route']!=2 or end['index']!=target or end['pattern'] or end['inputPressed']!=8 or group['objects']!=[0]*256 or len(group['maps'])!=2048:raise ValueError('Unowned later Start decision/storage')
    # This ancestry retains one-player title choices. Fresh campaign lives are
    # independently checked below; these aliases normalize observation field
    # names only and are never native initialization data.
    return dict(data,points=[dict(end,held=end['inputHeld'],pressed=end['inputPressed'],players=0)],maps=group['maps'],objects=group['objects'])

def capture(args):
    later=getattr(args,'later_parent',None);manifest=read(args.capture/'capture-summary.json');parent=read((later/'cycle.json') if later else args.parent_out/'exit.json');require_capture_reference(manifest,parent)
    if later:
        if args.parent_out!=later:raise ValueError('Detached later Start input prefix')
        parent=later_start_parent(parent)
    if (parent['inputCase'] not in CASES and not later) or parent['points'][-1]['route']!=2 or manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Detached selected Start control/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    groups=[dict(name=name,points=[],rawSongs=[],interrupts=[],polls=[],writes=[],rasters=[]) for name in GROUPS];active=complete=False;group_index=0;irq=None;palettes=waits=0;buttons=[];restart=None
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def fields():
        common=dict(tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b]);g=geometry();display=p.memory[0xc098];enabled=p.memory[0xffcf];pending=p.memory[0xff0f]&3;player=p.memory[0xc082]
        if group_index==0:return dict(common,palettes=palettes,waits=waits,**g,bgp=p.memory[0xff47],obp0=p.memory[0xff48],obp1=p.memory[0xff49],musicEnabled=enabled)
        if group_index==1:return dict(common,display=display,**g)
        if group_index==2:return dict(common,day0=p.memory[0xc088],day1=p.memory[0xc090],difficulty0=p.memory[0xc089],difficulty1=p.memory[0xc091],lives0=p.memory[0xc08a],lives1=p.memory[0xc092],lcdc=g['lcdc'],pendingRequests=pending)
        if group_index==3:return dict(common,lcdc=g['lcdc'],scrollY=g['scrollY'],display=display,stat=g['stat'],pendingRequests=pending,lives=p.memory[0xc08a],result=p.memory[0xc095])
        if group_index==4:return dict(common,player=player,stage=p.memory[0xc088+8*player],difficulty=p.memory[0xc089+8*player],lives=p.memory[0xc08a+8*player],display=display,stat=g['stat'],result=p.memory[0xc095],musicEnabled=enabled,lcdc=g['lcdc'],scrollY=g['scrollY'],pendingRequests=pending)
        return dict(common,musicEnabled=enabled,stage=p.memory[0xc088+8*player],display=display,stat=g['stat'],lcdc=g['lcdc'],scrollY=g['scrollY'],pendingRequests=pending,song=p.memory[0xffce] if enabled else -1)
    def hook(pc):
        nonlocal active,complete,group_index,irq,palettes,waits,restart
        if complete:return
        now=p._cycles()
        if not active:
            if pc!=0x0269 or now!=parent['points'][-1]['cycles']:return
            active=True
        while True:
            group=groups[group_index];table=TABLES[group_index]
            if pc not in table:break
            name=table[pc]
            if name=='begin':
                group.update(beforeMaps=p.title_maps_storage(),beforeObjects=list(p.memory[0xc100:0xc200]))
                if group_index==5:group['beforeTiles']=p.instruction_tiles_storage()
            if group_index==0:
                if name=='palette':palettes+=1
                if name=='tail':waits+=1
            group['points'].append(dict(name=name,cycles=now,**fields()))
            group['rawSongs'].append(p.memory[0xffce])
            if name!='end':break
            group.update(maps=p.title_maps_storage(),objects=list(p.memory[0xc100:0xc200]))
            if group_index==5:group['tiles']=p.instruction_tiles_storage();complete=True;return
            if irq:raise ValueError('Segment ended inside a vector')
            group_index+=1
        group=groups[group_index]
        if pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested selected Start vector')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
            if group_index==0 and pc==0x0048:group['rasters'].append(dict(boundary='begin',cycle=now,**geometry()))
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            phase=IRQ_PHASES[pc];irq['phases'][phase]=now
            if phase=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if phase=='music':irq['musicEnabled']=p.memory[0xffcf]
            if phase=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:
            irq['end']=now;group['interrupts'].append(irq);irq=None
            if group_index==0 and pc==0x2555:group['rasters'].append(dict(boundary='end',cycle=now,**geometry()))
        if pc==0x2598 and group_index==1:group['polls'].append(dict(cycle=now,ly=p.register_file.A))
        if pc in (0x2123,0x2363) and group_index>=2:group['polls'].append(dict(cycle=now,mode=p.register_file.A&3))
        address=STORES[group_index].get(pc);value=p.register_file.A;kind='map'
        if group_index==0 and pc in (0x251e,0x2532):value=(p.memory[0xc099]+1)&255
        if pc==0x2128 and group_index>=2:address=p.register_file.D*256+p.register_file.E
        if pc==0x2368 and group_index==5:address=p.register_file.D*256+p.register_file.E;kind='tile'
        if pc in (0x24a1,0x2559) and group_index>=3:address=0xff42;kind='scroll'
        if address is not None:
            entry=dict(cycle=now,address=address,value=value)
            if group_index==5:entry['kind']=kind
            group['writes'].append(entry)
            if group_index==2 and address==0xff40 and value==0xd1:restart=now+8
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        pcs={pc for table in TABLES for pc in table}|{pc for table in STORES for pc in table}|set(IRQ_PHASES)|{0x0040,0x0048,0x2484,0x2555,0x2598,0x2123,0x2128,0x2363,0x2368,0x24a1,0x2559}
        for pc in pcs:p.hook_register(0,pc,hook,pc)
        replay(p,read(args.capture/'events.json'));digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete selected instruction or changed control')
    data=dict(version=1,reference=metadata,inputCase=manifest['inputCase'],romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=parent['controlMemorySha256'],setupSha256=sha((args.capture/'setup.state').read_bytes()),storageReadOwner='direct-vram-title-v1',instructionReadOwner='direct-vram-instruction-v1',groups=groups,restartEpoch=restart,players=parent['points'][-1]['players'])
    if later:data.update(origin='later-title-start',targetPage=parent['targetPage'],parentCycleSha256=sha((later/'cycle.json').read_bytes()))
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'instruction.rejected.json',data);raise
    write_json(args.out/'instruction.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons));print(dict(case=data['inputCase'],boundaries=sum(len(g['points']) for g in groups),services=len(buttons)),flush=True)

def analyze(data,parent):
    later=data.get('origin')=='later-title-start'
    if data.get('origin') not in (None,'later-title-start'):raise ValueError('Unowned instruction origin')
    if later:parent=later_start_parent(parent)
    groups=data['groups'];first=groups[0]['points'][0];end=parent['points'][-1]
    if data.get('version')!=1 or (data['inputCase'] not in CASES and not later) or data['inputCase']!=parent['inputCase'] or data['parentControlMemorySha256']!=parent['controlMemorySha256'] or data['controlMemorySha256']!=parent['controlMemorySha256'] or end['route']!=2 or data['players']!=end['players'] or [g['name'] for g in groups]!=list(GROUPS) or first['cycles']!=end['cycles'] or any(first[k]!=end[k] for k in ('tick','countdown','stat','lcdc','scrollY','lyc')) or (first['inputHeld'],first['inputPressed'])!=(end['held'],end['pressed']):raise ValueError('Detached selected-instruction ancestry')
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data.get('instructionReadOwner')!='direct-vram-instruction-v1' or data['reference'].get('titleStorageObserver')!='direct-vram-title-v1' or data['reference'].get('instructionStorageObserver')!='direct-vram-instruction-v1':raise ValueError('Unqualified selected-instruction storage observer')
    previous_end=end['cycles'];maps=parent['maps'];objects=parent['objects'];tick=end['tick'];held=end['held'];pressed=end['pressed'];all_services=[]
    for index,group in enumerate(groups):
        points=group['points'];irqs=group['interrupts'];services=[p for p in irqs if p['kind']=='vblank'];names=list(TABLES[index].values())
        if index==0:names=['begin','fadeEntry']+['palette','wait','tail','wait','tail','wait','tail','wait','tail']*8+['fadeReturned','audioStop','stopEntry','resetEntry','stateCleared','presetsReady','waveReady','resetReturned','audioDisabled','end']
        if [p['name'] for p in points]!=names or points[0]['cycles']!=previous_end or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])) or len(group['rawSongs'])!=len(points):raise ValueError('Incomplete selected-instruction semantic boundaries')
        if group['beforeMaps']!=maps or len(group['maps'])!=2048 or group['beforeObjects']!=objects or group['objects']!=objects or objects!=[0]*256:raise ValueError('Detached selected-instruction maps/objects')
        if len(services)!=(33,0,0,4,1,4)[index]:raise ValueError('Incomplete selected-instruction service extent')
        if sum(p['kind']=='stat' for p in irqs)!=(67,0,0,4,1,4)[index] or len(group['rasters'])!=(134 if index==0 else 0):raise ValueError('Incomplete selected-instruction raster extent')
        if index==3 and [p['kind'] for p in irqs[:2]]!=['vblank','stat']:raise ValueError('Pending selected-instruction requests were accepted out of priority order')
        for n,p in enumerate(services):
            work=vblank_work(p)
            if p['tick']!=(tick+n)&65535 or p['countdown']!=54 or p['pressed']!=p['held']&~held or work['display']!=(116 if index==0 else 144) or len(p.get('voiceStates',[]))!=6 or p['musicEnabled']!=int(index in (0,5)):raise ValueError('Unowned selected-instruction input/music service')
            held=p['held']
        # Each boundary inherits the most recently completed real display.
        for p in points:
            finished=[r for r in services if r['end']+16<=p['cycles']];owner=finished[-1] if finished else dict(held=groups[index-1]['points'][-1]['inputHeld'] if index else end['held'],pressed=groups[index-1]['points'][-1]['inputPressed'] if index else end['pressed'])
            if p['tick']!=(tick+len(finished))&65535 or p['countdown']!=54 or (p['inputHeld'],p['inputPressed'])!=(owner['held'],owner['pressed']):raise ValueError('Detached selected-instruction boundary input/tick')
        if index in (1,2) and irqs:raise ValueError('Masked selected setup accepted a vector')
        if index==0:
            palettes=waits=0
            for p in points:
                palettes+=p['name']=='palette';waits+=p['name']=='tail'
                if (p['palettes'],p['waits'])!=(palettes,waits) or p['musicEnabled']!=int(p['name'] not in ('audioDisabled','end')):raise ValueError('Incomplete selected Start fade/stop')
            if (first['bgp'],first['obp0'],first['obp1'])!=(228,196,224) or any(points[-1][k] for k in ('bgp','obp0','obp1')):raise ValueError('Unowned selected Start palette endpoints')
            stop=next(p['cycles'] for p in points if p['name']=='audioStop')
            if any(p['start']>=stop for p in services):raise ValueError('Selected Start observed a partially reset voice through VBlank')
        if index==2:
            for n,p in enumerate(points):
                if (p['day0'],p['day1'],p['difficulty0'],p['difficulty1'],p['lives0'],p['lives1'])!=(1,1,0,0,5 if n>=3 else 0,5 if data['players'] and n>=3 else 0):raise ValueError('Selected campaign lost native choices/lives')
            restart=[w['cycle']+8 for w in group['writes'] if w['address']==0xff40 and w['value']==209]
            if restart!=[data['restartEpoch']]:raise ValueError('Selected campaign LCD epoch lacks its source store')
        if index==4 and any(p[k]!=v for p in points for k,v in dict(player=0,stage=1,difficulty=0,lives=5,result=0,display=5,stat=5,pendingRequests=0,musicEnabled=0).items()):raise ValueError('Selected header state changed')
        if index==5:
            for n,(p,song) in enumerate(zip(points,group['rawSongs'])):
                if p['stage']!=1 or p['display']!=5 or p['stat']!=5 or p['pendingRequests'] or p['song']!=(song if p['musicEnabled'] else -1) or (n and p['song']!=2):raise ValueError('Selected instruction music/picture state changed')
            tiles=[w['value'] for w in group['writes'] if w.get('kind')=='tile']
            if len(group['beforeTiles'])!=1024 or len(group['tiles'])!=1024 or tiles!=group['tiles']:raise ValueError('Selected picture does not match direct tile stores')
        maps=list(maps)
        for w in group['writes']:
            if 0x9800<=w['address']<0xa000:maps[w['address']-0x9800]=w['value']
        if maps!=group['maps']:raise ValueError('Incomplete selected-instruction map publication')
        if services:pressed=services[-1]['pressed']
        tick=(tick+len(services))&65535;previous_end=points[-1]['cycles'];all_services+=services
    return all_services

def later_arguments(args):
    return argparse.Namespace(**dict({k:v for k,v in vars(args).items() if k not in ('selected_out','exit_base','exit_control','exit_out','later_out','later_base')},native_base=args.later_base,cycle_out=args.later_out,cycle_control=args.exit_control))

def compare_later_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid later instruction batch')
    from title_cycle_reference import compare_many as qualify
    with contextlib.redirect_stdout(io.StringIO()):qualify([later_arguments(case) for case in cases])
    for case in cases:compare(case,_parent_qualified=True)

def compare(args,_parent_qualified=False):
    later=getattr(args,'later_out',None)
    if not _parent_qualified:
        if later:
            from title_cycle_reference import compare as qualify
            with contextlib.redirect_stdout(io.StringIO()):qualify(later_arguments(args))
        else:
            from air_title_players_exit_reference import compare as qualify
            with contextlib.redirect_stdout(io.StringIO()):qualify(args)
    from air_fourth_entry_reference import preserved_native_prefix
    from air_startup_reference import analyze as startup_epoch
    retained=preserved_native_prefix(args.native_base,args.exit_base);data=read(args.selected_out/'instruction.json');parent=read((later/'cycle.json') if later else args.exit_out/'exit.json');manifest=read(args.exit_control/'capture-summary.json')
    if later and (data.get('origin')!='later-title-start' or data.get('targetPage')!=parent['targetPage'] or data.get('parentCycleSha256')!=sha((later/'cycle.json').read_bytes())):raise ValueError('Detached later instruction recording')
    require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase')) or data['setupSha256']!=sha((args.exit_control/'setup.state').read_bytes()):raise ValueError('Changed selected-instruction control/setup')
    services=analyze(data,parent)
    if later:parent=later_start_parent(parent)
    if (args.selected_out/'buttons.txt').read_text()!=(args.exit_out/'buttons.txt').read_text()+''.join(str(p['held'])+'\n' for p in services):raise ValueError('Detached selected-instruction raw inputs')
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    previous=str(args.exit_base)+'.fifth.title-cycle.'+str(parent['targetPage']-1)+'.idle.summary.csv' if later else str(args.exit_base)+'.fifth.players-exit.summary.csv'
    with Path(previous).open(newline='') as f:before=next(csv.DictReader(f))
    preceding=int(before['displays']);stats=int(before['stats']);lcd=int(before['lcdEpoch']);differences=[];totals=dict(boundaries=0,services=0,vectors=0,polls=0,writes=0,rasterBoundaries=0,mapBytes=0,tileBytes=0,voiceRows=0)
    def check(kind,index,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if v!=int(q[k])}
        if delta:differences.append(dict(category=kind,index=index,fields=delta))
    def rows(stem,suffix):
        with Path(stem+suffix).open(newline='') as f:return list(csv.DictReader(f))
    carried=list(parent['maps'])
    for index,group in enumerate(data['groups']):
        name=group['name'];stem=str(args.native_base)+('.fifth.later.title-' if later else '.fifth.selected.title-')+name;points=group['points'];irqs=group['interrupts'];displays=[p for p in irqs if p['kind']=='vblank']
        native=rows(stem,'.csv');ns=rows(stem,'.services.csv');ni=rows(stem,'.interrupts.csv');np=rows(stem,'.polls.csv');nw=rows(stem,'.writes.csv');summary=rows(stem,'.summary.csv')
        if [len(native),len(ns),len(ni),len(np),len(nw),len(summary)]!=[len(points),len(displays),len(irqs),len(group['polls']),len(group['writes']),1]:raise ValueError('Incomplete selected '+name+' outputs')
        for n,(p,q) in enumerate(zip(points,native)):
            if p['name']!=q['boundary']:raise ValueError('Reordered selected '+name+' boundary')
            check(name+' boundary',n,dict(cycle=p['cycles']-epoch,**{k:v for k,v in p.items() if k not in ('name','cycles')}),q)
        for n,(p,q) in enumerate(zip(displays,ns)):
            work=vblank_work(p);check(name+' service',n,dict(service=preceding+n,cycle=p['start']-epoch,tick=p['tick'],countdown=54,display=work['display'],effects=work['effects'],music=work['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
        for n,(p,q) in enumerate(zip(irqs,ni)):
            if p['kind']!=q['kind']:raise ValueError('Reordered selected '+name+' vector')
            owner=3 if index==3 and n<2 else 2 if p['returnAddress']==0x261d else 1
            check(name+' vector',n,dict(vectorCycle=p['start']-epoch,owner=owner),q)
        for kind,source,target in [('poll',group['polls'],np),('write',group['writes'],nw)]:
            for n,(p,q) in enumerate(zip(source,target)):
                if 'kind' in p and p['kind']!=q['kind']:raise ValueError('Reordered selected picture store')
                check(name+' '+kind,n,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k!='kind'},q)
        if index==0:
            raster=rows(stem,'.raster.csv')
            if len(raster)!=len(group['rasters']):raise ValueError('Incomplete selected Start raster')
            for n,(p,q) in enumerate(zip(group['rasters'],raster)):
                if p['boundary']!=q['boundary']:raise ValueError('Reordered selected Start raster')
                check('start raster',n,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k!='boundary'},q)
            totals['rasterBoundaries']+=len(raster)
        if index in (0,5):
            voices=rows(stem,'.voices.csv');voice_differences=compare_voices(logical_voice_projection(displays),voices,preceding)
            for difference in voice_differences:difference['category']=name+' '+difference['category']
            differences+=voice_differences;totals['voiceRows']+=len(voices)
        for w in nw:
            address=int(w['address'])
            if 0x9800<=address<0xa000:carried[address-0x9800]=int(w['value'])
        if carried!=group['maps']:differences.append(dict(category=name+' carried maps',fields='Native stores do not reconstruct the directly observed map'))
        if index!=1:
            maps=rows(stem,'.maps.csv')
            if len(maps)!=2048:raise ValueError('Incomplete selected '+name+' map snapshot')
            for n,(value,q) in enumerate(zip(group['maps'],maps)):check(name+' map',n,dict(address=0x9800+n,value=value),q)
        totals['mapBytes']+=2048
        if index==5:
            tiles=rows(stem,'.tiles.csv')
            if len(tiles)!=1024:raise ValueError('Incomplete selected instruction tile snapshot')
            for n,(value,q) in enumerate(zip(group['tiles'],tiles)):check('picture tile',n,dict(address=0x8340+n,value=value),q)
            totals['tileBytes']+=1024
        preceding+=len(displays);stats+=sum(p['kind']=='stat' for p in irqs);last=points[-1];end=last['cycles']-epoch
        if index==2:lcd=data['restartEpoch']-epoch
        def deadline(line):
            value=lcd+(end-lcd)//70224*70224+line*456
            return value+70224 if value<=end else value
        common=dict(end=end,lcdEpoch=lcd,nextStat=deadline(last.get('lyc',95)),nextVBlank=deadline(144))
        if index==0:wanted=dict(common,tick=last['tick'],countdown=54,displays=preceding,stats=stats,musicEnabled=0)
        elif index==1:
            off=next(w for w in group['writes'] if w['address']==0xff40 and not w['value']&128);wanted=dict(end=end,lcdDisabled=off['cycle']+12-epoch,polls=len(group['polls']),pendingRequests=3,servicesMasked=1)
        elif index==2:wanted=dict(common,pendingRequests=3,servicesMasked=1,active=1,player=0)
        elif index==3:wanted=dict(common,displays=preceding,stats=stats,pendingRequests=0,servicesMasked=0,result=0)
        elif index==4:wanted=dict(common,tick=last['tick'],countdown=54,displays=preceding,stats=stats,pendingRequests=0,servicesMasked=0,result=0)
        else:wanted=dict(common,tick=last['tick'],countdown=54,displays=preceding,stats=stats,song=2)
        if set(wanted)!=set(summary[0]):raise ValueError('Unqualified selected '+name+' summary fields')
        check(name+' summary',0,wanted,summary[0])
        for key,number in [('boundaries',len(points)),('services',len(ns)),('vectors',len(ni)),('polls',len(np)),('writes',len(nw))]:totals[key]+=number
    report=dict(inputCase=data['inputCase'],origin=data.get('origin','selected-players'),targetPage=data.get('targetPage',0),players=data['players'],**{'compared'+k[0].upper()+k[1:]:v for k,v in totals.items()},preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],stoppedDriverPayloadCompared=False,productionSchedulerAccepted=False,evidenceLimit='Start fade/stop, masked setup, actual fresh lives, pending services, complete first header and instruction music/picture after the separately qualified parent. Disabled driver payloads are explicit logical silence. Later reveal/text/gameplay, frames/PCM, other choices and production scheduling remain separate.')
    write_json(Path(str(args.native_base)+'.selected-instruction.comparison.json'),report);print(report)
    if differences:raise ValueError('Selected instruction differs from the original')

def compare_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid selected instruction batch')
    ignored={'native_base','exit_base','players_base','players_out','players_control','exit_out','exit_control','selected_out'};common={k:v for k,v in vars(cases[0]).items() if k not in ignored}
    if any({k:v for k,v in vars(c).items() if k not in ignored}!=common for c in cases[1:]):raise ValueError('Mixed selected instruction ancestry')
    parents=[]
    for case in cases:
        values={k:v for k,v in vars(case).items() if k not in ('exit_base','selected_out')};values['native_base']=case.exit_base;parents.append(argparse.Namespace(**values))
    from air_title_players_exit_reference import compare_many as qualify
    with contextlib.redirect_stdout(io.StringIO()):qualify(parents)
    for case in cases:compare(case,_parent_qualified=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('capture');p.add_argument('rom',type=Path);p.add_argument('--later-parent',type=Path)
    for k in ('capture','parent-out','out'):p.add_argument('--'+k,type=Path,required=True)
    p=sub.add_parser('compare-batch');p.add_argument('manifest',type=Path)
    p=sub.add_parser('compare-later-batch');p.add_argument('manifest',type=Path);args=parser.parse_args()
    if args.mode=='capture':capture(args)
    else:(compare_later_many if args.mode=='compare-later-batch' else compare_many)([argparse.Namespace(**{k:Path(v) for k,v in c.items()}) for c in read(args.manifest)])
if __name__=='__main__':main()
