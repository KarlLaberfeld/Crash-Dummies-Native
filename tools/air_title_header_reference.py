"""Separate original comparison of the post-title instruction header."""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_reference import write_json
from air_instruction_header_reference import POINTS,analyze as header_analyze,compare_header
from air_timing import IRQ_PHASES
from reference_backend import reference_class,require_matching_backend,require_capture_reference

def capture(args):
    manifest=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'resume.json');require_capture_reference(manifest,parent)
    if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Changed title header ancestry/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    active=complete=False;points=[];polls=[];writes=[];scroll=[];irqs=[];irq=None;before=maps=objects=None;objects_unchanged=False;buttons=[]
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,before,maps,objects,objects_unchanged,irq
        if complete:return
        now=p._cycles()
        if pc==0x02ce and now==parent['points'][-1]['cycles']:active=True;before=p.title_maps_storage();objects=list(p.memory[0xc100:0xc200])
        if not active:return
        if pc in POINTS:
            player=p.memory[0xc082]
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),player=player,stage=p.memory[0xc088+8*player],difficulty=p.memory[0xc089+8*player],lives=p.memory[0xc08a+8*player],display=p.memory[0xc098],stat=p.memory[0xc099],result=p.memory[0xc095],musicEnabled=p.memory[0xffcf],inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],pendingRequests=p.memory[0xff0f]&3))
            if pc==0x031c:maps=p.title_maps_storage();objects_unchanged=objects==list(p.memory[0xc100:0xc200]);complete=True
        elif pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested title header interrupt')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            name=IRQ_PHASES[pc];irq['phases'][name]=now
            if name=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if name=='bookkeeping':irq.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
            if name=='effects':irq['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if name=='music':irq['musicEnabled']=p.memory[0xffcf]
        elif pc in (0x2484,0x2555) and irq:irq['end']=now;irqs.append(irq);irq=None
        elif pc==0x2123:polls.append(dict(cycles=now,mode=p.register_file.A&3))
        elif pc==0x2128:writes.append(dict(cycles=now,address=p.register_file.D*256+p.register_file.E,value=p.register_file.A))
        elif pc in (0x24a1,0x2559):scroll.append(dict(cycles=now,address=0xff42,value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*IRQ_PHASES,0x2123,0x2128,0x24a1,0x2559,0x0040,0x0048,0x2484,0x2555}:p.hook_register(0,pc,hook,pc)
        replay(p,read(args.capture/'events.json'));digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete title header or changed full control')
    data=dict(version=1,afterTitle=True,precedingDisplays=702,reference=metadata,storageReadOwner='direct-vram-title-v1',romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,polls=polls,writes=writes,scrollWrites=scroll,interrupts=irqs,beforeMaps=before,maps=maps,objectsUnchanged=objects_unchanged)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'header.rejected.json',data);raise
    write_json(args.out/'header.json',data)
    (args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons))
    print(dict(boundaries=len(points),polls=len(polls),writes=len(writes),scrollStores=len(scroll),vectors=len(irqs)))

