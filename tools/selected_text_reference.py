"""Append-only selected-player instruction reveal, typing, prompt and exit evidence."""
import argparse,contextlib,csv,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_title_text_controls import attachment
from air_title_players_reference import continuation_observation_start
from air_title_entrance_reference import POINTS as ENTRANCE,STORES as FADE_STORES,analyze as entrance_analyze
from air_instruction_text_reference import POINTS as TEXT,analyze as text_analyze,compare_text
from air_title_instruction_exit_reference import POINTS as EXIT,STORES as EXIT_STORES
from air_instruction_exit_reference import analyze as exit_analyze,compare_exit
from air_title_picture_reference import voice_states,compare_voices
from password_feedback_reference import logical_voice_projection
from air_timing import IRQ_PHASES,vblank_work,elapsed_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
GROUPS=('entrance','text','instruction-exit')
TABLES=(ENTRANCE,{k:v for k,v in TEXT.items() if k!=0x0c7a},EXIT)

def instruction_observation_start(events):
    suffix=[['press','start'],['tick',4,True],['release','start'],['tick',2,True],['tick',100,True]]
    if events[-5:]!=suffix:raise ValueError('Unknown later Start observation suffix')
    return len(events)-5


def picture_parent(parent):
    group=parent['groups'][-1]
    return dict(points=group['points'],maps=group['maps'],tiles=group['tiles'])

