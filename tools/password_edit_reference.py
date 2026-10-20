"""Original password cursor/digit/edit/submit-edge comparisons, before feedback."""
import argparse,contextlib,csv,io,shutil
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_title_actions_reference import event_sha,KEYS
from air_title_menu_reference import STORES
from air_title_picture_reference import voice_states,compare_voices
from air_timing import IRQ_PHASES,vblank_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
VALID_CASES=tuple('valid-'+str(i) for i in range(10))
CASES=('submit-start','submit-a','submit-b','navigation','digit-wrap','combined','held')+VALID_CASES
POINTS={0x2ba7:'wait',0x2baa:'ready',0x2bad:'pointerReady',0x2bb4:'leftReturned',0x2bbb:'rightReturned',0x2bc2:'upReturned',0x2bc9:'downReturned',0x2bcd:'submitDecision',0x2bcf:'end'}
RAM_STORES={0x2c40:0xc101,0x2c45:0xc100,0x2c4a:0xc102,0x2c4f:0xc103,0x2c2e:0xff9b,0x2c37:0xff9b}

def tail(case,digits=None):
    if case not in CASES:raise ValueError('Unknown password edit case')
    events=[['release',key] for key in KEYS]+[['tick',2,True]]
    def press(keys,frames=4):events.extend([['press',key] for key in keys]+[['tick',frames,True]]+[['release',key] for key in keys]+[['tick',2,True]])
    if case=='navigation':
        press(['left'])
        for _ in range(9):press(['right'])
        for _ in range(9):press(['left'])
    if case=='digit-wrap':
        press(['down']);press(['up'])
        for _ in range(10):press(['up'])
        press(['down']);press(['down'])
    if case=='combined':press(['left','right']);press(['up','down']);press(['right']);press(['left','up'])
    if case=='held':press(['up'],24);press(['right'],18);press(['down'],24)
    if case in VALID_CASES:
        if not isinstance(digits,list) or len(digits)!=8 or any(type(n) is not int or not 1<=n<=10 for n in digits):raise ValueError('Valid password controls need eight decoded digit inputs')
        for i,digit in enumerate(digits):
            for _ in range(digit):press(['up'])
            if i<7:press(['right'])
    press([case[7:] if case.startswith('submit-') else 'start']);events.append(['tick',12,True]);return events

def attachment(parent,child,events,changed,setup):
    if child['inputCase'] not in CASES or changed!=events+tail(child['inputCase'],child.get('digitInput')) or child['parentControlMemorySha256']!=parent['controlMemorySha256'] or child['parentEventsSha256']!=event_sha(events) or child['setupSha256']!=setup or child['romSha256']!=parent['romSha256']:raise ValueError('Detached password editing controls')
    if child['controlDifferences'] or child['prefixControlHashes']!=[parent['controlMemorySha256']]*2 or child['unhookedControlHashes']!=[child['controlMemorySha256']]*2:raise ValueError('Password editing controls are not repeatable')

def prepare(args):
    parent=read(args.capture/'capture-summary.json');events=read(args.capture/'events.json');setup=sha((args.capture/'setup.state').read_bytes())
    if parent['controlDifferences'] or sha(args.rom.read_bytes())!=parent['romSha256']:raise ValueError('Changed password editing ROM/control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(parent,metadata)
    rom=args.rom.read_bytes()
    for case in getattr(args,'cases',CASES):
        digits=list(rom[0x2cca+10*int(case[6:]):0x2cd2+10*int(case[6:])]) if case in VALID_CASES else None
        prefixes=[];hashes=[]
        for _ in range(2):
            p=Reference(str(args.rom),window='null',sound_volume=0)
            try:
                with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
                replay(p,events);prefixes.append(memory_sha(p));replay(p,tail(case,digits));hashes.append(memory_sha(p))
            finally:p.stop(save=False)
        child=dict(**metadata,inputCase=case,digitInput=digits,romSha256=parent['romSha256'],parentControlMemorySha256=parent['controlMemorySha256'],parentEventsSha256=event_sha(events),setupSha256=setup,controlMemorySha256=hashes[0],controlDifferences=[],prefixControlHashes=prefixes,unhookedControlHashes=hashes,referenceOnly=True)
        attachment(parent,child,events,events+tail(case,digits),setup);folder=args.out/case;folder.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.capture/'setup.state',folder/'setup.state');write_json(folder/'capture-summary.json',child);write_json(folder/'events.json',events+tail(case,digits));print(case,'two editing controls match',flush=True)

