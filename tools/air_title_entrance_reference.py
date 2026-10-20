"""Original first-instruction incoming fade; separate from later map transitions."""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work
from air_title_picture_reference import voice_states,compare_voices
from reference_backend import reference_class,require_matching_backend,require_capture_reference
POINTS={0x268b:'begin',0x26b2:'firstInstruction',0x20d1:'fadeEntry',0x20d6:'palette',0x20e4:'wait',0x20e7:'tail',0x0a0a:'end'}
STORES={0x26b4:0xc09d,0x20d7:0xff47,0x20db:0xff49,0x20e0:0xff48,0x24a1:0xff42,0x2559:0xff42}
def capture(args):
    manifest=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'picture.json');require_capture_reference(manifest,parent)
    if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Changed first-instruction fade ancestry/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    active=complete=False;points=[];writes=[];irqs=[];irq=None;before=maps=before_tiles=tiles=objects=None;objects_unchanged=False;buttons=[];palettes=waits=0
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,before,maps,before_tiles,tiles,objects,objects_unchanged,irq,palettes,waits
        if complete:return
        now=p._cycles()
        if pc==0x268b and now==parent['points'][-1]['cycles']:active=True;before=p.title_maps_storage();before_tiles=p.instruction_tiles_storage();objects=list(p.memory[0xc100:0xc200])
        if not active:return
        if pc in POINTS:
            if pc==0x20d6:palettes+=1
            if pc==0x20e7:waits+=1
            points.append(dict(name=POINTS[pc],cycles=now,palettes=palettes,waits=waits,tick=word(0xc00a),countdown=word(0xc0b7),alternate=p.memory[0xc09d],bgp=p.memory[0xff47],obp0=p.memory[0xff48],obp1=p.memory[0xff49],inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],display=p.memory[0xc098],stat=p.memory[0xc099],lcdc=p.memory[0xff40],lyc=p.memory[0xff45],musicEnabled=p.memory[0xffcf]))
            if pc==0x0a0a:maps=p.title_maps_storage();tiles=p.instruction_tiles_storage();objects_unchanged=objects==list(p.memory[0xc100:0xc200]);complete=True
        elif pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested first-instruction fade interrupt')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            name=IRQ_PHASES[pc];irq['phases'][name]=now
            if name=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if name=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:irq['end']=now;irqs.append(irq);irq=None
        if pc in STORES:writes.append(dict(cycle=now,address=STORES[pc],value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555}:p.hook_register(0,pc,hook,pc)
        replay(p,read(args.capture/'events.json'));digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete incoming instruction fade or changed control')
    data=dict(reference=metadata,storageReadOwner='direct-vram-instruction-v1',romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,writes=writes,interrupts=irqs,beforeMaps=before,maps=maps,beforeTiles=before_tiles,tiles=tiles,objectsUnchanged=objects_unchanged)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'entrance.rejected.json',data);raise
    write_json(args.out/'entrance.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons))
    print(dict(boundaries=len(points),services=len(buttons),vectors=len(irqs),writes=len(writes)))

def analyze(data,parent):
    points=data['points'];end=parent['points'][-1];irqs=data['interrupts'];services=[p for p in irqs if p['kind']=='vblank']
    names=['begin','firstInstruction','fadeEntry']+sum((['palette']+['wait','tail']*4 for _ in range(8)),[])+['end']
    if [p['name'] for p in points]!=names or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('tick','countdown','inputHeld','inputPressed','display','stat','lcdc','musicEnabled')) or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Detached first-instruction fade boundaries')
    if data.get('storageReadOwner')!='direct-vram-instruction-v1' or data['reference'].get('instructionStorageObserver')!='direct-vram-instruction-v1' or len(data['maps'])!=2048 or len(data['tiles'])!=1024 or data['beforeMaps']!=parent['maps'] or data['beforeTiles']!=parent['tiles'] or data['maps']!=data['beforeMaps'] or data['tiles']!=data['beforeTiles'] or data.get('objectsUnchanged') is not True:raise ValueError('Incoming fade changed/detached image storage')
    if len(services)!=32 or not 31<=len(irqs)-32<=33 or any(not points[0]['cycles']<p['start']<p['end']<points[-1]['cycles'] for p in irqs) or any(b['start']<=a['end'] for a,b in zip(irqs,irqs[1:])):raise ValueError('Unowned incoming fade service extent')
    previous=end['inputHeld'];service_count=0
    for p in irqs:
        if p['selector']!=5 or p['tick']!=(end['tick']+service_count)&65535 or p['countdown']!=end['countdown']:raise ValueError('Incoming fade changed callback/counters')
        if p['kind']=='vblank':
            w=vblank_work(p)
            if any(w[k]!=v for k,v in dict(prefix=180,dma=704,joypad=280,display=144,bookkeeping=240,effects=64,audioBank=68,restore=120).items()) or len(p.get('voiceStates',[]))!=6 or p['pressed']!=p['held']&~previous or not 0<=p['held']<=255 or p['held']&15==15:raise ValueError('Unowned incoming fade input/audio work')
            previous=p['held'];service_count+=1
        elif p['kind']!='stat' or p['end']-p['start']!=288:raise ValueError('Unowned incoming fade raster')
    writes=data['writes'];colors=[p for p in writes if p['address'] in (0xff47,0xff48,0xff49)];alternate=[p for p in writes if p['address']==0xc09d]
    if len(colors)!=24 or [p['address'] for p in colors]!=[0xff47,0xff49,0xff48]*8 or [(p['address'],p['value']) for p in alternate]!=[(0xc09d,1)] or any(b['cycle']<=a['cycle'] for a,b in zip(writes,writes[1:])):raise ValueError('Incomplete incoming fade palette/selector stores')
    for i in range(8):
        if colors[3*i+1]['value']!=colors[3*i]['value']&0xf3 or colors[3*i+2]['value']!=colors[3*i]['value']&0xcf:raise ValueError('Incoming fade object palette masks differ')
    expected=sorted([dict(cycle=p['start']+(1284 if p['kind']=='vblank' else 216),address=0xff42,value=0) for p in irqs]+colors+alternate,key=lambda p:p['cycle'])
    if writes!=expected or any(points[0][k] for k in ('alternate','bgp','obp0','obp1')) or (points[-1]['bgp'],points[-1]['obp0'],points[-1]['obp1'])!=(0xe4,0xc4,0xe0):raise ValueError('Changed incoming fade geometry/palette endpoints')
    palettes=waits=0
    for p in points:
        if p['name']=='palette':palettes+=1
        if p['name']=='tail':waits+=1
        finished=[s for s in services if s['end']+16<=p['cycles']];last=finished[-1] if finished else None
        wanted=dict(palettes=palettes,waits=waits,tick=(end['tick']+len(finished))&65535,countdown=end['countdown'],alternate=int(p['cycles']>=alternate[0]['cycle']+16),display=5,stat=5,lcdc=0xd1,lyc=95,musicEnabled=1,inputHeld=last['held'] if last else end['inputHeld'],inputPressed=last['pressed'] if last else end['inputPressed'])
        for key,address in [('bgp',0xff47),('obp0',0xff48),('obp1',0xff49)]:
            committed=[w for w in colors if w['address']==address and w['cycle']+12<=p['cycles']];wanted[key]=committed[-1]['value'] if committed else 0
        if any(p[k]!=v for k,v in wanted.items()):raise ValueError('Incoming fade boundary lost its actual palette/wait/display owner')
    from air_timing import elapsed_work
    if elapsed_work(points[0]['cycles'],points[1]['cycles'],irqs)!=32 or elapsed_work(points[1]['cycles'],points[2]['cycles'],irqs)!=40:raise ValueError('Wrong first-instruction alternate branch')
    return services

