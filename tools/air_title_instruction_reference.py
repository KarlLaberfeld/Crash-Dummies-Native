"""Read-only masked instruction LCD/register prefix after accepted title Start."""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_reference import write_json
from reference_backend import reference_class,require_matching_backend,require_capture_reference
POINTS={0x0272:'begin',0x0276:'lcdOffReturned',0x0292:'end'}
STORES={0x25a0:0xff40,0x0278:0xc098,0x027b:0xc099,0x027f:0xff43,0x0281:0xff42,0x0283:0xc09c,0x0288:0xff45,0x028c:0xff41,0x0290:0xff40}

def capture(args):
    manifest=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'start.json');require_capture_reference(manifest,parent)
    if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Changed instruction prefix ancestry/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    active=complete=False;points=[];polls=[];writes=[];vectors=[];maps=None;unchanged=False
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,maps,unchanged
        if complete:return
        now=p._cycles()
        if pc==0x0272 and now==parent['points'][-1]['cycles']:active=True;maps=p.title_maps_storage()
        if not active:return
        if pc in POINTS:
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],display=p.memory[0xc098],stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45]))
            if pc==0x0292:unchanged=maps==p.title_maps_storage();complete=True
        if pc==0x2598:polls.append(dict(cycle=now,ly=p.register_file.A))
        if pc in (0x0040,0x0048):vectors.append(dict(cycle=now,pc=pc))
        if pc in STORES:writes.append(dict(cycle=now,address=STORES[pc],value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,0x2598,0x0040,0x0048}:p.hook_register(0,pc,hook,pc)
        replay(p,read(args.capture/'events.json'));digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete instruction prefix or changed full control')
    data=dict(reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,polls=polls,writes=writes,vectors=vectors,mapsUnchanged=unchanged)
    analyze(data,parent);args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'instruction.json',data);print(dict(boundaries=3,polls=len(polls),writes=len(writes)))

def analyze(data,parent):
    points=data['points'];end=parent['points'][-1]
    if [p['name'] for p in points]!=list(POINTS.values()) or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('tick','countdown','inputHeld','inputPressed','stat','lcdc','scrollY','lyc')):raise ValueError('Detached instruction prefix')
    if data['vectors'] or data.get('mapsUnchanged') is not True or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])) or any(p[k]!=end[k] for p in points for k in ('tick','countdown','inputHeld','inputPressed')):raise ValueError('Masked prefix changed services/input/maps')
    if [(p['display'],p['stat'],p['lcdc'],p['scrollY'],p['lyc']) for p in points]!=[(0,2,0xfb,88,103),(0,2,0x7b,88,103),(5,5,0x51,0,95)]:raise ValueError('Unknown instruction register setup')
    polls=data['polls'];writes=data['writes']
    if not 0<len(polls)<=2200 or polls[-1]['ly']!=145 or any(p['ly']==145 for p in polls[:-1]) or any(b['cycle']-a['cycle']!=32 for a,b in zip(polls,polls[1:])):raise ValueError('Incomplete LCD-off equality wait')
    if [p['address'] for p in writes]!=list(STORES.values()) or [p['value'] for p in writes]!=[0x7b,5,5,0,0,0,95,0x44,0x51] or any(b['cycle']<=a['cycle'] for a,b in zip(writes,writes[1:])):raise ValueError('Incomplete instruction register stores')
    if not points[0]['cycles']<polls[0]['cycle']<=polls[-1]['cycle']<writes[0]['cycle']<points[1]['cycles']<writes[1]['cycle']<writes[-1]['cycle']<points[-1]['cycles']:raise ValueError('Instruction access escaped owner')

def compare(args):
    from air_title_start_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.title_start_base)
    data=read(args.instruction_out/'instruction.json');parent=read(args.title_start_out/'start.json');manifest=read(args.start_control/'capture-summary.json');require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed instruction recording')
    analyze(data,parent)
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-instruction'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');polls=rows('.polls.csv');writes=rows('.writes.csv');summary=rows('.summary.csv')
    if rows('.services.csv') or rows('.interrupts.csv') or [len(native),len(polls),len(writes),len(summary)]!=[3,len(data['polls']),9,1]:raise ValueError('Incomplete/unmasked native instruction prefix')
    differences=[]
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(kind=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered native instruction boundary')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:v for k,v in p.items() if k not in ('name','cycles')}),q)
    for kind,original,observed in [('poll',data['polls'],polls),('write',data['writes'],writes)]:
        for i,(p,q) in enumerate(zip(original,observed)):check(kind,i,{k:v-epoch if k=='cycle' else v for k,v in p.items()},q)
    with Path(str(args.native_base)+'.fifth.title-start.summary.csv').open(newline='') as f:prior=next(csv.DictReader(f))
    off=data['writes'][0]['cycle']+12-epoch
    check('summary',0,dict(end=data['points'][-1]['cycles']-epoch,lcdDisabled=off,polls=len(polls),pendingRequests=(2 if int(prior['nextStat'])<=off else 0)|(1 if int(prior['nextVBlank'])<=off else 0),servicesMasked=1),summary[0])
    report=dict(comparedBoundaries=3,comparedPolls=len(polls),comparedWrites=9,comparedVectors=0,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Masked LCD-off equality wait and instruction register setup only, before campaign configuration, map clearing and LCD restart. No instruction-screen completion, pixels/PCM or production timing claim.')
    write_json(Path(str(args.native_base)+'.title-instruction.comparison.json'),report);print(report)
    if differences:raise ValueError('Native instruction prefix differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    for k in ('parent-out',):record.add_argument('--'+k,type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','actions-out','actions-base','start-control','title-start-out','instruction-out','title-start-base'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)
