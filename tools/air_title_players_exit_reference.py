"""Full player-selection object clear, Start return and A/B page-zero return."""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from password_return_reference import prepare,attachment
from air_title_players_reference import CASES,MOTION,continuation_observation_start
from air_title_menu_reference import STORES
from air_title_picture_reference import voice_states,compare_voices
from air_timing import IRQ_PHASES,vblank_work,elapsed_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
POINTS={0x1b2f:'begin',0x1bd3:'objectsCleared',0x27a4:'objectsReturned',0x27a7:'pageStored',0x26ea:'closeCall',0x27e6:'closeWait',0x27e9:'closeReady',0x27f5:'centerStored',0x27f9:'clearEntry',0x26ed:'closeReturned',0x26f0:'clearReturned',0x2701:'pageCall',0x29ac:'pageEntry',0x22e4:'rectangleEntry',0x22f6:'rowReady',0x2301:'copyReturned',0x29b9:'pageReturn',0x2704:'pageReturned',0x27d4:'openWait',0x27d7:'openReady',0x27e3:'openStored',0x2707:'end',0x0269:'end'}
RAM_STORES={0x27a4:0xc03e}
def capture(args):
    manifest=read(args.control/'capture-summary.json');accepted=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'players.json');require_capture_reference(accepted,parent)
    old=read(args.capture/'events.json');events=read(args.control/'events.json');attachment(accepted,manifest,old,events,sha((args.control/'setup.state').read_bytes()))
    if parent['inputCase'] not in CASES or parent['points'][-1]['route'] not in (1,2) or parent['controlMemorySha256']!=accepted['controlMemorySha256'] or (args.capture/'setup.state').read_bytes()!=(args.control/'setup.state').read_bytes() or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Changed select ancestry')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    active=complete=False;points=[];irqs=[];irq=None;writes=[];polls=[];rasters=[];buttons=[];before=maps=before_objects=objects=None;closed=cleared=opened=rows=0;route=parent['points'][-1]['route'];target=0x0269 if route==2 else 0x2707
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def hook(pc):
        nonlocal active,complete,irq,before,maps,before_objects,objects,closed,cleared,opened,rows
        if complete:return
        now=p._cycles()
        if pc==0x1b2f and now==parent['points'][-1]['cycles']:active=True;before=p.title_maps_storage();before_objects=list(p.memory[0xc100:0xc200])
        if not active:return
        if pc in POINTS and (POINTS[pc]!='end' or pc==target):
            name=POINTS[pc]
            if name=='centerStored':closed+=1
            if name in ('closeReturned','clearReturned'):cleared+=1
            if name=='openStored':opened+=1
            if name=='rowReady':rows+=1
            points.append(dict(name=name,cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),center=p.memory[0xc09c],windowY=p.memory[0xff4a],closed=closed,cleared=cleared,opened=opened,rows=rows,page=p.memory[0xc03e],players=p.memory[0xc081],route=route,song=p.memory[0xffce],musicEnabled=p.memory[0xffcf],held=p.memory[0xff8a],pressed=p.memory[0xff8b],**geometry()))
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
        if 0x1b33<=pc<=0x1bd2:writes.append(dict(cycle=now,address=p.register_file.HL,value=p.register_file.A))
        if pc in RAM_STORES:writes.append(dict(cycle=now,address=RAM_STORES[pc],value=p.register_file.A))
        if pc in (0x2801,0x2123):polls.append(dict(cycle=now,mode=p.register_file.A&3))
        if pc in (0x2805,0x2128):writes.append(dict(cycle=now,address=p.register_file.HL if pc==0x2805 else p.register_file.D*256+p.register_file.E,value=p.register_file.A))
    try:
        with (args.control/'setup.state').open('rb') as f:p.load_state(f)
        watch_at=continuation_observation_start(old,parent['inputCase']) if parent.get('origin')=='later-title-select' else 0
        for i,e in enumerate(events):
            if i==watch_at:
                for pc in {*POINTS,*STORES,*MOTION,*RAM_STORES,*IRQ_PHASES,*range(0x1b33,0x1bd3),0x0040,0x0048,0x2484,0x2555,0x2801,0x2805,0x2123,0x2128}:p.hook_register(0,pc,hook,pc)
            replay(p,[e])
            if i==len(old)-1 and memory_sha(p)!=accepted['controlMemorySha256']:raise ValueError('Player-selection observer changed prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete player selection or changed full control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=accepted['controlMemorySha256'],inputCase=manifest['inputCase'],storageReadOwner='direct-vram-title-v1',points=points,interrupts=irqs,writes=writes,polls=polls,rasters=rasters,beforeMaps=before,maps=maps,beforeObjects=before_objects,objects=objects)
    if parent.get('origin')=='later-title-select':data.update(origin='later-title-select',targetPage=parent['targetPage'],parentPlayersSha256=sha((args.parent_out/'players.json').read_bytes()))
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'exit.rejected.json',data);raise
    write_json(args.out/'exit.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons));print(dict(case=manifest['inputCase'],boundaries=len(points),services=len(buttons)),flush=True)

def analyze(data,parent):
    points=data['points'];first=points[0];end=parent['points'][-1];irqs=data['interrupts'];services=[p for p in irqs if p['kind']=='vblank'];route=end['route']
    if parent.get('origin')=='later-title-select' and (data.get('origin')!='later-title-select' or data.get('targetPage')!=parent['targetPage']):raise ValueError('Detached retained player page')
    if data.get('version')!=1 or data['inputCase'] not in CASES or data['inputCase']!=parent['inputCase'] or route not in (1,2) or data['parentControlMemorySha256']!=parent['controlMemorySha256'] or first['cycles']!=end['cycles'] or any(first[k]!=end[k] for k in ('tick','countdown','center','windowY','players','route','song','musicEnabled','held','pressed','stat','lcdc','scrollY','lyc')):raise ValueError('Detached selected-player continuation')
    names=['begin','objectsCleared']
    if route==1:names+=['objectsReturned','pageStored','closeCall']+['closeWait','closeReady','centerStored']*40+['clearEntry','closeReturned','clearEntry','clearReturned','pageCall','pageEntry','rectangleEntry']+['rowReady']*10+['copyReturned','pageReturn','pageReturned']+['openWait','openReady','openStored']*40
    names+=['end']
    if [p['name'] for p in points]!=names or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])) or len(services)!=(82 if route==1 else 0):raise ValueError('Incomplete player continuation extent/order')
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data['reference'].get('titleStorageObserver')!='direct-vram-title-v1' or data['beforeMaps']!=parent['maps'] or data['beforeObjects']!=parent['objects'] or len(data['maps'])!=2048 or data['objects']!=[0]*160+data['beforeObjects'][160:]:raise ValueError('Detached player continuation storage')
    clear_return=next(p for p in points if p['name']==('objectsReturned' if route==1 else 'end'))
    if elapsed_work(first['cycles'],points[1]['cycles'],irqs)!=1296 or elapsed_work(first['cycles'],clear_return['cycles'],irqs)!=1316:raise ValueError('Incorrect object-clear mainline work')
    objects=[w for w in data['writes'] if 0xc100<=w['address']<0xc200]
    if [(w['address'],w['value']) for w in objects]!=[(0xc100+i,0) for i in range(160)] or [elapsed_work(first['cycles'],w['cycle'],irqs) for w in objects]!=[16+8*i for i in range(160)]:raise ValueError('Incomplete object-clear stores')
    page_stores=[w for w in data['writes'] if w['address']==0xc03e]
    if page_stores!=([dict(cycle=clear_return['cycles'],address=0xc03e,value=0)] if route==1 else []):raise ValueError('Incomplete retained title page-index store')
    previous=first['held']
    for i,p in enumerate(services):
        w=vblank_work(p)
        if p['tick']!=(first['tick']+i)&65535 or p['countdown']!=54 or p['pressed']!=p['held']&~previous or w['display']!=116 or p['musicEnabled']!=1 or len(p.get('voiceStates',[]))!=6:raise ValueError('Unowned player continuation service')
        previous=p['held']
    closed=cleared=opened=rows=0
    for point_index,p in enumerate(points):
        if p['name']=='centerStored':closed+=1
        if p['name'] in ('closeReturned','clearReturned'):cleared+=1
        if p['name']=='openStored':opened+=1
        if p['name']=='rowReady':rows+=1
        retained_page=parent.get('targetPage',0) if parent.get('origin')=='later-title-select' and (route==2 or point_index<3) else 0
        wanted=dict(closed=closed,cleared=cleared,opened=opened,rows=rows,page=retained_page,players=end['players'],route=route,countdown=54,song=1,musicEnabled=1,tick=(first['tick']+sum(r['end']+16<=p['cycles'] for r in services))&65535)
        completed=[r for r in services if r['end']+16<=p['cycles']];input_owner=completed[-1] if completed else first;wanted.update(held=input_owner['held'],pressed=input_owner['pressed'])
        if any(p[k]!=v for k,v in wanted.items()):raise ValueError('Player continuation state escaped its owner')
    if route==1:
        for label,centers,ys in [('centerStored',list(range(254,175,-2)),list(range(111,71,-1))),('openStored',list(range(178,255,2))+[0],list(range(73,113)))]:
            selected=[p for p in points if p['name']==label]
            if [p['center'] for p in selected]!=centers or [p['windowY'] for p in selected]!=ys:raise ValueError('Incomplete returned-title window motion')
    glyphs=[w for w in data['writes'] if 0x9800<=w['address']<0xa000]
    expected=[0x9dc0+i for _ in range(2) for i in range(320)]+[0x9dc0+32*y+x for y in range(10) for x in range(20)] if route==1 else []
    if [w['address'] for w in glyphs]!=expected or any(w['value'] for w in glyphs[:640] if route==1):raise ValueError('Incomplete returned-title glyph publication')
    maps=list(data['beforeMaps'])
    for w in glyphs:maps[w['address']-0x9800]=w['value']
    if maps!=data['maps'] or len(data['rasters'])!=2*sum(p['kind']=='stat' for p in irqs):raise ValueError('Incomplete continuation image/raster')
    return services