def capture(args):
    accepted=read(args.accepted_control/'capture-summary.json');manifest=read(args.capture/'capture-summary.json');parent=read(args.parent_out/'instruction.json')
    old=read(args.accepted_control/'events.json');events=read(args.capture/'events.json');setup=sha((args.capture/'setup.state').read_bytes())
    attachment(accepted,manifest,old,events,setup);require_capture_reference(accepted,parent)
    if parent['controlMemorySha256']!=accepted['controlMemorySha256'] or parent['inputCase']!=accepted['inputCase'] or manifest['romSha256']!=sha(args.rom.read_bytes()) or (args.capture/'setup.state').read_bytes()!=(args.accepted_control/'setup.state').read_bytes():raise ValueError('Detached selected text parent/setup/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0)
    groups=[dict(name=name,points=[],interrupts=[],polls=[],writes=[],scrollWrites=[]) for name in GROUPS];active=complete=False;index=0;irq=None;buttons=[];palettes=waits=0;campaign=None;preceding=len((args.parent_out/'buttons.txt').read_text().splitlines())
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def fields():
        common=dict(tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b])
        colors=dict(bgp=p.memory[0xff47],obp0=p.memory[0xff48],obp1=p.memory[0xff49],musicEnabled=p.memory[0xffcf])
        if index==0:return dict(common,**colors,palettes=palettes,waits=waits,alternate=p.memory[0xc09d],display=p.memory[0xc098],stat=p.memory[0xc099],lcdc=p.memory[0xff40],lyc=p.memory[0xff45])
        if index==1:return dict(common,scroll=p.memory[0xc09c],speed=p.memory[0xc03a],delay=p.memory[0xc039],skipMask=p.memory[0xc03b],layer=p.memory[0xc035],column=p.register_file.C,row=p.register_file.B)
        return dict(common,**colors,scroll=p.memory[0xc09c])
    def hook(pc):
        nonlocal active,complete,index,irq,palettes,waits,campaign,preceding
        if complete:return
        now=p._cycles()
        if not active:
            if pc!=0x268b or now!=parent['groups'][-1]['points'][-1]['cycles']:return
            active=True
        while pc in TABLES[index]:
            group=groups[index];name=TABLES[index][pc]
            if name=='begin':
                group.update(beforeMaps=p.title_maps_storage(),beforeTiles=p.instruction_tiles_storage(),beforeObjects=list(p.memory[0xc100:0xc200]),precedingInputSamples=preceding)
                if index==1:
                    player=p.memory[0xc082];campaign=dict(player=player,stage=p.memory[0xc088+8*player],difficulty=p.memory[0xc089+8*player])
            if index==0:palettes+=name=='palette';waits+=name=='tail'
            point=dict(name=name,cycles=now,**fields());group['points'].append(point)
            if index==1 and name=='skip':
                pointer=p.register_file.HL;player=campaign['player'];level=campaign['difficulty']
                point['skipContext']=1 if 0x2272+6*player<=pointer<=0x2276+6*player else 2 if 0x2297+3*level<=pointer<=0x2298+3*level else 0
            if name!='end':break
            group.update(maps=p.title_maps_storage(),tiles=p.instruction_tiles_storage(),objects=list(p.memory[0xc100:0xc200]))
            if irq:raise ValueError('Selected instruction segment ended in a vector')
            if index==2:
                group['endRawActiveFlags']=sum(bool(v['active']&128) for v in voice_states(p));complete=True;return
            index+=1
        group=groups[index]
        if pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested selected text vector')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],display=p.memory[0xc098],returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            phase=IRQ_PHASES[pc];irq['phases'][phase]=now
            if phase=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a]);preceding+=1
            if phase=='bookkeeping':irq.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
            if phase=='effects':irq['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if phase=='music':irq['musicEnabled']=p.memory[0xffcf]
            if phase=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:irq['end']=now;group['interrupts'].append(irq);irq=None
        if pc==0x2123 and index:group['polls'].append(dict(cycles=now,mode=p.register_file.A&3))
        if pc==0x2128 and index:group['writes'].append(dict(cycles=now,address=256*p.register_file.D+p.register_file.E,value=p.register_file.A))
        address=(FADE_STORES if index==0 else EXIT_STORES if index==2 else {0x24a1:0xff42,0x2559:0xff42,0x222c:0xc09c}).get(pc)
        if address is not None:group['scrollWrites'].append(dict(cycle=now,address=address,value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        pcs={pc for table in TABLES for pc in table}|set(FADE_STORES)|set(EXIT_STORES)|set(IRQ_PHASES)|{0x0040,0x0048,0x2484,0x2555,0x2123,0x2128,0x222c}
        origin=parent.get('origin');watch_at=continuation_observation_start(old,parent['inputCase'],[['tick',100,True]]) if origin=='later-title-selected-start' else instruction_observation_start(old) if origin=='later-title-start' else 0
        for n,event in enumerate(events):
            if n==watch_at:
                for pc in pcs:p.hook_register(0,pc,hook,pc)
            replay(p,[event])
            if n==len(old)-1 and memory_sha(p)!=accepted['controlMemorySha256']:raise ValueError('Observed selected text changed its accepted prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete selected text or changed original control')
    data=dict(version=1,reference=metadata,storageReadOwner='direct-vram-instruction-v1',romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=accepted['controlMemorySha256'],inputCase=manifest['inputCase'],parentInputCase=parent['inputCase'],players=parent['players'],setupSha256=setup,campaign=campaign,groups=groups)
    if parent.get('origin') in ('later-title-start','later-title-selected-start'):data.update(origin=parent['origin'],targetPage=parent['targetPage'],parentInstructionSha256=sha((args.parent_out/'instruction.json').read_bytes()))
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent,len((args.parent_out/'buttons.txt').read_text().splitlines()))
    except ValueError:write_json(args.out/'text.rejected.json',data);raise
    write_json(args.out/'text.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons));print(dict(case=data['inputCase'],parent=data['parentInputCase'],boundaries=sum(len(g['points']) for g in groups),services=len(buttons)),flush=True)

def projection(data,group):
    return dict(group,version=1,precedingDisplays=group['precedingInputSamples'],reference=data['reference'],campaign=data['campaign'],storageReadOwner=data['storageReadOwner'],objectsUnchanged=group['beforeObjects']==group['objects'],writes=group['scrollWrites'] if group['name']=='entrance' else group['writes'])

def analyze(data,parent,preceding):
    if data.get('origin') not in (None,'later-title-start','later-title-selected-start'):raise ValueError('Unowned instruction text origin')
    if data.get('origin')!=parent.get('origin'):raise ValueError('Mixed instruction text origin')
    if parent.get('origin') in ('later-title-start','later-title-selected-start') and (data.get('origin')!=parent['origin'] or data.get('targetPage')!=parent.get('targetPage')):raise ValueError('Detached later instruction text origin/page')
    if data.get('version')!=1 or data['inputCase'] not in ('full-prompt','skip-held') or data['parentInputCase']!=parent['inputCase'] or data['players']!=parent['players'] or data['parentControlMemorySha256']!=parent['controlMemorySha256'] or data['campaign']!=dict(player=0,stage=1,difficulty=0) or [g['name'] for g in data['groups']]!=list(GROUPS):raise ValueError('Detached selected text ancestry/campaign')
    if data.get('storageReadOwner')!='direct-vram-instruction-v1' or data['reference'].get('instructionStorageObserver')!='direct-vram-instruction-v1':raise ValueError('Unqualified selected text storage observer')
    before=picture_parent(parent);all_services=[];previous=before['points'][-1]
    for index,group in enumerate(data['groups']):
        points=group['points'];first=points[0];end=points[-1];irqs=group['interrupts'];source=projection(data,group)
        if group['precedingInputSamples']!=preceding or first['cycles']!=previous['cycles'] or any(first[k]!=previous[k] for k in ('tick','countdown','inputHeld','inputPressed')) or group['beforeMaps']!=before['maps'] or group['beforeTiles']!=before['tiles'] or len(group['maps'])!=2048 or len(group['tiles'])!=1024 or group['tiles']!=before['tiles'] or group['objects']!=group['beforeObjects'] or group['objects']!=[0]*256:raise ValueError('Detached selected text extent/storage/counters')
        if index==0:services=entrance_analyze(source,before)
        elif index==1:
            services=text_analyze(source)
            if bool(any(p['name']=='skip' for p in points))!=(data['inputCase']=='skip-held') or first['scroll']:raise ValueError('Selected text did not take its intended full/skip branch')
            centers=[p for p in group['scrollWrites'] if p['address']==0xc09c];steps=[p for p in points if p['name']=='scrollStored']
            if len(centers)!=len(steps) or any(w['value']!=p['scroll'] or elapsed_work(w['cycle'],p['cycles'],irqs)!=8 for w,p in zip(centers,steps)):raise ValueError('Detached selected text scroll centers')
            expected=list(centers)
            for irq in irqs:
                committed=[w for w in centers if w['cycle']+8<=irq['start']];value=committed[-1]['value'] if committed else 0
                expected.append(dict(cycle=irq['start']+(1284 if irq['kind']=='vblank' else 216),address=0xff42,value=0 if irq['kind']=='vblank' else value))
            if group['scrollWrites']!=sorted(expected,key=lambda p:p['cycle']):raise ValueError('Selected text raster stores differ')
        else:
            services=exit_analyze(source)
            if first['scroll']!=previous['scroll'] or any(p['name']=='prompt' for p in points)!=(data['inputCase']=='full-prompt') or type(group.get('endRawActiveFlags')) is not int or not 0<=group['endRawActiveFlags']<=6:raise ValueError('Selected prompt/held exit differs')
            colors=[p for p in group['scrollWrites'] if p['address'] in (0xff47,0xff48,0xff49)]
            if [p['address'] for p in colors]!=[0xff47,0xff49,0xff48]*8 or any(colors[3*i+1]['value']!=colors[3*i]['value']&0xf3 or colors[3*i+2]['value']!=colors[3*i]['value']&0xcf for i in range(8)):raise ValueError('Incomplete selected exit palette stores')
            expected=colors+[dict(cycle=p['start']+(1284 if p['kind']=='vblank' else 216),address=0xff42,value=0 if p['kind']=='vblank' else first['scroll']) for p in irqs]
            if group['scrollWrites']!=sorted(expected,key=lambda p:p['cycle']):raise ValueError('Selected exit raster stores differ')
        maps=list(before['maps'])
        for w in group['writes']:maps[w['address']-0x9800]=w['value']
        if maps!=group['maps']:raise ValueError('Selected text/prompt map publication differs')
        if any(p['tick']!=(first['tick']+n)&65535 or len(p.get('voiceStates',[]))!=6 for n,p in enumerate(services)):raise ValueError('Incomplete selected text live music/counters')
        preceding+=len(services);all_services+=services;previous=end;before=group
    return all_services

def compare(args,_parent_qualified=False):
    if not _parent_qualified:
        from selected_instruction_reference import compare as qualify
        with contextlib.redirect_stdout(io.StringIO()):qualify(argparse.Namespace(**dict(vars(args),native_base=args.selected_base)))
    from air_fourth_entry_reference import preserved_native_prefix
    from air_startup_reference import analyze as startup_epoch
    parent=read(args.selected_out/'instruction.json');data=read(args.selected_text_out/'text.json');accepted=read(args.exit_control/'capture-summary.json');manifest=read(args.text_control/'capture-summary.json')
    attachment(accepted,manifest,read(args.exit_control/'events.json'),read(args.text_control/'events.json'),sha((args.text_control/'setup.state').read_bytes()));require_capture_reference(manifest,data)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase','parentControlMemorySha256','setupSha256')):raise ValueError('Mixed selected text controls/recording')
    if parent.get('origin') in ('later-title-start','later-title-selected-start') and data.get('parentInstructionSha256')!=sha((args.selected_out/'instruction.json').read_bytes()):raise ValueError('Detached later instruction text file')
    preceding=len((args.selected_out/'buttons.txt').read_text().splitlines());services=analyze(data,parent,preceding)
    if (args.selected_text_out/'buttons.txt').read_text()!=(args.selected_out/'buttons.txt').read_text()+''.join(str(p['held'])+'\n' for p in services):raise ValueError('Detached selected text raw inputs')
    retained=preserved_native_prefix(args.native_base,args.selected_base);epoch=startup_epoch(read(args.startup/'startup.json'))['epoch'];differences=[];totals=dict(boundaries=0,services=0,vectors=0,polls=0,glyphStores=0,otherStores=0,mapBytes=0,tileBytes=0,voiceRows=0)
    def rows(stem,suffix):
        with Path(stem+suffix).open(newline='') as f:return list(csv.DictReader(f))
    native_stem='.fifth.later.selected.title-' if parent.get('origin')=='later-title-selected-start' else '.fifth.later.title-' if parent.get('origin')=='later-title-start' else '.fifth.selected.title-'
    prior=rows(str(args.selected_base)+native_stem+'picture','.summary.csv')[0];stats=int(prior['stats']);lcd=int(prior['lcdEpoch'])
    # Raw input files start before the native timing owner's display index was
    # reset. The parent's independently qualified summary owns that index;
    # absolute original cycles/ticks, service counts and prefix bytes remain
    # checked. This projection never initializes native execution.
    preceding=int(prior['displays'])
    def check(kind,index,wanted,q):
        delta={k:[v,int(q[k])] for k,v in wanted.items() if int(q[k])!=v}
        if delta:differences.append(dict(category=kind,index=index,fields=delta))
    for index,group in enumerate(data['groups']):
        name=group['name'];stem=str(args.native_base)+native_stem+name;points=group['points'];irqs=group['interrupts'];displays=[p for p in irqs if p['kind']=='vblank']
        native,ns,ni,np,nw,summary,maps,tiles,voices=[rows(stem,s) for s in ('.csv','.services.csv','.interrupts.csv','.polls.csv','.writes.csv','.summary.csv','.maps.csv','.tiles.csv','.voices.csv')]
        glyphs=[p for p in nw if 0x9800<=int(p['address'])<0x9c00];other=[p for p in nw if p not in glyphs]
        if [len(native),len(ns),len(ni),len(np),len(glyphs),len(other),len(summary),len(maps),len(tiles),len(voices)]!=[len(points),len(displays),len(irqs),len(group['polls']),len(group['writes']),len(group['scrollWrites']),1,2048,1024,6*len(displays)]:raise ValueError('Incomplete selected '+name+' native outputs')
        source=projection(data,group);source['precedingDisplays']=preceding
        if index:
            found=(compare_text if index==1 else compare_exit)(source,native,ns,ni,np,glyphs,summary,epoch)
            for difference in found:difference['category']=name+' '+difference['category']
            differences+=found
        else:
            for n,(p,q) in enumerate(zip(points,native)):
                if p['name']!=q['boundary']:raise ValueError('Reordered selected reveal boundaries')
                check(name+' boundary',n,dict(cycle=p['cycles']-epoch,**{k:v for k,v in p.items() if k not in ('name','cycles')}),q)
            for n,(p,q) in enumerate(zip(displays,ns)):
                work=vblank_work(p);check(name+' service',n,dict(service=preceding+n,cycle=p['start']-epoch,tick=p['tick'],countdown=p['countdown'],display=work['display'],effects=work['effects'],music=work['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
            for n,(p,q) in enumerate(zip(irqs,ni)):
                if p['kind']!=q['kind']:raise ValueError('Reordered selected reveal vectors')
                check(name+' vector',n,dict(vectorCycle=p['start']-epoch,owner=2 if p['returnAddress']==0x261d else 1),q)
        differences+=compare_voices(logical_voice_projection(displays),voices,preceding)
        for n,(p,q) in enumerate(zip(group['scrollWrites'],other)):check(name+' store',n,dict(p,cycle=p['cycle']-epoch),q)
        for kind,values,target,base in [('map',group['maps'],maps,0x9800),('tile',group['tiles'],tiles,0x8340)]:
            for n,(value,q) in enumerate(zip(values,target)):check(name+' '+kind,n,dict(address=base+n,value=value),q)
        preceding+=len(displays);stats+=sum(p['kind']=='stat' for p in irqs);last=points[-1];end=last['cycles']-epoch
        def deadline(line):
            value=lcd+(end-lcd)//70224*70224+line*456
            return value+70224 if value<=end else value
        wanted=dict(end=end,tick=last['tick'],countdown=last['countdown'],displays=preceding,stats=stats,lcdEpoch=lcd,nextStat=deadline(95),nextVBlank=deadline(144))
        if index==0:wanted.update({k:last[k] for k in ('alternate','bgp','obp0','obp1')})
        elif index==1:wanted.update(scroll=last['scroll'],skipped=int(data['inputCase']=='skip-held'))
        else:wanted.update(scroll=last['scroll'],musicEnabled=0,activeVoices=0)
        if set(wanted)!=set(summary[0]):raise ValueError('Unqualified selected '+name+' summary fields')
        check(name+' summary',0,wanted,summary[0])
        for key,value in [('boundaries',len(points)),('services',len(ns)),('vectors',len(ni)),('polls',len(np)),('glyphStores',len(glyphs)),('otherStores',len(other)),('mapBytes',2048),('tileBytes',1024),('voiceRows',len(voices))]:totals[key]+=value
    report=dict(inputCase=data['inputCase'],parentInputCase=data['parentInputCase'],players=data['players'],**{'compared'+k[0].upper()+k[1:]:v for k,v in totals.items()},preservedNativeFiles=retained,differences=len(differences),firstDifference=differences[:1],stoppedDriverPayloadCompared=False,productionSchedulerAccepted=False,evidenceLimit='Selected one/two-player instruction reveal, complete or deliberately skipped text, prompt/fresh Start or held Start, outgoing fade/audio stop. Original append-only controls and complete prior native outputs retained. Raw parked voice flags are not logical playback. Other campaigns/gameplay, rendered frames/PCM and production scheduling remain unqualified.')
    write_json(Path(str(args.native_base)+'.selected-text.comparison.json'),report);print(report)
    if differences:raise ValueError('Selected instruction text/exit differs from the original')

def compare_later_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid later instruction text batch')
    direct=[];selected=[];seen=set()
    for case in cases:
        parent=argparse.Namespace(**{k:v for k,v in vars(case).items() if k not in ('selected_base','text_control','selected_text_out')});parent.native_base=case.selected_base
        identity=tuple(sorted((k,str(v)) for k,v in vars(parent).items()))
        if identity not in seen:(selected if getattr(parent,'later_players_out',None) else direct).append(parent);seen.add(identity)
    from selected_instruction_reference import compare_later_many as qualify_direct,compare_later_selected_many as qualify_selected
    with contextlib.redirect_stdout(io.StringIO()):
        if direct:qualify_direct(direct)
        if selected:qualify_selected(selected)
    for case in cases:compare(case,_parent_qualified=True)

def compare_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid selected text batch')
    ignored={'native_base','selected_base','text_control','selected_text_out','exit_base','players_base','players_out','players_control','exit_out','exit_control','selected_out'};common={k:v for k,v in vars(cases[0]).items() if k not in ignored}
    if any({k:v for k,v in vars(c).items() if k not in ignored}!=common for c in cases[1:]):raise ValueError('Mixed selected text ancestry')
    parents=[];seen=set()
    for case in cases:
        parent=argparse.Namespace(**{k:v for k,v in vars(case).items() if k not in ('selected_base','text_control','selected_text_out')});parent.native_base=case.selected_base
        identity=tuple(sorted((k,str(v)) for k,v in vars(parent).items()))
        if identity not in seen:parents.append(parent);seen.add(identity)
    from selected_instruction_reference import compare_many as qualify
    with contextlib.redirect_stdout(io.StringIO()):qualify(parents)
    for case in cases:compare(case,_parent_qualified=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('capture');p.add_argument('rom',type=Path)
    for key in ('capture','accepted-control','parent-out','out'):p.add_argument('--'+key,type=Path,required=True)
    for mode in ('compare-batch','compare-later-batch'):
        p=sub.add_parser(mode);p.add_argument('manifest',type=Path)
    args=parser.parse_args()
    if args.mode=='capture':capture(args)
    else:(compare_later_many if args.mode=='compare-later-batch' else compare_many)([argparse.Namespace(**{k:Path(v) for k,v in c.items()}) for c in read(args.manifest)])
if __name__=='__main__':main()
