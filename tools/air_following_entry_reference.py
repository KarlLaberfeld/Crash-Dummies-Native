"""Original following resources/HUD/LCD entry and two display services through 03d8."""
import argparse,csv,hashlib,json
from pathlib import Path
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_timing import IRQ_PHASES,vblank_work,VBLANK_FIXED,vblank_bookkeeping_work
from air_reference import write_json
from air_following_scope import retry_capture_scope

POINTS={0x039c:'begin',0x039f:'scenePrepared',0x03a2:'resourceBank',0x03a8:'resourceCopy',0x03b9:'resourceReady',
        0x03bc:'hudReady',0x03c3:'lcdEnableCall',0x25ae:'lcdEnabled',0x03c6:'enableReturned',
        0x03c9:'displayReturned',0x03cb:'readyStored',0x03d8:'end'}
FIELDS=('tick','countdown','display','stat','lcdc','lyc','pendingRequests','cameraX','cameraY','mapScratch','ready','musicEnabled','inputHeld','inputPressed')

def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or hashlib.sha256(read_rom(args.rom)).hexdigest()!=manifest['romSha256']:raise ValueError('Changed original control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    player=Reference(str(args.rom),window='null',sound_volume=0);armed=False;active=False;complete=False;points=[];irqs=[];opened=None;buttons=[]
    scope=retry_capture_scope(args)
    include_pause=getattr(args,'include_entry_pause',False);point_names=dict(POINTS)
    if include_pause:point_names[0x1476]='pauseEntry'
    def word(a):return player.memory[a]+256*player.memory[a+1]
    def hook(pc):
        nonlocal armed,active,complete,opened
        if complete:return
        scope.observe(pc,player.memory[0xc098],len(buttons))
        if pc==0x268b and player.memory[0xc098] in (2,10):armed=True
        if pc==0x2436 and (scope.samples(player.memory[0xc098]) if scope.following else (player.memory[0xc098] in (2,10) or armed and player.memory[0xc098] in ((1,4,5,6) if include_pause else (4,5,6)))):buttons.append(player.memory[0xff8a])
        if pc==0x039c and scope.ready and armed:active=True
        if not active:return
        now=player._cycles()
        if pc in point_names:
            points.append(dict(name=point_names[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),display=player.memory[0xc098],stat=player.memory[0xc099],
                lcdc=player.memory[0xff40],lyc=player.memory[0xff45],pendingRequests=player.memory[0xff0f]&3,cameraX=word(0xff92),cameraY=word(0xff94),
                mapScratch=word(0xc00c),randomState=word(0xc09e),ready=player.memory[0xffae],musicEnabled=player.memory[0xffcf],
                inputHeld=player.memory[0xff8a],inputPressed=player.memory[0xff8b],hudCursor=player.memory[0xc04c],fadeRemaining=player.memory[0xffc9]))
            if pc==0x03d8:active=False;complete=True
        elif pc in (0x0040,0x0048):
            if opened:raise ValueError('Nested following entry IRQ')
            opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=player.memory[0xc099],display=player.memory[0xc098],returnAddress=word(player.register_file.SP),
                tick=word(0xc00a),ready=player.memory[0xffae],phases={})
        elif pc in IRQ_PHASES and opened and opened['kind']=='vblank':
            name=IRQ_PHASES[pc];opened['phases'][name]=now
            if name=='display':opened.update(held=player.memory[0xff8a],pressed=player.memory[0xff8b])
            if name=='bookkeeping':opened.update(resetEnabled=player.memory[0xc005],resetLatched=player.memory[0xc004])
            if name=='effects':opened['effectRequest']=-1 if player.memory[0xffc6]==255 else player.memory[0xffc6]
            if name=='music':opened['musicEnabled']=player.memory[0xffcf]
        elif pc in (0x2484,0x2555) and opened:opened['end']=now;irqs.append(opened);opened=None
    try:
        with (args.capture/'setup.state').open('rb') as stream:player.load_state(stream)
        for pc in {*point_names,*IRQ_PHASES,0x268b,0x0040,0x0048,0x2484,0x2555,0x0462}:player.hook_register(0,pc,hook,pc)
        for event in json.loads((args.capture/'events.json').read_text()):
            if event[0]=='tick':player.tick(event[1],event[2])
            elif event[0] in ('press','release'):getattr(player,'button_'+event[0])(event[1])
            else:raise ValueError('Unknown original control event')
        digest=hashlib.sha256(bytes(player.memory[0x8000:0x10000])).hexdigest()
    finally:player.stop(save=False)
    if not complete or opened or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete following entry or changed original control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,interrupts=irqs,
        precedingDisplays=len(buttons)-sum(r['kind']=='vblank' for r in irqs)-scope.display_offset,productionSchedulerAccepted=False)
    if scope.following:data['nextRetry']=True
    if scope.retry!=1:data['afterRetry']=scope.retry
    if include_pause:
        from air_following_pause_reference import analyze_paused_entry
        analyze_paused_entry(data)
    else:analyze(data)
    args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'entry.json',data)
    (args.out/'buttons.txt').write_text(''.join(str(b)+'\n' for b in buttons))
    print(json.dumps(dict(boundaries=len(points),services=sum(r['kind']=='vblank' for r in irqs),interrupts=len(irqs),controlDifferences=0),indent=2))

