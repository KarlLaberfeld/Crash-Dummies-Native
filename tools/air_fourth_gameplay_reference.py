"""Compare fourth Air continuation while preserving its accepted entry evidence."""
import argparse,contextlib,csv,io,json
from pathlib import Path
from types import SimpleNamespace
from air_reference import write_json
from air_next_retry_reference import preserved_prefix
from air_third_gameplay_reference import first_update,timer_rollovers
from air_fourth_entry_reference import compare as entry_compare
from reference_backend import require_capture_reference


def native_prefix(first,continued,attempt='fourth'):
    if attempt not in ('fourth','fifth'):raise ValueError('Unowned native continuation generation')
    instruction='third' if attempt=='fourth' else 'fifth'
    prefix='.'+attempt+'.next-gameplay'
    checked=[]
    for path in sorted(p for p in first.parent.glob(first.name+'*') if p.is_file() and p.name.endswith('.csv')):
        suffix=path.name[len(first.name):]
        if suffix==prefix+'.summary.csv':continue
        other=Path(str(continued)+suffix)
        if not other.is_file():raise ValueError('Missing continued native prefix: '+suffix)
        a=path.read_bytes();b=other.read_bytes()
        if suffix==prefix+'.map.csv':
            lines=a.splitlines(keepends=True)
            if not lines or not lines[-1].startswith(b'end,'):raise ValueError('Missing accepted row endpoint')
            a=b''.join(lines[:-1])
        if suffix.startswith(prefix):
            if not b.startswith(a):raise ValueError('Changed first native retry update: '+suffix)
        elif a!=b:raise ValueError('Changed accepted native entry history: '+suffix)
        checked.append(suffix)
    required=['','.'+instruction+'.next-text.summary.csv','.'+attempt+'.next-entry.summary.csv']+[prefix+suffix for suffix in ('.csv','.entities.csv','.services.csv','.interrupts.csv','.sprites.csv','.map.csv')]
    if not set(required).issubset(checked):raise ValueError('Incomplete accepted retry-entry native coverage')
    return checked


def fourth_first_update(first,continued):
    if any(data.get('afterRetry')!=2 for data in (first,continued)):raise ValueError('Wrong fourth-attempt generation')
    first_update(first,continued)


def compare(args):
    def read(folder,name):return json.loads((folder/name).read_text(encoding='utf-8'))
    parent=read(args.start_capture,'capture-summary.json');child=read(args.capture,'capture-summary.json')
    preserved_prefix(parent,child,read(args.start_capture,'events.json'),read(args.capture,'events.json'),[['tick',1800,True]])
    if Path(child['parentCapture']).resolve()!=args.start_capture.resolve():raise ValueError('Wrong explicit fourth-entry parent')
    for name in ('setup.state','inputs.txt'):
        if (args.start_capture/name).read_bytes()!=(args.capture/name).read_bytes():raise ValueError('Changed original setup/input file')
    data=read(args.out,'gameplay.json');first=read(args.start_out,'gameplay.json')
    startup=read(args.startup,'startup.json')
    for record in (data,startup):
        require_capture_reference(child,record)
        if any(record[k]!=child[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed continuing original records')
    fourth_first_update(first,data);timer=timer_rollovers(data)
    with contextlib.redirect_stdout(io.StringIO()):
        entry_compare(SimpleNamespace(native_base=args.first_base,capture=args.start_capture,out=args.start_out,startup=args.start_startup,
            parent_capture=args.parent_capture,parent_out=args.parent_out,parent_startup=args.parent_startup,parent_result_out=args.parent_result_out,accepted_base=args.instruction_base))
    files=native_prefix(args.first_base,args.native_base)
    from air_following_resource_reference import compare as resource_compare,analyze
    base=str(args.native_base)+'.fourth'
    with contextlib.redirect_stdout(io.StringIO()):
        resource_compare(SimpleNamespace(native_csv=Path(base+'.next-gameplay.csv'),entry_summary=Path(base+'.next-entry.summary.csv'),capture=args.capture,out=args.out,startup=args.startup))
    report=read(Path(base).parent,Path(base).name+'.next-gameplay.resource-comparison.json')
    from air_clock_compare import compare_sprites
    services=analyze(data)['services']
    with Path(base+'.next-gameplay.sprites.csv').open(newline='',encoding='utf-8-sig') as stream:
        sprites=[{k:int(v) for k,v in r.items()} for r in csv.DictReader(stream)]
    if len(sprites)!=40*len(services):raise ValueError('Incomplete fourth-attempt sprite publication')
    for i,row in enumerate(sprites):
        if row['service']!=data['precedingDisplays']+i//40 or row['slot']!=i%40:raise ValueError('Detached fourth-attempt sprite publication')
        row['service']=i//40
    differences=compare_sprites(services,sprites,expected_services=len(services))
    report.update(comparedPublishedSpriteSlots=len(sprites),differences=report['differences']+len(differences),firstSpriteDifference=differences[:1])
    report.update(**timer,afterRetry=2,nativePrefixFiles=len(files),acceptedFirstUpdateRetained=True,productionSchedulerAccepted=False,
        evidenceLimit='Bounded fourth Air continuation and published objects, attached to its unchanged accepted first update/entry. Includes that first update. Vacant done flags retain the documented initial mismatch. Full map/image/PCM, subsequent gameplay, other campaigns and production scheduling remain unqualified.')
    write_json(Path(str(args.native_base)+'.fourth-gameplay.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native fourth-attempt sprite publication differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('native_base',type=Path)
    for key in ('capture','out','startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base'):parser.add_argument('--'+key,type=Path,required=True)
    compare(parser.parse_args())