def capture(args):
    manifest=read(args.control/'capture-summary.json');accepted=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'password.json');require_capture_reference(accepted,parent)
    old=read(args.capture/'events.json');events=read(args.control/'events.json');attachment(accepted,manifest,old,events,sha((args.control/'setup.state').read_bytes()))
    if (args.capture/'setup.state').read_bytes()!=(args.control/'setup.state').read_bytes() or sha(args.rom.read_bytes())!=manifest['romSha256'] or parent['controlMemorySha256']!=accepted['controlMemorySha256']:raise ValueError('Changed editing ancestry')
    if manifest['inputCase'] in VALID_CASES:
        index=int(manifest['inputCase'][6:])
        if manifest['digitInput']!=list(args.rom.read_bytes()[0x2cca+10*index:0x2cd2+10*index]):raise ValueError('Password input digits differ from identified original table')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    active=complete=False;points=[];irqs=[];irq=None;writes=[];polls=[];rasters=[];buttons=[];before=maps=before_objects=objects=None
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def geometry():return dict(stat=p.memory[0xc099],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],lyc=p.memory[0xff45])
    def hook(pc):
        nonlocal active,complete,irq,before,maps,before_objects,objects
        if complete:return
        now=p._cycles()
        if pc==0x2ba7 and now==parent['points'][-1]['cycles']:active=True;before=p.title_maps_storage();before_objects=list(p.memory[0xc100:0xc200])
        if not active:return
        if pc in POINTS:
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),cursor=p.memory[0xff9b],submit=(p.memory[0xff8b]&11) if pc==0x2bcf else 0,held=p.memory[0xff8a],pressed=p.memory[0xff8b],**{'digit'+str(i):p.memory[0xc0a0+i] for i in range(8)}))
            if pc==0x2bcf:maps=p.title_maps_storage();objects=list(p.memory[0xc100:0xc200]);complete=True
        elif pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested password editing interrupt')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
            if pc==0x0048:rasters.append(dict(boundary='begin',cycle=now,**geometry()))
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            phase=IRQ_PHASES[pc];irq['phases'][phase]=now
            if phase=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if phase=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:
            if irq['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Mismatched editing vector')
            irq['end']=now;irqs.append(irq);irq=None
            if pc==0x2555:rasters.append(dict(boundary='end',cycle=now,**geometry()))
        if pc in STORES:
            value=p.memory[0xc099]+1 if pc in (0x251e,0x2532) else p.register_file.A;writes.append(dict(cycle=now,address=STORES[pc],value=value&255))
        if pc in RAM_STORES:
            value=p.memory[0xff9b]+(-1 if pc==0x2c2e else 1) if pc in (0x2c2e,0x2c37) else p.register_file.A;writes.append(dict(cycle=now,address=RAM_STORES[pc],value=value))
        if pc in (0x2c00,0x2c08,0x2c1c,0x2c24):writes.append(dict(cycle=now,address=p.register_file.HL,value=p.register_file.A))
        if pc==0x2123:polls.append(dict(cycle=now,mode=p.register_file.A&3))
        if pc==0x2128:writes.append(dict(cycle=now,address=p.register_file.D*256+p.register_file.E,value=p.register_file.A))
    try:
        with (args.control/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,*RAM_STORES,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x2c00,0x2c08,0x2c1c,0x2c24,0x2123,0x2128}:p.hook_register(0,pc,hook,pc)
        for i,e in enumerate(events):
            replay(p,[e])
            if i==len(old)-1 and memory_sha(p)!=accepted['controlMemorySha256']:raise ValueError('Editing observer changed accepted prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete editing case or changed full control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=accepted['controlMemorySha256'],inputCase=manifest['inputCase'],storageReadOwner='direct-vram-title-v1',points=points,interrupts=irqs,writes=writes,polls=polls,rasters=rasters,beforeMaps=before,maps=maps,beforeObjects=before_objects,objects=objects)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'edit.rejected.json',data);raise
    write_json(args.out/'edit.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons));print(dict(case=manifest['inputCase'],boundaries=len(points),services=len(buttons),vectors=len(irqs),polls=len(polls),stores=len(writes)),flush=True)

def analyze(data,parent):
    first=data['points'][0];end=parent['points'][-1];points=data['points'];irqs=data['interrupts'];services=[r for r in irqs if r['kind']=='vblank'];count=len(services)
    if data.get('version')!=1 or data['inputCase'] not in CASES or data['parentControlMemorySha256']!=parent['controlMemorySha256'] or first['name']!='wait' or first['cycles']!=end['cycles'] or any(first[k]!=end[k] for k in ('tick','countdown','held','pressed')) or first['cursor']!=0 or any(first['digit'+str(i)] for i in range(8)):raise ValueError('Detached password editing entry')
    names=['wait','ready','pointerReady','leftReturned','rightReturned','upReturned','downReturned','submitDecision']*count+['end']
    if not count or [p['name'] for p in points]!=names or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])) or any(p['countdown']!=54 or not 0<=p['cursor']<=7 or any(not 0<=p['digit'+str(i)]<=10 for i in range(8)) for p in points):raise ValueError('Incomplete/unowned password editing order')
    if [r['kind'] for r in irqs]!=['stat','stat','vblank']*count:raise ValueError('Incomplete steady title editing raster extent')
    last=first['cycles']
    for r in irqs:
        if not last<=r['start']<r['end'] or r['end']+16>points[-1]['cycles']:raise ValueError('Reordered editing vectors')
        last=r['end']+16
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data['reference'].get('titleStorageObserver')!='direct-vram-title-v1' or data['beforeMaps']!=parent['maps'] or len(data['maps'])!=2048 or data['beforeObjects']!=[0]*256 or len(data['objects'])!=256:raise ValueError('Detached editing storage')
    cursor=0;digits=[0]*8;previous=first['held']
    for i,r in enumerate(services):
        w=vblank_work(r)
        if r['pressed']!=r['held']&~previous or r['tick']!=(first['tick']+i)&65535 or r['countdown']!=54 or w['display']!=116 or w['effects']!=64 or len(r.get('voiceStates',[]))!=6:raise ValueError('Unowned editing input/audio/counter')
        previous=r['held'];pressed=r['pressed'];group=points[8*i:8*i+8]
        for j,p in enumerate(group):
            if p['tick']!=(first['tick']+i+(j!=0))&65535 or p['held']!=(r['held'] if j else first['held'] if i==0 else services[i-1]['held']) or p['pressed']!=(r['pressed'] if j else first['pressed'] if i==0 else services[i-1]['pressed']):raise ValueError('Editing boundary lost its actual service/input state')
            if j==3 and pressed&32:cursor=max(0,cursor-1)
            if j==4 and pressed&16:cursor=min(7,cursor+1)
            if j==5 and pressed&64:digits[cursor]=1 if digits[cursor]==10 else digits[cursor]+1
            if j==6 and pressed&128:digits[cursor]=10 if digits[cursor]<=1 else digits[cursor]-1
            if p['cursor']!=cursor or any(p['digit'+str(n)]!=v for n,v in enumerate(digits)):raise ValueError('Editing decisions do not follow independent fresh-input bounds/order')
        if bool(pressed&11)!=(i==count-1):raise ValueError('Password submitted early or failed to submit')
    if points[-1]['submit']!=services[-1]['pressed']&11 or any(p['submit'] for p in points[:-1]):raise ValueError('Wrong final submit edge')
    if points[-1]['tick']!=(first['tick']+count)&65535:raise ValueError('Wrong editing terminal counter')
    maps=list(data['beforeMaps']);objects=list(data['beforeObjects'])
    for r in data['writes']:
        a=r['address'];v=r['value']
        if 0x9800<=a<0xa000:maps[a-0x9800]=v
        if 0xc100<=a<0xc200:objects[a-0xc100]=v
    if maps!=data['maps'] or objects!=data['objects']:raise ValueError('Editing map/object publication incomplete')
    published=[(w['address'],w['value']) for w in data['writes'] if 0xc100<=w['address']<=0xc103]
    expected=[pair for i in range(count) for pair in ((0xc101,56+8*points[8*i+1]['cursor']),(0xc100,96),(0xc102,0x45),(0xc103,0x80))]
    if published!=expected:raise ValueError('Cursor publication did not precede direction handling')
    for rows in (data['writes'],data['polls']):
        if any(not first['cycles']<r['cycle']<points[-1]['cycles'] for r in rows) or any(b['cycle']<=a['cycle'] for a,b in zip(rows,rows[1:])):raise ValueError('Reordered editing stores/accesses')
    if any(p['mode'] not in (0,1,2,3) for p in data['polls']):raise ValueError('Unowned editing readiness mode')
    if len(data['rasters'])!=2*sum(r['kind']=='stat' for r in irqs):raise ValueError('Incomplete editing raster observations')
    for i,p in enumerate([r for r in irqs if r['kind']=='stat']):
        a,b=data['rasters'][2*i:2*i+2]
        if a['boundary']!='begin' or b['boundary']!='end' or a['cycle']!=p['start'] or b['cycle']!=p['end']:raise ValueError('Detached editing raster boundaries')
        phase=i%2;before=(1,0xc3,0,23) if phase==0 else (2,0xfb,88,103);after=(2,0xfb,88,103) if phase==0 else (1,0xc3,0,23)
        if tuple(a[k] for k in ('stat','lcdc','scrollY','lyc'))!=before or tuple(b[k] for k in ('stat','lcdc','scrollY','lyc'))!=after or p['end']-p['start']!=(460 if phase==0 else 384):raise ValueError('Unowned steady editing raster geometry/work')
        actual=[(w['cycle']-p['start'],w['address'],w['value']) for w in data['writes'] if p['start']<w['cycle']<p['end']]
        wanted=[(220,0xff40,0xfb),(256,0xff42,88),(344,0xff42,88),(364,0xff45,103),(388,0xc099,2)] if phase==0 else [(252,0xff40,0xc3),(268,0xff42,0),(288,0xff45,23),(308,0xc099,1)]
        if actual!=wanted:raise ValueError('Incomplete actual editing raster register stores')
    return services

