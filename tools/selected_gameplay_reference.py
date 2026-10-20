"""Initial selected Air gameplay attached to the accepted first game-entry displays."""
import argparse,contextlib,csv,io,shutil
from pathlib import Path
from air_title_start_reference import read,sha
from air_reference import write_json
from air_following_gameplay_reference import capture as observe,selected_extension
from air_following_quiet_reference import analyze as quiet_analyze,compare_quiet
from reference_backend import require_capture_reference

def prepare(args):
    from air_title_start_reference import replay,memory_sha
    from air_title_actions_reference import event_sha
    from reference_backend import reference_class,require_matching_backend
    parent=read(args.capture/'capture-summary.json');events=read(args.capture/'events.json');setup=sha((args.capture/'setup.state').read_bytes());tail=[['press','a'],['press','right'],['tick',300,True],['release','a'],['release','right'],['tick',4,True]]
    if parent['inputCase'] not in ('full-prompt','skip-held') or parent['controlDifferences'] or sha(args.rom.read_bytes())!=parent['romSha256']:raise ValueError('Changed selected gameplay parent/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(parent,metadata);prefixes=[];hashes=[]
    for _ in range(2):
        p=Reference(str(args.rom),window='null',sound_volume=0)
        try:
            with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
            replay(p,events);prefixes.append(memory_sha(p));replay(p,tail);hashes.append(memory_sha(p))
        finally:p.stop(save=False)
    data=dict(**metadata,inputCase=parent['inputCase'],gameplayUpdates=320,gameplayInput='a-right-held',romSha256=parent['romSha256'],controlMemorySha256=hashes[0],parentControlMemorySha256=parent['controlMemorySha256'],parentEventsSha256=event_sha(events),setupSha256=setup,controlDifferences=[],prefixControlHashes=prefixes,unhookedControlHashes=hashes,referenceOnly=True)
    selected_extension(parent,data,events,events+tail,setup);args.out.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.capture/'setup.state',args.out/'setup.state');write_json(args.out/'capture-summary.json',data);write_json(args.out/'events.json',events+tail)
    print('Two selected gameplay prefix/full controls match',flush=True)

def analyze(data,parent):
    end=parent['groups'][-1]['points'][-1];first=data['points'][0]
    if data.get('selectedEntryCycle')!=end['cycles'] or data.get('updates') not in (32,320) or data.get('parentControlMemorySha256',data['controlMemorySha256'])!=parent['controlMemorySha256'] or any(data[k]!=parent[k] for k in ('romSha256','inputCase','parentInputCase','players')) or first['cycles']!=end['cycles'] or any(first[k]!=end[v] for k,v in [('tick','tick'),('random','randomState'),('cameraX','cameraX'),('cameraY','cameraY'),('mapScratch','mapScratch'),('hudCursor','hudCursor'),('fadeRemaining','fadeRemaining'),('held','inputHeld'),('pressed','inputPressed')]) or data.get('entryPauseConsumed'):raise ValueError('Detached selected gameplay entry')
    if data['updates']==320:
        from air_following_resource_reference import analyze as resource_analyze
        return resource_analyze(data)['services']
    return quiet_analyze(data)

def capture(args):
    parent=read(args.parent_out/'entry.json');manifest=read(args.capture/'capture-summary.json');require_capture_reference(manifest,parent)
    updates=getattr(args,'updates',32)
    observe(argparse.Namespace(**dict(vars(args),selected_entry=args.parent_out/'entry.json',selected_parent_control=getattr(args,'accepted_control',None),updates=updates,resource_transfers=updates==320,busy_scenes=False,partial_rows=False,next_retry=False,after_retry=1,outro=False,terminal=False)))
    data=read(args.out/'gameplay.json');analyze(data,parent)

