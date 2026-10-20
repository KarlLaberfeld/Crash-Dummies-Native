"""Separate original comparison of the post-title instruction music and picture."""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_reference import write_json
from air_instruction_picture_reference import analyze as picture_analyze,compare_picture
from audio_timing import BYTE_FIELDS,WORD_FIELDS
from air_timing import vblank_work
POINTS={0x031c:"begin",0x0321:"musicReady",0x0324:"stageReady",0x0328:"tableDispatch",0x09ee:"resourceEntry",0x09f9:"copyCall",0x09fc:"copyReturned",0x0a07:"rectangleReady",0x268b:"end"}
VOICE_FIELDS=("position","remaining","fixed","loopCount","transpose","noTranspose","fineTune","note","targetNote","frequency","stage","envelopeCounter","volume","releaseCounter","tableIndex","arpCounter","direction","vibratoWait","vibratoCounter","pitchWait")
def voice_states(p):
    result=[]
    for i in range(6):
        row={name:p.memory[at[i]] if at[i] else 0 for name,at in BYTE_FIELDS.items()}
        row.update({name:p.memory[at[i]]+256*p.memory[at[i]+1] if at[i] else 0 for name,at in WORD_FIELDS.items()})
        if i in (3,5):row["frequency"]=p.memory[0xfff8 if i==3 else 0xfff9]
        result.append({k:row[k] for k in ("active",*VOICE_FIELDS)})
    return result
from air_timing import IRQ_PHASES
from reference_backend import reference_class,require_matching_backend,require_capture_reference

def capture(args):
    manifest=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'header.json');require_capture_reference(manifest,parent)
    if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Changed title picture ancestry/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    active=complete=False;points=[];polls=[];writes=[];scroll=[];irqs=[];irq=None;before=maps=objects=None;objects_unchanged=False;buttons=[];before_tiles=tiles=None
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,before,maps,objects,objects_unchanged,irq,before_tiles,tiles
        if complete:return
        now=p._cycles()
        if pc==0x031c and now==parent['points'][-1]['cycles']:active=True;before=p.title_maps_storage();objects=list(p.memory[0xc100:0xc200]);before_tiles=p.instruction_tiles_storage()
        if not active:return
        if pc in POINTS:
            player=p.memory[0xc082]
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),player=player,stage=p.memory[0xc088+8*player],difficulty=p.memory[0xc089+8*player],lives=p.memory[0xc08a+8*player],display=p.memory[0xc098],stat=p.memory[0xc099],result=p.memory[0xc095],musicEnabled=p.memory[0xffcf],inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b],lcdc=p.memory[0xff40],scrollY=p.memory[0xff42],pendingRequests=p.memory[0xff0f]&3,musicSelected=p.memory[0xffce]))
            if pc==0x268b:maps=p.title_maps_storage();objects_unchanged=objects==list(p.memory[0xc100:0xc200]);tiles=p.instruction_tiles_storage();complete=True
        elif pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested title picture interrupt')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            name=IRQ_PHASES[pc];irq['phases'][name]=now
            if name=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if name=='bookkeeping':irq.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
            if name=='effects':irq['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if name=='music':irq['musicEnabled']=p.memory[0xffcf]
            if name=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:irq['end']=now;irqs.append(irq);irq=None
        elif pc in (0x2123,0x2363):polls.append(dict(cycles=now,mode=p.register_file.A&3))
        elif pc in (0x2128,0x2368):writes.append(dict(kind="tile" if pc==0x2368 else "map",cycles=now,address=p.register_file.D*256+p.register_file.E,value=p.register_file.A))
        elif pc in (0x24a1,0x2559):scroll.append(dict(cycles=now,address=0xff42,value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*IRQ_PHASES,0x2123,0x2128,0x2363,0x2368,0x24a1,0x2559,0x0040,0x0048,0x2484,0x2555}:p.hook_register(0,pc,hook,pc)
        replay(p,read(args.capture/'events.json'));digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete title picture or changed full control')
    data=dict(version=1,afterTitle=True,precedingDisplays=703,reference=metadata,storageReadOwner='direct-vram-title-v1',romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,polls=polls,writes=writes,scrollWrites=scroll,interrupts=irqs,beforeMaps=before,maps=maps,objectsUnchanged=objects_unchanged,beforeTiles=before_tiles,tiles=tiles)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'picture.rejected.json',data);raise
    write_json(args.out/'picture.json',data)
    (args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons))
    print(dict(boundaries=len(points),polls=len(polls),writes=len(writes),scrollStores=len(scroll),vectors=len(irqs)))

