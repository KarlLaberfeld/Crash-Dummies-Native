"""Separate read-only final-life result/banner/music/fade/fixed-hold observations.

Source observations never initialize native execution. ROM and recordings stay local.
"""
import argparse,contextlib,csv,hashlib,io,json
from pathlib import Path
from types import SimpleNamespace
from air_reference import write_json
from air_following_scope import result_capture_scope
from air_timing import IRQ_PHASES,VBLANK_FIXED,vblank_work,vblank_bookkeeping_work,elapsed_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference

POINTS={0x0462:'playerReady',0x0575:'failurePortrait',0x0593:'failurePortraitReady',0x059a:'failureTextReady',
        0x25ae:'lcdWriteReturned',0x059d:'enable',0x059e:'enableFollower',0x05a4:'lifeStored',0x065b:'lifeExhausted',
        0x067a:'bannerReady',0x067d:'savingsPointer',0x0681:'savingsDigits',0x0684:'savingsMiddle',0x0687:'savingsComma',0x068c:'savingsCents',0x068f:'savingsReady',
        0x0692:'musicSelect',0x0694:'musicEntry',0x0697:'musicReady',0x20d1:'fadeEntry',0x20d6:'palette',0x20e4:'wait',0x20e7:'tail',0x069a:'fadeReturned',
        0x25c4:'holdWait',0x25c7:'holdTail',0x06a2:'gameOverHoldReturned'}

PREFIX=list(POINTS.values())[:20]


def final_life_scope(data):
    points=data.get('points',[])
    expected=PREFIX+[n for _ in range(8) for n in ('palette','wait','tail','wait','tail','wait','tail','wait','tail')]+['fadeReturned']+['holdWait','holdTail']*480+['gameOverHoldReturned']
    if data.get('version')!=1 or data.get('afterRetry')!=3 or [p['name'] for p in points]!=expected:raise ValueError('Incomplete/reordered final-life result or fixed hold')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Reordered final-result clock')
    first=points[0]
    for i,p in enumerate(points):
        if p.get('result')!=33 or p.get('display')!=10 or p.get('player')!=first.get('player') or p.get('player') not in (0,1):raise ValueError('Mixed final Air result/player')
        if type(p.get('lives')) is not int or p['lives']!=int(i<7):raise ValueError('Final life must be consumed exactly once at its store')
        if type(p.get('savings')) is not int or not 0<=p['savings']<1000000 or p['savings']!=first['savings']:raise ValueError('Game over changed native savings')
    return points


