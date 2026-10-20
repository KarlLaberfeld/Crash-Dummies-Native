"""Read-only post-campaign title layout and LCD restart, ending before EI."""
import argparse,contextlib,csv,hashlib,io,json
from pathlib import Path
from air_reference import write_json
from reference_backend import reference_class,require_matching_backend,require_capture_reference

POINTS={0x0206:'begin',0x020d:'bootSkipped',0x0212:'callbackReady',0x0217:'layoutCall',0x214f:'command',0x22e4:'rectangleEntry',0x22f6:'rowReady',0x2301:'copyReturned',0x0241:'layoutReturned',0x0243:'statWrite',0x0247:'lcdWrite',0x024b:'compareWrite',0x024f:'windowXWrite',0x0253:'windowYWrite',0x0255:'lcdEnableCall',0x25a8:'lcdEnableEntry',0x25ae:'lcdWriteReturned',0x0258:'enableEntry'}
STORES={0x020f:0xc099,0x0243:0xff41,0x0247:0xff40,0x024b:0xff45,0x024f:0xff4b,0x0253:0xff4a,0x25ac:0xff40}


def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());parent=json.loads((args.parent_out/'reset.json').read_text());require_capture_reference(manifest,parent)
    if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or hashlib.sha256(args.rom.read_bytes()).hexdigest()!=manifest['romSha256']:raise ValueError('Changed title-layout control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0);active=False;complete=False;points=[];writes=[];vectors=[];board=None;maps=None;command=-1;row=-1
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,board,maps,command,row
        if complete:return
        now=p._cycles()
        if pc==0x0206 and now==parent['points'][-1]['cycles']:active=True;board=list(p.memory[0xc051:0xc081])
        if not active:return
        if pc==0x214f:command+=1
        if pc==0x22e4:row=0
        if pc==0x2301:row=-1
        if pc==0x0241:command=-1
        if pc in POINTS:
            points.append(dict(name=POINTS[pc],cycles=now,command=command,row=row if pc==0x22f6 else -1,tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],lcdc=p.memory[0xff40],bank=p.memory[0xffc5],display=p.memory[0xc098],stat=p.memory[0xc099],bootShown=bool(p.memory[0xc005]),pending=p.memory[0xff0f]&3))
            if pc==0x0258:
                points[-1].update(scoresUnchanged=list(p.memory[0xc051:0xc081])==board,lyc=p.memory[0xff45],windowX=p.memory[0xff4b],windowY=p.memory[0xff4a]);maps=list(p.memory[0x9800:0xa000]);complete=True
        if pc==0x22f6:row+=1
        if pc in (0x0040,0x0048):vectors.append(dict(pc=pc,cycle=now))
        address=STORES.get(pc)
        if pc==0x2128:address=p.register_file.D*256+p.register_file.E
        if address is not None:writes.append(dict(cycle=now,address=address,value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,0x2128,0x0040,0x0048}:p.hook_register(0,pc,hook,pc)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            else:getattr(p,'button_'+e[0])(e[1])
        digest=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete title layout or changed full control')
    data=dict(reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,writes=writes,vectors=vectors,maps=maps)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'layout.rejected.json',data);raise
    write_json(args.out/'layout.json',data);print(json.dumps(dict(boundaries=len(points),writes=len(writes),mapBytes=len(maps))))


