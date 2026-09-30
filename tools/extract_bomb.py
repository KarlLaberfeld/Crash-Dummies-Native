"""Decode Bomb Factory's fixed room, actors and animation data locally."""
from pathlib import Path
import argparse
import json
import struct
from extract import address, read_rom, tile, sprite_frames, animation_records, roof_hud

HANDLERS={0x23e2:0,0x6ef2:1,0x737c:2,0x71b8:3,0x71c2:4,0x717c:5,
          0x7190:5,0x71a4:5,0x3bb3:6,0x727d:7,0x71f8:8,0x59be:9,0x59b6:10}
KINDS=[45,46,47,48,51,52,53]
ANIMATIONS=[0x704e,0x705d,0x7094,0x70ac,0x720c,0x72e6]

def extract_bomb(rom,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    payload=bytearray(b'TICDBOM1')
    for i in range(87):payload+=tile(rom,address(6,0x57e0)+i*16)
    room=rom[address(6,0x5d50):address(6,0x5d50)+7*17]
    layout=bytes(room[y*7+x%7] for y in range(17) for x in range(20))
    if max(layout)>=87:raise ValueError('Bomb room references an unloaded tile')
    payload+=layout
    for meta,pixels in sprite_frames(rom,33,0xeb3d,0xeaed,20,address(6,0x51a0)):payload+=meta+pixels
    levels=[]
    for d in range(4):
        a,b,c,quota,pointer=struct.unpack_from('<BBBBH',rom,0x10cf+d*6)
        quota=(quota>>4)*10+(quota&15)
        distribution=rom[pointer:pointer+32]
        if any(v not in [0,47,48,51,52,53] for v in distribution):raise ValueError('Invalid Bomb object distribution')
        payload+=bytes([a,b,c,quota])+distribution
        levels.append(dict(speeds=[a,b,c],quota=quota,distribution=list(distribution)))
    for kind in KINDS:
        pointer=struct.unpack_from('<H',rom,0x3430+kind*2)[0]
        frame,flags,handler,collision=struct.unpack_from('<BBHB',rom,pointer)
        payload+=bytes([kind,frame,flags,HANDLERS[handler],collision])+rom[pointer+5:pointer+12]
    roots,commands=animation_records(rom,ANIMATIONS,HANDLERS,{0x1747:0})
    payload+=struct.pack('<HH',len(roots),len(commands))
    for root in roots:payload+=struct.pack('<H',root)
    for command in commands:payload+=struct.pack('<BhhhH',*command)
    payload+=rom[0xeaed:0xeb3d:4]
    payload+=rom[0x6fad:0x6fb9]+rom[0x6fe4:0x6ff0]+rom[0x7007:0x700f]+rom[0x701e:0x7026]
    atlas,_,_=roof_hud(rom)
    payload+=atlas+rom[0x307a:0x308e]+bytes(rom[0x3071+i*2] for i in range(5))
    (output/'bomb.dat').write_bytes(payload)
    manifest=dict(format='TICDBOM1',frames=33,levels=levels)
    (output/'bomb-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path)
    p.add_argument('--out',type=Path,default=Path('build'));args=p.parse_args()
    print(json.dumps(extract_bomb(read_rom(args.rom),args.out),indent=2))