def analyze(data):
    points=final_life_scope(data);irqs=data['interrupts'];services=[];previous=points[0]['cycles']
    enable=points[5]
    if len(irqs)!=1028 or [r['kind'] for r in irqs[:2]]!=['vblank','stat'] or enable['interruptFlags']&3!=3 or irqs[0]['start']!=enable['cycles']+48:
        raise ValueError('Missing final-result pending/periodic vectors')
    if irqs[1]['start']!=irqs[0]['end']+36:raise ValueError('Final-result pending priority differs')
    for i,r in enumerate(irqs):
        if not previous<=r['start']<r['end'] or r['end']+16>points[-1]['cycles'] or r['selector']!=0 or r['returnAddress']!=(0x26de if i<2 else 0x261d):raise ValueError('Unowned final-result vector')
        previous=r['end']+16
        if r['kind']=='stat':
            if r['end']-r['start']!=248:raise ValueError('Unknown result STAT work')
        elif r['kind']=='vblank':
            work=vblank_work(r);fixed={**VBLANK_FIXED,'display':272,'effects':64,'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched'])}
            if r['effectRequest']!=-1 or any(work[k]!=v for k,v in fixed.items()) or r['countdown']!=600-len(services):raise ValueError('Unowned final-result display/effect/countdown work')
            services.append(r)
        else:raise ValueError('Unknown result vector')
    if len(services)!=514 or sum(r['kind']=='stat' for r in irqs)!=514:raise ValueError('Incomplete final-result display pairs')
    previous_input=points[0]['inputHeld']
    for r in services:
        if r['pressed']!=r['held']&~previous_input or r['held']&15==15:raise ValueError('Unowned final-result input/reset')
        previous_input=r['held']
    for p in points:
        finished=sum(r['end']+16<=p['cycles'] for r in services)
        if p['tick']!=(points[0]['tick']+finished)&65535 or p['countdown']!=600-finished:raise ValueError('Final-result counter lost its display owner')
        last=next((r for r in reversed(services[:finished])),None)
        wanted=(last['held'],last['pressed']) if last else (points[0]['inputHeld'],points[0]['inputPressed'])
        if (p['inputHeld'],p['inputPressed'])!=wanted:raise ValueError('Final-result boundary lost input state')
    # The final fixed hold ignores fresh action edges. Its loop tail is not
    # the skippable 25cd result hold, even though the caller still loads L.
    fade_end=next(i for i,p in enumerate(points) if p['name']=='fadeReturned')
    for p,q in zip(points[fade_end:],points[fade_end+1:]):
        work=elapsed_work(p['cycles'],q['cycles'],irqs)
        if p['name']=='fadeReturned' and work!=44:raise ValueError('Unknown final fixed-hold entry')
        if p['name']=='holdTail' and work!=(40 if q['name']=='gameOverHoldReturned' else 28):raise ValueError('Unknown final fixed-hold tail')
    start=points[8]['cycles'];end=next(p['cycles'] for p in points if p['name']=='savingsReady')
    empty=points[8]
    if empty.get('preparedObjectsClear') is not True or empty['lcd']['scx'] or empty['lcd']['lcdc']&32:raise ValueError('First-frame result lacks empty-object/non-window geometry')
    polls=data['polls'];writes=data['writes']
    epoch=enable['cycles']-20
    if not polls or not writes or any(not start<p['cycles']<end or not 456<=p['cycles']-4-epoch<143*456 or p['mode'] not in (0,1,2,3) for p in polls):raise ValueError('Missing bounded game-over text readiness')
    for a,b in zip(polls,polls[1:]):
        if b['cycles']<=a['cycles'] or a['mode']&2 and b['cycles']-a['cycles']!=32:raise ValueError('Invalid glyph readiness retry')
    for w in writes:
        if not start<w['cycles']<end or not 0x9c00<=w['address']<0xa000 or not 0<=w['value']<128:raise ValueError('Unowned game-over glyph store')
        before=next((p for p in reversed(polls) if p['cycles']<w['cycles']),None)
        if before is None or before['mode']&2 or w['cycles']-before['cycles']!=28:raise ValueError('Game-over store lacks its successful readiness read')
    return services


def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or hashlib.sha256(args.rom.read_bytes()).hexdigest()!=manifest['romSha256']:raise ValueError('Changed final-result control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0);scope=result_capture_scope(SimpleNamespace(next_retry=True,after_retry=3))
    active=False;complete=False;exhausted=False;points=[];irqs=[];opened=None;polls=[];writes=[];buttons=[]
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,opened,exhausted
        if complete:return
        scope.observe(pc,p.memory[0xc098],len(buttons))
        if pc==0x2436 and scope.samples(p.memory[0xc098]):buttons.append(p.memory[0xff8a])
        if pc==0x0462 and scope.ready and p.memory[0xc098]==10:active=True
        if not active:return
        now=p._cycles()
        if pc in POINTS:
            if pc==0x065b:exhausted=True
            player=p.memory[0xc082];packed=list(p.memory[0xc085+8*player:0xc088+8*player])
            if any((b>>4)>9 or (b&15)>9 for b in packed):raise ValueError('Invalid original savings')
            savings=sum(((b>>4)*10+(b&15))*100**(2-i) for i,b in enumerate(packed))
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),player=player,lives=p.memory[0xc08a+8*player],savings=savings,result=p.memory[0xc095],display=p.memory[0xc098],
                bgp=p.memory[0xff47],obp0=p.memory[0xff48],obp1=p.memory[0xff49],musicEnabled=p.memory[0xffcf],song=p.memory[0xffce],inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],lcd=p.lcd_snapshot(),interruptFlags=p.memory[0xff0f]))
            if pc==0x065b:points[-1]['preparedObjectsClear']=not any(p.memory[0xc100:0xc200])
            if pc==0x06a2:complete=True;active=False
        elif pc==0x2123 and exhausted:polls.append(dict(cycles=now,mode=p.register_file.A&3))
        elif pc==0x2128 and exhausted:writes.append(dict(cycles=now,address=256*p.register_file.D+p.register_file.E,value=p.register_file.A))
        elif pc in (0x0040,0x0048):
            if opened:raise ValueError('Nested final-result vector')
            opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and opened and opened['kind']=='vblank':
            opened['phases'][IRQ_PHASES[pc]]=now
            if IRQ_PHASES[pc]=='display':opened.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b])
            elif IRQ_PHASES[pc]=='bookkeeping':opened.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
            elif IRQ_PHASES[pc]=='effects':opened['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            elif IRQ_PHASES[pc]=='music':opened['musicEnabled']=p.memory[0xffcf]
        elif pc in (0x2484,0x2555) and opened:opened['end']=now;irqs.append(opened);opened=None
    try:
        with (args.capture/'setup.state').open('rb') as stream:p.load_state(stream)
        for pc in {*POINTS,*IRQ_PHASES,0x268b,0x03d8,0x2123,0x2128,0x0040,0x0048,0x2484,0x2555}:p.hook_register(0,pc,hook,pc)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            else:getattr(p,'button_'+e[0])(e[1])
        digest=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or opened or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete final result or changed original control')
    data=dict(version=1,afterRetry=3,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,interrupts=irqs,polls=polls,writes=writes)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data)
    except ValueError:
        write_json(args.out/'final-result.rejected.json',data);raise
    write_json(args.out/'final-result.json',data)
    (args.out/'buttons.txt').write_text(''.join(str(b)+'\n' for b in buttons))
    print(json.dumps(dict(boundaries=len(points),services=sum(r['kind']=='vblank' for r in irqs),interrupts=len(irqs),polls=len(polls),writes=len(writes),lives=points[-1]['lives'],savings=points[-1]['savings']),indent=2))


