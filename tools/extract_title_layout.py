"""Decode only the static title rectangle/layout data, never CPU instructions."""
import argparse,struct
from pathlib import Path
from extract import address,read_rom


def title_layout(rom,start=0x0218):
    commands=[];cursor=start;anchor=None
    for _ in range(128):
        if cursor>=len(rom):raise ValueError('Truncated title layout')
        op=rom[cursor];cursor+=1
        if op==0x80:
            commands.append((3,0,0,0,0,b''));return commands
        if op==0x82:
            if cursor>=len(rom) or rom[cursor]>1:raise ValueError('Invalid title layer')
            commands.append((0,rom[cursor],0,0,0,b''));cursor+=1
        elif op==0x81:
            if cursor+2>len(rom) or max(rom[cursor:cursor+2])>31:raise ValueError('Invalid title anchor')
            anchor=tuple(rom[cursor:cursor+2])
            commands.append((1,*rom[cursor:cursor+2],0,0,b''));cursor+=2
        elif op==0x83:
            if cursor+5>len(rom):raise ValueError('Truncated title rectangle')
            width,height,bank,pointer=struct.unpack_from('<BBBH',rom,cursor);cursor+=5
            if not 1<=width<=32 or not 1<=height<=32 or not 1<=bank<=7 or not 0x4000<=pointer<0x8000 or pointer+width*height>0x8000:raise ValueError('Invalid title rectangle')
            if anchor is None or anchor[0]+width>32 or anchor[1]+height>32:raise ValueError('Title rectangle outside map')
            source=address(bank,pointer);cells=rom[source:source+width*height]
            if len(cells)!=width*height:raise ValueError('Truncated title rectangle cells')
            commands.append((2,0,0,width,height,bytes(cells)))
        else:raise ValueError('Unsupported static title operation')
    raise ValueError('Unterminated title layout')


def pack(commands):
    return b'CDNTL001'+struct.pack('<H',len(commands))+b''.join(bytes(c[:5])+c[5] for c in commands)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--out',type=Path,default=Path('build/title-layout.dat'));a=p.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_bytes(pack(title_layout(read_rom(a.rom))))
    print('Decoded static title layout to',a.out)
