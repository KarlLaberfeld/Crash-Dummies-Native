"""Extract identified graphics/level records; never execute ROM machine code.

Only the exact documented US/EU cartridge revision is accepted. Outputs stay
local and are intentionally excluded from source control.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct

ROM_SHA256 = 'ef563c4a4b063ea045d71b435dd078c19d0738f85079928803167cee8f34a4ec'

# Native handler IDs shared with src/game.h; these are semantic game states.
HANDLERS = {0x23e2:0,0x55da:1,0x55e7:2,0x5626:3,0x563a:4,0x56de:5,
            0x5780:6,0x59be:7,0x3bb3:8,0x5aa2:9,0x5ba5:10,0x5bce:11,
            0x5c77:12,0x5b85:13,0x5d61:14,0x5d72:15,0x5dd7:16,
            0x5ee2:17,0x5850:18,0x589c:19,0x58e8:20,0x591e:21,0x596a:22,
            0x5f40:23,0x5b57:24,0x5d33:25,0x5c20:26,0x5e88:27,0x5ebd:28,
            0x59b6:29}
ANIMATIONS = [0x560e,0x5674,0x56a9,0x56cb,0x5a27,0x5a40,0x5a61,0x5a7a,
              0x5abd,0x5b46,0x5b2c,0x5b16,0x5b93,0x5cfC,0x5ccf,0x5da9,
              0x5e45,0x5e55,0x5e58,0x57cf,0x585e,0x58aa,0x58f6,0x592c,0x5978]

def animation_records(rom):
    """Decode only the game's animation language, not SM83 instructions."""
    sizes=[1,1,2,2,2,2,1,1,2,1,3,3,2,2,1,1,6,1,1,2,3]
    records={}
    todo=list(ANIMATIONS)
    while todo:
        pos=todo.pop()
        if pos in records:continue
        op=rom[pos]-0x80
        if not 0<=op<len(sizes):raise ValueError(f'Unexpected animation command at {pos:04x}')
        n=sizes[op];a=b=c=0;next_pos=pos+n
        if n==2:a=signed(rom[pos+1]) if op in (2,3,12,13) else rom[pos+1]
        if op==10:
            a=struct.unpack_from('<H',rom,pos+1)[0];todo.append(a);next_pos=0
        elif op==11:
            a=HANDLERS[struct.unpack_from('<H',rom,pos+1)[0]];next_pos=0
        elif op==16:
            a,b,c=struct.unpack_from('<hhB',rom,pos+1)
        elif op==20:raise ValueError('Unported native animation callback')
        if op in (0,14):next_pos=0
        records[pos]=(op,a,b,c,next_pos)
        if next_pos:todo.append(next_pos)
    indices={pos:i+1 for i,pos in enumerate(sorted(records))}
    output=[]
    for pos in sorted(records):
        op,a,b,c,nxt=records[pos]
        if op==10:a=indices[a]
        output.append((op,a,b,c,indices.get(nxt,0)))
    return [indices[x] for x in ANIMATIONS],output

def read_rom(path):
    data = Path(path).read_bytes()
    if len(data) != 131072 or hashlib.sha256(data).hexdigest() != ROM_SHA256:
        raise ValueError('Unsupported cartridge. Expected the documented 128 KiB US/EU revision.')
    return data

def address(bank, addr):
    if not 0 <= bank < 8 or not (0x4000 <= addr < 0x8000):
        raise ValueError(f'Invalid banked address {bank:02x}:{addr:04x}')
    return bank * 0x4000 + addr - 0x4000

def signed(n):
    return n if n < 128 else n - 256

def tile(data, base):
    if base < 0 or base+16 > len(data):
        raise ValueError('Tile outside data')
    return bytes(((data[base+y*2] >> (7-x)) & 1) |
                 (((data[base+y*2+1] >> (7-x)) & 1) << 1)
                 for y in range(8) for x in range(8))