def compare(args):
    from air_title_picture_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.picture_base)
    data=read(args.entrance_out/'entrance.json');parent=read(args.picture_out/'picture.json');manifest=read(args.start_control/'capture-summary.json');require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed incoming instruction fade controls')
    services=analyze(data,parent)
    if (args.entrance_out/'buttons.txt').read_text()!=(args.picture_out/'buttons.txt').read_text()+''.join(str(p['held'])+'\n' for p in services):raise ValueError('Detached incoming fade raw inputs')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-entrance'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');nw=rows('.writes.csv');summary=rows('.summary.csv');maps=rows('.maps.csv');tiles=rows('.tiles.csv');voices=rows('.voices.csv')
    if [len(native),len(ns),len(ni),len(nw),len(summary),len(maps),len(tiles),len(voices)]!=[len(data['points']),32,len(data['interrupts']),len(data['writes']),1,2048,1024,192] or rows('.polls.csv'):raise ValueError('Incomplete native incoming fade')
    differences=compare_voices(services,voices,707)
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(category=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        if p['name']!=q['boundary']:raise ValueError('Reordered incoming fade boundaries')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:v for k,v in p.items() if k not in ('name','cycles')}),q)
    for i,(p,q) in enumerate(zip(services,ns)):
        w=vblank_work(p);check('display',i,dict(service=707+i,cycle=p['start']-epoch,tick=p['tick'],countdown=p['countdown'],display=w['display'],effects=w['effects'],music=w['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],ni)):
        if p['kind']!=q['kind']:raise ValueError('Reordered incoming fade vectors')
        check('vector',i,dict(vectorCycle=p['start']-epoch,owner=2 if p['returnAddress']==0x261d else 1),q)
    for i,(p,q) in enumerate(zip(data['writes'],nw)):check('write',i,dict(cycle=p['cycle']-epoch,address=p['address'],value=p['value']),q)
    for kind,values,observed,base in [('map',data['maps'],maps,0x9800),('tile',data['tiles'],tiles,0x8340)]:
        for i,(value,q) in enumerate(zip(values,observed)):check(kind,i,dict(address=base+i,value=value),q)
    lcd=read(args.campaign_out/'campaign.json')['writes'][-1]['cycle']+8-epoch;end=data['points'][-1]['cycles']-epoch
    def deadline(line):
        value=lcd+(end-lcd)//70224*70224+line*456
        return value+70224 if value<=end else value
    check('summary',0,dict(end=end,tick=data['points'][-1]['tick'],countdown=54,displays=739,stats=936+sum(p['kind']=='stat' for p in data['interrupts']),lcdEpoch=lcd,nextStat=deadline(95),nextVBlank=deadline(144),alternate=1,bgp=0xe4,obp0=0xc4,obp1=0xe0),summary[0])
    report=dict(comparedBoundaries=len(native),comparedServices=32,comparedVectors=len(ni),comparedWrites=len(nw),comparedMapBytes=2048,comparedTileBytes=1024,comparedVoiceRows=192,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='First post-title incoming fade and native alternate-flag branch through text entry, including palettes, retained picture and active song-2 voice projection. Timed text/skip/prompt/exit, other choices, rendered frames/PCM and production timing remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-entrance.comparison.json'),report);print(report)
    if differences:raise ValueError('Native first-instruction incoming fade differs')

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--parent-out',type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','actions-out','actions-base','start-control','title-start-out','instruction-out','title-start-base','campaign-out','instruction-prefix-base','resume-out','campaign-base','title-header-out','resume-base','picture-out','header-base','entrance-out','picture-base'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)
if __name__=='__main__':main()
