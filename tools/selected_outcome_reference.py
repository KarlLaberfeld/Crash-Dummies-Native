"""Attached first selected Air failure through the next instruction picture.

The pinned reference is an observer only. Native replay receives raw buttons;
cycles, campaign state, audio state and graphics stores are comparison targets.
"""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from password_feedback_reference import attachment,prepare as prepare_control,logical_voice_projection
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
from air_timing import IRQ_PHASES
from air_exit_timing import POINTS as OUTRO
from air_result_prefix_reference import POINTS as PREFIX
from air_result_transition_reference import POINTS as RESULT,HOLD_POINTS
from air_handoff_reference import POINTS as HANDOFF
from air_instruction_header_reference import POINTS as HEADER
from air_title_picture_reference import voice_states,compare_voices

TAIL=[['release',key] for key in ('a','b','select','start','right','left','up','down')]+[['tick',800,True]]
NAMES=('outro','prefix','result','handoff','header','picture')
TABLES=(OUTRO,PREFIX,{**RESULT,**HOLD_POINTS},HANDOFF,HEADER,
    {0x031c:'begin',0x0321:'musicReady',0x0324:'stageReady',0x0328:'tableDispatch',
     0x09ee:'resourceEntry',0x09f9:'copyCall',0x09fc:'copyReturned',0x0a07:'rectangleReady',0x268b:'end'})
ENDS=(0x0409,0x0462,0x0514,0x02ce,0x031c,0x268b)

def prepare(args):
    parent=read(args.capture/'capture-summary.json')
    if parent.get('gameplayTerminal') is not True:raise ValueError('Outcome requires terminal gameplay control')
    prepare_control(args,TAIL)

def controls(args):
    parent=read(args.accepted_control/'capture-summary.json');child=read(args.capture/'capture-summary.json')
    old=read(args.accepted_control/'events.json');events=read(args.capture/'events.json')
    attachment(parent,child,old,events,sha((args.capture/'setup.state').read_bytes()),TAIL)
    if parent.get('gameplayTerminal') is not True or (args.accepted_control/'setup.state').read_bytes()!=(args.capture/'setup.state').read_bytes():raise ValueError('Detached terminal outcome control')
    return parent,child,old,events