def analyze(data,parent):
    services=picture_analyze(data);points=data['points'];end=parent['points'][-1]
    if data.get('afterTitle') is not True or data['precedingDisplays']!=703 or points[0]['cycles']!=end['cycles'] or any(points[0][k]!=end[k] for k in ('tick','countdown','inputHeld','inputPressed','lcdc','scrollY','stat','pendingRequests','lives','result','stage','difficulty','player')):raise ValueError('Detached post-title picture state')
    if data.get('storageReadOwner')!='direct-vram-title-v1' or data.get('reference',{}).get('instructionStorageObserver')!='direct-vram-instruction-v1' or data['beforeMaps']!=parent['maps'] or len(data['maps'])!=2048 or data.get('objectsUnchanged') is not True:raise ValueError('Detached direct instruction image storage')
    if len(data['beforeTiles'])!=1024 or len(data['tiles'])!=1024 or data['tiles']!=[p['value'] for p in data['writes'] if p['kind']=='tile']:raise ValueError('Instruction tile stores did not reach direct graphics storage')
    for i,p in enumerate(points):
        if p['player'] or p['stage']!=1 or p['difficulty'] or p['lives']!=5 or p['display']!=5 or p['stat']!=5 or p['lcdc']!=0xd1 or p['scrollY'] or p['pendingRequests'] or p['countdown']!=end['countdown'] or (i and p['musicSelected']!=2):raise ValueError('Unqualified instruction music/picture state')
        finished=[s for s in services if s['end']+16<=p['cycles']];last=finished[-1] if finished else None
        if p['tick']!=(end['tick']+len(finished))&65535 or (p['inputHeld'],p['inputPressed'])!=((last['held'],last['pressed']) if last else (end['inputHeld'],end['inputPressed'])):raise ValueError('Picture boundary lost actual input/tick owner')
    for i,p in enumerate(services):
        if p['tick']!=(end['tick']+i)&65535 or p['countdown']!=end['countdown'] or len(p.get('voiceStates',[]))!=6:raise ValueError('Missing music voice/counter observations')
    expected=sorted([dict(cycles=p['start']+(1284 if p['kind']=='vblank' else 216),address=0xff42,value=0) for p in data['interrupts']],key=lambda p:p['cycles'])
    if data['scrollWrites']!=expected:raise ValueError('Incomplete picture scroll stores')
    maps=list(data['beforeMaps'])
    for p in data['writes']:
        if p['kind']=='map':maps[p['address']-0x9800]=p['value']
    if maps!=data['maps']:raise ValueError('Incomplete final instruction picture map')
    return services

def compare_voices(services,rows,preceding=703):
    if len(rows)!=6*len(services):raise ValueError('Incomplete native instruction music voices')
    differences=[]
    for service,p in enumerate(services):
        for voice,post in enumerate(p['voiceStates']):
            q=rows[6*service+voice];active=bool(post['active']&128)
            if int(q['service'])!=preceding+service or int(q['voice'])!=voice:raise ValueError('Reordered native instruction music voices')
            wanted=dict(active=int(active),musicCost=vblank_work(p)['music'])
            if active:
                for name in VOICE_FIELDS:
                    if voice==2 and name in ('stage','envelopeCounter','volume','releaseCounter','tableIndex'):continue
                    if voice in (3,5) and name in ('transpose','noTranspose','fineTune','note','targetNote','vibratoWait','vibratoCounter'):continue
                    if name=='tableIndex' and not post['stage']&128:continue
                    wanted[name]=post[name]
            delta={k:[v,int(q[k])] for k,v in wanted.items() if v!=int(q[k])}
            if delta:differences.append(dict(category='voice',index=6*service+voice,fields=delta))
    return differences

def compare(args):
    from air_title_header_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.header_base)
    data=read(args.picture_out/'picture.json');parent=read(args.title_header_out/'header.json');manifest=read(args.start_control/'capture-summary.json');require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed picture recording/control')
    services=analyze(data,parent)
    if (args.picture_out/'buttons.txt').read_text()!=(args.title_header_out/'buttons.txt').read_text()+''.join(str(p['held'])+'\n' for p in services):raise ValueError('Detached picture raw input extension')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-picture'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');np=rows('.polls.csv');nw=rows('.writes.csv');summary=rows('.summary.csv');maps=rows('.maps.csv');tiles=rows('.tiles.csv');voices=rows('.voices.csv')
    graphics=[p for p in nw if p['kind']!='scroll'];scroll=[p for p in nw if p['kind']=='scroll']
    if len(scroll)!=len(data['scrollWrites']) or len(maps)!=2048 or len(tiles)!=1024:raise ValueError('Incomplete native picture storage/scroll coverage')
    differences=compare_picture(data,native,ns,ni,np,graphics,summary,epoch)+compare_voices(services,voices)
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(category=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],native)):
        check('state',i,{k:p[k] for k in ('stage','display','stat','lcdc','scrollY','pendingRequests')},q)
        if i:check('music',i,dict(song=p['musicSelected']),q)
    for i,(p,q) in enumerate(zip(data['scrollWrites'],scroll)):check('scroll',i,dict(cycle=p['cycles']-epoch,address=0xff42,value=p['value']),q)
    for kind,values,observed,base in [('map',data['maps'],maps,0x9800),('tile',data['tiles'],tiles,0x8340)]:
        for i,(value,q) in enumerate(zip(values,observed)):check(kind,i,dict(address=base+i,value=value),q)
    before=read(args.campaign_out/'campaign.json');lcd=before['writes'][-1]['cycle']+8-epoch;end=data['points'][-1]['cycles']-epoch
    def deadline(line):
        value=lcd+(end-lcd)//70224*70224+line*456
        return value+70224 if value<=end else value
    check('summary',0,dict(lcdEpoch=lcd,nextStat=deadline(95),nextVBlank=deadline(144),stats=932+sum(p['kind']=='stat' for p in data['interrupts']),song=2),summary[0])
    report=dict(comparedBoundaries=len(native),comparedServices=len(ns),comparedVectors=len(ni),comparedPolls=len(np),comparedGraphicsStores=len(graphics),comparedScrollStores=len(scroll),comparedMapBytes=2048,comparedTileBytes=1024,comparedVoiceRows=len(voices),preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Post-title Air/easy music selection, active voice projection, full instruction tiles/picture map and access timing through 268b. Active-field exclusions follow the existing audio qualification; PCM, rendered frames, later instruction/other routes and production timing remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-picture.comparison.json'),report);print(report)
    if differences:raise ValueError('Native title instruction music/picture differs')


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--parent-out',type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','actions-out','actions-base','start-control','title-start-out','instruction-out','title-start-base','campaign-out','instruction-prefix-base','resume-out','campaign-base','title-header-out','resume-base','picture-out','header-base'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)
if __name__=='__main__':main()