def compare(args,_parent_qualified=False):
    from air_title_password_reference import compare as prior_compare
    if not _parent_qualified:
        with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.password_base);data=read(args.edit_out/'edit.json');parent=read(args.password_out/'password.json');accepted=read(args.password_control/'capture-summary.json');child=read(args.edit_control/'capture-summary.json')
    attachment(accepted,child,read(args.password_control/'events.json'),read(args.edit_control/'events.json'),sha((args.edit_control/'setup.state').read_bytes()));require_capture_reference(child,data)
    if any(data[k]!=child[k] for k in ('romSha256','controlMemorySha256','inputCase')):raise ValueError('Mixed editing control')
    services=analyze(data,parent)
    if (args.edit_out/'buttons.txt').read_text()!=(args.password_out/'buttons.txt').read_text()+''.join(str(r['held'])+'\n' for r in services):raise ValueError('Detached editing raw input stream')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.password-edit'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');nr=rows('.raster.csv');np=rows('.polls.csv');nw=rows('.writes.csv');maps=rows('.maps.csv');objects=rows('.objects.csv');summary=rows('.summary.csv');voices=rows('.voices.csv')
    if [len(native),len(ns),len(ni),len(nr),len(np),len(nw),len(maps),len(objects),len(summary)]!=[len(data['points']),len(services),len(data['interrupts']),len(data['rasters']),len(data['polls']),len(data['writes']),2048,256,1]:raise ValueError('Incomplete native editing outputs')
    with Path(str(args.password_base)+'.fifth.title-password.summary.csv').open(newline='') as f:before=next(csv.DictReader(f))
    preceding=int(before['displays']);differences=compare_voices(services,voices,preceding)
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(category=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered native editing boundaries')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:v for k,v in p.items() if k not in ('name','cycles')}),q)
    for i,(p,q) in enumerate(zip(services,ns)):
        w=vblank_work(p);check('service',i,dict(service=preceding+i,cycle=p['start']-epoch,tick=p['tick'],countdown=54,display=w['display'],effects=w['effects'],music=w['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],ni)):
        if p['kind']!=q['kind']:raise ValueError('Reordered editing vector')
        check('vector',i,dict(vectorCycle=p['start']-epoch,owner=2 if p['returnAddress']==0x261d else 1),q)
    for kind,source,target in [('raster',data['rasters'],nr),('poll',data['polls'],np),('write',data['writes'],nw)]:
        for i,(p,q) in enumerate(zip(source,target)):
            if 'boundary' in p and p['boundary']!=q['boundary']:raise ValueError('Reordered editing raster')
            check(kind,i,{k:v-epoch if k=='cycle' else v for k,v in p.items() if k!='boundary'},q)
    for kind,source,target,base in [('map',data['maps'],maps,0x9800),('object',data['objects'],objects,0xc100)]:
        for i,(value,q) in enumerate(zip(source,target)):check(kind,i,dict(address=base+i,value=value),q)
    lcd=int(before['lcdEpoch']);end=data['points'][-1]['cycles']-epoch
    def deadline(line):
        value=lcd+(end-lcd)//70224*70224+line*456
        return value+70224 if value<=end else value
    check('summary',0,dict(end=end,tick=data['points'][-1]['tick'],countdown=54,displays=preceding+len(services),stats=int(before['stats'])+sum(p['kind']=='stat' for p in data['interrupts']),lcdEpoch=lcd,nextStat=deadline(23),nextVBlank=deadline(144),cursor=data['points'][-1]['cursor'],submit=data['points'][-1]['submit'],waits=len(services)),summary[0])
    report=dict(inputCase=data['inputCase'],comparedBoundaries=len(native),comparedServices=len(ns),comparedVectors=len(ni),comparedRasterBoundaries=len(nr),comparedPolls=len(np),comparedWrites=len(nw),comparedMapBytes=2048,comparedObjectBytes=256,comparedVoiceRows=len(voices),preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Initial password editing through submission edge at 2bcf. Feedback/validation/return and rendered frames/PCM remain unqualified. Active voice field exclusions retain prior instruction-music scope.')
    write_json(Path(str(args.native_base)+'.password-edit.comparison.json'),report);print(report)
    if differences:raise ValueError('Native password editing differs')

def compare_many(cases):
    """Qualify one parent once, then prove every case preserves its full CSVs."""
    if not cases or len(cases)>128:raise ValueError('Invalid editing comparison batch')
    ignored={'native_base','edit_out','edit_control'}
    common={k:v for k,v in vars(cases[0]).items() if k not in ignored}
    if any({k:v for k,v in vars(c).items() if k not in ignored}!=common for c in cases[1:]):raise ValueError('Batch mixes distinct parent qualification chains')
    from air_title_password_reference import compare as prior_compare
    parent=argparse.Namespace(**vars(cases[0]));parent.native_base=parent.password_base
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(parent)
    for case in cases:compare(case,_parent_qualified=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    make=sub.add_parser('prepare');make.add_argument('rom',type=Path)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    for k in ('control','parent-out'):record.add_argument('--'+k,type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    batch=sub.add_parser('compare-batch');batch.add_argument('manifest',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','unlock-out','password-out','password-control','unlock-base','edit-out','edit-control','password-base'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (make,record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args()
    if args.mode=='compare-batch':compare_many([argparse.Namespace(**{k:Path(v) for k,v in c.items()}) for c in read(args.manifest)])
    else:dict(prepare=prepare,capture=capture,compare=compare)[args.mode](args)
if __name__=='__main__':main()