def capture(args):
    accepted,manifest,old,events=controls(args);parent=read(args.parent_out/'gameplay.json')
    require_capture_reference(accepted,parent)
    if parent.get('terminalWait') is not True or parent['updates']!=accepted.get('gameplayUpdates') or parent['controlMemorySha256']!=accepted['controlMemorySha256'] or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Changed selected outcome parent/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0)
    groups=[dict(name=name,version=2 if i in (0,2) else 1,points=[],interrupts=[],polls=[],writes=[]) for i,name in enumerate(NAMES)]
    groups[0]['fadePalettes']=list(args.rom.read_bytes()[0x2118:0x2120]);groups[2]['failureHold']=True
    index=0;active=complete=False;irq=None;buttons=[];result_displays=0
    raw_preceding=len((args.parent_out/'buttons.txt').read_text().splitlines())
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def fields(pc):
        player=p.memory[0xc082];lives=p.memory[0xc08a+8*player]
        common=dict(tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b])
        display=p.memory[0xc098];enabled=p.memory[0xffcf];result=p.memory[0xc095]
        if index==0:return dict(tick=common['tick'],counter=p.memory[0xc009],ready=p.memory[0xffae],musicEnabled=enabled,bgp=p.memory[0xff47],obp0=p.memory[0xff48],obp1=p.memory[0xff49])
        if index==1:return dict(lcd=p.lcd_snapshot(),interruptFlags=p.memory[0xff0f],interruptEnable=p.memory[0xffff],result=result,state=dict(display=display,stat=p.memory[0xc099],countdown=common['countdown'],random=word(0xc09e),emitters=[list(p.memory[0xc200+16*i:0xc205+16*i]) for i in range(4)],player=player,lives=lives,tick=common['tick'],held=common['inputHeld'],pressed=common['inputPressed']))
        rest=dict(common,display=display,result=result,musicEnabled=enabled)
        if index==2:return dict(rest,pc=pc,player=player,lives=lives,song=p.memory[0xffce],bgp=p.memory[0xff47],obp0=p.memory[0xff48],obp1=p.memory[0xff49],interruptFlags=p.memory[0xff0f],lcd=p.lcd_snapshot())
        if index==3:return dict(rest,player=player,lives0=p.memory[0xc08a],lives1=p.memory[0xc092],lcd=p.lcd_snapshot())
        if index==4:return dict(rest,player=player,stage=p.memory[0xc088+8*player],difficulty=p.memory[0xc089+8*player],lives=lives)
        return dict(rest,stage=p.memory[0xc088+8*player],song=p.memory[0xffce])
    def hook(pc):
        nonlocal index,active,complete,irq,result_displays
        if complete:return
        now=p._cycles()
        if not active:
            if pc!=0x0403 or now!=parent['points'][-1]['cycles']:return
            active=True
        while pc in TABLES[index]:
            group=groups[index]
            if not group['points']:
                group['rawPrecedingInputSamples']=raw_preceding+len(buttons)
                group['precedingDisplays']=parent['precedingDisplays']+sum(r['kind']=='vblank' for r in parent['interrupts']) if index==0 else result_displays
            group['points'].append(dict(name=TABLES[index][pc],cycles=now,**fields(pc)))
            if pc!=ENDS[index]:break
            if irq:raise ValueError('Outcome segment ended inside an interrupt')
            if index==5:complete=True;return
            index+=1
        group=groups[index]
        if pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested outcome interrupt')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],display=p.memory[0xc098],returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),ready=p.memory[0xffae],result=p.memory[0xc095],phases={})
            if index==0 and pc==0x0040:irq['oam']=list(p.memory[0xc100:0xc1a0])
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            phase=IRQ_PHASES[pc];irq['phases'][phase]=now
            if phase=='display':
                irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
                if index>=2:result_displays+=1
                if index==0:irq['displayWorkload']=dict(map_pending=p.memory[0xc00d],ready=p.memory[0xffae],chunks=p.memory[0xffb5],cursor=p.memory[0xc04c],tick=word(0xc00a),fade_remaining=p.memory[0xffc9],collected=p.memory[0xc20a],quota=p.memory[0xffab])
            if phase=='bookkeeping':irq.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
            if phase=='effects':irq['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if phase=='music':irq['musicEnabled']=p.memory[0xffcf]
            if phase=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:
            if irq['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Mismatched outcome interrupt')
            irq['end']=now;group['interrupts'].append(irq);irq=None
        if index==1:
            if pc==0x2598:group['polls'].append(dict(cycles=now,ly=p.register_file.A))
            if pc==0x25a2:group['lcdOff']=dict(cycles=now,lcd=p.lcd_snapshot(),interruptFlags=p.memory[0xff0f])
        if index>=3:
            if pc==0x2123 or index==5 and pc==0x2363:group['polls'].append(dict(cycles=now,mode=p.register_file.A&3,lcd=p.lcd_snapshot()))
            if pc==0x2128 or index==5 and pc==0x2368:
                row=dict(cycles=now,address=256*p.register_file.D+p.register_file.E,value=p.register_file.A)
                if index==5:row['kind']='tile' if pc==0x2368 else 'map'
                group['writes'].append(row)
    tail=[['press','a'],['press','right'],['tick',parent['updates']-20,True],['release','a'],['release','right'],['tick',4,True]]
    if old[-len(tail):]!=tail:raise ValueError('Outcome parent has an unknown gameplay input suffix')
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        pcs={pc for table in TABLES for pc in table}|set(IRQ_PHASES)|{0x0040,0x0048,0x2484,0x2555,0x2598,0x25a2,0x2123,0x2128,0x2363,0x2368}
        for n,event in enumerate(events):
            if n==len(old)-len(tail):
                for pc in pcs:p.hook_register(0,pc,hook,pc)
            replay(p,[event])
            if n==len(old)-1 and memory_sha(p)!=accepted['controlMemorySha256']:raise ValueError('Outcome observer changed its accepted terminal prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete outcome observation or changed control')
    data=dict(version=1,origin='selected-initial-outcome',reference=metadata,inputCase=manifest['inputCase'],players=parent['players'],romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=accepted['controlMemorySha256'],parentGameplaySha256=sha((args.parent_out/'gameplay.json').read_bytes()),setupSha256=sha((args.capture/'setup.state').read_bytes()),groups=groups)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except (ValueError,KeyError):write_json(args.out/'outcome.rejected.json',data);raise
    write_json(args.out/'outcome.json',data)
    (args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons))
    print(dict(groups=len(groups),boundaries=sum(len(g['points']) for g in groups),services=len(buttons)),flush=True)

