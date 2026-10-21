"""Initial selected-Air row bytes attached to independently qualified gameplay.

Original observation only. Native row storage and publication are executed by
the existing semantic map owner; this file is never a native playback input.
"""
import argparse,contextlib,csv,io,json
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_reference import write_json
from air_map_reference import analyze as row_analyze,compare_rows
from reference_backend import reference_class,require_matching_backend,require_capture_reference


def owners(data,gameplay):
    for key in ('romSha256','controlMemorySha256','inputCase','parentInputCase','players','selectedEntryCycle','updates'):
        if data.get(key)!=gameplay.get(key):raise ValueError('Detached selected row gameplay owner')
    if any(type(item.get('terminalWait',False)) is not bool for item in (data,gameplay)) or data.get('terminalWait',False)!=gameplay.get('terminalWait',False):raise ValueError('Detached terminal selected row owner')
    points=row_analyze(data,direct_storage=True);services=[r for r in gameplay['interrupts'] if r['kind']=='vblank']
    if len(points)!=2+2*len(services) or points[0]['cycles']!=gameplay['points'][0]['cycles'] or points[-1]['cycles']!=gameplay['points'][-1]['cycles']:
        raise ValueError('Incomplete selected row extent')
    for before,after,irq in zip(points[1:-1:2],points[2:-1:2],services):
        # 0c3f/0c42 surround CALL 1f16. The entry follows the independently
        # observed display phase and its ready-test prefix, not fitted times.
        if before['cycles']!=irq['phases']['display']+116:raise ValueError('Detached selected row display phase')
    return points


def capture(args):
    parent=read(args.gameplay_out/'gameplay.json');manifest=read(args.capture/'capture-summary.json')
    require_capture_reference(manifest,parent)
    if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase')) or sha(args.rom.read_bytes())!=manifest['romSha256']:
        raise ValueError('Changed selected row input/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    first=parent['points'][0]['cycles'];last=parent['points'][-1]['cycles'];end_pc=0x0403 if parent.get('terminalWait') else 0x03d8;points=[];active=False;complete=False;service=-1
    p=Reference(str(args.rom),window='null',sound_volume=0)
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def snapshot(name):
        lcd=p.lcd_snapshot()
        points.append(dict(boundary=name,service=service+1 if name=='end' else max(service,0),cycles=p._cycles(),camera=word(0xff94),lastCamera=word(0xff96),pending=p.memory[0xc00d],row=p.memory[0xc00c]//8,buffer=list(p.memory[0xc00e:0xc02e]),tiles=p.title_maps_storage()[:1024],tilesReadOwner='direct-vram-title-v1',lcd=lcd))
    def hook(pc):
        nonlocal active,complete,service
        now=p._cycles()
        if complete:return
        if pc==0x03d8 and now==first:active=True;snapshot('startup')
        elif pc==end_pc and now==last:snapshot('end');active=False;complete=True
        elif active:
            if pc==0x2436:service+=1
            elif pc==0x0c3f:snapshot('before')
            elif pc==0x0c42:snapshot('after')
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {0x03d8,end_pc,0x2436,0x0c3f,0x0c42}:p.hook_register(0,pc,hook,pc)
        replay(p,read(args.capture/'events.json'));digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or digest!=manifest['controlMemorySha256']:raise ValueError('Changed selected row control or missing endpoint')
    data={k:parent[k] for k in ('romSha256','controlMemorySha256','inputCase','parentInputCase','players','selectedEntryCycle','updates')}
    if parent.get('terminalWait'):data['terminalWait']=True
    data.update(version=1,reference=metadata,gameplaySha256=sha((args.gameplay_out/'gameplay.json').read_bytes()),points=points)
    owners(data,parent);args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'map.json',data)
    print('Selected original row storage captured',len(points),flush=True)


def compare(args,_parent_qualified=False):
    if not _parent_qualified:
        from selected_gameplay_reference import compare as qualify
        with contextlib.redirect_stdout(io.StringIO()):qualify(args)
    game=read(args.gameplay_out/'gameplay.json');data=read(args.map_out/'map.json');control=getattr(args,'play_control',args.text_control);manifest=read(control/'capture-summary.json');require_capture_reference(manifest,data)
    if data.get('gameplaySha256')!=sha((args.gameplay_out/'gameplay.json').read_bytes()):raise ValueError('Changed selected row gameplay attachment')
    owners(data,game)
    from air_startup_reference import analyze as epoch
    with Path(str(args.native_base)+'.fifth.selected.title-gameplay.map.csv').open(newline='') as f:rows=list(csv.DictReader(f))
    differences=compare_rows(data,rows,epoch(read(args.startup/'startup.json'))['epoch'],direct_storage=True)
    report=dict(comparedBoundaries=len(rows),comparedBytes=len(rows)*1056,comparedDisplays=(len(rows)-2)//2,directStorageObserver='direct-vram-title-v1',blockedCpuReadBoundaries=sum(bool(p['lcd']['readBlocked']) for p in data['points']),differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Complete native row staging/destination and direct original 9800..9bff tile storage around every display in the attached selected gameplay extent. CPU read-block status is retained, never used for a CPU-style blocked VRAM read. Exact byte/time comparison; no pixels, arbitrary storage ranges, PCM or Windows scheduling claim.')
    write_json(Path(str(args.native_base)+'.selected-map.comparison.json'),report);print(report)
    if differences:raise ValueError('Selected initial row storage differs')


def compare_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid selected map batch')
    from selected_gameplay_reference import compare_many as qualify
    with contextlib.redirect_stdout(io.StringIO()):qualify(cases)
    for case in cases:compare(case,_parent_qualified=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('capture');p.add_argument('rom',type=Path)
    for key in ('capture','gameplay-out','out'):p.add_argument('--'+key,type=Path,required=True)
    p=sub.add_parser('compare-batch');p.add_argument('manifest',type=Path);args=parser.parse_args()
    if args.mode=='capture':capture(args)
    else:compare_many([argparse.Namespace(**{k:Path(v) for k,v in c.items()}) for c in read(args.manifest)])
if __name__=='__main__':main()