def analyze(data,parent):
    points=data['points'];end=parent['points'][-1];names=[p['name'] for p in points]
    if names[:4]!=['begin','bootSkipped','callbackReady','layoutCall'] or names[-10:]!=['layoutReturned','statWrite','lcdWrite','compareWrite','windowXWrite','windowYWrite','lcdEnableCall','lcdEnableEntry','lcdWriteReturned','enableEntry'] or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('tick','countdown','inputHeld','inputPressed','lcdc','bank')):raise ValueError('Detached title-reset/layout owner')
    if any(p['tick']!=end['tick'] or p['countdown']!=end['countdown'] or p['inputHeld']!=255 or p['inputPressed']!=end['inputPressed'] or p['bootShown'] is not True or p['display']!=0 or p['stat']!=(i>=2) for i,p in enumerate(points)) or data['vectors']:raise ValueError('Unowned first-boot or masked title services')
    if any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Reordered title boundaries')
    expected=[(name,-1,-1) for name in names[:4]]
    heights={2:3,4:5,7:4,9:10}
    for command in range(11):
        expected.append(('command',command,-1))
        if command in heights:
            expected.append(('rectangleEntry',command,-1));expected.extend(('rowReady',command,row) for row in range(heights[command]));expected.append(('copyReturned',command,-1))
    expected.extend((name,-1,-1) for name in names[-10:])
    if [(p['name'],p['command'],p['row']) for p in points]!=expected:raise ValueError('Reordered static title command/row ownership')
    for i,p in enumerate(points):
        lcdc=0x5b if i<=names.index('lcdWrite') else 0x43 if i<names.index('lcdWriteReturned') else 0xc3
        if p['lcdc']!=lcdc or p['bank']!=(7 if p['name']=='rowReady' else 1):raise ValueError('Unowned title bank/LCD sequence')
    commands=[p for p in points if p['name']=='command'];rows=[p for p in points if p['name']=='rowReady'];rects=[p for p in points if p['name']=='rectangleEntry'];returned=[p for p in points if p['name']=='copyReturned']
    if [p['command'] for p in commands]!=list(range(11)) or [p['command'] for p in rects]!=[2,4,7,9] or len(returned)!=4:raise ValueError('Incomplete static title command ownership')
    for command,height in [(2,3),(4,5),(7,4),(9,10)]:
        if [p['row'] for p in rows if p['command']==command]!=list(range(height)):raise ValueError('Missing title rectangle row')
    addresses=[]
    for layer,x,y,width,height in [(0x9800,3,0,14,3),(0x9800,0,13,20,5),(0x9c00,7,0,8,4),(0x9c00,7,4,6,10)]:addresses.extend(layer+32*(y+r)+x+c for r in range(height) for c in range(width))
    writes=data['writes'];expected=[0xc099]+addresses+[0xff41,0xff40,0xff45,0xff4b,0xff4a,0xff40]
    if [p['address'] for p in writes]!=expected or writes[0]['value']!=1 or [p['value'] for p in writes[-6:]]!=[0x44,0x43,23,166,112,0xc3]:raise ValueError('Incomplete title stores/registers')
    if any(b['cycle']<=a['cycle'] for a,b in zip(writes,writes[1:])) or not points[0]['cycles']<writes[0]['cycle']<writes[-1]['cycle']<points[-1]['cycles']:raise ValueError('Title stores escaped their owner')
    final=points[-1]
    if len(data['maps'])!=2048 or final.get('scoresUnchanged') is not True or final['lcdc']!=0xc3 or final['bank']!=1 or final['pending']!=3 or [final[k] for k in ('lyc','windowX','windowY')]!=[23,166,112]:raise ValueError('Incomplete title restart/storage state')
    painted=[0]*2048
    for p in writes[1:-6]:painted[p['address']-0x9800]=p['value']
    if painted!=data['maps']:raise ValueError('Title map changed outside identified rectangles')
    return dict(boundaries=len(points),writes=len(writes),mapBytes=2048)


def compare(args):
    from air_title_reset_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.reset_base)
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.layout_out/'layout.json').read_text());parent=json.loads((args.reset_out/'reset.json').read_text());require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed title layout recording')
    scope=analyze(data,parent)
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(json.loads((args.startup/'startup.json').read_text()))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-layout'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');writes=rows('.writes.csv');maps=rows('.maps.csv');summary=rows('.summary.csv')
    if rows('.services.csv') or rows('.interrupts.csv') or rows('.polls.csv'):raise ValueError('Masked layout cannot run services or LCD-on polls')
    if [len(native),len(writes),len(maps),len(summary)]!=[scope['boundaries'],scope['writes'],2048,1]:raise ValueError('Incomplete native title layout')
    differences=[]
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(kind=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered native title layout')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in ('command','row','tick','countdown','inputHeld','inputPressed','lcdc','bank','display','stat')}),q)
    for i,(p,q) in enumerate(zip(data['writes'],writes)):check('write',i,dict(cycle=p['cycle']-epoch,address=p['address'],value=p['value']),q)
    for i,(value,q) in enumerate(zip(data['maps'],maps)):check('map',i,dict(address=0x9800+i,value=value),q)
    final=data['points'][-1];lcd=data['points'][-2]['cycles']-4-epoch
    check('summary',0,dict(end=final['cycles']-epoch,lcdEpoch=lcd,tick=final['tick'],countdown=54,displays=546,stats=546,nextStat=lcd+23*456,nextVBlank=lcd+144*456,display=0,stat=1,lyc=23,windowX=166,windowY=112,servicesMasked=1),summary[0])
    report=dict(comparedBoundaries=scope['boundaries'],comparedWrites=scope['writes'],comparedMapBytes=2048,comparedVectors=0,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Post-campaign boot-skip branch, static title map/layout and masked LCD restart through EI entry only. Pending-service acceptance, first-frame pixels, tile payload/PCM, later title fade/menu and production timing remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-layout.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native title layout differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--parent-out',type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