def roof_frames(rom):
    result=[]
    for number in range(69):
        ptr=struct.unpack_from('<H',rom,0xd95c+number*2)[0]
        pos=address(3,ptr)
        header=rom[pos:pos+8]
        pieces=[]
        pos+=8
        for _ in range(40):
            if rom[pos]==255: break
            y,x,idx,flags=rom[pos:pos+4];pos+=4
            pieces.append((signed(x),signed(y),idx,flags))
        else: raise ValueError('Unterminated sprite')
        pixels=bytearray([255])*(96*96)
        for x,y,idx,flags in pieces:
            if number<35:
                desc=0xd8d0+number*4
                _,bank,ptr=struct.unpack_from('<BBH',rom,desc)
                base=address(bank,ptr)+(idx & ~1)*16
            else:
                base=address(4,0x4610)+(idx & ~1)*16
            for py in range(16):
                sy=15-py if flags&64 else py
                row=tile(rom,base+(sy//8)*16)
                for px in range(8):
                    sx=7-px if flags&32 else px
                    value=row[(sy%8)*8+sx]
                    # 00:1cdb/1cf3 add the half extents before emitting OAM.
                    # The hardware's +8/+16 coordinate bias cancels on screen.
                    dx=x+px+48+signed(header[0])+header[6]
                    dy=y+py+48+signed(header[1])+header[7]
                    if value and 0<=dx<96 and 0<=dy<96:
                        pixels[dy*96+dx]=value
        result.append((header,pixels))
    return result

def roof_map(rom, repeats):
    # 00:0926 loads 5 rows, repeats 4 rows N times, appends 9 rows.
    start=address(4,0x5338)
    rows=[rom[start+i*10:start+(i+1)*10] for i in range(18)]
    layout=rows[:5]+rows[5:9]*repeats+rows[9:18]
    height=len(layout)*16
    pixels=bytearray(160*height)
    for my,row in enumerate(layout):
        for mx,metatile in enumerate(row):
            for quadrant in range(4):
                idx=rom[address(4,0x51b0)+quadrant*0x62+metatile]
                decoded=tile(rom,address(4,0x4000)+idx*16)
                for y in range(8):
                    dest=(my*16+(quadrant//2)*8+y)*160+mx*16+(quadrant%2)*8
                    pixels[dest:dest+8]=decoded[y*8:y*8+8]
    return height,pixels

def title_image(rom):
    # Original startup composition from 00:0217; source tiles copied by 00:01e8.
    tile_ram=bytearray(0x1800)
    tile_ram[:0x1000]=rom[0xc000:0xd000]
    tile_ram[0x1000:0x1780]=rom[0xd000:0xd780]
    image=bytearray(160*144)
    for x,y,w,h,bank,ptr in [(3,0,14,3,7,0x5a80),(0,13,20,5,7,0x5aaa),(7,0,8,4,7,0x5bd6),(7,4,6,10,7,0x5bf6)]:
        # Last two rectangles use the window map and are not visible together
        # with the background map at startup. Export background only here.
        if ptr>=0x5bd6:continue
        base=address(bank,ptr)
        for ty in range(h):
            for tx in range(w):
                idx=rom[base+ty*w+tx]
                t=tile(tile_ram,0x1000+signed(idx)*16)
                for py in range(8):
                    out=((y+ty)*8+py)*160+(x+tx)*8
                    image[out:out+8]=t[py*8:py*8+8]
    return image

def extract(rom, output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    frames=roof_frames(rom)
    payload=bytearray(b'TICDNAT2')
    payload+=title_image(rom)
    # Font is a standalone decoded tile atlas; no ROM instruction bytes.
    for i in range(52):payload+=tile(rom,0xc000+i*16)
    for header,pixels in frames:payload+=header+pixels
    manifest={'source_sha256':ROM_SHA256,'format':'TICDNAT2','roof_difficulties':[]}
    for difficulty in range(4):
        ptr,repeats,quota,timer,fire_hits=struct.unpack_from('<HBBBB',rom,0x9b1+difficulty*6)
        height,pixels=roof_map(rom,repeats)
        objects=[]
        pos=ptr
        while rom[pos]!=255:
            kind,x,y=struct.unpack_from('<BHH',rom,pos)
            objects.append((kind,x+0x1000,y));pos+=5
        payload+=struct.pack('<HHHHH',height,quota,(timer>>4)*10+(timer&15),fire_hits,len(objects))
        payload+=pixels
        for kind,x,y in objects:payload+=struct.pack('<BHH',kind,x,y)
        manifest['roof_difficulties'].append({'difficulty':difficulty,'height':height,'objects':len(objects),'table':f'01:{ptr:04x}','repeated_rows':repeats,'timer_seconds':(timer>>4)*10+(timer&15),'fire_hits':fire_hits,'remaining_objects_initial':quota})
    for kind in range(16):
        ptr=struct.unpack_from('<H',rom,0x3430+kind*2)[0]
        frame,flags,handler,collision=struct.unpack_from('<BBHB',rom,ptr)
        payload+=struct.pack('<BBBB',frame,flags,HANDLERS[handler],collision)+rom[ptr+5:ptr+12]
    starts,commands=animation_records(rom)
    payload+=struct.pack('<HH',len(starts),len(commands))
    for start in starts:payload+=struct.pack('<H',start)
    for command in commands:payload+=struct.pack('<BhhhH',*command)
    (output/'crash.dat').write_bytes(payload)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--out',type=Path,default=Path('build'))
    args=p.parse_args()
    print(json.dumps(extract(read_rom(args.rom),args.out),indent=2))
