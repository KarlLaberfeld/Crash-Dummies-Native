"""Read-only FFCA inheritance and first steering branch observations.

This supplements an existing fourth-gameplay recording. Source cycle targets
select observations only; they are never supplied to native execution.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from air_reference import write_json
from air_following_gameplay_reference import POINTS,TERMINAL_POINTS
from reference_backend import reference_class,require_matching_backend,require_capture_reference

BRANCHES=(0x5fd6,0x5ff3,0x5ff6,0x6574,0x6578,0x657b,0x657c,0x6581,0x602c,0x602f)


def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());gameplay=json.loads((args.out/'gameplay.json').read_text())
    require_capture_reference(manifest,gameplay)
    if manifest['controlDifferences'] or gameplay.get('afterRetry') not in (2,3) or any(gameplay[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Requires unchanged fourth/fifth-gameplay recording')
    if hashlib.sha256(args.rom.read_bytes()).hexdigest()!=manifest['romSha256']:raise ValueError('Changed ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    selected={}
    for i,point in enumerate(gameplay['points']):selected.setdefault(point['cycles'],[]).append((i,point['name']))
    observed_points={**POINTS,**(TERMINAL_POINTS if gameplay.get('terminalWait') is True else {})}
    first=gameplay['points'][0]['cycles']
    transitions=[i for i,p in enumerate(gameplay['points']) if p['name']=='begin' and p['entities'][0]['handler']==0x5fc9 and p['entities'][0]['params'][0]==1]
    entry_only=gameplay.get('afterRetry')==3 and gameplay.get('updates',1)==1
    if (not entry_only and len(transitions)!=1) or (entry_only and transitions):raise ValueError('Requires one observed Wait-to-Play transition or bounded final entry')
    begin=-1 if entry_only else gameplay['points'][transitions[0]]['cycles'];end=-1 if entry_only else gameplay['points'][transitions[0]+2]['cycles']
    player=Reference(str(args.rom),window='null',sound_volume=0);rows=[];branches=[];previous=None
    def force():return (player.memory[0xffca]+128)%256-128
    def hook(pc):
        nonlocal previous
        now=player._cycles()
        if pc==0x0403 and now<first:
            previous=dict(cycles=now,lastForce=force(),result=player.memory[0xc095],player=player.memory[0xc082])
        if now in selected and pc in observed_points:
            for index,name in selected.pop(now):rows.append(dict(index=index,name=name,cycles=now,lastForce=force()))
        if begin<=now<=end and pc in BRANCHES:
            branches.append(dict(pc=pc,cycles=now,lastForce=force(),rate=(player.memory[0xffa5]+128)%256-128,transfer=player.memory[0xffb6]))
    try:
        with (args.capture/'setup.state').open('rb') as stream:player.load_state(stream)
        for pc in {*observed_points,0x0403}:player.hook_register(0,pc,hook,pc)
        for pc in BRANCHES:player.hook_register(1,pc,hook,pc)
        for event in json.loads((args.capture/'events.json').read_text()):
            if event[0]=='tick':player.tick(event[1],event[2])
            elif event[0] in ('press','release'):getattr(player,'button_'+event[0])(event[1])
            else:raise ValueError('Unknown original control event')
        digest=hashlib.sha256(bytes(player.memory[0x8000:0x10000])).hexdigest()
    finally:player.stop(save=False)
    if selected or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete side-push observation or changed control')
    data=dict(reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,afterRetry=gameplay['afterRetry'],previousTerminal=previous,points=rows,steering=branches)
    if entry_only:data['entryOnly']=True
    try:analyze(data)
    except ValueError:
        write_json(args.out/'side-push.rejected.json',data);raise
    write_json(args.out/'side-push.json',data)
    print(json.dumps(dict(points=len(rows),inherited=rows[0]['lastForce'],branchPoints=len(branches),controlDifferences=0),indent=2))


def analyze(data):
    rows=data['points'];previous=data.get('previousTerminal');branches=data['steering']
    if data.get('afterRetry') not in (2,3) or not rows or previous is None or previous['result']!=33 or not previous['cycles']<rows[0]['cycles']:raise ValueError('Missing preceding failed-game side push')
    if rows[0]['lastForce']!=previous['lastForce']:raise ValueError('Detached side-push inheritance')
    if any(p['index']!=i or p['lastForce'] not in (-4,0,4,12) for i,p in enumerate(rows)):raise ValueError('Invalid side-push observations')
    if any(b['cycles']<a['cycles'] for a,b in zip(rows,rows[1:])):raise ValueError('Reordered side-push observations')
    if data.get('entryOnly') is True:
        from air_following_gameplay_reference import ORDER
        if data['afterRetry']!=3 or len(rows)!=10 or [p['name'] for p in rows]!=ORDER or branches or any(p['lastForce']!=previous['lastForce'] for p in rows):raise ValueError('Unowned final-entry side-push change/extent')
        return dict(inheritedSidePush=rows[0]['lastForce'],entryOnly=True)
    if any(b['cycles']<=a['cycles'] for a,b in zip(branches,branches[1:])):raise ValueError('Reordered steering observations')
    points={p['pc']:p for p in branches}
    if not {0x5fd6,0x5ff3,0x6574,0x6578,0x657b,0x5ff6,0x602c,0x602f}.issubset(points):raise ValueError('Incomplete first steering/clear branch')
    retained=points[0x6578]['lastForce']
    if retained!=rows[0]['lastForce']:raise ValueError('Steering lost its inherited side push')
    if any(points[pc]['lastForce']!=retained for pc in (0x5fd6,0x6574,0x657b,0x602c)) or points[0x602f]['lastForce']!=0:raise ValueError('Unowned side-push clear ordering')
    if points[0x6574]['transfer'] or points[0x6574]['rate']:raise ValueError('Requires the isolated zero-rate steering case')
    if points[0x602f]['cycles']-points[0x602c]['cycles']!=16:raise ValueError('Unknown XOR/LDH clear work')
    body=points[0x5ff6]['cycles']-points[0x6574]['cycles']
    if body!=(60 if retained else 92):raise ValueError('Unknown retained-side-push steering work')
    if retained and any(pc in points for pc in (0x657c,0x6581)):raise ValueError('Nonzero side push did not return early')
    if not retained and not {0x657c,0x6581}.issubset(points):raise ValueError('Zero side push omitted the rate test')
    return dict(inheritedSidePush=rows[0]['lastForce'],firstSteeringBody=body)


def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'side-push.json').read_text());startup=json.loads((args.startup/'startup.json').read_text())
    for record in (data,startup):
        require_capture_reference(manifest,record)
        if any(record[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed side-push controls')
    if manifest['controlDifferences']:raise ValueError('Changed side-push control')
    detail=analyze(data)
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    with args.native_csv.open(newline='',encoding='utf-8-sig') as stream:native=list(csv.DictReader(stream))
    if len(native)!=len(data['points']):raise ValueError('Incomplete native side-push coverage')
    for p,q in zip(data['points'],native):
        if q['boundary']!=p['name'] or int(q['cycle'])!=p['cycles']-epoch or int(q['lastForce'])!=p['lastForce']:raise ValueError('Native side-push inheritance/clear differs')
    report=dict(**detail,comparedSidePushBoundaries=len(native),differences=0,productionSchedulerAccepted=False)
    write_json(args.native_csv.with_suffix('.comparison.json'),report);print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    verify=sub.add_parser('compare');verify.add_argument('native_csv',type=Path);verify.add_argument('--startup',type=Path,required=True)
    for command in (record,verify):
        command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
