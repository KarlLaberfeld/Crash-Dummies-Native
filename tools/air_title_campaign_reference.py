"""Masked title campaign/lives/window-clear/LCD-restart measurement only."""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_reference import write_json
from reference_backend import reference_class,require_matching_backend,require_capture_reference
POINTS={0x0292:'begin',0x029b:'daysReady',0x02a4:'difficultyReady',0x02b4:'livesReady',0x25af:'clearEntry',0x02b9:'windowCleared',0x25a8:'lcdEnableEntry',0x25ae:'lcdWriteReturned',0x02bc:'end'}
STORES={0x0295:0xc088,0x0298:0xc090,0x029e:0xc089,0x02a1:0xc091,0x02aa:0xc08a,0x02b1:0xc092,0x25af:0xc035,0x25ac:0xff40}

def capture(args):
    manifest=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'instruction.json');require_capture_reference(manifest,parent)
    if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Changed title campaign ancestry/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    active=complete=False;points=[];polls=[];writes=[];vectors=[];before=maps=objects=choices=None;objects_unchanged=False
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,before,maps,objects,objects_unchanged,choices
        if complete:return
        now=p._cycles()
        if pc==0x0292 and now==parent['points'][-1]['cycles']:
            active=True;before=p.title_maps_storage();objects=list(p.memory[0xc100:0xc200]);choices=dict(day=p.memory[0xc006],difficulty=p.memory[0xc007],twoPlayers=bool(p.memory[0xc081]))
        if not active:return
        if pc in POINTS:
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],day0=p.memory[0xc088],day1=p.memory[0xc090],difficulty0=p.memory[0xc089],difficulty1=p.memory[0xc091],lives0=p.memory[0xc08a],lives1=p.memory[0xc092],lcdc=p.memory[0xff40],pendingRequests=p.memory[0xff0f]&3))
            if pc==0x02bc:maps=p.title_maps_storage();objects_unchanged=objects==list(p.memory[0xc100:0xc200]);complete=True
        if pc==0x2123:polls.append(dict(cycle=now,mode=p.register_file.A&3))
        if pc in (0x0040,0x0048):vectors.append(dict(cycle=now,pc=pc))
        address=STORES.get(pc)
        if pc==0x2128:address=p.register_file.D*256+p.register_file.E
        if address is not None:writes.append(dict(cycle=now,address=address,value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,0x2123,0x2128,0x0040,0x0048}:p.hook_register(0,pc,hook,pc)
        replay(p,read(args.capture/'events.json'));digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete campaign setup or changed original control')
    data=dict(reference=metadata,storageReadOwner='direct-vram-title-v1',romSha256=manifest['romSha256'],controlMemorySha256=digest,choices=choices,points=points,polls=polls,writes=writes,vectors=vectors,beforeMaps=before,maps=maps,objectsUnchanged=objects_unchanged)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'campaign.rejected.json',data);raise
    write_json(args.out/'campaign.json',data);print(dict(boundaries=len(points),polls=len(polls),writes=len(writes)))

