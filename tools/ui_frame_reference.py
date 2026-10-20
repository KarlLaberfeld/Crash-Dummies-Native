"""Exact stable original grayscale frames versus the production native UI renderer."""
import argparse,contextlib,io
from pathlib import Path
from air_title_start_reference import read,sha,replay,memory_sha
from air_reference import write_json
from reference_backend import reference_class,require_matching_backend,require_capture_reference
WIDTH=160;HEIGHT=144;SHADES={255:0,170:1,85:2,0:3}

def logical_frame(frame):
    if frame.mode!='RGB' or frame.size!=(WIDTH,HEIGHT):raise ValueError('Unexpected original framebuffer format')
    output=bytearray();pixels=frame.tobytes()
    for offset in range(0,len(pixels),3):
        red,green,blue=pixels[offset:offset+3]
        if red!=green or red!=blue or red not in SHADES:raise ValueError('Original frame is not the pinned four-shade grayscale palette')
        output.append(SHADES[red])
    return bytes(output)

def compare_pixels(original,native):
    if len(original)!=WIDTH*HEIGHT or len(native)!=WIDTH*HEIGHT or any(v>3 for v in original+native):raise ValueError('Incomplete or invalid four-shade frame')
    changed=[index for index,(a,b) in enumerate(zip(original,native)) if a!=b]
    first=changed[0] if changed else None
    return dict(comparedPixels=WIDTH*HEIGHT,differences=len(changed),firstDifference=None if first is None else dict(x=first%WIDTH,y=first//WIDTH,original=original[first],native=native[first]))

def frame_owners(data,parent):
    if data.get('kind') not in ('instruction','title'):raise ValueError('Unknown stable frame kind')
    names=['instruction','prompt'] if data['kind']=='instruction' else ['title-1','title-2','title-3','title-4','title-0']
    if [frame['name'] for frame in data['frames']]!=names:raise ValueError('Incomplete stable frame set')
    for frame in data['frames']:
        if frame.get('frameSource')!='sameboy-direct-pixels-v1' or (frame['width'],frame['height'],frame['bgp'])!=(WIDTH,HEIGHT,228):raise ValueError('Unowned original framebuffer observation')
        if data['kind']=='instruction':
            point=parent['groups'][0]['points'][-1] if frame['name']=='instruction' else [p for p in parent['groups'][-1]['points'] if p['name']=='inputReady'][1]
            if frame['cycles']!=point['cycles'] or (frame['display'],frame['stat'],frame['lcdc'])!=(5,5,209):raise ValueError('Detached completed instruction reveal frame')
        elif frame['name']!='title-0':
            index=int(frame['name'][-1]);group=next(g for g in parent['groups'] if g['name']==str(index-1)+'.idle');point=[p for p in group['points'] if p['name']=='ready'][1]
            if frame['cycles']!=point['cycles'] or (frame['display'],frame['stat'],frame['lcdc'])!=(0,1,195):raise ValueError('Detached stable title frame')
        else:
            delta=frame['cycles']-parent['groups'][-1]['points'][-1]['cycles']
            if not 70224<delta<3*70224 or (frame['display'],frame['stat'],frame['lcdc'])!=(0,1,195):raise ValueError('Detached page-zero post-reopening stable frame')
    return names

def capture(args):
    manifest=read(args.capture/'capture-summary.json');parent=read(args.parent);require_capture_reference(manifest,parent)
    if manifest['controlDifferences'] or any(parent[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or sha(args.rom.read_bytes())!=manifest['romSha256']:raise ValueError('Detached frame controls/ROM/parent')
    instruction=args.kind=='instruction';wanted={};groups=parent['groups']
    if instruction:
        if [g['name'] for g in groups]!=['entrance','text','instruction-exit']:raise ValueError('Instruction frame needs the accepted full reveal')
        wanted[groups[0]['points'][-1]['cycles']]='instruction'
        ready=[p for p in groups[-1]['points'] if p['name']=='inputReady']
        if parent['inputCase']!='full-prompt' or len(ready)<2:raise ValueError('Instruction frame set requires complete text and a stable prompt')
        wanted[ready[1]['cycles']]='prompt'
    else:
        if [g['name'] for g in groups]!=[str(n)+suffix for n in range(5) for suffix in (('.page',) if n==4 else ('.page','.idle'))]:raise ValueError('Title frames need the complete accepted carousel')
        for group in groups:
            if group['name'].endswith('.idle'):wanted[[p for p in group['points'] if p['name']=='ready'][1]['cycles']]='title-'+str(group['page'])
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata);p=Reference(str(args.rom),window='null',sound_volume=0);frames=[];page_zero=None;ready_zero=0
    args.out.mkdir(parents=True,exist_ok=True)
    def hook(pc):
        nonlocal page_zero,ready_zero
        now=p._cycles();name=wanted.get(now) if pc in ((0x0a0a,0x25dd) if instruction else (0x270b,)) else None
        if not instruction:
            if pc==0x2707 and now==groups[-1]['points'][-1]['cycles']:page_zero=now
            if pc==0x270b and page_zero is not None and len(frames)<5:
                ready_zero+=1
                if ready_zero==2:name='title-0'
        if name is None:return
        if any(frame['name']==name for frame in frames):raise ValueError('Repeated original stable frame')
        if p.memory[0xff47]!=228 or p.memory[0xff43] or (name!='prompt' and p.memory[0xc09c]):raise ValueError('Frame does not have its qualified stable palette/scroll')
        image=p.screen.image;data=logical_frame(image);image.save(args.out/(name+'.png'));(args.out/(name+'.shades')).write_bytes(data)
        frames.append(dict(name=name,cycles=now,sha256=sha(data),width=WIDTH,height=HEIGHT,bgp=p.memory[0xff47],display=p.memory[0xc098],stat=p.memory[0xc099],lcdc=p.memory[0xff40],ly=p.memory[0xff44],frameSource='sameboy-direct-pixels-v1'))
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for pc in ((0x0a0a,0x25dd) if instruction else (0x2707,0x270b)):p.hook_register(0,pc,hook,pc)
        replay(p,read(args.capture/'events.json'));digest=memory_sha(p)
    finally:p.stop(save=False)
    expected=['instruction','prompt'] if instruction else ['title-1','title-2','title-3','title-4','title-0']
    if [frame['name'] for frame in frames]!=expected or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete original stable frames or changed observed control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,kind=args.kind,parentSha256=sha(args.parent.read_bytes()),frames=frames,productionSchedulerAccepted=False)
    write_json(args.out/'frames.json',data);print(dict(kind=args.kind,frames=len(frames),controlMatches=True),flush=True)

def compare(args,_parent_qualified=False):
    data=read(args.out/'frames.json');parent=read(args.parent);manifest=read(args.capture/'capture-summary.json');require_capture_reference(manifest,data);require_capture_reference(manifest,parent)
    if data.get('version')!=1 or any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')) or data['parentSha256']!=sha(args.parent.read_bytes()):raise ValueError('Detached frame capture/control/parent')
    frame_owners(data,parent)
    if not _parent_qualified:
        if data['kind']=='instruction':
            from selected_text_reference import compare as qualify
        else:
            from title_cycle_reference import compare as qualify
        with contextlib.redirect_stdout(io.StringIO()):qualify(args.qualification)
    reports=[]
    for frame in data['frames']:
        source=(args.out/(frame['name']+'.shades')).read_bytes()
        if sha(source)!=frame['sha256']:raise ValueError('Changed original framebuffer bytes')
        if data['kind']=='instruction':path=Path(str(args.qualification.native_base)+('.fifth.selected.title-entrance.frame.shades' if frame['name']=='instruction' else '.fifth.selected.title-instruction-exit.prompt.frame.shades'))
        else:path=Path(str(args.qualification.native_base)+'.fifth.title-cycle.'+str((int(frame['name'][-1])-1)%5)+'.page.frame.shades')
        native=path.read_bytes();reports.append(dict(name=frame['name'],sourceSha256=frame['sha256'],nativeSha256=sha(native),**compare_pixels(source,native)))
    report=dict(kind=data['kind'],frames=reports,comparedFrames=len(reports),comparedPixels=sum(p['comparedPixels'] for p in reports),differences=sum(p['differences'] for p in reports),productionSchedulerAccepted=False,evidenceLimit='Exact 160x144 stable logical-grayscale framebuffer comparison against production UiFlow::render using native-owned state. No tolerance, crop, fitting or original map/pixel inputs. Excludes transition/scanline/host-window timing, other frames, color themes, PCM and physical hardware.')
    write_json(args.out/'frames.comparison.json',report);print({k:v for k,v in report.items() if k!='frames'})
    if report['differences']:raise ValueError('Native stable UI frame differs from original pixels')

def compare_many(cases):
    if not cases or len(cases)>128:raise ValueError('Invalid stable frame batch')
    kinds=[read(case.out/'frames.json')['kind'] for case in cases]
    if any(kind not in ('instruction','title') for kind in kinds):raise ValueError('Unknown stable frame batch kind')
    for kind in ('instruction','title'):
        children=[case for case,value in zip(cases,kinds) if value==kind]
        if not children:continue
        if kind=='instruction':
            from selected_text_reference import compare_many as qualify
        else:
            from title_cycle_reference import compare_many as qualify
        with contextlib.redirect_stdout(io.StringIO()):qualify([case.qualification for case in children])
        for case in children:compare(case,_parent_qualified=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('capture');p.add_argument('rom',type=Path);p.add_argument('--kind',choices=('instruction','title'),required=True)
    p=sub.add_parser('compare');p.add_argument('--qualification',type=Path,required=True)
    for p in sub.choices.values():
        for key in ('capture','parent','out'):p.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    if args.mode=='compare':args.qualification=argparse.Namespace(**{k:Path(v) for k,v in read(args.qualification).items()})
    (capture if args.mode=='capture' else compare)(args)
if __name__=='__main__':main()
