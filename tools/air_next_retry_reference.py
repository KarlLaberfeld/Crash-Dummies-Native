"""Attach a second retry to its accepted parent text and compare native owners.

Parent observations retain their original hashes. A child must preserve the
complete parent event prefix, setup and input files, with two matching full-RAM
prefix/final controls. Only fresh Start followed by released frames is appended.
This verifier never supplies observations to native execution.
"""
import argparse,contextlib,io,json
from pathlib import Path
from types import SimpleNamespace
from air_reference import write_json
from reference_backend import require_capture_reference


def extension(parent,child,parent_events,child_events):
    if parent.get('controlDifferences')!=[] or child.get('controlDifferences')!=[]:
        raise ValueError('Changed original control')
    for key in ('romSha256','emulator','version','model','sourceRevision','referenceObserver'):
        if not parent.get(key) or parent[key]!=child.get(key):raise ValueError('Mixed parent/child provenance')
    if child.get('parentControlMemorySha256')!=parent['controlMemorySha256']:raise ValueError('Wrong parent digest')
    for key,digest in (('parentPrefixHashes',parent['controlMemorySha256']),('unhookedControlHashes',child['controlMemorySha256'])):
        values=child.get(key,[])
        if len(values)<2 or any(v!=digest for v in values):raise ValueError('Missing repeated unhooked controls')
    if not parent_events or child_events[:len(parent_events)]!=parent_events:raise ValueError('Changed parent input history')
    if child_events[len(parent_events):]!=[['press','start'],['tick',1,True],['release','start'],['tick',300,True]]:
        raise ValueError('Unowned second-retry input extension')


def attachments(parent_text,parent_handoff,records):
    exit,prefix,stage,entry,play=(records[k] for k in ('exit','prefix','stage','entry','gameplay'))
    if not parent_text.get('followingResult') or not parent_handoff.get('followingResult') or not exit.get('followingResult') or any(not r.get('nextRetry') for r in (prefix,stage,entry,play)):
        raise ValueError('Wrong retry scope')
    def join(left,right,fields):
        if any(left[k]!=right[k] for k in fields):raise ValueError('Detached original retry endpoints')
    join(parent_text['points'][-1],exit['points'][0],('cycles','tick','countdown','scroll','inputHeld','inputPressed'))
    join(exit['points'][-1],prefix['points'][0],('cycles','tick','countdown','musicEnabled'))
    join(prefix['points'][-1],stage['points'][0],('cycles','tick','countdown','player','lives','stage','difficulty','display','stat','lcdc','lyc','pendingRequests'))
    join(stage['points'][-1],entry['points'][0],('cycles','tick','countdown','display','stat','lcdc','lyc','pendingRequests','cameraX','cameraY','mapScratch','musicEnabled'))
    a,b=entry['points'][-1],play['points'][0]
    join(a,b,('cycles','tick','cameraX','cameraY','mapScratch','ready','lcdc','display'))
    if (a['randomState'],a['inputHeld'],a['inputPressed'])!=(b['random'],b['held'],b['pressed']):raise ValueError('Detached entry input/seed')
    hand=parent_handoff['points'][-1];player=hand['player'];lives=hand['lives'+str(player)]
    if not 1<=lives<=255 or parent_text['campaign']!=dict(player=player,stage=1,difficulty=0):raise ValueError('Unowned retry campaign')
    for data in (prefix,stage):
        if any((p['player'],p['lives'],p['stage'],p['difficulty'])!=(player,lives,1,0) for p in data['points']):raise ValueError('Retry lost campaign state')
    def displays(data):return sum(r['kind']=='vblank' for r in data['interrupts'])
    if exit['precedingDisplays']!=parent_text['precedingDisplays']+displays(parent_text) or entry['precedingDisplays']!=exit['precedingDisplays']+displays(exit) or play['precedingDisplays']!=entry['precedingDisplays']+displays(entry):
        raise ValueError('Retry restarted service numbering')