def analyze(data):
    points=data.get('points',[]);irqs=data.get('interrupts',[])
    if data.get('version')!=1 or [p['name'] for p in points]!=list(POINTS.values()) or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):
        raise ValueError('Incomplete/reordered following entry')
    if len(irqs)!=4 or [r['kind'] for r in irqs]!=['vblank','stat','stat','vblank'] or data.get('precedingDisplays',-1)<0:raise ValueError('Incomplete following entry vectors')
    first=points[0];previous=first['inputHeld'];services=[];last=first['cycles']
    if first['randomState']:raise ValueError('Incomplete following scene-seed reset')
    for i,p in enumerate(points):
        if any(p[k]!=first[k] for k in ('countdown','display','stat','lyc','cameraX','cameraY','mapScratch','musicEnabled')) or p['stat']!=4 or p['lyc']!=135 or p['display'] not in (4,6) or not p['musicEnabled']:
            raise ValueError('Unowned following entry state')
        if p['ready']!=(0 if i==len(points)-1 else 1) or p['pendingRequests']!=(3 if i<9 else 0) or p['inputPressed']&~p['inputHeld'] or p['inputHeld']&15==15:
            raise ValueError('Unowned following ready/input/reset gate')
        lcd=0x67 if i<7 else 0xe5 if i in (9,10) else 0xe7
        if p['lcdc']!=lcd:raise ValueError('Unowned following LCD enable/objects')
        if i>=1 and p['randomState']!=(first['tick']&255)<<8:raise ValueError('Unowned native scene seed')
    if [points[b]['cycles']-points[a]['cycles'] for a,b in ((0,1),(1,2),(2,3),(3,4),(5,6),(6,7),(7,8),(9,10))]!=[72,68,24,13976,88,56,16,12]:raise ValueError('Unowned following entry fixed work')
    epoch=points[7]['cycles']-4
    if irqs[0]['start']!=points[8]['cycles']+32 or irqs[1]['start']!=irqs[0]['end']+36 or irqs[2]['start']!=epoch+135*456+20 or irqs[3]['start']!=epoch+144*456+20:
        raise ValueError('Unowned pending/periodic following vectors')
    for i,r in enumerate(irqs):
        if not last<=r['start']<r['end'] or r['end']+16>points[-1]['cycles'] or r['selector']!=4 or r['returnAddress']!=(0x03c9 if i<2 else 0x261d):raise ValueError('Unowned following entry IRQ boundary')
        last=r['end']+16
        if r['kind']=='stat':
            if r['end']-r['start']!=288:raise ValueError('Unowned following STAT body')
        else:
            work=vblank_work(r);display=1508 if r['tick']&1 else 1676
            wanted={**VBLANK_FIXED,'display':display,'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched']),'effects':64}
            if r['display']!=first['display'] or r['ready']!=1 or any(work[k]!=v for k,v in wanted.items()) or work['music']<60 or not r['musicEnabled'] or r['effectRequest']!=-1 or r['pressed']!=r['held']&~previous:
                raise ValueError('Unowned following display/input/audio work')
            previous=r['held'];services.append(r)
    if points[-1]['tick']!=(first['tick']+2)&65535 or points[-1]['hudCursor']!=2 or points[-1]['fadeRemaining']!=7 or points[-1]['inputPressed']&8:raise ValueError('Unowned following entry terminal/pause')
    if points[9]['cycles']!=irqs[1]['end']+16 or points[-1]['cycles']!=irqs[-1]['end']+16+56+48:raise ValueError('Unowned startup/wait/ready tail')
    return services