def compare(args,_parent_qualified=False):
    if not _parent_qualified:
        from selected_game_entry_reference import compare as qualify
        with contextlib.redirect_stdout(io.StringIO()):qualify(argparse.Namespace(**{k:v for k,v in dict(vars(args),native_base=args.game_entry_base).items() if k not in ('game_entry_base','gameplay_out','play_control','early_gameplay_out','early_gameplay_base')}))
    from air_fourth_entry_reference import preserved_native_prefix
    from air_startup_reference import analyze as startup_epoch
    parent=read(args.game_entry_out/'entry.json');data=read(args.gameplay_out/'gameplay.json');control=getattr(args,'play_control',args.text_control);manifest=read(control/'capture-summary.json');require_capture_reference(manifest,data)
    if data['updates']==320:
        selected_extension(read(args.text_control/'capture-summary.json'),manifest,read(args.text_control/'events.json'),read(control/'events.json'),sha((control/'setup.state').read_bytes()))
        early=read(args.early_gameplay_out/'gameplay.json')
        if early['updates']!=32 or data['points'][:320]!=early['points'] or data['interrupts'][:64]!=early['interrupts']:raise ValueError('Changed accepted first 32 original updates')
        early_args=argparse.Namespace(**{k:v for k,v in dict(vars(args),native_base=args.early_gameplay_base,gameplay_out=args.early_gameplay_out).items() if k not in ('play_control','early_gameplay_out','early_gameplay_base')})
        with contextlib.redirect_stdout(io.StringIO()):compare(early_args,_parent_qualified=True)
        for suffix in ('.csv','.entities.csv','.services.csv','.interrupts.csv','.sprites.csv'):
            prefix=Path(str(args.early_gameplay_base)+'.fifth.selected.title-gameplay'+suffix).read_bytes();changed=Path(str(args.native_base)+'.fifth.selected.title-gameplay'+suffix).read_bytes()
            if not prefix or not changed.startswith(prefix):raise ValueError('Changed accepted first 32 native '+suffix)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase')):raise ValueError('Mixed selected gameplay control/recording')
    services=analyze(data,parent)
    if (args.gameplay_out/'buttons.txt').read_text()!=(args.game_entry_out/'buttons.txt').read_text()+''.join(str(r['held'])+'\n' for r in services):raise ValueError('Detached selected gameplay raw input prefix')
    retained=preserved_native_prefix(args.native_base,args.game_entry_base);epoch=startup_epoch(read(args.startup/'startup.json'))['epoch'];stem=str(args.native_base)+'.fifth.selected.title-gameplay'
    def rows(stem,suffix):
        with Path(stem+suffix).open(newline='') as f:return list(csv.DictReader(f))
    entry=rows(str(args.game_entry_base)+'.fifth.selected.title-game-entry','.summary.csv');projected=dict(data,precedingDisplays=int(entry[0]['displays']))
    points,entities,displays,irqs,summary=[rows(stem,suffix) for suffix in ('.csv','.entities.csv','.services.csv','.interrupts.csv','.summary.csv')]
    extent={}
    if data['updates']==320:
        from air_following_resource_reference import compare_resources
        differences,occupied,extent=compare_resources(projected,points,entities,displays,irqs,summary,entry,epoch)
    else:differences,occupied=compare_quiet(projected,points,entities,displays,irqs,summary,entry,epoch)
    from air_clock_compare import compare_sprites
    sprites=rows(stem,'.sprites.csv');normalized=[]
    if len(sprites)!=40*len(services):raise ValueError('Incomplete selected gameplay sprite slots')
    for n,row in enumerate(sprites):
        value={k:int(v) for k,v in row.items()}
        if value['service']!=projected['precedingDisplays']+n//40 or value['slot']!=n%40:raise ValueError('Reordered selected gameplay sprite publication')
        normalized.append(dict(value,service=n//40))
    differences+=compare_sprites(services,normalized,expected_services=len(services))
    report=dict(parentInputCase=data['parentInputCase'],inputCase=data['inputCase'],players=data['players'],comparedUpdates=data['updates'],comparedBoundaries=len(points),comparedActorSlots=len(entities),comparedOccupiedActors=occupied,comparedServices=len(displays),comparedVectors=len(irqs),comparedSpriteSlots=len(sprites),**{k:v for k,v in extent.items() if k!='services'},preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Bounded initial Air/easy gameplay after selected Start. Retained animation/timer state, actor/scalar work, actual display/input/music costs and sprite presence/positions/flags are compared. The 320-update scope includes identified request/upload/completion logic and preserves the first 32 updates exactly. Excludes sprite tile bytes, later/interrupted body work, map bytes, rendered frames/PCM and production scheduling.')
    write_json(Path(str(args.native_base)+'.selected-gameplay.comparison.json'),report);print(report)
    if differences:raise ValueError('Selected initial gameplay differs from the original')

def compare_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid selected gameplay batch')
    parents=[]
    for case in cases:
        parent=argparse.Namespace(**{k:v for k,v in vars(case).items() if k not in ('game_entry_base','gameplay_out','play_control','early_gameplay_out','early_gameplay_base')});parent.native_base=case.game_entry_base;parents.append(parent)
    from selected_game_entry_reference import compare_many as qualify
    with contextlib.redirect_stdout(io.StringIO()):qualify(parents)
    for case in cases:compare(case,_parent_qualified=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare');p.add_argument('rom',type=Path)
    for key in ('capture','out'):p.add_argument('--'+key,type=Path,required=True)
    p=sub.add_parser('capture');p.add_argument('rom',type=Path)
    p.add_argument('--accepted-control',type=Path);p.add_argument('--updates',type=int,choices=(32,320),default=32)
    for key in ('capture','parent-out','out'):p.add_argument('--'+key,type=Path,required=True)
    p=sub.add_parser('compare-batch');p.add_argument('manifest',type=Path);args=parser.parse_args()
    if args.mode=='capture':capture(args)
    elif args.mode=='prepare':prepare(args)
    else:compare_many([argparse.Namespace(**{k:Path(v) for k,v in c.items()}) for c in read(args.manifest)])
if __name__=='__main__':main()
