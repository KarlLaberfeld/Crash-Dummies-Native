"""Attached selected post-result map transition, typing, prompt and exit.

Reference state is comparison data only. The native continuation consumes
decoded local assets and the complete raw input stream, never these records.
"""
import argparse,contextlib,csv,io,shutil
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_title_actions_reference import event_sha
from selected_outcome_reference import TAIL as OUTCOME_TAIL
from air_instruction_text_reference import POINTS as TEXT,analyze as text_scope,compare_text
from air_instruction_exit_reference import analyze as exit_scope,compare_exit
from air_title_instruction_exit_reference import POINTS as EXIT,STORES as EXIT_STORES
from air_instruction_map_reference import analyze as map_scope,compare_map
from air_title_picture_reference import voice_states,compare_voices
from password_feedback_reference import logical_voice_projection
from air_reference import write_json
from air_timing import IRQ_PHASES,vblank_work,elapsed_work
from reference_backend import reference_class,require_matching_backend,require_capture_reference

MAP={0x268b:'begin',0x2691:'lineWait',0x2699:'objectsDisabled',0x269e:'scrollCleared',
     0x26a3:'callbacksReady',0x26a7:'enabled',0x26ab:'compareReady',0x26af:'mapJump',
     0x16c1:'mapBegin',0x16d2:'stepWait',0x16d5:'stepReady',0x16da:'mapWrite',
     0x16dc:'stepComplete',0x16e2:'mapReturn',0x0a0a:'end'}
NAMES=('map','text','exit');TABLES=(MAP,{k:v for k,v in TEXT.items() if k!=0x0c7a},EXIT)
TEXT_STORES={0x24a1:0xff42,0x2559:0xff42,0x222c:0xc09c}

CASES=('full-prompt','skip-held','scroll-held')
def tail(case):
    if case=='full-prompt':return [['tick',1200,True],['press','start'],['tick',4,True],['release','start'],['tick',80,True]]
    if case=='skip-held':return [['tick',16,True],['press','start'],['tick',60,True],['release','start'],['tick',80,True]]
    if case=='scroll-held':return [['press','start'],['tick',1200,True],['release','start'],['tick',80,True]]
    raise ValueError('Unknown following instruction control case')

def attachment(parent,child,old,events,setup):
    if events!=old+tail(child['inputCase']) or child['parentControlMemorySha256']!=parent['controlMemorySha256'] or child['parentEventsSha256']!=event_sha(old) or child['setupSha256']!=setup or child['romSha256']!=parent['romSha256']:raise ValueError('Detached append-only following instruction control')
    if child['controlDifferences'] or child['prefixControlHashes']!=[parent['controlMemorySha256']]*2 or child['unhookedControlHashes']!=[child['controlMemorySha256']]*2:raise ValueError('Following instruction controls lack repeated unobserved prefix/full fingerprints')

def prepare(args):
    parent=read(args.capture/'capture-summary.json');events=read(args.capture/'events.json');setup=sha((args.capture/'setup.state').read_bytes())
    if parent['controlDifferences'] or sha(args.rom.read_bytes())!=parent['romSha256'] or events[-len(OUTCOME_TAIL):]!=OUTCOME_TAIL:raise ValueError('Changed following instruction parent/ROM/input suffix')
    Reference,metadata=reference_class('sameboy');require_matching_backend(parent,metadata)
    chosen=(args.case,) if getattr(args,'case',None) else CASES[:2]
    for case in chosen:
        prefixes=[];hashes=[]
        for _ in range(2):
            p=Reference(str(args.rom),window='null',sound_volume=0)
            try:
                with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
                replay(p,events);prefixes.append(memory_sha(p));replay(p,tail(case));hashes.append(memory_sha(p))
            finally:p.stop(save=False)
        child=dict(**metadata,inputCase=case,romSha256=parent['romSha256'],parentControlMemorySha256=parent['controlMemorySha256'],parentEventsSha256=event_sha(events),setupSha256=setup,controlMemorySha256=hashes[0],controlDifferences=[],prefixControlHashes=prefixes,unhookedControlHashes=hashes,referenceOnly=True)
        attachment(parent,child,events,events+tail(case),setup);folder=args.out/case;folder.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.capture/'setup.state',folder/'setup.state');write_json(folder/'capture-summary.json',child);write_json(folder/'events.json',events+tail(case));print(case,'two original prefix/full hashes match',flush=True)

