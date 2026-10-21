"""Actual selected next-player Air setup, entry and first 32 updates.

The reference is observed independently; native code consumes raw buttons and
decoded local assets, never original cycles, actor snapshots or campaign state.
"""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha
from air_title_actions_reference import event_sha
from password_feedback_reference import prepare as prepare_control,attachment,logical_voice_projection
from selected_following_instruction_reference import tail as instruction_tail,CASES
from reference_backend import require_capture_reference
from air_reference import write_json
from selected_game_entry_reference import GROUPS
from air_following_setup_reference import analyze as prefix_scope,compare_prefix
from air_following_stage_reference import analyze as stage_scope,compare_stage
from air_following_entry_reference import analyze as entry_scope,compare_entry
from air_following_quiet_reference import analyze as play_scope,compare_quiet
from air_title_picture_reference import compare_voices
TAIL=[['tick',80,True]]

def observation_start(events,case):
    suffix=instruction_tail(case)+TAIL
    if events[-len(suffix):]!=suffix:raise ValueError('Unknown attached turn observation input suffix')
    return len(events)-len(suffix)

def prepare(args):
    parent=read(args.capture/'capture-summary.json')
    if parent['inputCase'] not in CASES:raise ValueError('Unknown selected following instruction parent')
    prepare_control(args,TAIL)

def controls(args):
    accepted=read(args.accepted_control/'capture-summary.json');manifest=read(args.capture/'capture-summary.json')
    old=read(args.accepted_control/'events.json');events=read(args.capture/'events.json');setup=sha((args.capture/'setup.state').read_bytes())
    attachment(accepted,manifest,old,events,setup,TAIL);observation_start(events,manifest['inputCase'])
    if (args.capture/'setup.state').read_bytes()!=(args.accepted_control/'setup.state').read_bytes():raise ValueError('Changed selected turn setup')
    return accepted,manifest,old,events

def entry_context(args):
    accepted,manifest,old,events=controls(args);parent=read(args.parent_out/'instruction.json');require_capture_reference(accepted,parent)
    if parent.get('origin')!='selected-following-instruction' or any(parent[k]!=accepted[k] for k in ('romSha256','controlMemorySha256','inputCase')) or parent['setupSha256']!=sha((args.capture/'setup.state').read_bytes()):raise ValueError('Detached selected turn instruction owner')
    return parent,manifest,accepted,old,events

def capture(args):
    from selected_game_entry_reference import capture as observe_entry
    from air_following_gameplay_reference import capture as observe_play
    observe_entry(argparse.Namespace(**dict(vars(args),turn=True)))
    observe_play(argparse.Namespace(**dict(vars(args),selected_entry=args.out/'entry.json',selected_parent_control=None,updates=32,terminal=False,outro=False,next_retry=False,after_retry=1)))
    data=read(args.out/'gameplay.json');entry=read(args.out/'entry.json');analyze_play(data,entry)

def component_scope(data):
    if data.get('version')!=1 or data.get('origin')!='selected-turn-entry' or data['inputCase'] not in CASES or data['parentInputCase'] not in ('full-prompt','skip-held') or data['players'] not in (0,1) or [g['name'] for g in data['groups']]!=list(GROUPS):raise ValueError('Unowned selected turn entry scope')
    cursor=data['groups'][0]['points'][0].get('previousMapCamera')
    if type(cursor) is not int or not 0<=cursor<=65535:raise ValueError('Missing retained original turn map cursor')
    if data['inputCase']=='scroll-held' and (data['players']!=1 or data['parentInputCase']!='full-prompt'):raise ValueError('Turn entry borrowed an unqualified ignored-scroll input path')
    player=1 if data['players'] else 0;life=5 if player else 4;previous=None
    for i,g in enumerate(data['groups']):
        (prefix_scope,stage_scope,entry_scope)[i](g);first=g['points'][0]
        if previous is not None and (first['cycles']!=previous['cycles'] or any(first[k]!=previous[k] for k in ('tick','countdown'))):raise ValueError('Detached turn entry component clocks')
        if i<2 and any((p['player'],p['stage'],p['difficulty'],p['lives'])!=(player,1,0,life) for p in g['points']):raise ValueError('Turn setup lost the actual next player and remaining lives')
        if i==1 and any(first[k]!=previous[k] for k in ('player','stage','difficulty','lives','lcdc','lyc','pendingRequests','display','stat','musicEnabled')):raise ValueError('Turn stage setup lost masked inherited state')
        if i==0 and any(p.get('previousMapCamera')!=first.get('previousMapCamera') for p in g['points']):raise ValueError('Masked turn prefix changed its retained map cursor')
        if i==2 and (any(first[k]!=previous[k] for k in ('cameraX','cameraY','mapScratch','ready','lcdc','lyc','display','stat','pendingRequests','musicEnabled')) or any(len(r.get('voiceStates',[]))!=6 for r in g['interrupts'] if r['kind']=='vblank')):raise ValueError('Turn resource/HUD entry lost its actual prepared state/voices')
        previous=g['points'][-1]
    stage=data['groups'][1]['points'];mapped=next(i for i,p in enumerate(stage) if p['name']=='mapPrepared')
    final=(stage[mapped]['cameraY']+128)&65535
    if any(p['previousMapCamera']!=cursor for p in stage[:mapped]) or any(p['previousMapCamera']!=final for p in stage[mapped:]+data['groups'][2]['points']):raise ValueError('Turn map cursor lacks its actual initial-row preparation owner')
    return [r for r in data['groups'][-1]['interrupts'] if r['kind']=='vblank']

