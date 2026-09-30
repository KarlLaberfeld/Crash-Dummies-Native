"""Reconstruct Ski Slope graphics and data without executing cartridge code."""
from pathlib import Path
import argparse
import json
import struct
from extract import address, read_rom, tile, sprite_frames, animation_records, roof_hud
from extract_air import template_map

HANDLERS={0x23e2:0,0x697d:1,0x6986:2,0x69fa:3,0x6a6d:4,0x3bb3:5,
          0x6d66:6,0x6dbe:7,0x6ddb:8,0x6e60:9,0x6e9c:10,0x59be:11,0x59b6:12}
ANIMATIONS=[0x6b69,0x6b7b,0x6b9f,0x6ba5,0x6c66,0x6cdf,0x6d57,0x6d74,
            0x6dc7,0x6de4,0x6e21]

def extract_ski(rom,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    payload=bytearray(b'TICDSKI1')
    for i in range(127):payload+=tile(rom,address(5,0x67e0)+i*16)
    payload+=bytes(64) # Tile 127 is not loaded or referenced by Ski's metatiles.
    quadrants=rom[address(5,0x7390):address(5,0x7490)]
    if max(quadrants)>=127:raise ValueError('Ski metatile references an unloaded tile')
    payload+=quadrants+rom[address(5,0x7490):address(5,0x7510)]
    for meta,pixels in sprite_frames(rom,39,0xe6f0,0xe6bc,13,address(5,0x6220)):payload+=meta+pixels
    manifest={'format':'TICDSKI1','difficulties':[]}
    for d in range(4):
        x,quota,timer,rows,map_ptr,object_ptr=struct.unpack_from('<BBBBHH',rom,0xe9c+d*8)
        # The final (0x80,0x1f) pair references RAM at d5c5, outside the declared
        # map height and below the clamped viewport. Do not invent its contents.
        cells,expanded_rows=template_map(rom,map_ptr,5,0x1ded,15,max_rows=rows)
        if expanded_rows!=rows:raise ValueError('Ski map height mismatch')
        if max(cells)>=64:raise ValueError('Ski metatile outside table')
        objects=[];pos=object_ptr
        while rom[pos]!=255:
            kind,ox,oy=struct.unpack_from('<BHH',rom,pos);pos+=5
            if not 36<=kind<=40:raise ValueError('Unexpected Ski object kind')
            objects.append((kind,(ox+0x4000)&65535,oy))
        seconds=(timer>>4)*10+(timer&15)
        payload+=struct.pack('<HBBHH',(x+0x3c)*256,seconds,quota,rows,len(objects))+cells
        for obj in objects:payload+=struct.pack('<BHH',*obj)
        manifest['difficulties'].append(dict(difficulty=d,rows=rows,expanded_rows=expanded_rows,objects=len(objects),seconds=seconds,flags=quota))
    for kind in range(35,45):
        ptr=struct.unpack_from('<H',rom,0x3430+kind*2)[0]
        frame,flags,handler,collision=struct.unpack_from('<BBHB',rom,ptr)
        payload+=struct.pack('<BBBB',frame,flags,HANDLERS[handler],collision)+rom[ptr+5:ptr+12]
    roots,commands=animation_records(rom,ANIMATIONS,HANDLERS)
    payload+=struct.pack('<HH',len(roots),len(commands))
    for root in roots:payload+=struct.pack('<H',root)
    for c in commands:payload+=struct.pack('<BhhhH',*c)
    payload+=rom[0x6bf8:0x6c02]+rom[0x6a64:0x6a6d]+rom[0x6ada:0x6ade]+rom[0xe6bc:0xe6f0:4]
    atlas,_,_=roof_hud(rom)
    atlas[0xf2*64:0xf3*64]=tile(rom,address(3,0x5800))
    payload+=atlas+rom[0x3013:0x3027]+bytes(rom[0x3006+i*2] for i in range(7))
    (output/'ski.dat').write_bytes(payload)
    (output/'ski-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path);p.add_argument('--out',type=Path,default=Path('build'))
    args=p.parse_args();print(json.dumps(extract_ski(read_rom(args.rom),args.out),indent=2))
