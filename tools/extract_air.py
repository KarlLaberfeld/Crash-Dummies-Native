"""Offline Air Bumper asset reconstruction. No cartridge instructions execute."""
from pathlib import Path
import argparse
import json
import struct
from extract import address, read_rom, sprite_frames, animation_records, tile

# Semantic state IDs for the forthcoming native Air Bumper handlers.
HANDLERS={0x23e2:0,0x5fa6:1,0x5fae:2,0x5fc9:3,0x5fd6:4,0x3bb3:5,
          0x6103:6,0x61c4:7,0x6246:8,0x62a9:9,0x62f6:10,0x6336:11,
          0x59b6:12,0x59be:13,0x6622:14,0x667b:15,0x6759:16,
          0x678c:17,0x67c1:18,0x682c:19,0x6848:20,0x686e:21,
          0x6891:22,0x66d8:23,0x66f7:24,0x693b:25,0x695c:26}
ANIMATIONS=[0x622d,0x6315,0x665f,0x6684,0x6773,0x679a,0x67d6,
            0x6835,0x685d,0x68c9,0x690a,0x6944,0x6965]

def air_map(rom,pointer):
    """Expand 00:1d41's 16x4 templates, with circular X offset per band.

    The source describes 16 metatiles per row and up to 256 rows. Each
    band rotates its sixteen columns. This is data decompression, not an
    interpreter for the machine instructions implementing it.
    """
    cells=bytearray(16*256)
    pos=address(4,pointer);band=0
    while rom[pos]!=255:
        if band>=64:raise ValueError('Air map exceeds 256 rows')
        shift,template=rom[pos:pos+2];pos+=2
        if template>=31:raise ValueError('Invalid Air map template')
        ptr=struct.unpack_from('<H',rom,0x1d78+template*2)[0]
        source=address(4,ptr)
        for y in range(4):
            for x in range(16):cells[(band*4+y)*16+((x+shift)&15)]=rom[source+y*16+x]
        band+=1
    return cells,band*4

def extract_air(rom,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    payload=bytearray(b'TICDAIR1')
    for i in range(128):payload+=tile(rom,address(4,0x688c)+i*16)
    payload+=rom[address(4,0x78cc):address(4,0x78cc)+512]
    payload+=rom[address(4,0x784c):address(4,0x784c)+128]
    frames=sprite_frames(rom,59,0xe0bf,0xe08f,12,address(5,0x4000))
    for meta,pixels in frames:payload+=meta+pixels
    manifest={'format':'TICDAIR1','difficulties':[]}
    for d in range(4):
        x,y,timer,quota,map_ptr,objects_ptr=struct.unpack_from('<BBBBHH',rom,0xc1f+d*8)
        cells,rows=air_map(rom,map_ptr)
        if max(cells)>=128:raise ValueError('Air metatile outside table')
        objects=[];pos=objects_ptr
        while rom[pos]!=255:
            kind,ox,oy=struct.unpack_from('<BHH',rom,pos);pos+=5
            if not 18<=kind<=30:raise ValueError('Unexpected Air placement kind')
            objects.append((kind,ox+0x4000,oy))
        seconds=(timer>>4)*10+(timer&15)
        payload+=struct.pack('<HHBBHH',(x+0x43)*256,y*256+128,seconds,quota,rows,len(objects))
        payload+=cells
        for obj in objects:payload+=struct.pack('<BHH',*obj)
        manifest['difficulties'].append(dict(difficulty=d,rows=rows,objects=len(objects),seconds=seconds,quota=quota))
    for kind in range(17,35):
        ptr=struct.unpack_from('<H',rom,0x3430+kind*2)[0]
        frame,flags,handler,collision=struct.unpack_from('<BBHB',rom,ptr)
        payload+=struct.pack('<BBBB',frame,flags,HANDLERS[handler],collision)+rom[ptr+5:ptr+12]
    starts,commands=animation_records(rom,ANIMATIONS,HANDLERS)
    payload+=struct.pack('<HH',len(starts),len(commands))
    for start in starts:payload+=struct.pack('<H',start)
    for command in commands:payload+=struct.pack('<BhhhH',*command)
    # Five sets of six world-collision probes, speed curve, five tilt records.
    payload+=rom[0x648c:0x6504]+rom[0x6554:0x6574]+rom[0x65f8:0x660c]
    (output/'air.dat').write_bytes(payload)
    (output/'air-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom',type=Path);parser.add_argument('--out',type=Path,default=Path('build'))
    args=parser.parse_args();print(json.dumps(extract_air(read_rom(args.rom),args.out),indent=2))