def analyze_entry(data,parent):
    services=component_scope(data);first=data['groups'][0]['points'][0];end=parent['groups'][-1]['points'][-1]
    if parent.get('origin')!='selected-following-instruction' or any(data[k]!=parent[k] for k in ('romSha256','inputCase','parentInputCase','players')) or data['parentControlMemorySha256']!=parent['controlMemorySha256'] or first['cycles']!=end['cycles'] or any(first[k]!=end[k] for k in ('tick','countdown')) or end['musicEnabled'] or end['inputPressed']&~end['inputHeld']:raise ValueError('Selected turn entry is detached from instruction completion')
    wanted=dict(player=1 if data['players'] else 0,stage=1,difficulty=0,lives0=4,lives1=5 if data['players'] else 0,result=0)
    if parent['campaign']!=wanted:raise ValueError('Turn entry cannot borrow another campaign')
    return services

def gameplay_entry_boundary(data,manifest):
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase')):raise ValueError('Changed selected turn gameplay control')
    component_scope(data)
    return data['groups'][-1]['points'][-1]['cycles']

def analyze_play(data,entry):
    if data.get('origin')!='selected-turn-gameplay' or data.get('updates')!=32 or data.get('entryPauseConsumed') or any(data[k]!=entry[k] for k in ('romSha256','controlMemorySha256','inputCase','parentInputCase','players')):raise ValueError('Detached selected turn gameplay scope')
    first=data['points'][0];end=entry['groups'][-1]['points'][-1]
    if first['cycles']!=end['cycles'] or data.get('selectedEntryCycle')!=end['cycles'] or any(first[k]!=end[v] for k,v in (('tick','tick'),('random','randomState'),('cameraX','cameraX'),('cameraY','cameraY'),('lastMapCamera','previousMapCamera'),('mapScratch','mapScratch'),('hudCursor','hudCursor'),('fadeRemaining','fadeRemaining'),('held','inputHeld'),('pressed','inputPressed'))):raise ValueError('Turn gameplay lost its actual completed entry')
    return play_scope(data)

