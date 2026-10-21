"""Attached selected-player instruction exit to first native Air gameplay entry."""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_following_setup_reference import POINTS as PREFIX,analyze as prefix_analyze,compare_prefix
from air_following_stage_reference import COMMON,AIR,analyze as stage_analyze,compare_stage
from air_following_entry_reference import POINTS as ENTRY,analyze as entry_analyze,compare_entry
from air_title_picture_reference import voice_states,compare_voices
from password_feedback_reference import logical_voice_projection
from air_timing import IRQ_PHASES
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
GROUPS=('prefix','stage','entry');TABLES=(PREFIX,COMMON|AIR,ENTRY)

def capture(args):
    turn=getattr(args,'turn',False);old=None;events=read(args.capture/'events.json');watch=0
    if turn:
        from selected_turn_reference import entry_context,observation_start
        parent,manifest,accepted,old,events=entry_context(args);watch=observation_start(events,parent['inputCase'])
    else:
        manifest=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'text.json')
        if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase')):raise ValueError('Detached selected initial game entry control')
    require_capture_reference(manifest,parent)
    if sha(args.rom.read_bytes())!=manifest['romSha256'] or parent['setupSha256']!=sha((args.capture/'setup.state').read_bytes()):raise ValueError('Detached selected game entry ROM/setup')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    groups=[dict(name=name,version=1,points=[],interrupts=[],polls=[],writes=[]) for name in GROUPS];active=complete=False;index=0;irq=None;buttons=[]
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def fields():
        player=p.memory[0xc082];common=dict(tick=word(0xc00a),countdown=word(0xc0b7),display=p.memory[0xc098],stat=p.memory[0xc099],lcdc=p.memory[0xff40],lyc=p.memory[0xff45],pendingRequests=p.memory[0xff0f]&3,musicEnabled=p.memory[0xffcf])
        if turn:common['previousMapCamera']=word(0xff96)
        if index<2:common.update(player=player,stage=p.memory[0xc088+8*player],difficulty=p.memory[0xc089+8*player],lives=p.memory[0xc08a+8*player],interruptEnable=p.memory[0xffff]&3)
        if index>=1:common.update(cameraX=word(0xff92),cameraY=word(0xff94),mapScratch=word(0xc00c),ready=p.memory[0xffae])
        if index==1:common['reverse']=int(bool(p.memory[0xff90]))
        if index==2:common.update(randomState=word(0xc09e),hudCursor=p.memory[0xc04c],fadeRemaining=p.memory[0xffc9],inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b])
        return common
    def hook(pc):
        nonlocal active,complete,index,irq
        if complete:return
        now=p._cycles()
        if not active:
            if pc!=0x0355 or now!=parent['groups'][-1]['points'][-1]['cycles']:return
            active=True
        while pc in TABLES[index]:
            group=groups[index];name=TABLES[index][pc];group['points'].append(dict(name=name,cycles=now,**fields()))
            if pc!=(0x0367,0x039c,0x03d8)[index]:break
            if irq:raise ValueError('Selected game entry segment ended inside vector')
            if index==2:complete=True;return
            index+=1
        group=groups[index]
        if pc==0x2598 and index==0:group['polls'].append(dict(cycles=now,ly=p.register_file.A))
        if pc==0x195d and index==0:group['writes'].append(dict(cycles=now,address=p.register_file.HL,value=p.register_file.A))
        if pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested selected game entry vector')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],display=p.memory[0xc098],returnAddress=word(p.register_file.SP),tick=word(0xc00a),ready=p.memory[0xffae],phases={})
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            phase=IRQ_PHASES[pc];irq['phases'][phase]=now
            if phase=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if phase=='bookkeeping':irq.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
            if phase=='effects':irq['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if phase=='music':irq['musicEnabled']=p.memory[0xffcf]
            if phase=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:irq['end']=now;group['interrupts'].append(irq);irq=None
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for n,event in enumerate(events):
            if n==watch:
                for pc in {pc for table in TABLES for pc in table}|set(IRQ_PHASES)|{0x2598,0x195d,0x0040,0x0048,0x2484,0x2555}:p.hook_register(0,pc,hook,pc)
            replay(p,[event])
            if turn and n==len(old)-1 and memory_sha(p)!=accepted['controlMemorySha256']:raise ValueError('Turn entry observer changed its accepted instruction prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete selected game entry or changed original control')
    groups[-1]['precedingDisplays']=len((args.parent_out/'buttons.txt').read_text().splitlines())
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,inputCase=parent['inputCase'],parentInputCase=parent['parentInputCase'],players=parent['players'],groups=groups)
    if turn:
        from air_title_actions_reference import event_sha
        data.update(origin='selected-turn-entry',parentInstructionSha256=sha((args.parent_out/'instruction.json').read_bytes()),parentControlMemorySha256=accepted['controlMemorySha256'],captureEventsSha256=event_sha(events),setupSha256=sha((args.capture/'setup.state').read_bytes()))
    args.out.mkdir(parents=True,exist_ok=True)
    try:
        if turn:
            from selected_turn_reference import analyze_entry as turn_analyze
            turn_analyze(data,parent)
        else:analyze(data,parent)
    except ValueError:write_json(args.out/'entry.rejected.json',data);raise
    write_json(args.out/'entry.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons));print(dict(parent=data['parentInputCase'],case=data['inputCase'],boundaries=sum(len(g['points']) for g in groups),services=len(buttons)),flush=True)

def analyze(data,parent):
    groups=data['groups'];previous=parent['groups'][-1]['points'][-1]
    if data.get('version')!=1 or data['inputCase'] not in ('full-prompt','skip-held') or data['players'] not in (0,1) or any(data[k]!=parent[k] for k in ('romSha256','controlMemorySha256','inputCase','parentInputCase','players')) or [g['name'] for g in groups]!=list(GROUPS):raise ValueError('Detached selected game entry ancestry')
    for index,group in enumerate(groups):
        first=group['points'][0];last=group['points'][-1]
        if first['cycles']!=previous['cycles'] or any(first[k]!=previous[k] for k in ('tick','countdown')) or first['countdown']!=54:raise ValueError('Detached selected game entry counters/time')
        if index==0:
            prefix_analyze(group)
            if first['player'] or first['stage']!=1 or first['difficulty'] or first['lives']!=5 or previous['musicEnabled'] or previous['inputPressed']&~previous['inputHeld']:raise ValueError('Selected initial Air campaign differs')
        elif index==1:
            stage_analyze(group)
            if any(first[k]!=previous[k] for k in ('player','stage','difficulty','lives','lcdc','lyc','pendingRequests','display','stat','musicEnabled')):raise ValueError('Detached selected masked setup')
        else:
            entry_analyze(group)
            if any(first[k]!=previous[k] for k in ('cameraX','cameraY','mapScratch','ready','lcdc','lyc','display','stat','pendingRequests','musicEnabled')) or len([r for r in group['interrupts'] if r['kind']=='vblank'])!=2 or any(len(r.get('voiceStates',[]))!=6 for r in group['interrupts'] if r['kind']=='vblank'):raise ValueError('Detached selected scene/HUD/audio entry')
        previous=last
    return [r for r in groups[-1]['interrupts'] if r['kind']=='vblank']

def compare(args,_parent_qualified=False):
    if not _parent_qualified:
        from selected_text_reference import compare as qualify
        parent_args=argparse.Namespace(**{k:v for k,v in dict(vars(args),native_base=args.text_base).items() if k not in ('text_base','game_entry_out')})
        with contextlib.redirect_stdout(io.StringIO()):qualify(parent_args)
    from air_fourth_entry_reference import preserved_native_prefix
    from air_startup_reference import analyze as startup_epoch
    parent=read(args.selected_text_out/'text.json');data=read(args.game_entry_out/'entry.json');manifest=read(args.text_control/'capture-summary.json');require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase')):raise ValueError('Mixed selected game entry recording/control')
    services=analyze(data,parent)
    if (args.game_entry_out/'buttons.txt').read_text()!=(args.selected_text_out/'buttons.txt').read_text()+''.join(str(r['held'])+'\n' for r in services):raise ValueError('Detached selected game entry raw inputs')
    retained=preserved_native_prefix(args.native_base,args.text_base);epoch=startup_epoch(read(args.startup/'startup.json'))['epoch'];stem=str(args.native_base)+'.fifth.selected.title-game-'
    def rows(name,suffix):
        with Path(stem+name+suffix).open(newline='') as f:return list(csv.DictReader(f))
    prefix,stage,entry=data['groups'];prefix_summary=rows('prefix','.summary.csv');stage_summary=rows('stage','.summary.csv');entry_summary=rows('entry','.summary.csv')
    differences=compare_prefix(prefix,rows('prefix','.csv'),rows('prefix','.polls.csv'),rows('prefix','.writes.csv'),prefix_summary,epoch)
    differences+=compare_stage(stage,rows('stage','.csv'),stage_summary,prefix_summary,epoch)
    with Path(str(args.text_base)+'.fifth.selected.title-instruction-exit.summary.csv').open(newline='') as f:prior=next(csv.DictReader(f))
    entry=dict(entry,precedingDisplays=int(prior['displays']));differences+=compare_entry(entry,rows('entry','.csv'),rows('entry','.services.csv'),rows('entry','.interrupts.csv'),entry_summary,stage_summary,epoch)
    differences+=compare_voices(logical_voice_projection(services),rows('entry','.voices.csv'),int(prior['displays']))
    def check(kind,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(category=kind,fields=delta))
    check('prefix retained counters',dict(displays=int(prior['displays']),stats=int(prior['stats'])),prefix_summary[0])
    for name in ('prefix','stage'):
        if rows(name,'.services.csv') or rows(name,'.interrupts.csv'):raise ValueError('Masked selected game setup accepted native services')
    if rows('stage','.polls.csv') or rows('stage','.writes.csv') or rows('entry','.polls.csv') or rows('entry','.writes.csv'):raise ValueError('Unexpected selected game setup access outputs')
    check('entry summary',dict(entryPauseComplete=0),entry_summary[0])
    report=dict(parentInputCase=data['parentInputCase'],inputCase=data['inputCase'],players=data['players'],comparedBoundaries=sum(len(g['points']) for g in data['groups']),comparedServices=2,comparedVectors=4,comparedPolls=len(prefix['polls']),comparedWrites=len(prefix['writes']),comparedVoiceRows=12,preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,evidenceLimit='Selected initial Air/easy campaign from instruction exit through LCD-off clears, masked stage setup, resource/HUD work, game-music startup, pending/periodic vectors and first two displays through 03d8. Inherited scratch fields before overwrite follow existing explicit stage exclusions. Does not qualify copied scene/HUD/actor contents, subsequent gameplay, frames/PCM or production scheduler.')
    write_json(Path(str(args.native_base)+'.selected-game-entry.comparison.json'),report);print(report)
    if differences:raise ValueError('Selected game entry differs from the original')

def compare_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid selected game entry batch')
    parents=[]
    for case in cases:
        parent=argparse.Namespace(**{k:v for k,v in vars(case).items() if k not in ('text_base','game_entry_out')});parent.native_base=case.text_base;parents.append(parent)
    from selected_text_reference import compare_many as qualify
    with contextlib.redirect_stdout(io.StringIO()):qualify(parents)
    for case in cases:compare(case,_parent_qualified=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('capture');p.add_argument('rom',type=Path)
    for key in ('capture','parent-out','out'):p.add_argument('--'+key,type=Path,required=True)
    p=sub.add_parser('compare-batch');p.add_argument('manifest',type=Path);args=parser.parse_args()
    if args.mode=='capture':capture(args)
    else:compare_many([argparse.Namespace(**{k:Path(v) for k,v in c.items()}) for c in read(args.manifest)])
if __name__=='__main__':main()
