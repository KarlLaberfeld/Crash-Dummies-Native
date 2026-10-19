"""Attach complete third-attempt failure to the accepted 1,000-update control."""
import argparse,contextlib,io,json
from pathlib import Path
from types import SimpleNamespace
from air_reference import write_json
from air_next_retry_reference import preserved_prefix
from air_third_gameplay_reference import compare as accepted_compare,native_prefix,timer_rollovers


def original_prefix(earlier,later):
    if not earlier.get('nextRetry') or not later.get('nextRetry') or earlier.get('terminalWait') or later.get('terminalWait') is not True or not 1<earlier.get('updates',0)<later.get('updates',0):
        raise ValueError('Wrong continuing/terminal third-attempt scopes')
    if earlier['points']!=later['points'][:len(earlier['points'])] or earlier['interrupts']!=later['interrupts'][:len(earlier['interrupts'])] or earlier['precedingDisplays']!=later['precedingDisplays']:
        raise ValueError('Changed accepted original gameplay prefix')


def compare(args):
    def read(folder,name):return json.loads((folder/name).read_text(encoding='utf-8'))
    parent=read(args.accepted_capture,'capture-summary.json');child=read(args.capture,'capture-summary.json')
    preserved_prefix(parent,child,read(args.accepted_capture,'events.json'),read(args.capture,'events.json'),[['tick',1000,True]])
    if Path(child['parentCapture']).resolve()!=args.accepted_capture.resolve():raise ValueError('Wrong accepted third-attempt parent')
    for name in ('setup.state','inputs.txt'):
        if (args.accepted_capture/name).read_bytes()!=(args.capture/name).read_bytes():raise ValueError('Changed original setup/input file')
    gameplay=read(args.out,'gameplay.json');prior=read(args.accepted_out,'gameplay.json')
    original_prefix(prior,gameplay);timer=timer_rollovers(gameplay)
    transition=read(args.out,'result-transition.json')
    if transition.get('failureHold') is not True or transition['points'][-1]['name']!='failureResultReturned':raise ValueError('Incomplete third-attempt result hold')
    accepted=dict(native_base=args.accepted_base,capture=args.accepted_capture,out=args.accepted_out,startup=args.accepted_startup)
    for key in ('first_base','start_capture','start_out','start_startup','parent_capture','parent_out','parent_startup'):accepted[key]=getattr(args,key)
    with contextlib.redirect_stdout(io.StringIO()):accepted_compare(SimpleNamespace(**accepted))
    files=native_prefix(args.accepted_base,args.native_base)
    from air_following_resource_reference import compare as resources
    from air_following_outro_reference import compare as outgoing
    from air_following_result_reference import compare as result
    from air_map_reference import compare as rows
    base=str(args.native_base);common=dict(capture=args.capture,out=args.out,startup=args.startup)
    with contextlib.redirect_stdout(io.StringIO()):
        resources(SimpleNamespace(native_csv=Path(base+'.next-gameplay.csv'),entry_summary=Path(base+'.next-entry.summary.csv'),**common))
        outgoing(SimpleNamespace(native_csv=Path(base+'.next-outro.csv'),entry_summary=Path(base+'.next-gameplay.summary.csv'),**common))
        result(SimpleNamespace(native_base=args.native_base,native_scope='next',**common))
        rows(SimpleNamespace(native_csv=Path(base+'.next-gameplay.map.csv'),**common))
    reports={key:read(args.native_base.parent,args.native_base.name+suffix) for key,suffix in (
        ('gameplay','.next-gameplay.resource-comparison.json'),('outgoing','.next-outro.comparison.json'),('result','.next-result.comparison.json'),('rows','.next-gameplay.map.comparison.json'))}
    report=dict(**timer,gameplay=reports['gameplay'],outgoing=reports['outgoing'],result=reports['result'],rows=reports['rows'],
        nativePrefixFiles=len(files),acceptedThousandUpdatePrefixRetained=True,
        sharedOffsetInterrupts=sum(0x20<=r['returnAddress']<=0x22 and r.get('callerAddress')==0x1ae0 for r in gameplay['interrupts']),
        partialRowDisplays=sum(r['kind']=='vblank' and r['ready']==0 and 0x1ead<=r['returnAddress']<0x1f16 for r in gameplay['interrupts']),
        differences=sum(r['differences'] for r in reports.values()),productionSchedulerAccepted=False,
        evidenceLimit='One fixed easy Air third-attempt history through terminal gameplay, outgoing fade, result setup/incoming and complete failure hold. Earlier prefixes overlap prior acceptance. Excludes following campaign handoff, other paths, full pixels/PCM and production scheduling.')
    write_json(Path(base+'.third-result.comparison.json'),report);print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('native_base',type=Path)
    for key in ('capture','out','startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup'):parser.add_argument('--'+key,type=Path,required=True)
    compare(parser.parse_args())
