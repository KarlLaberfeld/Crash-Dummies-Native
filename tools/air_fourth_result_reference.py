"""Attach fourth Air failure and one-life result to its accepted continuation."""
import argparse,contextlib,io,json
from pathlib import Path
from types import SimpleNamespace
from air_reference import write_json
from air_next_retry_reference import preserved_prefix
from air_third_result_reference import original_prefix
from air_third_gameplay_reference import timer_rollovers
from air_fourth_gameplay_reference import compare as accepted_compare,native_prefix


def fourth_result_scope(records):
    if any(r.get('afterRetry')!=2 for r in records.values()):raise ValueError('Mixed fourth-attempt result generations')
    game=records['gameplay'];prefix=records['result-prefix'];transition=records['result-transition']
    if game.get('terminalWait') is not True or game['points'][-1].get('result')!=33:raise ValueError('Requires complete fourth Air failure')
    if transition.get('failureHold') is not True or transition['points'][-1].get('name')!='failureResultReturned':raise ValueError('Incomplete fourth failure hold')
    if prefix['points'][0]['state'].get('lives')!=2 or transition['points'][-1].get('lives')!=1:raise ValueError('Fourth failure must retain exactly one life')


def compare(args):
    def read(folder,name):return json.loads((folder/name).read_text(encoding='utf-8'))
    parent=read(args.accepted_capture,'capture-summary.json');child=read(args.capture,'capture-summary.json')
    preserved_prefix(parent,child,read(args.accepted_capture,'events.json'),read(args.capture,'events.json'),[['tick',1000,True]])
    if Path(child['parentCapture']).resolve()!=args.accepted_capture.resolve():raise ValueError('Wrong accepted fourth-attempt parent')
    for name in ('setup.state','inputs.txt'):
        if (args.accepted_capture/name).read_bytes()!=(args.capture/name).read_bytes():raise ValueError('Changed original setup/input file')
    records={part:read(args.out,part+'.json') for part in ('gameplay','outro','result-prefix','result-transition','map')}
    fourth_result_scope(records);prior=read(args.accepted_out,'gameplay.json')
    if prior.get('afterRetry')!=2:raise ValueError('Wrong accepted fourth-gameplay prefix')
    original_prefix(prior,records['gameplay']);timer=timer_rollovers(records['gameplay'])
    accepted=dict(native_base=args.accepted_base,capture=args.accepted_capture,out=args.accepted_out,startup=args.accepted_startup)
    for key in ('first_base','start_capture','start_out','start_startup','parent_capture','parent_out','parent_startup','parent_result_out','instruction_base'):accepted[key]=getattr(args,key)
    with contextlib.redirect_stdout(io.StringIO()):accepted_compare(SimpleNamespace(**accepted))
    files=native_prefix(args.accepted_base,args.native_base)
    from air_following_resource_reference import compare as resources
    from air_following_outro_reference import compare as outgoing
    from air_following_result_reference import compare as result
    from air_map_reference import compare as rows
    base=str(args.native_base)+'.fourth';common=dict(capture=args.capture,out=args.out,startup=args.startup)
    with contextlib.redirect_stdout(io.StringIO()):
        resources(SimpleNamespace(native_csv=Path(base+'.next-gameplay.csv'),entry_summary=Path(base+'.next-entry.summary.csv'),**common))
        outgoing(SimpleNamespace(native_csv=Path(base+'.next-outro.csv'),entry_summary=Path(base+'.next-gameplay.summary.csv'),**common))
        result(SimpleNamespace(native_base=Path(base),native_scope='next',**common))
        rows(SimpleNamespace(native_csv=Path(base+'.next-gameplay.map.csv'),**common))
    reports={key:read(Path(base).parent,Path(base).name+suffix) for key,suffix in (
        ('gameplay','.next-gameplay.resource-comparison.json'),('outgoing','.next-outro.comparison.json'),('result','.next-result.comparison.json'),('rows','.next-gameplay.map.comparison.json'))}
    report=dict(**timer,**reports,nativePrefixFiles=len(files),acceptedThousandUpdatePrefixRetained=True,
        differences=sum(r['differences'] for r in reports.values()),productionSchedulerAccepted=False,
        evidenceLimit='One fixed easy Air fourth-attempt history through terminal gameplay, outgoing fade and complete failed result retaining one life. Includes earlier accepted prefixes. Following one-life campaign/UI, final attempt, other campaigns, full images/PCM and production scheduling remain unqualified.')
    write_json(Path(str(args.native_base)+'.fourth-result.comparison.json'),report);print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('native_base',type=Path)
    for key in ('capture','out','startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base'):parser.add_argument('--'+key,type=Path,required=True)
    compare(parser.parse_args())
