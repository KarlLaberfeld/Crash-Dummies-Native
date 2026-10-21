"""Attached actual subsequent-player Air active/resource comparison, 320 updates.

Original observations are independent comparison targets, never native inputs.
"""
import argparse,contextlib,io
from pathlib import Path
from air_title_start_reference import read,sha
from air_title_actions_reference import event_sha
from air_reference import write_json
from password_feedback_reference import attachment,prepare as prepare_control
from selected_following_instruction_reference import CASES
from selected_turn_reference import observation_start,analyze_play,rows
from reference_backend import require_capture_reference
TAIL=[['press','a'],['press','right'],['tick',300,True],['release','a'],['release','right'],['tick',4,True]]

def extension(parent,child,events,changed,setup):
    attachment(parent,child,events,changed,setup,TAIL)
    if child.get('gameplayScope')!='selected-turn-active' or child.get('gameplayUpdates')!=320 or child.get('gameplayTerminal',False) is not False or child['inputCase'] not in CASES:
        raise ValueError('Unqualified subsequent-player active scope')
    observation_start(events,parent['inputCase'])

def prepare(args):
    parent=read(args.capture/'capture-summary.json');events=read(args.capture/'events.json')
    observation_start(events,parent['inputCase'])
    prepare_control(args,TAIL)
    path=args.out/'capture-summary.json';child=read(path)
    child.update(gameplayScope='selected-turn-active',gameplayUpdates=320)
    extension(parent,child,events,read(args.out/'events.json'),sha((args.out/'setup.state').read_bytes()))
    write_json(path,child)

def controls(args):
    parent=read(args.accepted_control/'capture-summary.json');child=read(args.capture/'capture-summary.json')
    old=read(args.accepted_control/'events.json');events=read(args.capture/'events.json')
    extension(parent,child,old,events,sha((args.capture/'setup.state').read_bytes()))
    if (args.accepted_control/'setup.state').read_bytes()!=(args.capture/'setup.state').read_bytes():raise ValueError('Changed active turn setup')
    return parent,child

def preserve_early(data,early,entry):
    analyze_play(early,entry)
    if data.get('origin')!='selected-turn-gameplay' or data.get('updates')!=320 or data.get('resourceTransfers') is not True or data.get('busyScenes') or data.get('terminalWait') or data.get('entryPauseConsumed'):
        raise ValueError('Unowned actual-turn active extent')
    if any(data[k]!=early[k] for k in ('romSha256','inputCase','parentInputCase','players','selectedEntryCycle','precedingDisplays','parentControlMemorySha256','parentEntrySha256')):
        raise ValueError('Active turn borrowed another entry')
    if data['points'][:320]!=early['points'] or data['interrupts'][:64]!=early['interrupts']:
        raise ValueError('Changed accepted first 32 original turn updates')
    from air_following_resource_reference import analyze
    return analyze(data)

def capture(args):
    controls(args);entry=read(args.parent_out/'entry.json');early=read(args.parent_out/'gameplay.json')
    analyze_play(early,entry)
    # The accepted folder's button file already contains its first 32 updates.
    # Reuse the identical entry record, with only its complete entry input prefix.
    count=entry['groups'][-1]['precedingDisplays']+2
    buttons=(args.parent_out/'buttons.txt').read_text().splitlines(keepends=True)
    if len(buttons)!=count+32:raise ValueError('Incomplete accepted turn entry/button prefix')
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'entry.json').write_bytes((args.parent_out/'entry.json').read_bytes())
    (args.out/'buttons.txt').write_text(''.join(buttons[:count]))
    from air_following_gameplay_reference import capture as observe
    observe(argparse.Namespace(**dict(vars(args),selected_entry=args.out/'entry.json',selected_parent_control=args.accepted_control,updates=320,resource_transfers=True,next_retry=False,after_retry=1,outro=False,terminal=False)))
    preserve_early(read(args.out/'gameplay.json'),early,entry)

def native_prefix(base,parent):
    prefix='.fifth.selected.turn.title-gameplay';complete=0
    files=[p for p in parent.parent.glob(parent.name+'*') if p.name.endswith('.csv')]
    required={parent.name,parent.name+'.next-gameplay.csv',parent.name+'.next-incoming.summary.csv',parent.name+'.third.next-text.summary.csv'}
    if not required.issubset(p.name for p in files):raise ValueError('Incomplete accepted turn native parent')
    for old in files:
        suffix=old.name[len(parent.name):];new=base.parent/(base.name+suffix)
        if suffix.startswith(prefix):continue
        if not new.exists() or old.read_bytes()!=new.read_bytes():raise ValueError('Changed complete accepted turn ancestor: '+suffix)
        complete+=1
    for suffix in ('.csv','.entities.csv','.services.csv','.interrupts.csv','.sprites.csv'):
        old=Path(str(parent)+prefix+suffix).read_bytes();new=Path(str(base)+prefix+suffix).read_bytes()
        if not old or not new.startswith(old):raise ValueError('Changed accepted first 32 native turn updates: '+suffix)
    if complete<580:raise ValueError('Incomplete accepted turn native graph')
    return complete