def compare(args):
    def read(folder,name):return json.loads((folder/name).read_text(encoding='utf-8'))
    parent=read(args.parent_capture,'capture-summary.json');child=read(args.capture,'capture-summary.json')
    extension(parent,child,read(args.parent_capture,'events.json'),read(args.capture,'events.json'))
    if Path(child['parentCapture']).resolve()!=args.parent_capture.resolve():raise ValueError('Wrong explicit parent control')
    for name in ('setup.state','inputs.txt'):
        if (args.capture/name).read_bytes()!=(args.parent_capture/name).read_bytes():raise ValueError('Changed parent setup/input file')
    records={k:read(args.out,k+'.json') for k in ('exit','prefix','stage','entry','gameplay')}
    startup=read(args.startup,'startup.json');parent_startup=read(args.parent_startup,'startup.json')
    for manifest,observations in ((child,[startup,*records.values()]),(parent,[parent_startup])):
        for record in observations:
            require_capture_reference(manifest,record)
            if any(record[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed original recording')
    from air_startup_reference import analyze as startup_epoch
    if startup_epoch(startup)['epoch']!=startup_epoch(parent_startup)['epoch']:raise ValueError('Changed initial LCD epoch')
    attachments(read(args.parent_out,'text.json'),read(args.parent_out,'handoff.json'),records)
    from air_following_resource_reference import compare as gameplay_parent
    from air_following_outro_reference import compare as outro_parent
    from air_following_result_reference import compare as result_parent
    from air_next_instruction_reference import compare as instruction_parent
    from air_instruction_exit_reference import compare as exit_compare
    from air_following_setup_reference import compare as prefix_compare
    from air_following_stage_reference import compare as stage_compare
    from air_following_entry_reference import compare as entry_compare
    from air_following_gameplay_reference import compare as play_compare
    base=str(args.native_base)
    common=dict(capture=args.parent_capture,out=args.parent_out,startup=args.parent_startup)
    # Reuse each strict source-work analyzer; do not weaken parent provenance to
    # pretend its final RAM hash belongs to the extended child recording.
    tasks=[(gameplay_parent,dict(native_csv=Path(base+'.following-gameplay.csv'),entry_summary=Path(base+'.following-entry.summary.csv'),**common)),
        (outro_parent,dict(native_csv=Path(base+'.following-outro.csv'),entry_summary=Path(base+'.following-gameplay.summary.csv'),**common)),
        (result_parent,dict(native_base=args.native_base,**common)),(instruction_parent,dict(native_base=args.native_base,**common))]
    common=dict(capture=args.capture,out=args.out,startup=args.startup)
    for part,fn,prior in [('exit',exit_compare,None),('prefix',prefix_compare,'exit'),('stage',stage_compare,'prefix'),('entry',entry_compare,'stage'),('gameplay',play_compare,'entry')]:
        values=dict(native_csv=Path(base+'.next-'+part+'.csv'),**common)
        if prior:values[prior+'_summary']=Path(base+'.next-'+prior+'.summary.csv')
        tasks.append((fn,values))
    with contextlib.redirect_stdout(io.StringIO()):
        for fn,values in tasks:fn(SimpleNamespace(**values))
    reports=[read(Path(base).parent,Path(base).name+'.next-'+part+'.comparison.json') for part in ('exit','prefix','stage','entry','gameplay')]
    totals={key:sum(r.get(key,0) for r in reports) for key in ('comparedBoundaries','comparedServices','comparedInterrupts','comparedPolls','comparedWrites','comparedActorSlots')}
    report=dict(**totals,differences=0,parentPrefixAccepted=True,parentComparisons=4,childComparisons=5,productionSchedulerAccepted=False,
        evidenceLimit='One input-only easy Air second-retry history through first update/next input gate. Parent gameplay/result/text overlap previous acceptance. Excludes subsequent gameplay, other players/stunts, pixels/PCM and production scheduling.')
    write_json(Path(base+'.next-retry.comparison.json'),report);print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('native_base',type=Path)
    for key in ('capture','out','startup','parent-capture','parent-out','parent-startup'):parser.add_argument('--'+key,type=Path,required=True)
    compare(parser.parse_args())
