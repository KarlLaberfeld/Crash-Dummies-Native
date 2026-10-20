"""Initial selected Air gameplay attached to the accepted first game-entry displays."""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read
from air_reference import write_json
from air_following_gameplay_reference import capture as observe
from air_following_quiet_reference import analyze as quiet_analyze,compare_quiet
from reference_backend import require_capture_reference

def analyze(data,parent):
    end=parent['groups'][-1]['points'][-1];first=data['points'][0]
    if data.get('selectedEntryCycle')!=end['cycles'] or data.get('updates')!=32 or any(data[k]!=parent[k] for k in ('romSha256','controlMemorySha256','inputCase','parentInputCase','players')) or first['cycles']!=end['cycles'] or any(first[k]!=end[v] for k,v in [('tick','tick'),('random','randomState'),('cameraX','cameraX'),('cameraY','cameraY'),('mapScratch','mapScratch'),('hudCursor','hudCursor'),('fadeRemaining','fadeRemaining'),('held','inputHeld'),('pressed','inputPressed')]) or data.get('entryPauseConsumed'):raise ValueError('Detached selected gameplay entry')
    return quiet_analyze(data)

def capture(args):
    parent=read(args.parent_out/'entry.json');manifest=read(args.capture/'capture-summary.json');require_capture_reference(manifest,parent)
    observe(argparse.Namespace(**dict(vars(args),selected_entry=args.parent_out/'entry.json',updates=32,resource_transfers=False,busy_scenes=False,partial_rows=False,next_retry=False,after_retry=1,outro=False,terminal=False)))
    data=read(args.out/'gameplay.json');analyze(data,parent)

def compare(args,_parent_qualified=False):
    if not _parent_qualified:
        from selected_game_entry_reference import compare as qualify
        with contextlib.redirect_stdout(io.StringIO()):qualify(argparse.Namespace(**{k:v for k,v in dict(vars(args),native_base=args.game_entry_base).items() if k not in ('game_entry_base','gameplay_out')}))
    from air_fourth_entry_reference import preserved_native_prefix
    from air_startup_reference import analyze as startup_epoch
    parent=read(args.game_entry_out/'entry.json');data=read(args.gameplay_out/'gameplay.json');manifest=read(args.text_control/'capture-summary.json');require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase')):raise ValueError('Mixed selected gameplay control/recording')
    services=analyze(data,parent)
    if (args.gameplay_out/'buttons.txt').read_text()!=(args.game_entry_out/'buttons.txt').read_text()+''.join(str(r['held'])+'\n' for r in services):raise ValueError('Detached selected gameplay raw input prefix')
    retained=preserved_native_prefix(args.native_base,args.game_entry_base);epoch=startup_epoch(read(args.startup/'startup.json'))['epoch'];stem=str(args.native_base)+'.fifth.selected.title-gameplay'
    def rows(stem,suffix):
        with Path(stem+suffix).open(newline='') as f:return list(csv.DictReader(f))
    entry=rows(str(args.game_entry_base)+'.fifth.selected.title-game-entry','.summary.csv');projected=dict(data,precedingDisplays=int(entry[0]['displays']))
    points,entities,displays,irqs,summary=[rows(stem,suffix) for suffix in ('.csv','.entities.csv','.services.csv','.interrupts.csv','.summary.csv')]
    differences,occupied=compare_quiet(projected,points,entities,displays,irqs,summary,entry,epoch)
    from air_clock_compare import compare_sprites
    sprites=rows(stem,'.sprites.csv');normalized=[]
    if len(sprites)!=40*len(services):raise ValueError('Incomplete selected gameplay sprite slots')
    for n,row in enumerate(sprites):
        value={k:int(v) for k,v in row.items()}
        if value['service']!=projected['precedingDisplays']+n//40 or value['slot']!=n%40:raise ValueError('Reordered selected gameplay sprite publication')
        normalized.append(dict(value,service=n//40))
    differences+=compare_sprites(services,normalized,expected_services=len(services))
    report=dict(parentInputCase=data['parentInputCase'],inputCase=data['inputCase'],players=data['players'],comparedUpdates=32,comparedBoundaries=len(points),comparedActorSlots=len(entities),comparedOccupiedActors=occupied,comparedServices=len(displays),comparedVectors=len(irqs),comparedSpriteSlots=len(sprites),preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='First 32 initial Air/easy gameplay updates after selected one/two-player Start. Native retained animation/timer state, actor/scalar work, actual display/input/music costs and published sprite presence/positions/flags are compared. Excludes sprite tile bytes, later resource requests/interruptions, map bytes, rendered frames/PCM and production scheduling.')
    write_json(Path(str(args.native_base)+'.selected-gameplay.comparison.json'),report);print(report)
    if differences:raise ValueError('Selected initial gameplay differs from the original')

def compare_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid selected gameplay batch')
    parents=[]
    for case in cases:
        parent=argparse.Namespace(**{k:v for k,v in vars(case).items() if k not in ('game_entry_base','gameplay_out')});parent.native_base=case.game_entry_base;parents.append(parent)
    from selected_game_entry_reference import compare_many as qualify
    with contextlib.redirect_stdout(io.StringIO()):qualify(parents)
    for case in cases:compare(case,_parent_qualified=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('capture');p.add_argument('rom',type=Path)
    for key in ('capture','parent-out','out'):p.add_argument('--'+key,type=Path,required=True)
    p=sub.add_parser('compare-batch');p.add_argument('manifest',type=Path);args=parser.parse_args()
    if args.mode=='capture':capture(args)
    else:compare_many([argparse.Namespace(**{k:Path(v) for k,v in c.items()}) for c in read(args.manifest)])
if __name__=='__main__':main()
