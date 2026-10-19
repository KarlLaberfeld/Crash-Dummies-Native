"""Attach fourth Air entry to the accepted two-life instruction and third game.

Observations are comparison-only. Native execution receives decoded assets and
raw button samples; earlier native CSVs must remain byte-identical to the
accepted parent replay. Parent and child retain their separate control hashes.
"""
import argparse,contextlib,csv,io,json
from pathlib import Path
from types import SimpleNamespace
from air_reference import write_json
from reference_backend import require_capture_reference
from air_next_retry_reference import extension,attachments


def generation(text,handoff,records):
    if any(r.get('afterRetry')!=2 for r in (text,handoff,*records.values())):
        raise ValueError('Fourth entry requires the completed two-life instruction generation')
    player=handoff['points'][-1]['player']
    if handoff['points'][-1]['lives'+str(player)]!=2:
        raise ValueError('Fourth entry requires two remaining lives')
    attachments(text,handoff,records)


def current_game_inheritance(preceding,play):
    if preceding.get('nextRetry') is not True or preceding.get('terminalWait') is not True or preceding.get('afterRetry',1)!=1:
        raise ValueError('Missing completed third game')
    if play.get('afterRetry')!=2:raise ValueError('Missing fourth game selection')
    last=preceding['points'][-1];first=play['points'][0]
    if last.get('name')!='terminalEnd' or last.get('result')!=33:
        raise ValueError('Unowned preceding failed game endpoint')
    if first['secondTicks']!=last['secondTicks']:
        raise ValueError('Fourth entry lost the current partial second')
    if len(last['entities'])!=16 or len(first['entities'])!=16:
        raise ValueError('Missing inherited animation blocks')
    for slot,(old,new) in enumerate(zip(last['entities'],first['entities'])):
        fields=('delay','period')+(('state',) if slot>=2 else ())
        if any(old[k]!=new[k] for k in fields):raise ValueError('Fourth entry lost current animation state')


def preserved_native_prefix(base,accepted):
    files=sorted(p for p in accepted.parent.glob(accepted.name+'*') if p.name.endswith('.csv'))
    required={accepted.name,accepted.name+'.next-gameplay.csv',accepted.name+'.next-incoming.summary.csv',accepted.name+'.third.next-text.summary.csv'}
    if not required.issubset(p.name for p in files):raise ValueError('Incomplete accepted native parent')
    for source in files:
        target=Path(str(base)+source.name[len(accepted.name):])
        if not target.is_file() or source.read_bytes()!=target.read_bytes():
            raise ValueError('Changed accepted native prefix: '+source.name)
    return len(files)


def native_animation_blocks(play,rows):
    # The ordinary first-update comparator omits unused vacant actor payloads.
    # Check their surviving delay/period separately. Never-allocated vacant
    # done flags still differ at initial construction (native true, source
    # false); no parity claim for those flags is made here.
    first=play['points'][0]['entities'];rows=rows[:16]
    if len(first)!=16 or len(rows)!=16:raise ValueError('Incomplete native inherited animation blocks')
    for slot,(source,row) in enumerate(zip(first,rows)):
        if row['boundary']!='begin' or int(row['slot'])!=slot:raise ValueError('Reordered native inherited animation blocks')
        expected=dict(delay=source['delay'],period=source['period'])
        if source['frame']!=255:expected.update(done=int(bool(source['state']&128)),waiting=int(bool(source['state']&64)))
        if any(int(row[k])!=v for k,v in expected.items()):raise ValueError('Native inherited animation block differs')


def compare(args):
    def read(folder,name):return json.loads((folder/name).read_text(encoding='utf-8'))
    parent=read(args.parent_capture,'capture-summary.json');child=read(args.capture,'capture-summary.json')
    extension(parent,child,read(args.parent_capture,'events.json'),read(args.capture,'events.json'))
    if Path(child['parentCapture']).resolve()!=args.parent_capture.resolve():raise ValueError('Wrong explicit parent control')
    for name in ('setup.state','inputs.txt'):
        if (args.capture/name).read_bytes()!=(args.parent_capture/name).read_bytes():raise ValueError('Changed parent setup/input file')
    records={part:read(args.out,part+'.json') for part in ('exit','prefix','stage','entry','gameplay')}
    text=read(args.parent_out,'text.json');handoff=read(args.parent_out,'handoff.json');third=read(args.parent_result_out,'gameplay.json')
    startup=read(args.startup,'startup.json');parent_startup=read(args.parent_startup,'startup.json')
    for manifest,observations in ((child,[startup,*records.values()]),(parent,[text,handoff,third,parent_startup])):
        for record in observations:
            require_capture_reference(manifest,record)
            if any(record[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed original recording')
    from air_startup_reference import analyze as startup_epoch
    if startup_epoch(startup)['epoch']!=startup_epoch(parent_startup)['epoch']:raise ValueError('Changed initial LCD epoch')
    generation(text,handoff,records);current_game_inheritance(third,records['gameplay'])
    count=preserved_native_prefix(args.native_base,args.accepted_base)
    from air_next_instruction_reference import compare as instruction_compare
    from air_instruction_exit_reference import compare as exit_compare
    from air_following_setup_reference import compare as prefix_compare
    from air_following_stage_reference import compare as stage_compare
    from air_following_entry_reference import compare as entry_compare
    from air_following_gameplay_reference import compare as play_compare
    base=str(args.native_base)+'.fourth'
    with Path(base+'.next-gameplay.entities.csv').open(newline='',encoding='utf-8-sig') as stream:
        native_animation_blocks(records['gameplay'],list(csv.DictReader(stream)))
    with contextlib.redirect_stdout(io.StringIO()):
        instruction_compare(SimpleNamespace(native_base=args.native_base,capture=args.parent_capture,out=args.parent_out,startup=args.parent_startup,result_out=args.parent_result_out,after_retry=2))
        for part,fn,prior in [('exit',exit_compare,None),('prefix',prefix_compare,'exit'),('stage',stage_compare,'prefix'),('entry',entry_compare,'stage'),('gameplay',play_compare,'entry')]:
            values=dict(native_csv=Path(base+'.next-'+part+'.csv'),capture=args.capture,out=args.out,startup=args.startup)
            if prior:values[prior+'_summary']=Path(base+'.next-'+prior+'.summary.csv')
            fn(SimpleNamespace(**values))
    reports=[read(Path(base).parent,Path(base).name+'.next-'+part+'.comparison.json') for part in records]
    totals={key:sum(r.get(key,0) for r in reports) for key in ('comparedBoundaries','comparedServices','comparedInterrupts','comparedPolls','comparedWrites','comparedActorSlots')}
    report=dict(**totals,differences=0,afterRetry=2,lives=2,inheritedSecondTicks=records['gameplay']['points'][0]['secondTicks'],inheritedDelayPeriodSlots=16,preservedNativeFiles=count,productionSchedulerAccepted=False,
        evidenceLimit='Two-life fresh-Start instruction exit, LCD-off setup, fourth Air entry and first update only. Earlier native CSVs are byte-identical to the accepted parent. Never-allocated vacant done flags differ (native true/source false) and are excluded; occupied actor flags and all sixteen delay/period blocks are checked. Excludes subsequent gameplay, full map/sprite bytes, images/PCM, other campaigns and production scheduling.')
    write_json(Path(base+'.comparison.json'),report);print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('native_base',type=Path)
    for key in ('capture','out','startup','parent-capture','parent-out','parent-startup','parent-result-out','accepted-base'):parser.add_argument('--'+key,type=Path,required=True)
    compare(parser.parse_args())
