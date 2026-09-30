"""Decode Cruise Missile's column-major map and original actor data."""
from pathlib import Path
import argparse
import json
import struct
from extract import pack_frames, address, read_rom, tile, sprite_frames, animation_records, roof_hud

HANDLERS={0x23e2:0,0x73ed:1,0x73fd:2,0x744a:3,0x75de:4,0x76f8:5,
          0x77d3:6,0x75f6:7,0x7870:8,0x77a6:9,0x77ed:10,0x7755:11,
          0x769c:12,0x7807:13,0x782d:14,0x784d:15,0x74a6:16,
          0x78ad:17,0x59b6:18,0x59be:19,0x3bb3:20}
KINDS=[49,50]+list(range(57,66))
ANIMATIONS=[0x75e7,0x77dc,0x768f,0x7879,0x77f6,0x7763,0x76ae,0x7787,0x7856,0x78b6]

def extract_cruise(rom,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    payload=bytearray(b'TICDCRU2')
    for i in range(82):payload+=tile(rom,address(7,0x4980)+i*16)
    payload+=rom[address(7,0x4180):address(7,0x4980)]
    payload+=rom[address(7,0x5940):address(7,0x5a80)]
    payload+=pack_frames(sprite_frames(rom,42,0xefd8,0xefa8,12,address(7,0x4ea0),True))
    levels=[]
    for d in range(4):
        initial,timer,pointer=struct.unpack_from('<BBH',rom,0x1315+d*4)
        objects=[]
        while rom[pointer]!=255:
            obj=struct.unpack_from('<BHH',rom,pointer);pointer+=5
            if obj[0] not in KINDS:raise ValueError('Unexpected Cruise object')
            objects.append(obj)
        seconds=(timer>>4)*10+(timer&15)
        payload+=struct.pack('<BBH',initial,seconds,len(objects))
        for obj in objects:payload+=struct.pack('<BHH',*obj)
        levels.append(dict(initial=initial,seconds=seconds,objects=len(objects)))
    for kind in KINDS:
        pointer=struct.unpack_from('<H',rom,0x3430+kind*2)[0]
        frame,flags,handler,collision=struct.unpack_from('<BBHB',rom,pointer)
        payload+=bytes([kind,frame,flags,HANDLERS[handler],collision])+rom[pointer+5:pointer+12]
    roots,commands=animation_records(rom,ANIMATIONS,HANDLERS)
    payload+=struct.pack('<HH',len(roots),len(commands))
    for root in roots:payload+=struct.pack('<H',root)
    for command in commands:payload+=struct.pack('<BhhhH',*command)
    payload+=rom[0xefa8:0xefd8:4]+rom[0x759e:0x75de]+rom[0x74bb:0x74cb]+rom[0x77c0:0x77d0]
    atlas,_,_=roof_hud(rom);atlas[0xf2*64:0xf3*64]=tile(rom,address(3,0x5800))
    payload+=atlas+rom[0x30eb:0x30ff]+bytes(rom[0x30de+i*2] for i in range(7))
    (output/'cruise.dat').write_bytes(payload)
    manifest=dict(format='TICDCRU2',frames=42,levels=levels)
    (output/'cruise-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path)
    p.add_argument('--out',type=Path,default=Path('build'));args=p.parse_args()
    print(json.dumps(extract_cruise(read_rom(args.rom),args.out),indent=2))
