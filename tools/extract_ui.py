"""Reconstruct original menu maps without executing cartridge instructions."""
from pathlib import Path
import argparse
import json
import struct
from extract import address, read_rom, tile, title_image

TITLE_SCRIPTS=[0x29ad,0x29bb,0x2a97,0x2a1b,0x2ade,0x2750]

def menu_map(rom,script,initial=None,player=0,position=0):
    """Decode the identified static subset of the original text/layout language.

    Unknown operations fail rather than interpreting SM83 code or guessing.
    Maps use the original 32-column pitch, including offscreen rows.
    """
    result=bytearray(1024) if initial is None else bytearray(initial)
    anchor=0;row=0
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
        elif op==0x8b:
            word=rom[0x22dc if player==0 else 0x22e0:0x22df if player==0 else 0x22e3]
            result[position:position+3]=word;position+=3
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

INSTRUCTIONS=[(0x5f02,61,0x06b7,0x06c5),(0x62d2,64,0x09fd,0x0a0b),
              (0x66d2,64,0x0c6d,0x0c7b),(0x6ad2,64,0x0eea,0x0ef8),
              (0x6ed2,64,0x110b,0x1119)]
# Native result dispatch mirrors explicit branches at 0797/0ac8/0d34/11ce.
RESULT_SCRIPTS=[0x0756,0x0a88,0x0d08,0x0f79,0x1190,
                0x07a9,0x0806,0x0847,0x087e,0x0ad0,0x0b0f,
                0x0d3c,0x0da1,0x0f93,0x11d6,0x1203]

def text_stream(rom,start):
    """Copy only the recognized instruction text language, never machine code."""
    p=start
    for _ in range(4096):
        op=rom[p];p+=1
        if op==0x80:return bytes(rom[start:p])
        if op<128 or op in (0x84,0x85,0x89,0x8a,0x8b,0x8c):continue
        if op==0x81:p+=2
        elif op in (0x82,0x86,0x87):p+=1
        else:raise ValueError(f'Unported instruction text operation {op:02x}')
    raise ValueError('Unterminated instruction text')

def overlay_tiles(rom,atlas,bank,pointer,start,count):
    result=bytearray(atlas)
    for i in range(count):result[(start+i)*64:(start+i+1)*64]=tile(rom,address(bank,pointer)+i*16)
    return result

def hidden_passwords(rom):
    # Explicitly identified handlers: five stage choices, four difficulties,
    # then music test. Only digit data enter the package, never code addresses.
    handlers=[0x2d2f,0x2d35,0x2d3b,0x2d41,0x2d47,0x2d4d,0x2d53,0x2d59,0x2d5f,0x2d65]
    result=bytearray()
    for index,handler in enumerate(handlers):
        pos=0x2cca+index*10
        if struct.unpack_from('<H',rom,pos+8)[0]!=handler:raise ValueError('Unknown password action')
        digits=rom[pos:pos+8]
        if len(digits)!=8 or any(n<1 or n>10 for n in digits):raise ValueError('Invalid password digits')
        result+=digits
    if rom[0x2d2e]!=255:raise ValueError('Unknown password table end')
    return result

def extract_ui(rom,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    atlas=b''.join(tile(rom,address(3,0x4000)+i*16) for i in range(256))
    initial=bytearray(1024)
    for x,y,w,h,pointer in [(7,0,8,4,0x5bd6),(7,4,6,10,0x5bf6)]:
        source=address(7,pointer)
        for dy in range(h):initial[(y+dy)*32+x:(y+dy)*32+x+w]=rom[source+dy*w:source+(dy+1)*w]
    maps=[menu_map(rom,p,initial) for p in TITLE_SCRIPTS]
    records=rom[0xa3:0xd3];high_score_rows(maps[2],records)
    payload=bytearray(b'TICDUI06')+atlas+title_image(rom)
    for canvas in maps:payload+=canvas
    payload+=records
    for gfx,count,layout,text in INSTRUCTIONS:
        payload+=overlay_tiles(rom,atlas,7,gfx,52,count)
        payload+=menu_map(rom,layout)
        stream=text_stream(rom,text)
        payload+=struct.pack('<H',len(stream))+stream
    # Header maps: player, day, difficulty. Lives are inserted at runtime.
    for player in range(2):
        for day in range(5):
            for difficulty in range(4):
                canvas=menu_map(rom,0x02cf,player=player)
                canvas=menu_map(rom,0x02f3,canvas)
                word=text_stream(rom,[0x263d,0x2643,0x2649,0x2651,0x2658][day])[:-1]
                canvas[36:36+len(word)]=word
                canvas=menu_map(rom,0x0303,canvas)
                word=text_stream(rom,[0x266d,0x2674,0x2679,0x2680][difficulty])[:-1]
                canvas[75:75+len(word)]=word
                payload+=canvas
    for gfx in (0x72d2,0x76d2,0x7ad2):payload+=overlay_tiles(rom,atlas,7,gfx,116,64)
    for index,script in enumerate(RESULT_SCRIPTS):
        canvas=menu_map(rom,script)
        # All three portrait maps use the same tile positions; selected separately.
        payload+=canvas
    for script in (0x0589,0x0548,0x0568,0x04aa,0x13b3,0x13d3,0x0493,0x065c):
        payload+=menu_map(rom,script)
    payload+=overlay_tiles(rom,atlas,6,0x6667,52,44)
    for player in range(2):payload+=menu_map(rom,0x05e9,player=player)
    # Macro expansions and final prompt remain ROM-derived local data.
    for start,length in [(0x2271,5),(0x2277,5),(0x2296,12),(0x22bb,12),(0x0332,20)]:payload+=rom[start:start+length]
    payload+=overlay_tiles(rom,atlas,3,0x5840,38,1)
    for player in range(2):
        canvas=menu_map(rom,0x322a)
        canvas[39:42]=rom[0x263d:0x2640] if player==0 else rom[0x2643:0x2646]
        payload+=menu_map(rom,0x323c,canvas,position=42)
    payload+=menu_map(rom,0x2814)+initial+rom[0x2118:0x2120]
    for script in (0x2b57,0x2c7f,0x2ca6,0x2d6c):payload+=menu_map(rom,script,initial)
    payload+=hidden_passwords(rom)
    # 1476 saves only the 20-tile HUD row, then installs these eight tiles
    # and the row at 00d3. The rest of the paused scene remains unchanged.
    pause_tiles=overlay_tiles(rom,atlas,3,0x5850,248,8)
    pause_map=menu_map(rom,0x14ad)
    for y in range(8):
        for x in range(160):payload.append(pause_tiles[pause_map[x//8]*64+y*8+x%8])
    (output/'ui.dat').write_bytes(payload)
    manifest=dict(format='TICDUI06',title_pages=len(maps),page_durations=[480,480,960,480,960],
                  high_scores=8,instructions=5,result_texts=16,ending_players=2)
    (output/'ui-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path)
    p.add_argument('--out',type=Path,default=Path('build'));args=p.parse_args()
    print(json.dumps(extract_ui(read_rom(args.rom),args.out),indent=2))