def controls(args):
    accepted=read(args.accepted_control/'capture-summary.json');manifest=read(args.capture/'capture-summary.json')
    old=read(args.accepted_control/'events.json');events=read(args.capture/'events.json');setup=sha((args.capture/'setup.state').read_bytes())
    attachment(accepted,manifest,old,events,setup)
    if old[-len(OUTCOME_TAIL):]!=OUTCOME_TAIL or (args.capture/'setup.state').read_bytes()!=(args.accepted_control/'setup.state').read_bytes():raise ValueError('Detached following instruction control/setup')
    return accepted,manifest,old,events,setup

def capture(args):
    accepted,manifest,old,events,setup=controls(args);parent=read(args.parent_out/'outcome.json');require_capture_reference(accepted,parent)
    if parent.get('origin')!='selected-initial-outcome' or parent['controlMemorySha256']!=accepted['controlMemorySha256'] or parent['inputCase']!=accepted['inputCase'] or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Changed selected outcome parent/ROM')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0)
    groups=[dict(name=name,version=1,points=[],interrupts=[],polls=[],writes=[],scrollWrites=[]) for name in NAMES]
    index=0;active=complete=False;irq=None;buttons=[];raw=len((args.parent_out/'buttons.txt').read_text().splitlines());campaign=None
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def current_campaign():
        player=p.memory[0xc082]
        return dict(player=player,stage=p.memory[0xc088+8*player],difficulty=p.memory[0xc089+8*player],lives0=p.memory[0xc08a],lives1=p.memory[0xc092],result=p.memory[0xc095])
    def storage():return dict(maps=p.title_maps_storage(),tiles=p.instruction_tiles_storage(),objects=list(p.memory[0xc100:0xc200]))
    def fields():
        common=dict(tick=word(0xc00a),countdown=word(0xc0b7),inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b])
        if index==0:return dict(common,lcdc=p.memory[0xff40],lyc=p.memory[0xff45],scroll=p.memory[0xc09c],alternate=p.memory[0xc09d],display=p.memory[0xc098],stat=p.memory[0xc099])
        if index==1:return dict(common,scroll=p.memory[0xc09c],speed=p.memory[0xc03a],delay=p.memory[0xc039],skipMask=p.memory[0xc03b],layer=p.memory[0xc035],column=p.register_file.C,row=p.register_file.B)
        return dict(common,scroll=p.memory[0xc09c],bgp=p.memory[0xff47],obp0=p.memory[0xff48],obp1=p.memory[0xff49],musicEnabled=p.memory[0xffcf])
    def hook(pc):
        nonlocal active,complete,index,irq,campaign
        if complete:return
        now=p._cycles()
        if not active:
            if pc!=0x268b or now!=parent['groups'][-1]['points'][-1]['cycles']:return
            active=True;campaign=current_campaign()
        while pc in TABLES[index]:
            group=groups[index];name=TABLES[index][pc]
            if not group['points']:
                group.update(before=storage(),campaignBefore=current_campaign(),rawPrecedingInputSamples=raw+len(buttons))
            point=dict(name=name,cycles=now,**fields());group['points'].append(point)
            if index==1 and name=='skip':
                pointer=p.register_file.HL;player=campaign['player'];level=campaign['difficulty']
                point['skipContext']=1 if 0x2272+6*player<=pointer<=0x2276+6*player else 2 if 0x2297+3*level<=pointer<=0x2298+3*level else 0
            if name!='end':break
            if irq:raise ValueError('Following instruction ended a segment inside an interrupt')
            group.update(after=storage(),campaignAfter=current_campaign())
            if index==2:group['endRawActiveFlags']=sum(bool(v['active']&128) for v in voice_states(p));complete=True;return
            index+=1
        group=groups[index]
        if pc in (0x0040,0x0048):
            if irq:raise ValueError('Nested following instruction vector')
            irq=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],display=p.memory[0xc098],returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
        elif pc in IRQ_PHASES and irq and irq['kind']=='vblank':
            phase=IRQ_PHASES[pc];irq['phases'][phase]=now
            if phase=='display':irq.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b]);buttons.append(p.memory[0xff8a])
            if phase=='bookkeeping':irq.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
            if phase=='effects':irq['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if phase=='music':irq['musicEnabled']=p.memory[0xffcf]
            if phase=='restore':irq['voiceStates']=voice_states(p)
        elif pc in (0x2484,0x2555) and irq:
            if irq['kind']!=('vblank' if pc==0x2484 else 'stat'):raise ValueError('Mismatched following instruction vector')
            irq['end']=now;group['interrupts'].append(irq);irq=None
        if index==0 and pc==0x2627:group['polls'].append(dict(cycles=now,ly=p.register_file.A))
        if index:
            if pc==0x2123:group['polls'].append(dict(cycles=now,mode=p.register_file.A&3))
            if pc==0x2128:group['writes'].append(dict(cycles=now,address=p.register_file.D*256+p.register_file.E,value=p.register_file.A))
            address=(TEXT_STORES if index==1 else EXIT_STORES).get(pc)
            if address is not None:group['scrollWrites'].append(dict(cycle=now,address=address,value=p.register_file.A))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        pcs={pc for table in TABLES for pc in table}|set(IRQ_PHASES)|set(TEXT_STORES)|set(EXIT_STORES)|{0x0040,0x0048,0x2484,0x2555,0x2627,0x2123,0x2128}
        for n,event in enumerate(events):
            if n==len(old)-len(OUTCOME_TAIL):
                for pc in pcs:p.hook_register(0,pc,hook,pc)
            replay(p,[event])
            if n==len(old)-1 and memory_sha(p)!=accepted['controlMemorySha256']:raise ValueError('Following instruction observer changed accepted outcome prefix')
        digest=memory_sha(p)
    finally:p.stop(save=False)
    if not complete or irq or digest!=manifest['controlMemorySha256']:
        args.out.mkdir(parents=True,exist_ok=True)
        write_json(args.out/'instruction.incomplete.json',dict(accepted=False,active=active,complete=complete,index=index,groups=groups,openedInterrupt=irq,observedControlMemorySha256=digest,expectedControlMemorySha256=manifest['controlMemorySha256']))
        raise ValueError('Incomplete following instruction or changed source control')
    data=dict(version=1,origin='selected-following-instruction',reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,parentControlMemorySha256=accepted['controlMemorySha256'],setupSha256=setup,inputCase=manifest['inputCase'],parentInputCase=parent['inputCase'],players=parent['players'],campaign=campaign,parentOutcomeSha256=sha((args.parent_out/'outcome.json').read_bytes()),groups=groups,storageReadOwner='direct-vram-instruction-v1')
    args.out.mkdir(parents=True,exist_ok=True)
    try:analyze(data,parent,raw)
    except (ValueError,KeyError):write_json(args.out/'instruction.rejected.json',data);raise
    write_json(args.out/'instruction.json',data);(args.out/'buttons.txt').write_text((args.parent_out/'buttons.txt').read_text()+''.join(str(b)+'\n' for b in buttons))
    print(dict(case=data['inputCase'],parent=data['parentInputCase'],player=campaign['player'],boundaries=sum(len(g['points']) for g in groups),services=len(buttons)),flush=True)

def projected(data,group,preceding):
    # The shared map validator's followingResult flag owns inherited scroll
    # before 2699..269e clears it. This is an actual post-result continuation,
    # not a retry relabeling or an initial-instruction callback.
    return dict(group,followingResult=True,precedingDisplays=preceding,reference=data['reference'],campaign=data['campaign'])

def attachment_scope(data,parent,raw):
    groups=data['groups'];player=1 if parent['players'] else 0
    wanted=dict(player=player,stage=1,difficulty=0,lives0=4,lives1=5 if player else 0,result=0)
    if data.get('version')!=1 or data.get('origin')!='selected-following-instruction' or parent.get('origin')!='selected-initial-outcome' or data['inputCase'] not in CASES or data['parentInputCase']!=parent['inputCase'] or data['players']!=parent['players'] or data['parentControlMemorySha256']!=parent['controlMemorySha256'] or data['romSha256']!=parent['romSha256'] or data['campaign']!=wanted or [g['name'] for g in groups]!=list(NAMES):raise ValueError('Detached following instruction ancestry/campaign')
    if data.get('storageReadOwner')!='direct-vram-instruction-v1' or data['reference'].get('instructionStorageObserver')!='direct-vram-instruction-v1':raise ValueError('Unqualified following instruction storage observer')
    previous=parent['groups'][-1]['points'][-1];storage=None
    for index,g in enumerate(groups):
        first=g['points'][0]
        if g['campaignBefore']!=wanted or g['campaignAfter']!=wanted or g['rawPrecedingInputSamples']!=raw or first['cycles']!=previous['cycles'] or any(first[k]!=previous[k] for k in ('tick','countdown','inputHeld','inputPressed')):raise ValueError('Following instruction lost actual time/input/lives/turn')
        before,after=g['before'],g['after']
        if storage is not None and before!=storage:raise ValueError('Following instruction storage does not inherit its actual parent')
        if len(before['maps'])!=2048 or len(after['maps'])!=2048 or len(before['tiles'])!=1024 or after['tiles']!=before['tiles'] or before['objects']!=[0]*256 or after['objects']!=before['objects']:raise ValueError('Following instruction graphics extent/objects/tiles changed')
        maps=list(before['maps'])
        for w in g['writes']:
            if not 0x9800<=w['address']<0x9c00:raise ValueError('Instruction glyph store is outside owned background')
            maps[w['address']-0x9800]=w['value']
        if maps!=after['maps']:raise ValueError('Following instruction map stores do not explain its publication')
        previous=g['points'][-1];storage=after;raw+=sum(r['kind']=='vblank' for r in g['interrupts'])
    if bool(any(p['name']=='skip' for p in groups[1]['points']))!=(data['inputCase']=='skip-held') or bool(any(p['name']=='prompt' for p in groups[2]['points']))!=(data['inputCase']=='full-prompt'):raise ValueError('Following instruction did not take its intended text/prompt branch')
    if data['inputCase']=='scroll-held':
        text=groups[1];edges=[r for r in text['interrupts'] if r.get('pressed',0)&8]
        if player!=1 or data['parentInputCase']!='full-prompt' or len(edges)!=1 or not any(a['name']=='scrollWait' and b['name']=='scrollReady' and a['cycles']<edges[0]['start']<b['cycles'] for a,b in zip(text['points'],text['points'][1:])) or not groups[2]['points'][0]['inputHeld']&8:raise ValueError('Ignored Start requires its actual second-player scroll wait and held exit')
    if groups[1]['points'][0]['scroll'] or groups[2]['points'][0]['scroll']!=groups[1]['points'][-1]['scroll'] or type(groups[2].get('endRawActiveFlags')) is not int or not 0<=groups[2]['endRawActiveFlags']<=6:raise ValueError('Following instruction text/exit scroll or audio endpoint is unowned')

def analyze(data,parent,raw):
    attachment_scope(data,parent,raw);preceding=0;services=[]
    for i,g in enumerate(data['groups']):
        found=(map_scope,text_scope,exit_scope)[i](projected(data,g,preceding));services+=found;preceding+=len(found)
        first=g['points'][0]
        if any(r['tick']!=(first['tick']+n)&65535 or len(r.get('voiceStates',[]))!=6 for n,r in enumerate(found)):raise ValueError('Following instruction lacks exact counter/music coverage')
        if i:
            colors=[w for w in g['scrollWrites'] if w['address'] in (0xff47,0xff48,0xff49)]
            centers=[w for w in g['scrollWrites'] if w['address']==0xc09c]
            if i==1:
                steps=[p for p in g['points'] if p['name']=='scrollStored']
                if colors or len(centers)!=len(steps) or any(w['value']!=p['scroll'] or elapsed_work(w['cycle'],p['cycles'],g['interrupts'])!=8 for w,p in zip(centers,steps)):raise ValueError('Following text scroll stores are detached')
            elif centers or [w['address'] for w in colors]!=[0xff47,0xff49,0xff48]*8 or any(colors[3*n+1]['value']!=colors[3*n]['value']&0xf3 or colors[3*n+2]['value']!=colors[3*n]['value']&0xcf for n in range(8)):raise ValueError('Following exit palette stores are incomplete')
            expected=colors+centers
            for r in g['interrupts']:
                committed=[w for w in centers if w['cycle']+8<=r['start']]
                scroll=committed[-1]['value'] if committed else first['scroll']
                expected.append(dict(cycle=r['start']+(1284 if r['kind']=='vblank' else 216),address=0xff42,value=0 if r['kind']=='vblank' else scroll))
            if g['scrollWrites']!=sorted(expected,key=lambda w:w['cycle']):raise ValueError('Following instruction raster stores differ')
    return services

def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def compare(args,_parent_qualified=False):
    from selected_outcome_reference import compare as qualify
    from air_fourth_entry_reference import preserved_native_prefix
    from air_startup_reference import analyze as startup
    if not _parent_qualified:
        cases=[c for c in read(args.parent_manifest) if Path(c['native_base'])==args.parent_base and Path(c['capture'])==args.accepted_control and Path(c['out'])==args.parent_out and Path(c['startup'])==args.startup]
        if len(cases)!=1:raise ValueError('Following instruction lacks explicit outcome qualification')
        parent_args=argparse.Namespace(**{k:Path(v) for k,v in cases[0].items() if k!='rom'})
        parent_args.parent_manifest=args.terminal_manifest
        with contextlib.redirect_stdout(io.StringIO()):qualify(parent_args)
    accepted,manifest,_,_,setup=controls(args);parent=read(args.parent_out/'outcome.json');data=read(args.out/'instruction.json')
    require_capture_reference(manifest,data);require_capture_reference(accepted,parent)
    origin=read(args.startup/'startup.json');require_capture_reference(manifest,origin)
    if any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256','inputCase','parentControlMemorySha256')) or data['setupSha256']!=setup or data['parentOutcomeSha256']!=sha((args.parent_out/'outcome.json').read_bytes()) or parent['controlMemorySha256']!=accepted['controlMemorySha256'] or origin['romSha256']!=data['romSha256']:raise ValueError('Changed following instruction controls/recordings')
    raw=len((args.parent_out/'buttons.txt').read_text().splitlines());services=analyze(data,parent,raw)
    if (args.out/'buttons.txt').read_text()!=(args.parent_out/'buttons.txt').read_text()+''.join(str(r['held'])+'\n' for r in services):raise ValueError('Detached complete following instruction input prefix')
    retained=preserved_native_prefix(args.native_base,args.parent_base);epoch=startup(origin)['epoch'];diff=[]
    root=str(args.native_base)+'.fifth.selected.selected-next-'
    prior=rows(Path(str(args.parent_base)+'.fifth.selected.selected-next-picture.summary.csv'))[0]
    preceding=int(prior['displays']);stats=int(prior['stats']);lcd=int(prior['lcdEpoch']);totals=dict(boundaries=0,services=0,vectors=0,polls=0,glyphStores=0,otherStores=0,mapBytes=0,tileBytes=0,voiceRows=0)
    def check(kind,n,wanted,actual):
        delta={k:[v,int(actual[k])] for k,v in wanted.items() if int(actual[k])!=v}
        if delta:diff.append(dict(category=kind,index=n,fields=delta))
    for i,g in enumerate(data['groups']):
        stem=root+g['name'];points,ns,ni,np,nw,summary,maps,tiles,voices=[rows(Path(stem+s)) for s in ('.csv','.services.csv','.interrupts.csv','.polls.csv','.writes.csv','.summary.csv','.maps.csv','.tiles.csv','.voices.csv')]
        glyphs=[w for w in nw if 0x9800<=int(w['address'])<0x9c00];other=[w for w in nw if not 0x9800<=int(w['address'])<0x9c00]
        source=projected(data,g,preceding);vbs=[r for r in g['interrupts'] if r['kind']=='vblank']
        if [len(glyphs),len(other),len(maps),len(tiles),len(voices)]!=[len(g['writes']),len(g['scrollWrites']),1024,1024,6*len(vbs)]:raise ValueError('Incomplete native following instruction storage/voices')
        found=compare_map(source,points,ns,ni,np,summary,epoch) if i==0 else (compare_text if i==1 else compare_exit)(source,points,ns,ni,np,glyphs,summary,epoch)
        diff += [dict(component=g['name'],**d) for d in found]
        diff+=compare_voices(logical_voice_projection(vbs),voices,preceding)
        for n,(w,q) in enumerate(zip(g['scrollWrites'],other)):check(g['name']+' store',n,dict(w,cycle=w['cycle']-epoch),q)
        for name,wanted,target,address in (('map',g['after']['maps'][:1024],maps,0x9800),('tile',g['after']['tiles'],tiles,0x8340)):
            for n,(v,q) in enumerate(zip(wanted,target)):check(g['name']+' '+name,n,dict(address=address+n,value=v),q)
        preceding+=len(vbs);stats+=len(g['interrupts'])-len(vbs);end=g['points'][-1];relative=end['cycles']-epoch
        def deadline(line):
            d=lcd+(relative-lcd)//70224*70224+line*456
            return d+70224 if d<=relative else d
        wanted=dict(end=relative,tick=end['tick'],countdown=end['countdown'],displays=preceding,stats=stats,lcdEpoch=lcd,nextStat=deadline(95),nextVBlank=deadline(144),player=data['campaign']['player'],lives0=4,lives1=data['campaign']['lives1'],scroll=end['scroll'])
        if i<2:wanted.update(result=0,stage=1,difficulty=0,skipped=int(i==1 and data['inputCase']=='skip-held'))
        else:wanted.update(musicEnabled=0,activeVoices=0)
        if set(wanted)!=set(summary[0]):raise ValueError('Unqualified following instruction summary fields')
        check(g['name']+' summary',0,wanted,summary[0])
        for key,n in [('boundaries',len(points)),('services',len(ns)),('vectors',len(ni)),('polls',len(np)),('glyphStores',len(glyphs)),('otherStores',len(other)),('mapBytes',len(maps)),('tileBytes',len(tiles)),('voiceRows',len(voices))]:totals[key]+=n
    report=dict(**totals,inputCase=data['inputCase'],parentInputCase=data['parentInputCase'],players=data['players'],preservedNativeFiles=retained,differences=len(diff),firstDifference=diff[:1],productionSchedulerAccepted=False,evidenceLimit='Attached selected post-failure map transition, actual player substitution, full/late-skip text or ignored Start during scroll, prompt/held exit, palettes/raster stores, owned background/tile bytes and logical voices. Excludes native window-map parity, final frames/PCM, following gameplay and production scheduling.')
    write_json(Path(str(args.native_base)+'.selected-following-instruction.comparison.json'),report);print(report,flush=True)
    if diff:raise ValueError('Selected following instruction differs from original')

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    for mode in ('prepare','capture','compare'):
        p=sub.add_parser(mode)
        if mode!='compare':p.add_argument('rom',type=Path)
        if mode=='prepare':p.add_argument('--case',choices=CASES)
        keys=('capture','out')+(('accepted-control','parent-out') if mode!='prepare' else ())+(('native-base','parent-base','parent-manifest','terminal-manifest','startup') if mode=='compare' else ())
        for key in keys:p.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();globals()[args.mode](args)
if __name__=='__main__':main()
