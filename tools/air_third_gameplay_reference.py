"""Compare longer third-attempt work without replacing accepted prefix evidence."""
import argparse,contextlib,csv,io,json
from pathlib import Path
from types import SimpleNamespace
from air_reference import write_json
from air_next_retry_reference import preserved_prefix,compare as first_compare
from reference_backend import require_capture_reference


def first_update(first,longer):
    if not first.get('nextRetry') or not longer.get('nextRetry') or first.get('updates')!=1 or longer.get('updates',0)<=1:
        raise ValueError('Wrong first/continuing retry scope')
    if first['points']!=longer['points'][:10] or first['interrupts']!=longer['interrupts'][:2] or first['precedingDisplays']!=longer['precedingDisplays']:
        raise ValueError('Changed original first update')


def native_prefix(first_base,long_base):
    checked=[]
    for path in first_base.parent.glob(first_base.name+'*.csv'):
        suffix=path.name[len(first_base.name):]
        if suffix.startswith('.next-gameplay.summary'):continue
        other=Path(str(long_base)+suffix)
        a=path.read_bytes().replace(b'\r\n',b'\n');b=other.read_bytes().replace(b'\r\n',b'\n')
        if suffix.startswith('.next-gameplay'):
            if not b.startswith(a):raise ValueError('Changed native first-update prefix: '+suffix)
        elif a!=b:raise ValueError('Changed native entry history: '+suffix)
        checked.append(suffix)
    required=['.next-gameplay.csv','.next-gameplay.entities.csv','.next-gameplay.services.csv','.next-gameplay.interrupts.csv','.next-gameplay.sprites.csv','.next-entry.summary.csv','.next-text.csv']
    if any(s not in checked for s in required):raise ValueError('Missing native accepted-prefix coverage')
    return checked


def timer_rollovers(data):
    points=data['points'];phase=points[0]['secondTicks'];increments=0;rollovers=[]
    if not 0<phase<60 or len(points)!=10*data['updates']:raise ValueError('Missing inherited timer extent')
    for update in range(data['updates']):
        block=points[10*update:10*(update+1)]
        before=tuple(block[0][k] for k in ('secondTicks','seconds'))
        after=tuple(block[2][k] for k in ('secondTicks','seconds'))
        if tuple(block[1][k] for k in ('secondTicks','seconds'))!=before or any(tuple(p[k] for k in ('secondTicks','seconds'))!=after for p in block[2:]):
            raise ValueError('Timer changed outside actor work')
        if after!=before:
            expected=((before[0]+1)%60,max(0,before[1]-int(before[0]==59)))
            if after!=expected:raise ValueError('Timer skipped/reset its inherited phase')
            increments+=1
            if before[0]==59:rollovers.append(update)
    if not increments or not rollovers:raise ValueError('Continuation does not exercise timer rollover')
    return dict(inheritedSecondTicks=phase,timerIncrements=increments,timerRollovers=len(rollovers),firstRolloverUpdate=rollovers[0])


def compare(args):
    def read(folder,name):return json.loads((folder/name).read_text(encoding='utf-8'))
    start=read(args.start_capture,'capture-summary.json');manifest=read(args.capture,'capture-summary.json')
    preserved_prefix(start,manifest,read(args.start_capture,'events.json'),read(args.capture,'events.json'),[['tick',1800,True]])
    if Path(manifest['parentCapture']).resolve()!=args.start_capture.resolve():raise ValueError('Wrong accepted entry control')
    for name in ('setup.state','inputs.txt'):
        if (args.start_capture/name).read_bytes()!=(args.capture/name).read_bytes():raise ValueError('Changed original setup/input file')
    data=read(args.out,'gameplay.json');first=read(args.start_out,'gameplay.json')
    require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed continuing recording')
    first_update(first,data);timer=timer_rollovers(data)
    with contextlib.redirect_stdout(io.StringIO()):
        first_compare(SimpleNamespace(native_base=args.first_base,capture=args.start_capture,out=args.start_out,startup=args.start_startup,
            parent_capture=args.parent_capture,parent_out=args.parent_out,parent_startup=args.parent_startup))
    files=native_prefix(args.first_base,args.native_base)
    from air_following_resource_reference import compare as resource_compare,analyze
    with contextlib.redirect_stdout(io.StringIO()):
        resource_compare(SimpleNamespace(native_csv=Path(str(args.native_base)+'.next-gameplay.csv'),capture=args.capture,out=args.out,startup=args.startup,entry_summary=Path(str(args.native_base)+'.next-entry.summary.csv')))
    # OAM publication is independently observed at each source DMA service,
    # including quiet-body histories that contain no interrupted scene work.
    from air_clock_compare import compare_sprites
    services=analyze(data)['services'];path=Path(str(args.native_base)+'.next-gameplay.sprites.csv')
    with path.open(encoding='utf-8-sig',newline='') as stream:rows=[{k:int(v) for k,v in r.items()} for r in csv.DictReader(stream)]
    if len(rows)!=40*len(services):raise ValueError('Incomplete third-attempt sprite publication')
    normalized=[]
    for i,row in enumerate(rows):
        if row['service']!=data['precedingDisplays']+i//40 or row['slot']!=i%40:raise ValueError('Detached third-attempt sprite publication')
        normalized.append(dict(row,service=i//40))
    differences=compare_sprites(services,normalized,expected_services=len(services))
    report=read(args.native_base.parent,args.native_base.name+'.next-gameplay.resource-comparison.json')
    report.update(**timer,comparedPublishedSpriteSlots=len(rows),nativePrefixFiles=len(files),acceptedFirstUpdateRetained=True,
        differences=report['differences']+len(differences),firstSpriteDifference=differences[:1],productionSchedulerAccepted=False)
    write_json(Path(str(args.native_base)+'.third-gameplay.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native third-attempt sprite publication differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('native_base',type=Path)
    for key in ('capture','out','startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup'):parser.add_argument('--'+key,type=Path,required=True)
    compare(parser.parse_args())
