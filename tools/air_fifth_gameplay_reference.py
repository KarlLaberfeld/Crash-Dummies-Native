"""Attach complete final Air gameplay/outgoing fade to its accepted one-life entry.

Original recordings are comparison targets only, never native replay input.
This deliberately stops before last-life result accounting and game over.
"""
import argparse,contextlib,io,json
from pathlib import Path
from types import SimpleNamespace
from air_reference import write_json
from air_next_retry_reference import preserved_prefix
from air_third_gameplay_reference import first_update,timer_rollovers
from air_fourth_gameplay_reference import native_prefix
from air_fifth_entry_reference import compare as entry_compare
from reference_backend import require_capture_reference


def final_scope(first,records):
    if first.get('afterRetry')!=3 or any(r.get('afterRetry')!=3 for r in records.values()):raise ValueError('Mixed final-attempt generation')
    game=records['gameplay']
    if game.get('terminalWait') is not True or game['points'][-1].get('result')!=33:raise ValueError('Requires complete final Air failure')
    first_update(first,game)


def compare(args):
    def read(folder,name):return json.loads((folder/name).read_text(encoding='utf-8'))
    parent=read(args.start_capture,'capture-summary.json');child=read(args.capture,'capture-summary.json')
    preserved_prefix(parent,child,read(args.start_capture,'events.json'),read(args.capture,'events.json'),[['tick',1800,True]])
    if Path(child['parentCapture']).resolve()!=args.start_capture.resolve():raise ValueError('Wrong final-entry parent')
    for name in ('setup.state','inputs.txt'):
        if (args.start_capture/name).read_bytes()!=(args.capture/name).read_bytes():raise ValueError('Changed original setup/input file')
    records={part:read(args.out,part+'.json') for part in ('gameplay','outro','map','side-push')}
    startup=read(args.startup,'startup.json')
    for record in (startup,*records.values()):
        require_capture_reference(child,record)
        if any(record[k]!=child[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed final-game original records')
    first=read(args.start_out,'gameplay.json');final_scope(first,records);timer=timer_rollovers(records['gameplay'])
    with contextlib.redirect_stdout(io.StringIO()):
        entry_compare(SimpleNamespace(native_base=args.first_base,capture=args.start_capture,out=args.start_out,startup=args.start_startup,
            parent_capture=args.parent_capture,parent_out=args.parent_out,parent_startup=args.parent_startup,parent_result_out=args.parent_result_out,accepted_base=args.instruction_base))
    files=native_prefix(args.first_base,args.native_base,'fifth')
    from air_following_resource_reference import compare as resources
    from air_following_outro_reference import compare as outgoing
    from air_map_reference import compare as rows
    from air_side_push_reference import compare as scratch
    base=str(args.native_base)+'.fifth';common=dict(capture=args.capture,out=args.out,startup=args.startup)
    with contextlib.redirect_stdout(io.StringIO()):
        resources(SimpleNamespace(native_csv=Path(base+'.next-gameplay.csv'),entry_summary=Path(base+'.next-entry.summary.csv'),**common))
        outgoing(SimpleNamespace(native_csv=Path(base+'.next-outro.csv'),entry_summary=Path(base+'.next-gameplay.summary.csv'),**common))
        rows(SimpleNamespace(native_csv=Path(base+'.next-gameplay.map.csv'),**common))
        scratch(SimpleNamespace(native_csv=Path(base+'.next-gameplay.side-push.csv'),**common))
    reports={key:read(Path(base).parent,Path(base).name+suffix) for key,suffix in (
        ('gameplay','.next-gameplay.resource-comparison.json'),('outgoing','.next-outro.comparison.json'),('rows','.next-gameplay.map.comparison.json'),('scratch','.next-gameplay.side-push.comparison.json'))}
    report=dict(**timer,**reports,afterRetry=3,livesAtEntry=1,nativePrefixFiles=len(files),acceptedFirstUpdateRetained=True,
        differences=sum(r['differences'] for r in reports.values()),productionSchedulerAccepted=False,
        evidenceLimit='One fixed easy Air history through final-attempt failure and outgoing fade, including its accepted first update. Last-life result/eliminated-player/game-over paths, vacant done flags, other campaigns, complete images/PCM and production scheduling remain unqualified.')
    write_json(Path(str(args.native_base)+'.fifth-gameplay.comparison.json'),report);print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('native_base',type=Path)
    for key in ('capture','out','startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base'):parser.add_argument('--'+key,type=Path,required=True)
    compare(parser.parse_args())