def analyze(data,parent):
    points=data['points'];end=parent['points'][-1]
    if [p['name'] for p in points]!=list(POINTS.values()) or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('tick','countdown','inputHeld','inputPressed','lcdc')):raise ValueError('Detached title campaign setup')
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data.get('reference',{}).get('titleStorageObserver')!='direct-vram-title-v1':raise ValueError('Campaign map storage needs direct-read provenance')
    if data['choices']!=dict(day=1,difficulty=0,twoPlayers=False):raise ValueError('Unqualified original campaign choices')
    if data['vectors'] or data.get('objectsUnchanged') is not True or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])) or any(p[k]!=end[k] for p in points for k in ('tick','countdown','inputHeld','inputPressed')):raise ValueError('Masked campaign advanced services/input/objects')
    for i,p in enumerate(points):
        if any(p[k]!=v for k,v in dict(day0=1,day1=1,difficulty0=0,difficulty1=0,lives0=0 if i<3 else 5,lives1=0,lcdc=0x51 if i<7 else 0xd1,pendingRequests=3).items()):raise ValueError('Unowned campaign/lives/LCD/request progression')
    if len(data['polls'])!=1024 or any(p['mode'] for p in data['polls']) or any(b['cycle']-a['cycle']!=144 for a,b in zip(data['polls'],data['polls'][1:])):raise ValueError('Incomplete LCD-off window readiness')
    writes=data['writes'];addresses=list(STORES.values())[:-1]+list(range(0x9c00,0xa000))+[0xff40]
    if [p['address'] for p in writes]!=addresses or [p['value'] for p in writes]!=[1,1,0,0,5,0,0x9c]+[0]*1024+[0xd1] or any(b['cycle']<=a['cycle'] for a,b in zip(writes,writes[1:])):raise ValueError('Incomplete native choices/window/LCD stores')
    if any(w['cycle']-p['cycle']!=28 for p,w in zip(data['polls'],writes[7:-1])):raise ValueError('Window store detached from readiness read')
    if len(data['beforeMaps'])!=2048 or len(data['maps'])!=2048 or data['maps']!=data['beforeMaps'][:1024]+[0]*1024:raise ValueError('Campaign changed background or left uncleared window cells')
    if not points[4]['cycles']<data['polls'][0]['cycle']<data['polls'][-1]['cycle']<writes[-2]['cycle']<points[5]['cycles']<points[6]['cycles']<writes[-1]['cycle']<points[7]['cycles']<points[8]['cycles']:raise ValueError('Campaign access escaped owner')

def compare(args):
    from air_title_instruction_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.instruction_prefix_base)
    data=read(args.campaign_out/'campaign.json');parent=read(args.instruction_out/'instruction.json');manifest=read(args.start_control/'capture-summary.json');require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or data['beforeMaps']!=read(args.title_start_out/'start.json')['maps']:raise ValueError('Mixed campaign recording/maps')
    analyze(data,parent)
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-campaign'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');polls=rows('.polls.csv');writes=rows('.writes.csv');maps=rows('.maps.csv');summary=rows('.summary.csv')
    if rows('.services.csv') or rows('.interrupts.csv') or [len(native),len(polls),len(writes),len(maps),len(summary)]!=[9,1024,1032,2048,1]:raise ValueError('Incomplete/unmasked native campaign setup')
    differences=[]
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(kind=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered campaign boundary')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:v for k,v in p.items() if k not in ('name','cycles')}),q)
    for kind,original,observed in [('poll',data['polls'],polls),('write',data['writes'],writes)]:
        for i,(p,q) in enumerate(zip(original,observed)):check(kind,i,{k:v-epoch if k=='cycle' else v for k,v in p.items()},q)
    for i,(value,q) in enumerate(zip(data['maps'],maps)):check('map',i,dict(address=0x9800+i,value=value),q)
    lcd=data['writes'][-1]['cycle']+8-epoch
    check('summary',0,dict(end=data['points'][-1]['cycles']-epoch,lcdEpoch=lcd,nextStat=lcd+95*456,nextVBlank=lcd+144*456,pendingRequests=3,servicesMasked=1,active=1,player=0),summary[0])
    report=dict(comparedBoundaries=9,comparedPolls=1024,comparedWrites=1032,comparedMapBytes=2048,comparedVectors=0,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Retained single-player Air/easy choices, fresh campaign lives, masked window clear and LCD restart before EI. Two-player/other choices have native functional tests only; pending service acceptance, instruction content, pixels/PCM and production timing remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-campaign.comparison.json'),report);print(report)
    if differences:raise ValueError('Native title campaign setup differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    for k in ('parent-out',):record.add_argument('--'+k,type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','actions-out','actions-base','start-control','title-start-out','instruction-out','title-start-base','campaign-out','instruction-prefix-base'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)