def compare(args,_parent_qualified=False):
    parents=[c for c in read(args.parent_manifest) if Path(c['capture'])==args.accepted_control and Path(c['out'])==args.parent_out and Path(c['native_base'])==args.parent_base]
    if len(parents)!=1:raise ValueError('Active turn lacks its explicit accepted 32-update qualification')
    parent_args=argparse.Namespace(**{k:Path(v) for k,v in parents[0].items() if k!='rom'})
    if not _parent_qualified:
        from selected_turn_reference import compare as qualify
        parent_args.parent_manifest=args.instruction_manifest;parent_args.outcome_manifest=args.outcome_manifest;parent_args.terminal_manifest=args.terminal_manifest
        with contextlib.redirect_stdout(io.StringIO()):qualify(parent_args)
    accepted,manifest=controls(args);entry=read(args.parent_out/'entry.json');early=read(args.parent_out/'gameplay.json');data=read(args.out/'gameplay.json')
    for record in (entry,early):
        require_capture_reference(accepted,record)
        if any(record[k]!=accepted[k] for k in ('romSha256','inputCase','controlMemorySha256')):raise ValueError('Changed accepted quiet turn control/recording')
    require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','inputCase','controlMemorySha256')) or data.get('parentControlMemorySha256')!=accepted['controlMemorySha256'] or entry.get('captureEventsSha256')!=event_sha(read(args.accepted_control/'events.json')) or data.get('parentEntrySha256')!=sha((args.parent_out/'entry.json').read_bytes()) or (args.out/'entry.json').read_bytes()!=(args.parent_out/'entry.json').read_bytes():raise ValueError('Detached active turn observation/entry')
    extent=preserve_early(data,early,entry);services=extent['services']
    if (args.out/'buttons.txt').read_text()!=(args.parent_out/'buttons.txt').read_text()+''.join(str(r['held'])+'\n' for r in services[32:]):raise ValueError('Changed active turn raw input prefix')
    retained=native_prefix(args.native_base,args.parent_base)
    from air_startup_reference import analyze as startup
    from air_following_resource_reference import compare_resources
    from air_clock_compare import compare_sprites
    origin=read(parent_args.startup/'startup.json');require_capture_reference(manifest,origin)
    if origin['romSha256']!=manifest['romSha256']:raise ValueError('Changed active turn startup ROM')
    epoch=startup(origin)['epoch'];stem=str(args.native_base)+'.fifth.selected.turn.title-gameplay'
    entry_summary=rows(Path(str(args.native_base)+'.fifth.selected.turn.title-game-entry.summary.csv'))
    points,actors,displays,interrupts,summary=[rows(Path(stem+s+'.csv')) for s in ('','.entities','.services','.interrupts','.summary')]
    projected=dict(data,precedingDisplays=int(entry_summary[0]['displays']))
    diff,occupied,extent=compare_resources(projected,points,actors,displays,interrupts,summary,entry_summary,epoch)
    sprites=rows(Path(stem+'.sprites.csv'));normalized=[]
    if len(sprites)!=40*len(services):raise ValueError('Incomplete active turn sprite publications')
    for n,r in enumerate(sprites):
        row={k:int(v) for k,v in r.items()}
        if row['service']!=projected['precedingDisplays']+n//40 or row['slot']!=n%40:raise ValueError('Reordered active turn sprites')
        normalized.append(dict(row,service=n//40))
    diff+=compare_sprites(services,normalized,expected_services=len(services))
    wanted=dict(player=1 if data['players'] else 0,lives0=4,lives1=5 if data['players'] else 0,stage=1,difficulty=0,result=0)
    if any(int(summary[0][k])!=v for k,v in wanted.items()):diff.append(dict(category='campaign',expected=wanted,native=summary[0]))
    report=dict(players=data['players'],inputCase=data['inputCase'],updates=320,boundaries=len(points),actorSlots=len(actors),occupiedActors=occupied,services=len(displays),vectors=len(interrupts),spriteSlots=len(sprites),preservedCompleteNativeFiles=retained,**{k:v for k,v in extent.items() if k!='services'},differences=len(diff),firstDifference=diff[:1],productionSchedulerAccepted=False,evidenceLimit='Actual subsequent-player Air/easy first 320 updates, active resource requests/uploads/completions, actor/scalar timing and sprite positions/flags. Preserves accepted entry and first 32 original/native updates. Excludes later/deferred/interrupted/pause/terminal work, sprite tile and map bytes, frames/PCM and production scheduling.')
    write_json(Path(str(args.native_base)+'.selected-turn-active.comparison.json'),report);print(report,flush=True)
    if diff:raise ValueError('Actual subsequent-player active Air differs from original')

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    for mode in ('prepare','capture','compare'):
        p=sub.add_parser(mode)
        if mode!='compare':p.add_argument('rom',type=Path)
        for key in ('capture','out')+(('accepted-control','parent-out') if mode!='prepare' else ())+(('native-base','parent-base','parent-manifest','instruction-manifest','outcome-manifest','terminal-manifest') if mode=='compare' else ()):
            p.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();globals()[args.mode](args)
if __name__=='__main__':main()
