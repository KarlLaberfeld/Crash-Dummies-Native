"""Local original sprite-publication capture. A separate measurement tool only.

One boundary hook avoids interference from interrupt-enable/wait hooks. Original
sprite records stay local; failed final-control verification discards the capture.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

from air_reference import write_json
from extract import read_rom


def capture(args):
    rom=read_rom(args.rom)
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or manifest['romSha256']!=hashlib.sha256(rom).hexdigest():
        raise ValueError('Requires matching verified control capture')
    if args.reference_lib:sys.path.insert(0,str(args.reference_lib.resolve()))
    if importlib.metadata.version('pyboy')!='2.7.0':raise ValueError('Requires PyBoy 2.7.0')
    from pyboy import PyBoy
    p=PyBoy(str(args.rom),window='null',sound_volume=0);p.set_emulation_speed(0)
    rows=[]
    def hook(_):
        if p.memory[0xc098]==4:rows.append(dict(kind='vblank',cycles=p._cycles(),oam=list(p.memory[0xc100:0xc1a0])))
    try:
        with (args.capture/'setup.state').open('rb') as stream:p.load_state(stream)
        p.hook_register(0,0x2430,hook,None)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            elif e[0] in ('press','release'):getattr(p,'button_'+e[0])(e[1])
            else:raise ValueError('Unknown replay event')
        control=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if control!=manifest['controlMemorySha256'] or not rows:raise ValueError('Changed sprite-capture control memory or empty capture')
    args.out.mkdir(parents=True,exist_ok=True)
    write_json(args.out/'sprites.json',dict(version=1,romSha256=manifest['romSha256'],controlMemorySha256=control,
        emulator='PyBoy 2.7.0',hook='00:2430',interrupts=rows))
    print(json.dumps(dict(displayServices=len(rows),controlMemorySha256=control,pixelsCompared=False)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('rom',type=Path)
    parser.add_argument('--reference-lib',type=Path);parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    capture(parser.parse_args())
