"""Extract semantic Air/Ski startup workload metadata, never instructions/times.

All output is original-derived data and remains local. Ski's extra offscreen
band is counted for work only; its RAM template contents are not invented.
"""
import argparse,struct
from pathlib import Path
from extract import address,read_rom

def profiles(rom):
    result=[]
    for stage,table,bank,lookup,roots in ((1,0xc1f,4,0x1d78,0x608f),(2,0xe9c,5,0x1ded,0x66bc)):
        chunks=rom[address(3,roots)]
        for difficulty in range(4):
            x,second,timer,fourth,map_pointer,object_pointer=struct.unpack_from('<BBBBHH',rom,table+8*difficulty)
            pos=address(bank,map_pointer);bands=0;carries=0
            while rom[pos]!=255:
                if bands>=64:raise ValueError('Startup map exceeds its native band buffer')
                selector=rom[pos+1]
                if selector>=(31 if stage==1 else 15) and not(stage==2 and selector==31 and rom[pos]==128 and rom[pos+2]==255):
                    raise ValueError('Unrecognized startup map template')
                carries+=int((lookup&255)+2*selector>255);bands+=1;pos+=2
            pos=object_pointer;placements=0
            while rom[pos]!=255:
                if placements>=512 or not (18<=rom[pos]<=30 if stage==1 else 36<=rom[pos]<=40):raise ValueError('Invalid startup placement')
                placements+=1;pos+=5
            camera_x=(x+(0x43 if stage==1 else 0x3c))*256
            camera_y=second*256+128 if stage==1 else 0
            if timer>>4>9 or timer&15>9 or not 1<=chunks<=13:raise ValueError('Invalid startup scalar/resource')
            result.append((bands,carries,placements,chunks,camera_x,camera_y))
    return result

def extract(rom,target):
    values=profiles(rom);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(b'TICDFS01'+b''.join(struct.pack('<6H',*record) for record in values))
    return values

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('rom',type=Path);parser.add_argument('--out',type=Path,default=Path('build/following-setup.dat'))
    args=parser.parse_args();print(extract(read_rom(args.rom),args.out))