def analyze(data,parent):
    services=header_analyze(data);points=data['points'];end=parent['points'][-1]
    if data.get('afterTitle') is not True or data['precedingDisplays']!=702 or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('tick','countdown','inputHeld','inputPressed','lcdc','scrollY','stat','pendingRequests','lives','result')):raise ValueError('Detached post-title header state')
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data.get('reference',{}).get('titleStorageObserver')!='direct-vram-title-v1' or data['beforeMaps']!=parent['maps'] or len(data['maps'])!=2048 or data.get('objectsUnchanged') is not True:raise ValueError('Detached title header map/object storage')
    if any(data['beforeMaps']) or any(p['player'] or p['stage']!=1 or p['difficulty'] or p['lives']!=5 or p['display']!=5 or p['stat']!=5 or p['lcdc']!=0xd1 or p['scrollY'] or p['pendingRequests'] or p['countdown']!=end['countdown'] for p in points):raise ValueError('Unqualified post-title choices/geometry/countdown')
    for p in points:
        finished=[s for s in services if s['end']+16<=p['cycles']];last=finished[-1] if finished else None
        if p['tick']!=(end['tick']+len(finished))&65535 or (p['inputHeld'],p['inputPressed'])!=((last['held'],last['pressed']) if last else (end['inputHeld'],end['inputPressed'])):raise ValueError('Header boundary lost actual display input/tick owner')
    for i,p in enumerate(services):
        if p['tick']!=(end['tick']+i)&65535 or p['countdown']!=end['countdown']:raise ValueError('Header service changed native counters')
    expected=sorted([dict(cycles=p['start']+(1284 if p['kind']=='vblank' else 216),address=0xff42,value=0) for p in data['interrupts']],key=lambda p:p['cycles'])
    if data['scrollWrites']!=expected:raise ValueError('Incomplete header scroll stores')
    maps=list(data['beforeMaps'])
    for p in data['writes']:maps[p['address']-0x9800]=p['value']
    if maps!=data['maps']:raise ValueError('Incomplete header map contents')
    if not services or services[-1]['returnAddress']!=0x261d or services[-1]['end']+16+56!=points[-1]['cycles']:raise ValueError('Header first wait lost counter-service completion')
    return services

def compare(args):
    from air_title_resume_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.resume_base)
    data=read(args.title_header_out/'header.json');parent=read(args.resume_out/'resume.json');manifest=read(args.start_control/'capture-summary.json');require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed title header recording/control')
    services=analyze(data,parent)
    if (args.title_header_out/'buttons.txt').read_text()!=(args.resume_out/'buttons.txt').read_text()+''.join(str(p['held'])+'\n' for p in services):raise ValueError('Detached title header raw input extension')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-header'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');np=rows('.polls.csv');nw=rows('.writes.csv');summary=rows('.summary.csv');maps=rows('.maps.csv')
    glyphs=[p for p in nw if 0x9800<=int(p['address'])<0x9c00];scroll=[p for p in nw if int(p['address'])==0xff42]
    if len(nw)!=len(glyphs)+len(scroll) or len(scroll)!=len(data['scrollWrites']) or len(maps)!=2048:raise ValueError('Incomplete native header stores/maps')
    differences=compare_header(data,native,ns,ni,np,glyphs,summary,epoch)
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(category=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        check('state',i,{k:p[k] for k in ('lives','display','stat','result','musicEnabled','lcdc','scrollY','pendingRequests')},q)
    for i,(p,q) in enumerate(zip(data['scrollWrites'],scroll)):check('scroll',i,dict(cycle=p['cycles']-epoch,address=0xff42,value=p['value']),q)
    for i,(value,q) in enumerate(zip(data['maps'],maps)):check('map',i,dict(address=0x9800+i,value=value),q)
    before=read(args.campaign_out/'campaign.json');lcd=before['writes'][-1]['cycle']+8-epoch;end=data['points'][-1]['cycles']-epoch
    def deadline(line):
        value=lcd+(end-lcd)//70224*70224+line*456
        return value+70224 if value<=end else value
    check('summary',0,dict(lcdEpoch=lcd,nextStat=deadline(95),nextVBlank=deadline(144),stats=931+sum(p['kind']=='stat' for p in data['interrupts']),pendingRequests=0,servicesMasked=0,result=0),summary[0])
    report=dict(comparedBoundaries=len(native),comparedServices=len(ns),comparedVectors=len(ni),comparedPolls=len(np),comparedGlyphStores=len(glyphs),comparedScrollStores=len(scroll),comparedMapBytes=2048,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Post-title single-player Air/easy player/lives/day/difficulty header and first counter wait through 031c. Later instruction content/music/fades, other paths, pixels/PCM and production timing remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-header.comparison.json'),report);print(report)
    if differences:raise ValueError('Native title instruction header differs')

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--parent-out',type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','actions-out','actions-base','start-control','title-start-out','instruction-out','title-start-base','campaign-out','instruction-prefix-base','resume-out','campaign-base','title-header-out','resume-base'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)
if __name__=='__main__':main()