def analyze(data,parent):
    if data.get('version')!=1 or data.get('origin')!='selected-initial-outcome' or parent.get('terminalWait') is not True or data['players']!=parent['players'] or data['parentControlMemorySha256']!=parent['controlMemorySha256'] or any(data[k]!=parent[k] for k in ('romSha256','inputCase')) or [g['name'] for g in data['groups']]!=list(NAMES):raise ValueError('Detached selected outcome ancestry')
    from air_following_outro_reference import analyze as outro
    from air_result_prefix_reference import analyze as prefix
    from air_result_transition_reference import analyze as result
    from air_handoff_reference import analyze as handoff
    from air_instruction_header_reference import analyze as header
    from air_instruction_picture_reference import analyze as picture
    groups=data['groups'];outro(groups[0],parent)
    for check,g in zip((prefix,result,handoff,header,picture),groups[1:]):check(g)
    campaign_attachment(data,parent)
    return groups

def campaign_attachment(data,parent):
    """Cross-owner continuity, in addition to each component's strict scope."""
    groups=data['groups']
    previous=parent['points'][-1]
    for g in groups:
        first=g['points'][0]
        if first['cycles']!=previous['cycles']:raise ValueError('Outcome segment lacks its actual preceding endpoint')
        previous=g['points'][-1]
    state=groups[1]['points'][0]['state'];terminal=parent['points'][-1]
    if terminal['result']!=1:raise ValueError('Selected outcome requires its actual failed attempt')
    outgoing=[r for r in groups[0]['interrupts'] if r['kind']=='vblank']
    wanted=dict(tick=groups[0]['points'][-1]['tick'],random=terminal['random'],player=0,lives=5,held=outgoing[-1]['held'],pressed=outgoing[-1]['pressed'])
    if any(state.get(k)!=v for k,v in wanted.items()):raise ValueError('Masked setup lost the actual terminal campaign/seed/input')
    for n,p in enumerate(groups[1]['points']):
        if p['result']!=1 or any(p['state'].get(k)!=v for k,v in wanted.items()) or (p['state']['display'],p['state']['stat'],p['state']['countdown'])!=((4,4,state['countdown']) if n<5 else (10,0,600)):raise ValueError('Masked setup changed inherited state or callback ownership')
    first=groups[2]['points'][0]
    if any(first[k]!=v for k,v in dict(tick=state['tick'],player=0,lives=5,inputHeld=state['held'],inputPressed=state['pressed'],countdown=600,result=1).items()):raise ValueError('Result incoming is detached from its actual masked setup')
    preceding=0
    for i,g in enumerate(groups):
        if i>=2:
            if g['precedingDisplays']!=preceding:raise ValueError('Outcome diagnostic display numbering is detached')
            preceding+=sum(r['kind']=='vblank' for r in g['interrupts'])
        if i>=3:
            before=groups[i-1]['points'][-1];after=g['points'][0]
            if any(before[k]!=after[k] for k in ('tick','countdown','inputHeld','inputPressed')):raise ValueError('Outcome boundary lost inherited time/input')
    points=groups[2]['points'];consumed=False
    for p in points:
        consumed|=p['name']=='failureWait'
        if p['player']!=0 or p['lives']!=(4 if consumed else 5):raise ValueError('Selected initial failure did not consume exactly one actual life')
    if not consumed:raise ValueError('Selected failure omits its life consumption')
    lives=[4,5 if data['players'] else 0];player=1 if data['players'] else 0
    if any([p['lives0'],p['lives1']]!=lives for p in groups[3]['points']) or groups[3]['points'][-1]['player']!=player:raise ValueError('Selected outcome lost the actual next live player')
    if any((p['player'],p['stage'],p['difficulty'],p['lives'])!=(player,1,0,lives[player]) for p in groups[4]['points']):raise ValueError('Next header lost the selected campaign')
    if any(p['song']!=2 for p in groups[5]['points'][1:]):raise ValueError('Next instruction song is not owned by its source start')

