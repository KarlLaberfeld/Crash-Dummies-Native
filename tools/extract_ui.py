"""Reconstruct original menu maps without executing cartridge instructions."""
from pathlib import Path
import argparse
import json
import struct
from extract import address, read_rom, tile, title_image

TITLE_SCRIPTS=[0x29ad,0x29bb,0x2a97,0x2a1b,0x2ade,0x2750]

def menu_map(rom,script,initial=None):
    """Decode the identified static subset of the original text/layout language.

    Unknown operations fail rather than interpreting SM83 code or guessing.
    Maps use the original 32-column pitch, including offscreen rows.
    """
    result=bytearray(1024) if initial is None else bytearray(initial)
    position=0;anchor=0;row=0
    for _ in range(4096):
        op=rom[script];script+=1
        if op<128:
            if not 0<=position<1024:raise ValueError('Menu text outside map')
            result[position]=op;position+=1
        elif op==0x80:return result
        elif op==0x81:
            anchor,row=rom[script:script+2];script+=2;position=row*32+anchor
        elif op==0x82:
            script+=1 # All selected scripts target the menu/window layer.
        elif op==0x83:
            width,height,bank,pointer=struct.unpack_from('<BBBH',rom,script);script+=5
            source=address(bank,pointer) if pointer>=0x4000 else pointer
            for y in range(height):
                begin=position+y*32
                if not 0<=begin<=1024-width:raise ValueError('Menu rectangle outside map')
                result[begin:begin+width]=rom[source+y*width:source+(y+1)*width]
        elif op==0x84:
            row+=1;position=row*32+anchor
        else:raise ValueError(f'Unported menu operation {op:02x} at {script-1:04x}')
    raise ValueError('Unterminated menu script')

def high_score_rows(canvas,records):
    for index in range(8):
        name=records[index*6:index*6+3];packed=records[index*6+3:index*6+6]
        row=16+index;canvas[row*32+3]=index+2;canvas[row*32+5:row*32+8]=name
        digits=[n for b in packed for n in (b>>4,b&15)]
        first=next((i for i,n in enumerate(digits[:3]) if n),3)
        for j in range(4):canvas[row*32+10+j]=digits[j]+1 if j>=first else 0
        canvas[row*32+9+first]=0x33
        canvas[row*32+14]=0x2c
        canvas[row*32+15:row*32+17]=bytes([digits[4]+1,digits[5]+1])

def extract_ui(rom,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    atlas=b''.join(tile(rom,address(3,0x4000)+i*16) for i in range(256))
    initial=bytearray(1024)
    for x,y,w,h,pointer in [(7,0,8,4,0x5bd6),(7,4,6,10,0x5bf6)]:
        source=address(7,pointer)
        for dy in range(h):initial[(y+dy)*32+x:(y+dy)*32+x+w]=rom[source+dy*w:source+(dy+1)*w]
    maps=[menu_map(rom,p,initial) for p in TITLE_SCRIPTS]
    records=rom[0xa3:0xd3];high_score_rows(maps[2],records)
    payload=bytearray(b'TICDUI01')+atlas+title_image(rom)
    for canvas in maps:payload+=canvas
    payload+=records
    (output/'ui.dat').write_bytes(payload)
    manifest=dict(format='TICDUI01',title_pages=len(maps),page_durations=[480,480,960,480,960],high_scores=8)
    (output/'ui-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path)
    p.add_argument('--out',type=Path,default=Path('build'));args=p.parse_args()
    print(json.dumps(extract_ui(read_rom(args.rom),args.out),indent=2))
