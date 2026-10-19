"""Attach final Air entry to the accepted one-life instruction and fourth game."""
import argparse,contextlib,csv,io,json
from pathlib import Path
from types import SimpleNamespace
from air_reference import write_json
from reference_backend import require_capture_reference
from air_next_retry_reference import extension
from air_fourth_entry_reference import generation,current_game_inheritance,native_animation_blocks,preserved_native_prefix


def compare(args):
    def read(folder,name):return json.loads((folder/name).read_text(encoding='utf-8'))
    parent=read(args.parent_capture,'capture-summary.json');child=read(args.capture,'capture-summary.json')
    extension(parent,child,read(args.parent_capture,'events.json'),read(args.capture,'events.json'))
    if Path(child['parentCapture']).resolve()!=args.parent_capture.resolve():raise ValueError('Wrong explicit fourth-result parent')
    for name in ('setup.state','inputs.txt'):
        if (args.capture/name).read_bytes()!=(args.parent_capture/name).read_bytes():raise ValueError('Changed parent setup/input file')
    records={part:read(args.out,part+'.json') for part in ('exit','prefix','stage','entry','gameplay')}
    text=read(args.parent_out,'text.json');handoff=read(args.parent_out,'handoff.json');fourth=read(args.parent_result_out,'gameplay.json')
    startup=read(args.startup,'startup.json');parent_startup=read(args.parent_startup,'startup.json')
    for manifest,observations in ((child,[startup,*records.values()]),(parent,[text,handoff,fourth,parent_startup])):
        for record in observations:
            require_capture_reference(manifest,record)
            if any(record[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed original recording')
    from air_startup_reference import analyze as startup_epoch
    if startup_epoch(startup)['epoch']!=startup_epoch(parent_startup)['epoch']:raise ValueError('Changed initial LCD epoch')
    generation(text,handoff,records,3,1);current_game_inheritance(fourth,records['gameplay'],3)
    files=preserved_native_prefix(args.native_base,args.accepted_base)
    from air_next_instruction_reference import compare as instruction_compare
    from air_instruction_exit_reference import compare as exit_compare
    from air_following_setup_reference import compare as prefix_compare
    from air_following_stage_reference import compare as stage_compare
    from air_following_entry_reference import compare as entry_compare
    from air_following_gameplay_reference import compare as play_compare
    from air_side_push_reference import compare as side_push_compare
    base=str(args.native_base)+'.fifth'
    with Path(base+'.next-gameplay.entities.csv').open(newline='',encoding='utf-8-sig') as stream:
        native_animation_blocks(records['gameplay'],list(csv.DictReader(stream)))
    with contextlib.redirect_stdout(io.StringIO()):
        instruction_compare(SimpleNamespace(native_base=args.native_base,capture=args.parent_capture,out=args.parent_out,startup=args.parent_startup,result_out=args.parent_result_out,after_retry=3))
        for part,fn,prior in [('exit',exit_compare,None),('prefix',prefix_compare,'exit'),('stage',stage_compare,'prefix'),('entry',entry_compare,'stage'),('gameplay',play_compare,'entry')]:
            values=dict(native_csv=Path(base+'.next-'+part+'.csv'),capture=args.capture,out=args.out,startup=args.startup)
            if prior:values[prior+'_summary']=Path(base+'.next-'+prior+'.summary.csv')
            fn(SimpleNamespace(**values))
        side_push_compare(SimpleNamespace(native_csv=Path(base+'.next-gameplay.side-push.csv'),capture=args.capture,out=args.out,startup=args.startup))
    reports=[read(Path(base).parent,Path(base).name+'.next-'+part+'.comparison.json') for part in records]
    totals={key:sum(r.get(key,0) for r in reports) for key in ('comparedBoundaries','comparedServices','comparedInterrupts','comparedPolls','comparedWrites','comparedActorSlots')}
    scratch=read(args.out,'side-push.json')
    report=dict(**totals,differences=0,afterRetry=3,lives=1,inheritedSecondTicks=records['gameplay']['points'][0]['secondTicks'],inheritedSidePush=scratch['points'][0]['lastForce'],inheritedDelayPeriodSlots=16,preservedNativeFiles=files,productionSchedulerAccepted=False,
        evidenceLimit='One-life instruction exit, fifth/final Air entry and first update only, attached to the actual fourth game/result. Vacant done flags retain the documented initial mismatch. Subsequent gameplay, final-life consumption/eliminated-player paths, images/PCM and production scheduling remain unqualified.')
    write_json(Path(base+'.comparison.json'),report);print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('native_base',type=Path)
    for key in ('capture','out','startup','parent-capture','parent-out','parent-startup','parent-result-out','accepted-base'):parser.add_argument('--'+key,type=Path,required=True)
    compare(parser.parse_args())