def rows(path,numeric=False):
    with path.open(encoding='utf-8-sig',newline='') as f:
        return [{k:int(v) if numeric and k not in ('kind','phase','boundary') else v for k,v in r.items()} for r in csv.DictReader(f)]

def compare(args,_parent_qualified=False):
    from air_fourth_entry_reference import preserved_native_prefix
    from air_startup_reference import analyze as startup
    from air_following_outro_reference import compare_outro
    from air_result_prefix_reference import compare_prefix
    from air_result_transition_reference import compare_transition
    from air_handoff_reference import compare_handoff
    from air_instruction_header_reference import compare_header
    from air_instruction_picture_reference import compare_picture
    if not _parent_qualified:
        from selected_map_reference import compare as qualify
        cases=[c for c in read(args.parent_manifest) if Path(c['native_base'])==args.parent_base and Path(c['play_control'])==args.accepted_control and Path(c['gameplay_out'])==args.parent_out]
        if len(cases)!=1 or Path(cases[0]['startup'])!=args.startup:raise ValueError('Outcome lacks its explicit accepted terminal qualification/startup')
        with contextlib.redirect_stdout(io.StringIO()):qualify(argparse.Namespace(**{k:Path(v) for k,v in cases[0].items()}))
    accepted,manifest,_,_=controls(args);data=read(args.out/'outcome.json');parent=read(args.parent_out/'gameplay.json')
    require_capture_reference(manifest,data);require_capture_reference(accepted,parent)
    if data['parentGameplaySha256']!=sha((args.parent_out/'gameplay.json').read_bytes()) or data['setupSha256']!=sha((args.capture/'setup.state').read_bytes()) or data['controlMemorySha256']!=manifest['controlMemorySha256']:raise ValueError('Changed selected outcome files/controls')
    origin=read(args.startup/'startup.json');require_capture_reference(manifest,origin)
    if origin['romSha256']!=data['romSha256'] or parent['controlMemorySha256']!=accepted['controlMemorySha256'] or parent['updates']!=accepted.get('gameplayUpdates'):raise ValueError('Changed terminal parent or startup ROM/backend')
    groups=analyze(data,parent);epoch=startup(origin)['epoch'];differences=[]
    root=str(args.native_base)+'.fifth.selected.'
    stems=('selected-outro','selected-result-prefix','selected-result','selected-handoff','selected-next-header','selected-next-picture')
    def table(i,suffix='',numeric=False):return rows(Path(root+stems[i]+suffix+'.csv'),numeric)
    entry=rows(Path(str(args.native_base)+'.fifth.selected.title-gameplay.summary.csv'),True)
    # The incoming result owner resets diagnostic display indices. The raw
    # source input sample index is retained separately; no source clock resets.
    if groups[0]['rawPrecedingInputSamples']!=len((args.parent_out/'buttons.txt').read_text().splitlines()):raise ValueError('Detached raw outcome input prefix')
    raw=groups[0]['rawPrecedingInputSamples']
    for g in groups:
        if g['rawPrecedingInputSamples']!=raw:raise ValueError('Detached raw outcome segment inputs')
        raw+=sum(r['kind']=='vblank' for r in g['interrupts'])
    preceding=entry[0]['displays'];projected=dict(parent,precedingDisplays=preceding-sum(r['kind']=='vblank' for r in parent['interrupts']))
    outgoing=dict(groups[0],precedingDisplays=preceding)
    differences+=compare_outro(outgoing,projected,table(0,numeric=True),*[table(0,'.'+k,True) for k in ('services','interrupts','sprites','summary')],entry,epoch)
    differences+=compare_prefix(groups[1],table(1),table(1,'.polls'),table(1,'.summary'),epoch)
    s=groups[1]['points'][-1]['state'];native=table(1,'.summary')[0]
    wanted=dict(display=10,stat=0,countdown=600,random=s['random'],tick=s['tick'],player=s['player'],lives=s['lives'],inputHeld=s['held'],inputPressed=s['pressed'])
    delta={k:[v,int(native[k])] for k,v in wanted.items() if int(native[k])!=v}
    if delta:differences.append(dict(category='inheritedPrefixState',fields=delta))
    differences+=compare_transition(groups[2],table(2),table(2,'.services'),table(2,'.interrupts'),table(2,'.summary'),epoch)
    enabled=next(p for p in groups[2]['points'] if p['name']=='enable')['cycles']-20-epoch
    displays=sum(r['kind']=='vblank' for r in groups[2]['interrupts'])
    native=table(2,'.summary')[0]
    wanted=dict(player=0,lives=4,nextStat=enabled+143*456+(displays-1)*70224,nextVBlank=enabled+144*456+(displays-1)*70224)
    delta={k:[v,int(native[k])] for k,v in wanted.items() if int(native[k])!=v}
    if delta:differences.append(dict(category='resultCampaignDeadlines',fields=delta))
    for i,check in ((3,compare_handoff),(4,compare_header),(5,compare_picture)):
        target=groups[i]
        if i==3:target=dict(target,polls=[{k:v for k,v in r.items() if k!='lcd'} for r in target['polls']])
        differences+=check(target,table(i),*[table(i,'.'+k) for k in ('services','interrupts','polls','writes','summary')],epoch)
        wanted=dict(player=1 if data['players'] else 0,lives0=4,lives1=5 if data['players'] else 0,result=0,stage=1,difficulty=0)
        native=table(i,'.summary')[0]
        delta={k:[v,int(native[k])] for k,v in wanted.items() if int(native[k])!=v}
        if delta:differences.append(dict(category=NAMES[i]+'Campaign',fields=delta))
    for n,(p,q) in enumerate(zip(groups[4]['points'],table(4))):
        if int(q['lives'])!=p['lives']:differences.append(dict(category='headerLives',boundary=n,expected=p['lives'],native=int(q['lives'])))
    for i in (2,5):
        for n,(p,q) in enumerate(zip(groups[i]['points'],table(i))):
            wanted=dict(song=p['song'] if p['musicEnabled'] else -1)
            if i==2:wanted.update(player=p['player'],lives=p['lives'])
            delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
            if delta:differences.append(dict(group=NAMES[i],boundary=n,fields=delta))
        vbs=[r for r in groups[i]['interrupts'] if r['kind']=='vblank']
        differences+=compare_voices(logical_voice_projection(vbs),table(i,'.voices'),groups[i]['precedingDisplays'])
    retained=preserved_native_prefix(args.native_base,args.parent_base)
    expected=(args.parent_out/'buttons.txt').read_text()+''.join(str(r['held'])+'\n' for g in groups for r in g['interrupts'] if r['kind']=='vblank')
    if (args.out/'buttons.txt').read_text()!=expected:raise ValueError('Outcome buttons do not extend their exact source ancestor')
    report=dict(groups=len(groups),boundaries=sum(len(g['points']) for g in groups),vectors=sum(len(g['interrupts']) for g in groups),services=sum(r['kind']=='vblank' for g in groups for r in g['interrupts']),polls=sum(len(g['polls']) for g in groups),writes=sum(len(g['writes']) for g in groups),voiceRows=sum(len(table(i,'.voices')) for i in (2,5)),players=data['players'],preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='First selected Air/easy failed attempt, actual life decrement and next live-player header/music/tile/picture stores through 268b. Excludes subsequent instruction transition/text, second-player gameplay, rendered frames/PCM and production scheduling.')
    write_json(Path(str(args.native_base)+'.selected-outcome.comparison.json'),report);print(report,flush=True)
    if differences:raise ValueError('Selected outcome differs from original')

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    for mode in ('prepare','capture','compare'):
        p=sub.add_parser(mode)
        if mode!='compare':p.add_argument('rom',type=Path)
        for key in ('capture','out')+(('accepted-control','parent-out') if mode!='prepare' else ())+(('native-base','parent-base','parent-manifest','startup') if mode=='compare' else ()):p.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();globals()[args.mode](args)
if __name__=='__main__':main()
