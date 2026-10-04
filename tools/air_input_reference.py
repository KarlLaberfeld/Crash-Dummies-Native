"""Single-boundary original Air button sampling; measurements stay local.

The authorized reference emulator is used only by capture. Neither original
per-update counters nor recorded button edges drive the native clock probe.
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
    rom=read_rom(args.rom);manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['romSha256']!=hashlib.sha256(rom).hexdigest() or manifest['controlDifferences']:
        raise ValueError('Requires matching control-verified Air replay')
    if args.reference_lib:sys.path.insert(0,str(args.reference_lib.resolve()))
    if importlib.metadata.version('pyboy')!='2.7.0':raise ValueError('Requires PyBoy 2.7.0')
    from pyboy import PyBoy
    p=PyBoy(str(args.rom),window='null',sound_volume=0);p.set_emulation_speed(0)
    samples=[]
    def sample(_):
        if p.memory[0xc098]!=4:return
        samples.append(dict(service=len(samples),tick=p.memory[0xc00a]+256*p.memory[0xc00b],
            held=p.memory[0xff8a],pressed=p.memory[0xff8b]))
    try:
        with (args.capture/'setup.state').open('rb') as stream:p.load_state(stream)
        p.hook_register(0,0x2436,sample,None)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            elif e[0] in ('press','release'):getattr(p,'button_'+e[0])(e[1])
            else:raise ValueError('Unknown input replay event')
        control=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if control!=manifest['controlMemorySha256'] or not samples:raise ValueError('Changed control memory or missing input samples')
    args.out.mkdir(parents=True,exist_ok=True)
    write_json(args.out/'inputs.json',dict(version=1,romSha256=manifest['romSha256'],controlMemorySha256=control,samples=samples))
    print(json.dumps(dict(samples=len(samples),controlDifferences=0,evidenceLimit='Single source joypad-return boundary. Recorded edges are comparison targets, never native input. Physical input timing remains unverified.'),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom',type=Path);parser.add_argument('--reference-lib',type=Path)
    parser.add_argument('--capture',type=Path,default=Path('local/original-air-steer44'))
    parser.add_argument('--out',type=Path,default=Path('local/air-steer44-input-reference'))
    capture(parser.parse_args())