def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def compare(args,_parent_qualified=False):
    if not _parent_qualified:
        from selected_following_instruction_reference import compare as qualify
        candidates=[c for c in read(args.parent_manifest) if Path(c['native_base'])==args.parent_base and Path(c['capture'])==args.accepted_control and Path(c['out'])==args.parent_out and Path(c['startup'])==args.startup]
        if len(candidates)!=1:raise ValueError('Turn lacks its explicit accepted instruction qualification')
        parent_args=argparse.Namespace(**{k:Path(v) for k,v in candidates[0].items() if k!='rom'});parent_args.parent_manifest=args.outcome_manifest;parent_args.terminal_manifest=args.terminal_manifest
        with contextlib.redirect_stdout(io.StringIO()):qualify(parent_args)
    from air_startup_reference import analyze as startup
    from air_fourth_entry_reference import preserved_native_prefix
    from air_clock_compare import compare_sprites
    parent,manifest,accepted,_,events=entry_context(args);entry=read(args.out/'entry.json');play=read(args.out/'gameplay.json');origin=read(args.startup/'startup.json')
    for record in (entry,play,origin):require_capture_reference(manifest,record)
    if origin['romSha256']!=manifest['romSha256'] or entry.get('parentInstructionSha256')!=sha((args.parent_out/'instruction.json').read_bytes()) or entry.get('setupSha256')!=sha((args.capture/'setup.state').read_bytes()) or entry.get('captureEventsSha256')!=event_sha(events) or any(entry[k]!=manifest[k] or play[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase')) or play.get('parentEntrySha256')!=sha((args.out/'entry.json').read_bytes()):raise ValueError('Changed turn controls/recordings/ancestry')
    services=analyze_entry(entry,parent);displays=analyze_play(play,entry)
    prefix=(args.parent_out/'buttons.txt').read_text()
    if entry['groups'][-1]['precedingDisplays']!=len(prefix.splitlines()) or play['precedingDisplays']!=len(prefix.splitlines())+2 or (args.out/'buttons.txt').read_text()!=prefix+''.join(str(r['held'])+'\n' for r in services+displays):raise ValueError('Detached complete turn raw input prefix')
    retained=preserved_native_prefix(args.native_base,args.parent_base);epoch=startup(origin)['epoch'];stem=str(args.native_base)+'.fifth.selected.turn.title-game-';diff=[]
    def table(name,suffix=''):return rows(Path((stem[:-1]+'play' if name=='gameplay' else stem+name)+suffix+'.csv'))
    prior=rows(Path(str(args.parent_base)+'.fifth.selected.selected-next-exit.summary.csv'))[0]
    prefix_summary=table('prefix','.summary');stage_summary=table('stage','.summary');entry_summary=table('entry','.summary')
    diff+=compare_prefix(entry['groups'][0],table('prefix'),table('prefix','.polls'),table('prefix','.writes'),prefix_summary,epoch)
    diff+=compare_stage(entry['groups'][1],table('stage'),stage_summary,prefix_summary,epoch)
    seed=rows(Path(str(args.native_base)+'.fifth.selected.turn.title-game-map-seed.csv'))
    if len(seed)!=1:raise ValueError('Missing native retained turn map cursor')
    if int(seed[0]['previousMapCamera'])!=entry['groups'][0]['points'][0]['previousMapCamera']:diff.append(dict(category='retainedMapCursor',expected=entry['groups'][0]['points'][0]['previousMapCamera'],native=seed[0]))
    projected=dict(entry['groups'][2],precedingDisplays=int(prior['displays']))
    diff+=compare_entry(projected,table('entry'),table('entry','.services'),table('entry','.interrupts'),entry_summary,stage_summary,epoch)
    diff+=compare_voices(logical_voice_projection(services),table('entry','.voices'),int(prior['displays']))
    for key in ('tick','countdown','displays','stats'):
        if int(prefix_summary[0][key])!=int(prior[key]):raise ValueError('Masked turn setup changed its inherited counters')
    for name in ('prefix','stage'):
        if table(name,'.services') or table(name,'.interrupts'):raise ValueError('Masked turn setup accepted unexpected services')
    for name in ('stage','entry'):
        if table(name,'.polls') or table(name,'.writes'):raise ValueError('Unexpected turn setup access stream')
    if int(entry_summary[0]['entryPauseComplete']):raise ValueError('Turn entry borrowed an unqualified pause')
    projected_play=dict(play,precedingDisplays=int(entry_summary[0]['displays']))
    points,actors,nv,ni,summary=[table('gameplay',s) for s in ('','.entities','.services','.interrupts','.summary')]
    delta,occupied=compare_quiet(projected_play,points,actors,nv,ni,summary,entry_summary,epoch);diff+=delta
    # Vacant actor payloads remain excluded, but their surviving animation
    # delay/period are owned by the preceding native game even across turns.
    for slot,(p,q) in enumerate(zip(play['points'][0]['entities'],actors[:16])):
        if any(int(q[k])!=p[k] for k in ('delay','period')):diff.append(dict(category='inheritedAnimation',slot=slot))
    sprites=table('gameplay','.sprites');normalized=[]
    if len(sprites)!=40*len(displays):raise ValueError('Incomplete turn sprite publications')
    for n,q in enumerate(sprites):
        value={k:int(v) for k,v in q.items()}
        if value['service']!=projected_play['precedingDisplays']+n//40 or value['slot']!=n%40:raise ValueError('Reordered turn sprite publications')
        normalized.append(dict(value,service=n//40))
    diff+=compare_sprites(displays,normalized,expected_services=32)
    campaign=parent['campaign'];s=summary[0]
    wanted=dict(player=campaign['player'],lives0=4,lives1=campaign['lives1'],stage=1,difficulty=0,result=0)
    if any(int(s[k])!=v for k,v in wanted.items()):diff.append(dict(category='gameplayCampaign',expected=wanted,native=s))
    report=dict(inputCase=entry['inputCase'],parentInputCase=entry['parentInputCase'],players=entry['players'],entryBoundaries=sum(len(g['points']) for g in entry['groups']),entryServices=2,entryVectors=4,entryPolls=len(entry['groups'][0]['polls']),entryWrites=512,entryVoiceRows=12,updates=32,boundaries=len(points),actorSlots=len(actors),occupiedActors=occupied,services=len(nv),vectors=len(ni),spriteSlots=len(sprites),preservedNativeFiles=retained,differences=len(diff),firstDifference=diff[:1],productionSchedulerAccepted=False,evidenceLimit='Actual next live player after selected Air/easy failure: native setup/entry, retained global animation/partial-second/side-push state, first 32 quiet updates, actor/scalar work, display/input/audio costs and sprite positions/flags. Excludes vacant actor payloads except inherited delay/period, sprite tile bytes, map publication bytes, later gameplay/pause/outcome, final frames/PCM and production scheduling.')
    write_json(Path(str(args.native_base)+'.selected-turn.comparison.json'),report);print(report,flush=True)
    if diff:raise ValueError('Selected next-player Air entry/gameplay differs from original')

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    for mode in ('prepare','capture','compare'):
        p=sub.add_parser(mode)
        if mode!='compare':p.add_argument('rom',type=Path)
        keys=('capture','out')+(('accepted-control','parent-out') if mode!='prepare' else ())+(('native-base','parent-base','parent-manifest','outcome-manifest','terminal-manifest','startup') if mode=='compare' else ())
        for key in keys:p.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();globals()[args.mode](args)
if __name__=='__main__':main()