def compare(args,_parent_qualified=False):
    if not _parent_qualified:
        from air_title_players_reference import compare as prior_compare
        with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.players_base);data=read(args.exit_out/'exit.json');parent=read(args.players_out/'players.json');accepted=read(args.players_control/'capture-summary.json');child=read(args.exit_control/'capture-summary.json')
    if parent.get('origin')=='later-title-select' and data.get('parentPlayersSha256')!=sha((args.players_out/'players.json').read_bytes()):raise ValueError('Detached later player continuation file')
    attachment(accepted,child,read(args.players_control/'events.json'),read(args.exit_control/'events.json'),sha((args.exit_control/'setup.state').read_bytes()));require_capture_reference(child,data)
    if any(data[k]!=child[k] for k in ('romSha256','controlMemorySha256','inputCase')):raise ValueError('Mixed player-selection controls')
    services=analyze(data,parent)
    if (args.exit_out/'buttons.txt').read_text()!=(args.players_out/'buttons.txt').read_text()+''.join(str(p['held'])+'\n' for p in services):raise ValueError('Detached player-selection buttons')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+('.fifth.later.players-exit' if getattr(args,'later_out',None) else '.fifth.players-exit')+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');nr=rows('.raster.csv');np=rows('.polls.csv');nw=rows('.writes.csv');maps=rows('.maps.csv');objects=rows('.objects.csv');summary=rows('.summary.csv');voices=rows('.voices.csv')
    if [len(native),len(ns),len(ni),len(nr),len(np),len(nw),len(maps),len(objects),len(summary)]!=[len(data['points']),len(services),len(irqs:=data['interrupts']),len(data['rasters']),len(data['polls']),len(data['writes']),2048,256,1]:raise ValueError('Incomplete native player-selection outputs')
    with Path(str(args.players_base)+('.fifth.later.title-players.summary.csv' if getattr(args,'later_out',None) else '.fifth.title-players.summary.csv')).open(newline='') as f:before=next(csv.DictReader(f))
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
    check('summary',0,dict(end=end,tick=last['tick'],countdown=54,displays=preceding+len(services),stats=int(before['stats'])+sum(p['kind']=='stat' for p in irqs),lcdEpoch=lcd,nextStat=deadline(23),nextVBlank=deadline(144),**{k:last[k] for k in ('center','closed','cleared','opened','rows','page','players','route','song','musicEnabled')},titleReturned=int(last['route']==1)),summary[0])
    report=dict(inputCase=data['inputCase'],comparedBoundaries=len(native),comparedServices=len(ns),comparedVectors=len(ni),comparedRasterBoundaries=len(nr),comparedPolls=len(np),comparedWrites=len(nw),comparedMapBytes=2048,comparedObjectBytes=256,comparedVoiceRows=len(voices),preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Complete selected-player object clear and Start return or A/B page-zero menu return. Selected campaign continuation, other game paths, frames/PCM and production scheduler remain unqualified.')
    if data.get('origin'):report.update(origin=data['origin'],targetPage=data['targetPage'])
    write_json(Path(str(args.native_base)+'.players-exit.comparison.json'),report);print(report)
    if differences:raise ValueError('Native player selection differs')

def compare_later_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid later continuation batch')
    parents=[]
    for case in cases:
        values={k:v for k,v in vars(case).items() if k not in ('players_base','exit_out','exit_control')};values['native_base']=case.players_base;parents.append(argparse.Namespace(**values))
    from air_title_players_reference import compare_later_many as qualify
    with contextlib.redirect_stdout(io.StringIO()):qualify(parents)
    for case in cases:compare(case,_parent_qualified=True)

def compare_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid player continuation batch')
    ignored={'native_base','players_base','players_out','players_control','exit_out','exit_control'};common={k:v for k,v in vars(cases[0]).items() if k not in ignored}
    if any({k:v for k,v in vars(c).items() if k not in ignored}!=common for c in cases[1:]):raise ValueError('Mixed player continuation ancestry')
    parents=[]
    for case in cases:
        values={k:v for k,v in vars(case).items() if k not in ('players_base','exit_out','exit_control')};values['native_base']=case.players_base;parents.append(argparse.Namespace(**values))
    from air_title_players_reference import compare_many as qualify
    with contextlib.redirect_stdout(io.StringIO()):qualify(parents)
    for case in cases:compare(case,_parent_qualified=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    for mode in ('prepare','capture'):
        p=sub.add_parser(mode);p.add_argument('rom',type=Path)
        for name in ('capture','out')+(('control','parent-out') if mode=='capture' else ()):p.add_argument('--'+name,type=Path,required=True)
    for mode in ('compare-batch','compare-later-batch'):
        p=sub.add_parser(mode);p.add_argument('manifest',type=Path)
    args=parser.parse_args()
    if args.mode in ('compare-batch','compare-later-batch'):(compare_later_many if args.mode=='compare-later-batch' else compare_many)([argparse.Namespace(**{k:Path(v) for k,v in c.items()}) for c in read(args.manifest)])
    else:dict(prepare=prepare,capture=capture)[args.mode](args)
if __name__=='__main__':main()
