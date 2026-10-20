"""Attached first-instruction full text and deliberate Start-skip measurements."""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_title_text_controls import attachment
from air_title_picture_reference import voice_states,compare_voices
from air_instruction_text_reference import POINTS,analyze as text_analyze,compare_text
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work,elapsed_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference

def capture(args):
    accepted=read(args.accepted_control/'capture-summary.json');manifest=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'entrance.json')
    old=read(args.accepted_control/'events.json');events=read(args.capture/'events.json')
    attachment(accepted,manifest,old,events,sha((args.capture/'setup.state').read_bytes()));require_capture_reference(accepted,parent)
    if parent['controlMemorySha256']!=accepted['controlMemorySha256'] or manifest['romSha256']!=sha(args.rom.read_bytes()) or (args.capture/'setup.state').read_bytes()!=(args.accepted_control/'setup.state').read_bytes():raise ValueError('Detached first-instruction text ancestry')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    active=False;armed=False;complete=False;points=[];irqs=[];opened=None;polls=[];writes=[];buttons=[];campaign=None;before=maps=before_tiles=tiles=objects=None;objects_unchanged=False;scroll=[]
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,armed,complete,opened,campaign,before,maps,before_tiles,tiles,objects,objects_unchanged
        if complete:return
        if pc==0x0a0a and p._cycles()==parent['points'][-1]['cycles']:
            active=True;player=p.memory[0xc082];campaign=dict(player=player,stage=p.memory[0xc088+8*player],difficulty=p.memory[0xc089+8*player]);before=p.title_maps_storage();before_tiles=p.instruction_tiles_storage();objects=list(p.memory[0xc100:0xc200])
        if not active:return
        now=p._cycles()
        if pc in POINTS:
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),scroll=p.memory[0xc09c],speed=p.memory[0xc03a],
                delay=p.memory[0xc039],skipMask=p.memory[0xc03b],layer=p.memory[0xc035],column=p.register_file.C,row=p.register_file.B,
                inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b]))
            if pc==0x2186:
                pointer=p.register_file.HL;player=campaign['player'];level=campaign['difficulty']
                points[-1]['skipContext']=1 if 0x2272+6*player<=pointer<=0x2276+6*player else 2 if 0x2297+3*level<=pointer<=0x2298+3*level else 0
            if pc==0x032b:maps=p.title_maps_storage();tiles=p.instruction_tiles_storage();objects_unchanged=objects==list(p.memory[0xc100:0xc200]);complete=True
        elif pc in (0x0040,0x0048):
            if opened:raise ValueError('Nested text interrupt')
            opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],display=p.memory[0xc098],returnAddress=word(p.register_file.SP),
                tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and opened and opened['kind']=='vblank':
            name=IRQ_PHASES[pc];opened['phases'][name]=now
            if name=='display':opened.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if name=='bookkeeping':opened.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
            if name=='effects':opened['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if name=='music':opened['musicEnabled']=p.memory[0xffcf]
            if name=='restore':opened['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and opened:
            if opened['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Mismatched text interrupt')
            opened['end']=now;irqs.append(opened);opened=None
        elif pc in (0x24a1,0x2559,0x222c):scroll.append(dict(cycle=now,address=0xc09c if pc==0x222c else 0xff42,value=p.register_file.A))
        elif pc==0x2123:polls.append(dict(cycles=now,mode=p.register_file.A&3))
        elif pc==0x2128:writes.append(dict(cycles=now,address=256*p.register_file.D+p.register_file.E,value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in (*POINTS,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x2123,0x2128,0x24a1,0x2559,0x222c,0x268b,0x03d8,0x0462):p.hook_register(0,pc,hook,pc)
        for i,e in enumerate(events):
            replay(p,[e])
            if i==len(old)-1 and memory_sha(p)!=accepted['controlMemorySha256']:raise ValueError('Observed text changed original accepted prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or opened or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete text or changed control')
    data=dict(version=1,reference=metadata,storageReadOwner='direct-vram-instruction-v1',romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=accepted['controlMemorySha256'],inputCase=manifest['inputCase'],campaign=campaign,precedingDisplays=739,points=points,interrupts=irqs,polls=polls,writes=writes,scrollWrites=scroll,beforeMaps=before,maps=maps,beforeTiles=before_tiles,tiles=tiles,objectsUnchanged=objects_unchanged)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'text.rejected.json',data);raise
    write_json(args.out/'text.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons))
    print(dict(case=data['inputCase'],boundaries=len(points),services=len(buttons),vectors=len(irqs),polls=len(polls),glyphs=len(writes),scrollStores=len(scroll)),flush=True)

def analyze(data,parent):
    services=text_analyze(data);first=data['points'][0];end=parent['points'][-1]
    if data['campaign']!=dict(player=0,stage=1,difficulty=0) or data['precedingDisplays']!=739 or first['cycles']!=end['cycles'] or first['scroll'] or any(first[k]!=end[k] for k in ('tick','countdown','inputHeld','inputPressed')):raise ValueError('Detached first-instruction text state')
    if data['inputCase'] not in ('full-prompt','skip-held') or bool(any(p['name']=='skip' for p in data['points']))!=(data['inputCase']=='skip-held'):raise ValueError('Text case did not exercise its full/skip branch')
    if data.get('storageReadOwner')!='direct-vram-instruction-v1' or data['reference'].get('instructionStorageObserver')!='direct-vram-instruction-v1' or data['beforeMaps']!=parent['maps'] or data['beforeTiles']!=parent['tiles'] or len(data['maps'])!=2048 or data['tiles']!=data['beforeTiles'] or len(data['tiles'])!=1024 or data.get('objectsUnchanged') is not True:raise ValueError('Detached text picture/maps/object storage')
    maps=list(data['beforeMaps'])
    for p in data['writes']:maps[p['address']-0x9800]=p['value']
    if maps!=data['maps']:raise ValueError('Text map publication incomplete')
    centers=[p for p in data['scrollWrites'] if p['address']==0xc09c];steps=[p for p in data['points'] if p['name']=='scrollStored']
    if len(centers)!=len(steps) or any(w['value']!=p['scroll'] or elapsed_work(w['cycle'],p['cycles'],data['interrupts'])!=8 for w,p in zip(centers,steps)):raise ValueError('Text scroll-center store lost its boundary')
    expected=list(centers)
    for p in data['interrupts']:
        if p['kind']=='vblank':value=0;offset=1284
        else:
            committed=[w for w in centers if w['cycle']+8<=p['start']];value=committed[-1]['value'] if committed else 0;offset=216
        expected.append(dict(cycle=p['start']+offset,address=0xff42,value=value))
    if data['scrollWrites']!=sorted(expected,key=lambda p:p['cycle']):raise ValueError('Text actual scroll register stores differ')
    for i,p in enumerate(services):
        if p['tick']!=(first['tick']+i)&65535 or p['countdown']!=54 or len(p.get('voiceStates',[]))!=6:raise ValueError('Text music/counter projection incomplete')
    return services

def compare(args):
    from air_title_entrance_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.entrance_base)
    parent_control=read(args.start_control/'capture-summary.json');manifest=read(args.text_control/'capture-summary.json');data=read(args.title_text_out/'text.json');parent=read(args.entrance_out/'entrance.json')
    attachment(parent_control,manifest,read(args.start_control/'events.json'),read(args.text_control/'events.json'),sha((args.text_control/'setup.state').read_bytes()));require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase','parentControlMemorySha256')):raise ValueError('Mixed text control/recording')
    services=analyze(data,parent)
    if (args.title_text_out/'buttons.txt').read_text()!=(args.entrance_out/'buttons.txt').read_text()+''.join(str(p['held'])+'\n' for p in services):raise ValueError('Detached text raw input prefix')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-text'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');np=rows('.polls.csv');nw=rows('.writes.csv');summary=rows('.summary.csv');maps=rows('.maps.csv');tiles=rows('.tiles.csv');voices=rows('.voices.csv')
    glyphs=[p for p in nw if 0x9800<=int(p['address'])<0x9c00];scroll=[p for p in nw if int(p['address']) in (0xc09c,0xff42)]
    if len(nw)!=len(glyphs)+len(scroll) or len(scroll)!=len(data['scrollWrites']) or len(maps)!=2048 or len(tiles)!=1024:raise ValueError('Incomplete native text storage/scroll coverage')
    differences=compare_text(data,native,ns,ni,np,glyphs,summary,epoch)+compare_voices(services,voices,739)
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(category=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['scrollWrites'],scroll)):check('scroll',i,dict(cycle=p['cycle']-epoch,address=p['address'],value=p['value']),q)
    for kind,values,observed,base in [('map',data['maps'],maps,0x9800),('tile',data['tiles'],tiles,0x8340)]:
        for i,(value,q) in enumerate(zip(values,observed)):check(kind,i,dict(address=base+i,value=value),q)
    lcd=read(args.campaign_out/'campaign.json')['writes'][-1]['cycle']+8-epoch;end=data['points'][-1]['cycles']-epoch
    def deadline(line):
        value=lcd+(end-lcd)//70224*70224+line*456
        return value+70224 if value<=end else value
    check('summary',0,dict(stats=968+sum(p['kind']=='stat' for p in data['interrupts']),lcdEpoch=lcd,nextStat=deadline(95),nextVBlank=deadline(144)),summary[0])
    report=dict(inputCase=data['inputCase'],comparedBoundaries=len(native),comparedServices=len(ns),comparedVectors=len(ni),comparedPolls=len(np),comparedGlyphStores=len(glyphs),comparedScrollStores=len(scroll),comparedMapBytes=2048,comparedTileBytes=1024,comparedVoiceRows=len(voices),preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='First Air/easy complete text or deliberate Start skip through 032b, with macro/scroll work, direct maps/tiles and active voice projection. Unused inherited delay/cursor exclusions remain explicit; prompt/exit, other campaigns, rendered frames/PCM and production scheduling remain unqualified.')
    write_json(Path(str(args.native_base)+'.title-text.comparison.json'),report);print(report)
    if differences:raise ValueError('Native first-instruction text differs')

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--parent-out',type=Path,required=True);record.add_argument('--accepted-control',type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','actions-out','actions-base','start-control','title-start-out','instruction-out','title-start-base','campaign-out','instruction-prefix-base','resume-out','campaign-base','title-header-out','resume-base','picture-out','header-base','entrance-out','picture-base','title-text-out','text-control','entrance-base'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)
if __name__=='__main__':main()
