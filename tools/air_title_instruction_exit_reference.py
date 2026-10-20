"""Attached first-instruction prompt/fresh/held Start and exit measurements."""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_title_picture_reference import voice_states,compare_voices
from air_instruction_exit_reference import analyze as exit_analyze,compare_exit,FIELDS
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference
POINTS={0x032b:'begin',0x0331:'prompt',0x0347:'promptReady',0x0349:'inputCall',0x25da:'inputWait',0x25dd:'inputReady',0x034c:'fadeCall',0x034f:'fadeReturned',0x0352:'audioStop',0x0355:'end',0x20b9:'fadePalette',0x20bc:'bgpReady',0x20c7:'fadeWait',0x20ca:'fadeReady'}
STORES={0x20ba:0xff47,0x20be:0xff49,0x20c3:0xff48,0x24a1:0xff42,0x2559:0xff42}
def capture(args):
    manifest=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'text.json');require_capture_reference(manifest,parent)
    if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase')) or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Changed first-instruction exit ancestry')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    active=complete=False;points=[];irqs=[];irq=None;polls=[];writes=[];extra=[];buttons=[];before=maps=before_tiles=tiles=objects=None;objects_unchanged=False;end_active=end_raw_active=None
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
        nonlocal active,complete,irq,before,maps,before_tiles,tiles,objects,objects_unchanged,end_active,end_raw_active
        if complete:return
        now=p._cycles()
        if pc==0x032b and now==parent['points'][-1]['cycles']:active=True;before=p.title_maps_storage();before_tiles=p.instruction_tiles_storage();objects=list(p.memory[0xc100:0xc200])
        if not active:return
        if pc in POINTS:
            points.append(dict(name=POINTS[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),scroll=p.memory[0xc09c],bgp=p.memory[0xff47],obp0=p.memory[0xff48],obp1=p.memory[0xff49],musicEnabled=p.memory[0xffcf],inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b]))
            if pc==0x0355:
                maps=p.title_maps_storage();tiles=p.instruction_tiles_storage();objects_unchanged=objects==list(p.memory[0xc100:0xc200])
                end_raw_active=sum(bool(v['active']&128) for v in voice_states(p))
                # 369f reinstalls parked voice presets; 3710 disables the
                # driver. Raw preset flags are not logical playing voices.
                end_active=end_raw_active if p.memory[0xffcf] else 0;complete=True
        elif pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested first-instruction exit interrupt')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],display=p.memory[0xc098],returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            name=IRQ_PHASES[pc];irq['phases'][name]=now
            if name=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if name=='bookkeeping':irq.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
            if name=='effects':irq['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if name=='music':irq['musicEnabled']=p.memory[0xffcf]
            if name=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:irq['end']=now;irqs.append(irq);irq=None
        if pc in STORES:extra.append(dict(cycle=now,address=STORES[pc],value=p.register_file.A))
        if pc==0x2123:polls.append(dict(cycles=now,mode=p.register_file.A&3))
        if pc==0x2128:writes.append(dict(cycles=now,address=p.register_file.D*256+p.register_file.E,value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in {*POINTS,*STORES,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x2123,0x2128}:p.hook_register(0,pc,hook,pc)
        replay(p,read(args.capture/'events.json'));digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete first-instruction exit or changed control')
    data=dict(version=1,reference=metadata,storageReadOwner='direct-vram-instruction-v1',romSha256=manifest['romSha256'],controlMemorySha256=digest,inputCase=manifest['inputCase'],precedingDisplays=parent['precedingDisplays']+sum(p['kind']=='vblank' for p in parent['interrupts']),points=points,interrupts=irqs,polls=polls,writes=writes,extraWrites=extra,beforeMaps=before,maps=maps,beforeTiles=before_tiles,tiles=tiles,objectsUnchanged=objects_unchanged,endActiveVoices=end_active,endRawActiveFlags=end_raw_active)
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent)
    except ValueError:write_json(args.out/'exit.rejected.json',data);raise
    write_json(args.out/'exit.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons))
    print(dict(case=data['inputCase'],boundaries=len(points),services=len(buttons),vectors=len(irqs),glyphs=len(writes),extraStores=len(extra)),flush=True)

def analyze(data,parent):
    services=exit_analyze(data);first=data['points'][0];end=parent['points'][-1]
    if data['inputCase']!=parent['inputCase'] or data['precedingDisplays']!=739+sum(p['kind']=='vblank' for p in parent['interrupts']) or first['cycles']!=end['cycles'] or any(first[k]!=end[k] for k in ('tick','countdown','scroll','inputHeld','inputPressed')):raise ValueError('Detached first-instruction text/exit state')
    prompt=any(p['name']=='prompt' for p in data['points'])
    if prompt!=(data['inputCase']=='full-prompt') or data['endActiveVoices']!=0 or type(data.get('endRawActiveFlags')) is not int or not 0<=data['endRawActiveFlags']<=6:raise ValueError('First-instruction exit did not take its prompt/held branch or logically stop its driver')
    if data.get('storageReadOwner')!='direct-vram-instruction-v1' or data['reference'].get('instructionStorageObserver')!='direct-vram-instruction-v1' or data['beforeMaps']!=parent['maps'] or data['beforeTiles']!=parent['tiles'] or data['tiles']!=data['beforeTiles'] or len(data['maps'])!=2048 or len(data['tiles'])!=1024 or data.get('objectsUnchanged') is not True:raise ValueError('Detached instruction exit image storage')
    maps=list(data['beforeMaps'])
    for p in data['writes']:maps[p['address']-0x9800]=p['value']
    if maps!=data['maps']:raise ValueError('Prompt maps changed unrelated image storage')
    for i,p in enumerate(services):
        if p['tick']!=(first['tick']+i)&65535 or len(p.get('voiceStates',[]))!=6:raise ValueError('Exit music/counter projection incomplete')
    extra=data['extraWrites'];colors=[p for p in extra if p['address'] in (0xff47,0xff48,0xff49)]
    if [p['address'] for p in colors]!=[0xff47,0xff49,0xff48]*8 or any(colors[3*i+1]['value']!=colors[3*i]['value']&0xf3 or colors[3*i+2]['value']!=colors[3*i]['value']&0xcf for i in range(8)):raise ValueError('Incomplete outgoing instruction palette writes')
    expected=sorted(colors+[dict(cycle=p['start']+(1284 if p['kind']=='vblank' else 216),address=0xff42,value=0 if p['kind']=='vblank' else first['scroll']) for p in data['interrupts']],key=lambda p:p['cycle'])
    if extra!=expected:raise ValueError('Outgoing instruction actual scroll stores differ')
    return services

def compare(args):
    from air_title_text_reference import compare as prior_compare
    with contextlib.redirect_stdout(io.StringIO()):prior_compare(args)
    from air_fourth_entry_reference import preserved_native_prefix
    retained=preserved_native_prefix(args.native_base,args.title_text_base)
    data=read(args.title_instruction_exit_out/'exit.json');parent=read(args.title_text_out/'text.json');manifest=read(args.text_control/'capture-summary.json');require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase')):raise ValueError('Mixed first-instruction exit controls')
    services=analyze(data,parent)
    if (args.title_instruction_exit_out/'buttons.txt').read_text()!=(args.title_text_out/'buttons.txt').read_text()+''.join(str(p['held'])+'\n' for p in services):raise ValueError('Detached exit raw input prefix')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(read(args.startup/'startup.json'))['epoch']
    def rows(suffix):
        with Path(str(args.native_base)+'.fifth.title-instruction-exit'+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native=rows('.csv');ns=rows('.services.csv');ni=rows('.interrupts.csv');np=rows('.polls.csv');nw=rows('.writes.csv');summary=rows('.summary.csv');maps=rows('.maps.csv');tiles=rows('.tiles.csv');voices=rows('.voices.csv')
    glyphs=[p for p in nw if 0x9800<=int(p['address'])<0x9c00];extra=[p for p in nw if int(p['address'])>=0xff00]
    if len(nw)!=len(glyphs)+len(extra) or len(extra)!=len(data['extraWrites']) or len(maps)!=2048 or len(tiles)!=1024:raise ValueError('Incomplete native first-instruction exit storage')
    differences=compare_exit(data,native,ns,ni,np,glyphs,summary,epoch)+compare_voices(services,voices,data['precedingDisplays'])
    def check(kind,i,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(category=kind,index=i,fields=delta))
    for i,(p,q) in enumerate(zip(data['extraWrites'],extra)):check('store',i,dict(cycle=p['cycle']-epoch,address=p['address'],value=p['value']),q)
    for kind,values,observed,base in [('map',data['maps'],maps,0x9800),('tile',data['tiles'],tiles,0x8340)]:
        for i,(value,q) in enumerate(zip(values,observed)):check(kind,i,dict(address=base+i,value=value),q)
    with Path(str(args.native_base)+'.fifth.title-text.summary.csv').open(newline='') as f:before=list(csv.DictReader(f))[0]
    lcd=int(before['lcdEpoch']);end=data['points'][-1]['cycles']-epoch
    def deadline(line):
        value=lcd+(end-lcd)//70224*70224+line*456
        return value+70224 if value<=end else value
    check('summary',0,dict(scroll=data['points'][0]['scroll'],stats=int(before['stats'])+sum(p['kind']=='stat' for p in data['interrupts']),lcdEpoch=lcd,nextStat=deadline(95),nextVBlank=deadline(144),musicEnabled=0,activeVoices=0),summary[0])
    report=dict(inputCase=data['inputCase'],comparedBoundaries=len(native),comparedServices=len(ns),comparedVectors=len(ni),comparedPolls=len(np),comparedPromptGlyphs=len(glyphs),comparedExtraStores=len(extra),comparedMapBytes=2048,comparedTileBytes=1024,comparedVoiceRows=len(voices),preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='First Air/easy prompt/fresh-Start or held-Start exit through fade, final wait and logical audio/voice stop at 0355. Full maps/tiles, actual scroll/palette stores and active music projection included; reset voice payloads, next gameplay, other paths, frames/PCM and production timing remain unqualified.')
    report.update(stoppedDriverRawActiveFlags=data['endRawActiveFlags'],stoppedDriverVoicePayloadCompared=False)
    write_json(Path(str(args.native_base)+'.title-instruction-exit.comparison.json'),report);print(report)
    if differences:raise ValueError('Native first-instruction exit differs')

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--parent-out',type=Path,required=True)
    verify=sub.add_parser('compare');verify.add_argument('native_base',type=Path)
    for k in ('startup','accepted-base','accepted-capture','accepted-out','accepted-startup','first-base','start-capture','start-out','start-startup','parent-capture','parent-out','parent-startup','parent-result-out','instruction-base','return-out','final-base','return-base','reset-out','reset-base','layout-out','layout-base','fade-out','fade-base','close-out','close-base','page-out','page-base','case-control','actions-out','actions-base','start-control','title-start-out','instruction-out','title-start-base','campaign-out','instruction-prefix-base','resume-out','campaign-base','title-header-out','resume-base','picture-out','header-base','entrance-out','picture-base','title-text-out','text-control','entrance-base','title-instruction-exit-out','title-text-base'):verify.add_argument('--'+k,type=Path,required=True)
    for p in (record,verify):
        for k in ('capture','out'):p.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)
if __name__=='__main__':main()
