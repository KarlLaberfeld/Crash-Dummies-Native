"""Independent original result-to-player selection and LCD-safe map clear.

The reference emulator is used only to capture; native execution receives raw
buttons, never original clocks, lives, writes, polls or result decisions.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work,VBLANK_FIXED,vblank_bookkeeping_work,elapsed_work
from air_loop_timing import stat_cycles
from air_following_scope import FollowingAirCaptureScope

POINTS={0x0514:'begin',0x0523:'switchEntry',0x02bd:'selectionEntry',0x02c0:'livesTest',
        0x02c5:'backgroundClear',0x02ca:'backgroundCleared',0x02ce:'instructionEntry'}

def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or hashlib.sha256(read_rom(args.rom)).hexdigest()!=manifest['romSha256']:
        raise ValueError('Requires an independently matched original control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0);p.set_emulation_speed(0)
    scope=FollowingAirCaptureScope(getattr(args,'following',False))
    active=False;complete=False;points=[];irqs=[];opened=None;polls=[];writes=[];buttons=[]
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,opened
        if complete:return
        scope.observe(pc,p.memory[0xc098],len(buttons))
        if pc==0x2436 and (scope.samples(p.memory[0xc098]) if scope.following else p.memory[0xc098] in (2,10)):buttons.append(p.memory[0xff8a])
        if pc==0x0514 and scope.ready and p.memory[0xc098] in (2,10):active=True
        if not active:return
        now=p._cycles()
        if pc in POINTS:
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),
                player=p.memory[0xc082],lives0=p.memory[0xc08a],lives1=p.memory[0xc092],
                result=p.memory[0xc095],display=p.memory[0xc098],musicEnabled=p.memory[0xffcf],
                inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],lcd=p.lcd_snapshot()))
            if pc==0x02ce:active=False;complete=True
        elif pc in (0x0040,0x0048):
            if opened:raise ValueError('Nested handoff interrupt')
            opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],
                returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),result=p.memory[0xc095],phases={})
        elif pc in IRQ_PHASES and opened and opened['kind']=='vblank':
            name=IRQ_PHASES[pc];opened['phases'][name]=now
            if name=='display':
                opened.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b])
                if p.memory[0xc098]==2:opened['visible']=list(p.memory[0xfe00:0xfea0])
            if name=='bookkeeping':opened.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
            if name=='effects':opened['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if name=='music':opened['musicEnabled']=p.memory[0xffcf]
        elif pc in (0x151e,0x249b) and opened and opened['kind']=='vblank' and p.memory[0xc098]==2:
            state=dict(random=word(0xc09e),emitters=[list(p.memory[0xc200+16*i:0xc205+16*i]) for i in range(4)])
            if pc==0x151e:opened['celebration']=dict(start=now,tick=word(0xc00a),before=state)
            elif p.memory[0xc095]&4:
                if 'celebration' not in opened:raise ValueError('Missing handoff celebration entry')
                opened['celebration'].update(end=now,after=state,prepared=list(p.memory[0xc100:0xc1a0]))
            else:opened['celebration']=dict(start=now,end=now,tick=word(0xc00a),before=state,after=state,prepared=list(p.memory[0xc100:0xc1a0]))
        elif pc in (0x2484,0x2555) and opened:
            if opened['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Mismatched handoff IRQ return')
            opened['end']=now;irqs.append(opened);opened=None
        elif pc==0x2123:polls.append(dict(cycles=now,mode=p.register_file.A&3))
        elif pc==0x2128:writes.append(dict(cycles=now,address=256*p.register_file.D+p.register_file.E,value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in (*POINTS,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x2123,0x2128,0x151e,0x249b,0x268b,0x03d8,0x0462):p.hook_register(0,pc,hook,pc)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            elif e[0] in ('press','release'):getattr(p,'button_'+e[0])(e[1])
            else:raise ValueError('Unknown original input event')
        digest=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or opened or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete handoff or changed original control')
    data=dict(version=2 if points[0]['result']&4 else 1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,
        points=points,interrupts=irqs,polls=polls,writes=writes)
    if scope.following:data.update(followingResult=True,precedingDisplays=len(buttons)-sum(r['kind']=='vblank' for r in irqs)-scope.display_offset)
    analyze(data);args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'handoff.json',data)
    (args.out/'buttons.txt').write_text(''.join(str(b)+'\n' for b in buttons))
    print(json.dumps(dict(boundaries=len(points),interrupts=len(irqs),polls=len(polls),writes=len(writes),
        begin=points[0],end=points[-1],controlDifferences=0),indent=2))

def analyze(data):
    if data.get('version') not in (1,2):raise ValueError('Recapture handoff reference')
    points=data.get('points',[]);irqs=data.get('interrupts',[]);polls=data.get('polls',[]);writes=data.get('writes',[])
    if not points or points[0]['name']!='begin' or points[-1]['name']!='instructionEntry':raise ValueError('Incomplete handoff terminal coverage')
    groups=(len(points)-3)//4
    expected=[name for _ in range(groups) for name in ('begin','switchEntry','selectionEntry','livesTest')]+['backgroundClear','backgroundCleared','instructionEntry']
    if groups not in (1,2) or [p['name'] for p in points]!=expected:raise ValueError('Missing/reordered handoff selection')
    first=points[0];lives=[first['lives0'],first['lives1']];result=first['result'];player=first['player']
    perfect=bool(result&4)
    if player not in (0,1) or any(not 0<=v<=255 for v in lives) or not any(lives) or not result&1 or (perfect and (result!=7 or data['version']!=2)):
        raise ValueError('Separate eliminated/special-result owner required')
    for index,p in enumerate(points):
        if index and p['cycles']<=points[index-1]['cycles']:raise ValueError('Handoff boundaries do not increase')
        if p['display']!=(2 if perfect else 10) or p['musicEnabled'] or (p['inputHeld']&15)==15 or not p['lcd']['lcdc']&128:
            raise ValueError('Unowned handoff display/music/reset/LCD state')
        if [p['lives0'],p['lives1']]!=lives or p['result']!=(0 if index==len(points)-1 else result):raise ValueError('Unexpected campaign/result mutation')
    for group in range(groups):
        a,b,c,d=points[4*group:4*group+4]
        if a['player']!=player or b['player']!=player:raise ValueError('Player changed before switch completion')
        player^=1
        if c['player']!=player or d['player']!=player:raise ValueError('Player switch did not complete')
        if bool(lives[player])!=(group==groups-1):raise ValueError('Live-player branch is incomplete')
    if any(p['player']!=player for p in points[-3:]):raise ValueError('Selected player changed during map clear')
    services=[];last=first['cycles'];previous=first['inputHeld']
    for r in irqs:
        if not last<=r['start']<r['end'] or r['end']+16>points[-1]['cycles']:raise ValueError('Incomplete/overlapping handoff IRQ')
        last=r['end']+16
        if r['kind']=='stat':
            selector=4 if perfect else 0
            if r['selector']!=selector or r['end']-r['start']!=stat_cycles(selector):raise ValueError('Unowned handoff STAT')
        elif r['kind']=='vblank':
            c=vblank_work(r);display=228 if r['countdown']==1 else 272
            if perfect:
                celebration=r.get('celebration',{})
                if not celebration or len(r.get('visible',[]))!=160:raise ValueError('Missing handoff celebration/publication')
                active=bool(r['result']&4)
                if not r['phases']['display']<celebration['start']<=celebration.get('end',0)<r['phases']['bookkeeping'] or active!=(celebration['end']>celebration['start']):raise ValueError('Incorrect handoff celebration branch')
                display+=(80+celebration['end']-celebration['start']) if active else 68
            fixed={**VBLANK_FIXED,'display':display,'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched']),'effects':64,'music':60}
            if r['countdown']<1 or any(c[k]!=v for k,v in fixed.items()) or r['effectRequest']!=-1 or r['musicEnabled']:
                raise ValueError('Unowned handoff display/audio service')
            if (r['held']&15)==15 or r['pressed']!=r['held']&~previous:raise ValueError('Handoff fresh input/reset differs')
            previous=r['held'];services.append(r)
        else:raise ValueError('Unknown handoff IRQ')
    if perfect:
        from air_celebration_reference import analyze as analyze_component
        analyze_component(dict(version=1,terminal='handoff',services=[r['celebration'] for r in services]))
        for a,b in zip(services,services[1:]):
            if b['visible']!=a['celebration']['prepared']:raise ValueError('Handoff publication continuity differs')
    for p,q in zip(points,points[1:]):
        if p['name']=='backgroundClear':continue
        work=elapsed_work(p['cycles'],q['cycles'],irqs)
        wanted={'begin':48,'switchEntry':56,'selectionEntry':88,'livesTest':24 if lives[p['player']] else 28,'backgroundCleared':20}[p['name']]
        if work!=wanted:raise ValueError('Handoff source branch work differs')
    if len(writes)!=1024 or any(r['address']!=0x9800+i or r['value'] for i,r in enumerate(writes)):
        raise ValueError('Map clear is incomplete or writes outside its destination')
    begin=points[-3]['cycles'];end=points[-2]['cycles']
    if not polls or len(polls)<1024 or any(not begin<=r['cycles']<end or r['mode'] not in (0,1,2,3) for r in polls):
        raise ValueError('Invalid/missing handoff readiness polls')
    if any(b['cycles']<=a['cycles'] for a,b in zip(polls,polls[1:])) or any(b['cycles']<=a['cycles'] for a,b in zip(writes,writes[1:])):
        raise ValueError('Reordered handoff accesses')
    poll_index=0
    for write in writes:
        first_poll=poll_index
        while poll_index<len(polls) and polls[poll_index]['cycles']<write['cycles']:
            poll_index+=1
        group=polls[first_poll:poll_index]
        if not group or group[-1]['mode']&2 or any(not r['mode']&2 for r in group[:-1]) or not begin<write['cycles']<end:
            raise ValueError('Glyph store lacks its own busy/ready poll sequence')
    if poll_index!=len(polls):raise ValueError('Trailing readiness reads after map clear')
    return services

def compare_handoff(data,points,services,irqs,polls,writes,summary,epoch,celebrations=None):
    original_services=analyze(data)
    if (len(points),len(services),len(irqs),len(polls),len(writes),len(summary))!=(len(data['points']),len(original_services),len(data['interrupts']),len(data['polls']),1024,1):
        raise ValueError('Native handoff coverage is incomplete')
    differences=[]
    def delta(where,target,row):
        fields={key:[value,int(row[key])] for key,value in target.items() if int(row[key])!=value}
        if fields:differences.append(dict(at=where,fields=fields))
    for i,(target,row) in enumerate(zip(data['points'],points)):
        if target['name']!=row['boundary']:raise ValueError('Native handoff points are reordered')
        expected={k:target[k] for k in ('tick','countdown','player','lives0','lives1','result','inputHeld','inputPressed')};expected['cycle']=target['cycles']-epoch
        delta('boundary '+str(i),expected,row)
    for i,(target,row) in enumerate(zip(original_services,services)):
        c=vblank_work(target);delta('service '+str(i),dict(cycle=target['start']-epoch,tick=target['tick'],
            countdown=max(1,target['countdown']-1),display=c['display'],effects=c['effects'],music=c['music'],inputHeld=target['held'],inputPressed=target['pressed']),row)
        if i and int(row['service'])!=int(services[i-1]['service'])+1:raise ValueError('Native handoff services are reordered')
    for i,(target,row) in enumerate(zip(data['interrupts'],irqs)):
        if target['kind']!=row['kind'] or int(row['owner'])!=1:raise ValueError('Native handoff IRQ lacks its source completion owner')
        delta('interrupt '+str(i),dict(vectorCycle=target['start']-epoch),row)
    for kind,targets,rows in [('poll',data['polls'],polls),('write',data['writes'],writes)]:
        for i,(target,row) in enumerate(zip(targets,rows)):
            expected={k:v for k,v in target.items() if k!='cycles'};expected['cycle']=target['cycles']-epoch;delta(kind+' '+str(i),expected,row)
    last=data['points'][-1]
    expected={k:last[k] for k in ('tick','countdown','player','lives0','lives1','result')};expected['end']=last['cycles']-epoch
    delta('summary',expected,summary[0])
    if services and int(summary[0]['displays'])!=int(services[-1]['service'])+1:
        raise ValueError('Native handoff display terminal differs')
    if data['points'][0]['result']&4:
        from air_celebration_reference import compare_component
        if celebrations is None:raise ValueError('Missing native perfect handoff celebration')
        component=dict(version=1,terminal='handoff',services=[r['celebration'] for r in original_services])
        differences.extend(dict(celebration=d) for d in compare_component(component,celebrations,int(services[0]['service'])))
        for i,(p,q) in enumerate(zip(original_services,celebrations)):
            if any(f'visible{j}' not in q for j in range(160)):raise ValueError('Missing native handoff published list')
            delta('publication '+str(i),{f'visible{j}':v for j,v in enumerate(p['visible'])},q)
    return differences

def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'handoff.json').read_text())
    startup=json.loads((args.startup/'startup.json').read_text())
    for recording in (data,startup):
        require_capture_reference(manifest,recording)
        if any(recording[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed handoff original controls')
    if manifest['controlDifferences']:raise ValueError('Original control differs')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    path=args.native_csv
    values=[rows(path)]+[rows(path.with_suffix('.'+kind+'.csv')) for kind in ('services','interrupts','polls','writes','summary')]
    celebrations=rows(path.with_suffix('.celebration.csv')) if data['points'][0]['result']&4 else None
    differences=compare_handoff(data,*values,epoch,celebrations)
    report=dict(comparedBoundaries=len(data['points']),comparedServices=len(values[1]),comparedInterrupts=len(values[2]),
        comparedPolls=len(values[3]),comparedWrites=len(values[4]),differences=len(differences),firstDifference=differences[:1],
        productionSchedulerAccepted=False,perfectHandoffAccepted=bool(data['points'][0]['result']&4),
        evidenceLimit='Native live-player selection and full LCD-safe background clear through 02ce; perfect version 2 additionally requires ongoing celebration work/state and prepared/published lists. Subsequent labels, instructions, gameplay entry and all-eliminated/title paths remain separate owners.')
    write_json(path.with_suffix('.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native handoff differs from independently controlled original')

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--following',action='store_true')
    verify=sub.add_parser('compare');verify.add_argument('native_csv',type=Path);verify.add_argument('--startup',type=Path,required=True)
    for command in (record,verify):
        command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
if __name__=='__main__':main()