def compare_entry(data,points,services,irqs,summary,stage_summary,epoch):
    expected_services=analyze(data)
    if [len(r) for r in (points,services,irqs,summary,stage_summary)]!=[12,2,4,1,1]:raise ValueError('Incomplete native following entry coverage')
    differences=[]
    def check(category,index,wanted,actual):
        delta={k:[v,int(actual[k])] for k,v in wanted.items() if int(actual[k])!=v}
        if delta:differences.append(dict(category=category,index=index,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],points)):
        if q['boundary']!=p['name']:raise ValueError('Reordered native following entry')
        fields=list(FIELDS)+['randomState']
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in fields}),q)
    for i,(p,q) in enumerate(zip(expected_services,services)):
        work=vblank_work(p);check('service',i,dict(service=data['precedingDisplays']+i,cycle=p['start']-epoch,tick=p['tick'],display=work['display'],effects=work['effects'],music=work['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],irqs)):
        if q['kind']!=p['kind'] or int(q['owner'])!=(3 if i<2 else 2):raise ValueError('Unowned native following vector')
        check('interrupt',i,dict(vectorCycle=p['start']-epoch),q)
    end=data['points'][-1];new_epoch=data['points'][7]['cycles']-4-epoch
    check('summary',0,dict(end=end['cycles']-epoch,tick=end['tick'],countdown=end['countdown'],lcdEpoch=new_epoch,
        nextStat=new_epoch+135*456+70224,nextVBlank=new_epoch+144*456+70224,randomState=end['randomState'],hudCursor=2,fadeRemaining=7),summary[0])
    if int(stage_summary[0]['end'])!=data['points'][0]['cycles']-epoch or int(summary[0]['displays'])!=int(stage_summary[0]['displays'])+2 or int(summary[0]['stats'])!=int(stage_summary[0]['stats'])+2:
        raise ValueError('Native following entry is not attached to its masked stage')
    return differences

def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'entry.json').read_text());startup=json.loads((args.startup/'startup.json').read_text())
    for recording in (data,startup):
        require_capture_reference(manifest,recording)
        if any(recording[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed following entry controls')
    if manifest['controlDifferences']:raise ValueError('Changed original control')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
    path=args.native_csv;values=[rows(path)]+[rows(path.with_suffix('.'+key+'.csv')) for key in ('services','interrupts','summary')]+[rows(args.stage_summary)]
    differences=compare_entry(data,*values,epoch)
    report=dict(comparedBoundaries=12,comparedServices=2,comparedInterrupts=4,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,
        evidenceLimit='039c..03d8 source resources/HUD work, native scene seed, LCD restart, complete pending and first periodic vectors, input/audio and ready-clear. Excludes fresh-entry pause, copied glyph/HUD/actor bytes, pixels/PCM, subsequent gameplay and production Windows scheduling.')
    write_json(path.with_suffix('.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native following entry differs')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--next-retry',action='store_true')
    record.add_argument('--after-retry',type=int,choices=(1,2),default=1)
    verify=sub.add_parser('compare');verify.add_argument('native_csv',type=Path);verify.add_argument('--startup',type=Path,required=True);verify.add_argument('--stage-summary',type=Path,required=True)
    for command in (record,verify):command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
