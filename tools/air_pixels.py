"""Matched local Air frame comparison; no original pixels drive the port.

The original completed framebuffer is observed before the next DMA. Native
after-display publication projects the following frame. Partial visible graphics
writes and scanline changes are deliberately not certified by that projection.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image
from air_reference import write_json
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference


def selection(text):
    values=[int(s) for s in text.split(',')]
    if not values or len(set(values))!=len(values) or min(values)<1:raise ValueError('Select unique original service indices after service zero')
    return set(values)


def capture(args):
    wanted=selection(args.services);manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or hashlib.sha256(read_rom(args.rom)).hexdigest()!=manifest['romSha256']:
        raise ValueError('Requires matching control-verified original')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    player=Reference(str(args.rom),window='null',sound_volume=0);player.set_emulation_speed(0)
    args.out.mkdir(parents=True,exist_ok=True);service=0;air_seen=False;frames=[]
    def hook(_):
        nonlocal service,air_seen
        selector=player.memory[0xc098]
        if selector==4:air_seen=True
        if not air_seen or selector not in (1,4):return
        if service in wanted:
            image=player.screen.image
            if image.size!=(160,144) or any(color not in ((255,255,255),(170,170,170),(85,85,85),(0,0,0)) for _,color in image.getcolors(23041) or []):
                raise ValueError('Original framebuffer has unknown palette/geometry')
            name=f'original-{service}.png';image.save(args.out/name)
            frames.append(dict(service=service,nativePublishedService=service-1,cycles=player._cycles(),displaySelector=selector,
                image=name,imageSha256=hashlib.sha256(image.tobytes()).hexdigest(),bgp=player.memory[0xff47],
                obp0=player.memory[0xff48],obp1=player.memory[0xff49],scx=player.memory[0xff43],scy=player.memory[0xff42]))
        service+=1
    try:
        with (args.capture/'setup.state').open('rb') as stream:player.load_state(stream)
        player.hook_register(0,0x2430,hook,None)
        for event in json.loads((args.capture/'events.json').read_text()):
            if event[0]=='tick':player.tick(event[1],event[2])
            elif event[0] in ('press','release'):getattr(player,'button_'+event[0])(event[1])
            else:raise ValueError('Unknown original control event')
        control=hashlib.sha256(bytes(player.memory[0x8000:0x10000])).hexdigest()
    finally:player.stop(save=False)
    if {f['service'] for f in frames}!=wanted or control!=manifest['controlMemorySha256']:
        raise ValueError('Incomplete selected frames or changed original control')
    write_json(args.out/'frames.json',dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=control,
        frames=frames,completedServices=service,alignment='original-pre-next-DMA/native-after-prior-display'))
    print(json.dumps(dict(frames=len(frames),controlDifferences=0,selectedServices=sorted(wanted))))


def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'frames.json').read_text())
    require_capture_reference(manifest,data)
    if manifest['controlDifferences'] or any(data.get(k)!=manifest.get(k) for k in ('romSha256','controlMemorySha256')):
        raise ValueError('Mixed original frame controls')
    if data.get('version')!=1 or data.get('alignment')!='original-pre-next-DMA/native-after-prior-display' or not data.get('frames'):
        raise ValueError('Unowned frame alignment')
    results=[]
    for frame in data['frames']:
        original=Image.open(args.out/frame['image']).convert('RGB')
        if hashlib.sha256(original.tobytes()).hexdigest()!=frame['imageSha256']:raise ValueError('Changed original frame')
        native=Image.open(args.native_dir/f"native-{frame['nativePublishedService']}.pgm").convert('RGB')
        if original.size!=(160,144) or native.size!=original.size:raise ValueError('Invalid frame geometry')
        old=original.tobytes();new=native.tobytes()
        changed=[i for i in range(160*144) if old[3*i:3*i+3]!=new[3*i:3*i+3]]
        changed_set=set(changed)
        image=Image.new('RGB',original.size);image.putdata([(255,0,0) if i in changed_set else tuple(c//3 for c in old[3*i:3*i+3]) for i in range(160*144)])
        image.save(args.out/f"difference-{frame['service']}.png")
        results.append(dict(service=frame['service'],nativePublishedService=frame['nativePublishedService'],differingPixels=len(changed),
            differingRows=sorted(set(i//160 for i in changed)),firstDifference=[changed[0]%160,changed[0]//160] if changed else None))
    result=dict(comparedFrames=len(results),comparedPixels=len(results)*160*144,frames=results,
        productionPixelsAccepted=False,evidenceLimit='Selected complete original framebuffers compared with native after-display projection. This does not certify partial visible writes, scanline interrupts, fades outside selection, other scenarios or production Windows scheduling.')
    write_json(args.out/'native-comparison.json',result);print(json.dumps(result,indent=2))
    if any(r['differingPixels'] for r in results):raise ValueError('Native selected pixels differ from the original; inspect local difference images')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--services',required=True)
    check=sub.add_parser('compare');check.add_argument('--native-dir',type=Path,required=True)
    for command in (record,check):
        command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)