def compare(args):
    def read(folder,name):return json.loads((folder/name).read_text(encoding='utf-8'))
    parent=read(args.accepted_capture,'capture-summary.json');child=read(args.capture,'capture-summary.json')
    from air_next_retry_reference import preserved_prefix
    preserved_prefix(parent,child,read(args.accepted_capture,'events.json'),read(args.capture,'events.json'),[['tick',1000,True]])
    if Path(child['parentCapture']).resolve()!=args.accepted_capture.resolve():raise ValueError('Wrong final-gameplay parent')
    for name in ('setup.state','inputs.txt'):
        if (args.accepted_capture/name).read_bytes()!=(args.capture/name).read_bytes():raise ValueError('Changed original setup/input file')
    data=read(args.out,'final-result.json');prefix=read(args.out,'result-prefix.json');startup=read(args.startup,'startup.json')
    for r in (data,prefix,startup):
        require_capture_reference(child,r)
        if any(r[k]!=child[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed final-result observations')
    services=analyze(data)
    from air_startup_reference import analyze as startup_epoch
    from air_result_prefix_reference import analyze as prefix_scope,compare_prefix
    prefix_scope(prefix);epoch=startup_epoch(startup)['epoch']
    game=read(args.accepted_out,'gameplay.json');outro=read(args.accepted_out,'outro.json')
    if prefix.get('afterRetry')!=3 or not prefix.get('nextRetry') or game.get('afterRetry')!=3 or prefix['points'][0]['cycles']!=outro['points'][-1]['cycles'] or prefix['points'][0]['result']!=game['points'][-1]['result']:raise ValueError('Final result is detached from its terminal/outgoing parent')
    initial=prefix['points'][0]['state'];first=data['points'][0]
    if initial['lives']!=1 or first['cycles']!=prefix['points'][-1]['cycles'] or any(first[k]!=initial[j] for k,j in (('tick','tick'),('player','player'),('lives','lives'),('inputHeld','held'),('inputPressed','pressed'))):raise ValueError('Final result lost campaign/input ownership')
    for point in prefix['points']:
        if point['result']!=33 or any(point['state'][k]!=initial[k] for k in ('tick','random','player','lives','held','pressed')):raise ValueError('Masked final setup changed campaign/input/seed state')
    last_service=next(r for r in reversed(outro['interrupts']) if r['kind']=='vblank')
    if (initial['tick'],initial['random'],initial['held'],initial['pressed'])!=(outro['points'][-1]['tick'],game['points'][-1]['random'],last_service['held'],last_service['pressed']):raise ValueError('Final setup lost outgoing counter/seed/input state')
    from air_fifth_gameplay_reference import compare as parent_compare
    values=dict(native_base=args.accepted_base,capture=args.accepted_capture,out=args.accepted_out,startup=args.accepted_startup)
    for k in ('first_base','start_capture','start_out','start_startup','parent_capture','parent_out','parent_startup','parent_result_out','instruction_base'):values[k]=getattr(args,k)
    with contextlib.redirect_stdout(io.StringIO()):parent_compare(SimpleNamespace(**values))
    from air_fourth_entry_reference import preserved_native_prefix
    files=preserved_native_prefix(args.native_base,args.accepted_base)
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth'+suffix).open(newline='',encoding='utf-8-sig') as stream:return list(csv.DictReader(stream))
    differences=compare_prefix(prefix,rows('.next-result.csv'),rows('.next-result.polls.csv'),rows('.next-result.summary.csv'),epoch)
    def check(category,index,wanted,actual):
        delta={k:[v,int(actual[k])] for k,v in wanted.items() if int(actual[k])!=v}
        if delta:differences.append(dict(category=category,index=index,fields=delta))
    native=rows('.final-result.csv');nservices=rows('.final-result.services.csv');nirqs=rows('.final-result.interrupts.csv');npolls=rows('.final-result.polls.csv');nwrites=rows('.final-result.writes.csv');summary=rows('.final-result.summary.csv')
    if [len(x) for x in (native,nservices,nirqs,npolls,nwrites,summary)]!=[len(data['points']),len(services),len(data['interrupts']),len(data['polls']),len(data['writes']),1]:raise ValueError('Incomplete native final-result coverage')
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if q['boundary']!=p['name']:raise ValueError('Reordered native final result')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in ('tick','countdown','bgp','obp0','obp1','musicEnabled','lives','savings','inputHeld','inputPressed')}),q)
    for i,(r,q) in enumerate(zip(services,nservices)):
        work=vblank_work(r)
        check('service',i,dict(service=i,cycle=r['start']-epoch,tick=r['tick'],countdown=r['countdown']-1,display=work['display'],effects=work['effects'],music=work['music'],musicEnabled=r['musicEnabled'],inputHeld=r['held'],inputPressed=r['pressed']),q)
    for i,(r,q) in enumerate(zip(data['interrupts'],nirqs)):
        if r['kind']!=q['kind'] or int(q['owner'])!=(3 if i<2 else 2):raise ValueError('Unowned/reordered native final-result vector')
        check('vector',i,dict(vectorCycle=r['start']-epoch),q)
    for category,source,native,fields in (('poll',data['polls'],npolls,('mode',)),('write',data['writes'],nwrites,('address','value'))):
        for i,(p,q) in enumerate(zip(source,native)):check(category,i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in fields}),q)
    end=data['points'][-1];lcd=next(p['cycles']-20-epoch for p in data['points'] if p['name']=='enable')
    check('summary',0,dict(end=end['cycles']-epoch,lcdEpoch=lcd,tick=end['tick'],countdown=end['countdown'],displays=514,stats=514,nextStat=lcd+143*456+513*70224,nextVBlank=lcd+144*456+513*70224,player=end['player'],lives=0,savings=end['savings']),summary[0])
    p=rows('.next-result.summary.csv')[0]
    check('inheritedState',0,dict(random=initial['random'],tick=initial['tick'],player=initial['player'],lives=1,inputHeld=initial['held'],inputPressed=initial['pressed']),p)
    report=dict(comparedPrefixBoundaries=len(prefix['points']),comparedPrefixPolls=len(prefix['polls']),comparedBoundaries=len(data['points']),comparedServices=len(services),comparedInterrupts=len(nirqs),comparedPolls=len(npolls),comparedWrites=len(nwrites),fixedHoldDisplays=480,livesBefore=1,livesAfter=0,savings=end['savings'],preservedNativeFiles=files,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,
        evidenceLimit='Final Air failure through game-over banner, native zero savings, song 13, incoming fade and fixed 480-display hold. Includes the source-checked single life decrement and bounded first visible-frame text readiness after the first line. High-score selection/name entry, subsequent eliminated-player/title flow, nonzero-savings original cases, full images/PCM, hardware and production Windows scheduling remain unqualified.')
    write_json(Path(str(args.native_base)+'.final-result.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native final-life result differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for key in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base'):verify.add_argument('--'+key,type=Path,required=True)
    for command in (record,verify):
        for key in ('capture','out'):command.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
